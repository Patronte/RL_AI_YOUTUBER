import json
from pathlib import Path

import numpy as np
import pandas as pd

JSON_PATH = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

# --- SOGLIE E PARAMETRI DI FILTRAGGIO HIGHLIGHTS ---
MAX_CAR_DISTANCE = 300.0   # distanza massima auto-palla per un tocco
HIT_LAG_FRAMES = 45        # finestra per cercare HitTeamNum dopo l'impatto
GOAL_LINE_Y = 5120.0       # linea di porta
GOAL_HALF_WIDTH = 893.0    # semi-larghezza della porta

# Soglie restrittive per tiri ed eventi salienti:
SHOT_MARGIN = 150.0        # Tolleranza laterale più stretta (solo tiri nello specchio)
SHOT_MIN_SPEED = 1400.0    # Velocità minima aumentata per prendere solo tiri potenti
ASSIST_MAX_FRAMES = 300    # Un assist deve precedere il gol di al massimo ~14 s
SAVE_WINDOW_FRAMES = 90    # Finestra per attribuire una parata

with JSON_PATH.open("r", encoding="utf-8") as f:
    replay = json.load(f)

props = replay["Properties"]
name_team = {p["Name"]: p["Team"] for p in props["PlayerStats"]}

# --- PRI -> nome ------------------------------------------------
actors, pri_names = {}, {}
for frame in replay["Frames"]:
    for u in frame.get("ActorUpdates", []):
        ch, state = u.get("ChannelId"), u.get("State")
        if state == "Close":
            actors.pop(ch, None)
            continue
        if state == "Open":
            actors[ch] = u.get("ObjectName")
        if actors.get(ch) == "TAGame.PRI_TA":
            n = (u.get("ActorData") or {}).get("PlayerName")
            if n:
                pri_names[ch] = n
pri_team = {pri: name_team.get(n) for pri, n in pri_names.items()}

# --- Dati di telemetria ----------------------------------------
ball = pd.read_csv("ball_telemetry.csv")
cars = pd.read_csv("car_telemetry.csv")
cars = cars[cars["pri"] != -1].copy()
impacts = pd.read_csv("ball_impacts.csv")

frames_all = np.arange(cars["frame"].min(), cars["frame"].max() + 1)
car_pos = {}
for pri, p in cars.sort_values(["pri", "frame"]).groupby("pri"):
    p = p.drop_duplicates("frame", keep="last").set_index("frame")
    car_pos[pri] = p[["x", "y", "z"]].reindex(frames_all).ffill()

phys = (
    ball[ball["is_physics_update"]]
    .drop_duplicates("frame", keep="last")
    .set_index("frame")
)
hits = ball[ball["is_hit_update"]][["frame", "hit_team"]]

# --- 1. TOCCHI ---------------------------------------------------
touches = []
for _, r in impacts.iterrows():
    f = int(r["frame"])
    bx, by, bz = r["x"], r["y"], r["z"]

    dists = {}
    for pri, p in car_pos.items():
        if f in p.index and not p.loc[f].isna().any():
            c = p.loc[f]
            dists[pri] = float(
                np.sqrt((c["x"] - bx) ** 2 + (c["y"] - by) ** 2 + (c["z"] - bz) ** 2)
            )
    close = {p: d for p, d in dists.items() if d <= MAX_CAR_DISTANCE}
    if not close:
        continue

    later = hits[
        (hits["frame"] >= r["first_frame"])
        & (hits["frame"] <= r["last_frame"] + HIT_LAG_FRAMES)
    ]
    hit_team = later.iloc[0]["hit_team"] if not later.empty else None

    if hit_team is None:
        pri = min(close, key=close.get)
        status = "non_verificato"
    else:
        same_team = {p: d for p, d in close.items() if pri_team.get(p) == hit_team}
        if same_team:
            pri = min(same_team, key=same_team.get)
            nearest = min(close, key=close.get)
            status = "confermato" if pri == nearest else "contrasto_risolto"
        else:
            pri = min(close, key=close.get)
            status = "incerto"

    row = phys.loc[f] if f in phys.index else None
    vx, vy, vz = (
        (row["vx"], row["vy"], row["vz"]) if row is not None else (np.nan,) * 3
    )
    touches.append(
        {
            "frame": f,
            "time": r["time"],
            "type": "touch",
            "pri": pri,
            "player": pri_names.get(pri),
            "team": pri_team.get(pri),
            "distance": round(close[pri], 1),
            "status": status,
            "bx": bx, "by": by, "bz": bz,
            "vx": vx, "vy": vy, "vz": vz,
        }
    )

touches = pd.DataFrame(touches)

