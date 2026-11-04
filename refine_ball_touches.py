import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description="Riffinisce i tocchi della palla.")
parser.add_argument(
    "--json_path", 
    type=str, 
    default=str(Path("parsed") / "rocketrp_test" / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"),
    help="Percorso al file JSON del match da analizzare."
)
args = parser.parse_args()

JSON_PATH = Path(args.json_path)
print(f"🎯 Raffinamento tocchi basato su: {JSON_PATH}")

WINDOW_BEFORE = 8
WINDOW_AFTER = 3
MAX_TOUCH_DISTANCE = 300

with JSON_PATH.open("r", encoding="utf-8") as f:
    replay = json.load(f)

players = replay["Properties"]["PlayerStats"]
name_team = {p["Name"]: p["Team"] for p in players}

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

ball = pd.read_csv("ball_telemetry.csv")
cars = pd.read_csv("car_telemetry.csv")
cars = cars[cars["pri"] != -1].copy()

frames_all = np.arange(cars["frame"].min(), cars["frame"].max() + 1)
car_pos = {}
for pri, p in cars.sort_values(["pri", "frame"]).groupby("pri"):
    p = p.drop_duplicates("frame", keep="last").set_index("frame")
    car_pos[pri] = p[["x", "y", "z"]].reindex(frames_all).ffill()

phys = ball[ball["is_physics_update"]].drop_duplicates(
    "frame", keep="last"
).set_index("frame")
phys = phys.dropna(subset=["vx", "vy", "vz"]).copy()
phys["dv"] = np.sqrt(
    phys["vx"].diff() ** 2
    + phys["vy"].diff() ** 2
    + phys["vz"].diff() ** 2
)

hits = ball[ball["is_hit_update"]]

rows = []
for _, h in hits.iterrows():
    f = int(h["frame"])
    hit_team = h["hit_team"]

    window = phys.loc[f - WINDOW_BEFORE : f + WINDOW_AFTER]
    if window.empty or window["dv"].isna().all():
        impact_frame, dv = f, np.nan
    else:
        impact_frame = int(window["dv"].idxmax())
        dv = window["dv"].max()

    bx, by, bz = (
        phys.loc[impact_frame, ["x", "y", "z"]]
        if impact_frame in phys.index
        else (h["x"], h["y"], h["z"])
    )

    dists = {}
    for pri, p in car_pos.items():
        if impact_frame not in p.index or p.loc[impact_frame].isna().any():
            continue
        c = p.loc[impact_frame]
        dists[pri] = float(
            np.sqrt((c["x"] - bx) ** 2 + (c["y"] - by) ** 2 + (c["z"] - bz) ** 2)
        )

    team_dists = {p: d for p, d in dists.items() if pri_team.get(p) == hit_team}
    if not team_dists:
        continue

    toucher = min(team_dists, key=team_dists.get)
    other = min(
        (d for p, d in dists.items() if pri_team.get(p) != hit_team),
        default=np.nan,
    )

    rows.append(
        {
            "hit_frame": f,
            "impact_frame": impact_frame,
            "dv": round(dv, 1) if not np.isnan(dv) else None,
            "team": int(hit_team),
            "player": pri_names.get(toucher),
            "dist": round(team_dists[toucher], 1),
            "opponent_dist": round(other, 1),
            "reliable": team_dists[toucher] <= MAX_TOUCH_DISTANCE,
        }
    )

res = pd.DataFrame(rows)

print("\n========== TOCCHI ATTRIBUITI ==========")
print(f"Tocchi totali: {len(res)}")
res.to_csv("ball_touches.csv", index=False)
print("\nFile creato: ball_touches.csv")
print("========== COMPLETATO ==========")