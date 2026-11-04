import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description="Verifica gli eventi e la telemetria della palla.")
parser.add_argument(
    "--json_path", 
    type=str, 
    default=str(Path("parsed") / "rocketrp_test" / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"),
    help="Percorso al file JSON del match da analizzare."
)
args = parser.parse_args()

JSON_PATH = Path(args.json_path)
print(f"🔍 Verifica eventi palla basata su: {JSON_PATH}")

with JSON_PATH.open("r", encoding="utf-8") as f:
    replay = json.load(f)

props = replay["Properties"]
goals = props["Goals"]
timeline = replay["TimelineKeyframes"]

ball = pd.read_csv("ball_telemetry.csv")
cars = pd.read_csv("car_telemetry.csv")
cars = cars[cars["pri"] != -1].copy()

# ---------------------------------------------------------------
# Mappa PRI -> nome giocatore (dagli attori TAGame.PRI_TA).
# ---------------------------------------------------------------
actors = {}
pri_names = {}

for frame in replay["Frames"]:
    for u in frame.get("ActorUpdates", []):
        ch = u.get("ChannelId")
        state = u.get("State")
        if state == "Close":
            actors.pop(ch, None)
            continue
        if state == "Open":
            actors[ch] = u.get("ObjectName")
        if actors.get(ch) == "TAGame.PRI_TA":
            name = (u.get("ActorData") or {}).get("PlayerName")
            if name:
                pri_names[ch] = name

name_team = {p["Name"]: p["Team"] for p in props["PlayerStats"]}
pri_team = {pri: name_team.get(n) for pri, n in pri_names.items()}

print("\n========== PRI -> GIOCATORE ==========")
for pri in sorted(pri_names):
    print(f"PRI {pri}: {pri_names[pri]} (team {pri_team[pri]})")

# ---------------------------------------------------------------
# CONTROLLO 1: gol vs cambio di channel della palla.
# ---------------------------------------------------------------
print("\n========== CONTROLLO 1: GOL vs CAMBIO PALLA ==========")

first_frame_of_channel = (
    ball.groupby("channel")["frame"].min().sort_values()
)
new_ball_frames = list(first_frame_of_channel.iloc[1:])

for g in sorted(goals, key=lambda x: x["frame"]):
    later = [f for f in new_ball_frames if f >= g["frame"]]
    nxt = later[0] if later else None
    delta = (nxt - g["frame"]) if nxt is not None else None
    print(
        f"Gol frame {g['frame']:>5} ({g['PlayerName']}, team {g['PlayerTeam']})"
        f" -> nuova palla al frame {nxt} (+{delta})"
    )

# ---------------------------------------------------------------
# CONTROLLO 2: chi tocca la palla (HitTeamNum).
# ---------------------------------------------------------------
print("\n========== CONTROLLO 2: TOCCHI ==========")

hits = ball[ball["is_hit_update"]].copy()

cars = cars.sort_values(["pri", "frame"])
frames_all = np.arange(cars["frame"].min(), cars["frame"].max() + 1)
pos = {}
for pri, p in cars.groupby("pri"):
    p = p.drop_duplicates("frame", keep="last").set_index("frame")
    p = p[["x", "y", "z"]].reindex(frames_all).ffill()
    pos[pri] = p

results = []
for _, h in hits.iterrows():
    f = int(h["frame"])
    best_pri, best_dist = None, None
    for pri, p in pos.items():
        if f not in p.index or p.loc[f].isna().any():
            continue
        d = np.sqrt(
            (p.loc[f, "x"] - h["x"]) ** 2
            + (p.loc[f, "y"] - h["y"]) ** 2
            + (p.loc[f, "z"] - h["z"]) ** 2
        )
        if best_dist is None or d < best_dist:
            best_pri, best_dist = pri, d
    team_ok = (
        pri_team.get(best_pri) == h["hit_team"]
        if best_pri is not None
        else None
    )
    results.append(
        {
            "frame": f,
            "hit_team": h["hit_team"],
            "pri_vicino": best_pri,
            "team_vicino": pri_team.get(best_pri),
            "distanza": round(best_dist, 1) if best_dist is not None else None,
            "team_coincide": team_ok,
        }
    )

res = pd.DataFrame(results)
print(f"Tocchi analizzati: {len(res)}")
print(f"Team coincidente col più vicino: {int(res['team_coincide'].sum())}")
print(f"Distanza mediana: {res['distanza'].median()}")
print(f"Distanza massima: {res['distanza'].max()}")

# ---------------------------------------------------------------
# CONTROLLO 3: eventi TimelineKeyframes vs posizione palla.
# ---------------------------------------------------------------
print("\n========== CONTROLLO 3: TIMELINE vs POSIZIONE PALLA ==========")

ball_by_frame = ball.drop_duplicates("frame", keep="last").set_index("frame")

for ev in timeline:
    f = ev["frame"]
    nearby = ball_by_frame.loc[
        (ball_by_frame.index >= f - 5) & (ball_by_frame.index <= f + 60)
    ]
    if nearby.empty:
        print(f"{ev['Type']:<10} frame {f}: nessun dato palla")
        continue
    y_max = nearby["y"].abs().max()
    print(
        f"{ev['Type']:<10} frame {f:>5}: |Y| massimo palla nei 60 frame"
        f" successivi = {y_max:.0f}"
    )

print("\n========== COMPLETATO ==========")