# --- 2. TIRI RESTRITTIVI (SOLO EVENTI SIGNIFICATIVI) ------------
def is_shot(t):
    if t["status"] == "incerto" or np.isnan(t["vy"]):
        return False
    target_y = GOAL_LINE_Y if t["team"] == 0 else -GOAL_LINE_Y
    toward = (t["vy"] > 0) if t["team"] == 0 else (t["vy"] < 0)
    speed = np.sqrt(t["vx"] ** 2 + t["vy"] ** 2 + t["vz"] ** 2)
    
    # Filtro velocità minima e traiettoria
    if not toward or speed < SHOT_MIN_SPEED:
        return False
    secs = (target_y - t["by"]) / t["vy"]
    if secs <= 0 or secs > 5: # Ridotto a massimo 5 secondi prima di arrivare in porta
        return False
    x_at_goal = t["bx"] + t["vx"] * secs
    return abs(x_at_goal) <= GOAL_HALF_WIDTH + SHOT_MARGIN

touches["is_shot"] = touches.apply(is_shot, axis=1)

# --- 3. GOL, ASSIST, PARATE E HIGHLIGHTS ------------------------
events = []
goals = sorted(props["Goals"], key=lambda g: g["frame"])
frame_time = {i: fr.get("Time") for i, fr in enumerate(replay["Frames"])}

assists_found = {}
for g in goals:
    gf = g["frame"]
    events.append(
        {
            "frame": gf,
            "time": frame_time.get(gf),
            "type": "goal",
            "player": g["PlayerName"],
            "team": g["PlayerTeam"],
            "status": "da_replay",
            "is_highlight": True
        }
    )
    # Assist: ultimo tocco di un compagno prima del gol
    before = touches[(touches["frame"] <= gf)
                     & (touches["frame"] >= gf - ASSIST_MAX_FRAMES)]
    before = before[before["status"] != "incerto"].sort_values("frame")
    scorer_touches = before[before["player"] == g["PlayerName"]]
    if scorer_touches.empty:
        continue
    last_scorer_frame = scorer_touches.iloc[-1]["frame"]
    prev = before[before["frame"] < last_scorer_frame]
    if prev.empty:
        continue
    p = prev.iloc[-1]
    if p["team"] == g["PlayerTeam"] and p["player"] != g["PlayerName"]:
        assists_found[p["player"]] = assists_found.get(p["player"], 0) + 1
        events.append(
            {
                "frame": int(p["frame"]),
                "time": p["time"],
                "type": "assist",
                "player": p["player"],
                "team": p["team"],
                "status": "stimato",
                "is_highlight": True
            }
        )

# Parate
saves_found = {}
for t in replay["TimelineKeyframes"]:
    if "Save" not in t["Type"]:
        continue
    team = 0 if t["Type"].startswith("Team0") else 1
    f = t["frame"]
    cand = touches[
        (touches["team"] == team)
        & (touches["frame"] >= f)
        & (touches["frame"] <= f + SAVE_WINDOW_FRAMES)
    ]
    player = cand.iloc[0]["player"] if not cand.empty else None
    saves_found[player] = saves_found.get(player, 0) + 1
    events.append(
        {
            "frame": f,
            "time": frame_time.get(f),
            "type": "save",
            "player": player,
            "team": team,
            "status": "stimato" if player else "giocatore_ignoto",
            "is_highlight": True
        }
    )

# Tiri qualificati come Highlights
shots = touches[touches["is_shot"]]
for _, s in shots.iterrows():
    events.append(
        {
            "frame": int(s["frame"]),
            "time": s["time"],
            "type": "shot",
            "player": s["player"],
            "team": s["team"],
            "status": "stimato",
            "is_highlight": True
        }
    )

# Tocchi ordinari (salvati per telemetria ma marcati is_highlight = False)
for _, t in touches.iterrows():
    if not t["is_shot"]:
        events.append(
            {
                "frame": int(t["frame"]),
                "time": t["time"],
                "type": "touch",
                "player": t["player"],
                "team": t["team"],
                "status": t["status"],
                "is_highlight": False
            }
        )

ev = pd.DataFrame(events).sort_values(["frame", "type"]).reset_index(drop=True)
ev.to_csv("match_events.csv", index=False)

# --- CREAZIONE FILE RESTRITTIVO SOLO PER HIGHLIGHTS ---
highlights_only = ev[ev["is_highlight"] == True].copy()
highlights_only.to_csv("highlight_events.csv", index=False)

print("\n========== RESOCONTO EVENTI ==========")
print(f"Totale eventi registrati: {len(ev)}")
print(f"Totale HIGHLIGHTS (Gol, Parate, Assist, Tiri forti): {len(highlights_only)}")

print("\nFile creati:")
print(" - match_events.csv (Tutti gli eventi per le statistiche)")
print(" - highlight_events.csv (Solo gli highlights salienti da montare)")
print("========== COMPLETATO ==========")