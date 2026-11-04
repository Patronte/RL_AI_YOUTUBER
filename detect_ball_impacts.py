import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description="Rileva gli impatti sulla palla.")
parser.add_argument(
    "--json_path", 
    type=str, 
    default=str(Path("parsed") / "rocketrp_test" / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"),
    help="Percorso al file JSON del match da analizzare."
)
args = parser.parse_args()

JSON_PATH = Path(args.json_path)
print(f"💥 Analisi impatti palla basata su: {JSON_PATH}")

GRAVITY_Z = -650.0          
MIN_VELOCITY_CHANGE = 150.0 
MAX_CAR_DISTANCE = 250.0    
MAX_FRAME_GAP = 3           
MERGE_FRAMES = 4            
HIT_LAG_FRAMES = 45         

with JSON_PATH.open("r", encoding="utf-8") as f:
    replay = json.load(f)

name_team = {p["Name"]: p["Team"] for p in replay["Properties"]["PlayerStats"]}

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

phys = (
    ball[ball["is_physics_update"]]
    .drop_duplicates("frame", keep="last")
    .dropna(subset=["vx", "vy", "vz"])
    .sort_values("frame")
    .reset_index(drop=True)
)

same_ball = phys["channel"] == phys["channel"].shift()
dt = phys["time"].diff()
exp_vz = phys["vz"].shift() + GRAVITY_Z * dt
change = np.sqrt(
    (phys["vx"] - phys["vx"].shift()) ** 2
    + (phys["vy"] - phys["vy"].shift()) ** 2
    + (phys["vz"] - exp_vz) ** 2
)
phys["change"] = change.where(
    same_ball & ((phys["frame"] - phys["frame"].shift()) <= MAX_FRAME_GAP)
)

candidates = phys[phys["change"] > MIN_VELOCITY_CHANGE]

impacts = []
for _, row in candidates.iterrows():
    f = int(row["frame"])
    dists = {}
    for pri, p in car_pos.items():
        if f not in p.index or p.loc[f].isna().any():
            continue
        c = p.loc[f]
        dists[pri] = float(
            np.sqrt(
                (c["x"] - row["x"]) ** 2
                + (c["y"] - row["y"]) ** 2
                + (c["z"] - row["z"]) ** 2
            )
        )
    if not dists:
        continue
    pri = min(dists, key=dists.get)
    if dists[pri] > MAX_CAR_DISTANCE:
        continue  
    impacts.append(
        {
            "frame": f,
            "time": row["time"],
            "pri": pri,
            "player": pri_names.get(pri),
            "team": pri_team.get(pri),
            "distance": round(dists[pri], 1),
            "velocity_change": round(row["change"], 1),
            "ball_speed_after": round(
                float(np.sqrt(row["vx"] ** 2 + row["vy"] ** 2 + row["vz"] ** 2)), 1
            ),
            "x": row["x"], "y": row["y"], "z": row["z"],
        }
    )

imp = pd.DataFrame(impacts)

merged = []
for _, r in imp.iterrows():
    if (
        merged
        and merged[-1]["pri"] == r["pri"]
        and r["frame"] - merged[-1]["last_frame"] <= MERGE_FRAMES
    ):
        merged[-1]["last_frame"] = r["frame"]
        if r["velocity_change"] > merged[-1]["velocity_change"]:
            merged[-1].update(r.to_dict() | {"first_frame": merged[-1]["first_frame"],
                                              "last_frame": r["frame"]})
        continue
    d = r.to_dict()
    d["first_frame"] = d["last_frame"] = int(r["frame"])
    merged.append(d)
imp = pd.DataFrame(merged)

hits = ball[ball["is_hit_update"]][["frame", "hit_team"]].reset_index(drop=True)
checks = []
for _, r in imp.iterrows():
    later = hits[(hits["frame"] >= r["first_frame"]) &
                 (hits["frame"] <= r["last_frame"] + HIT_LAG_FRAMES)]
    if later.empty:
        checks.append(None)
    else:
        checks.append(bool(later.iloc[0]["hit_team"] == r["team"]))
imp["hit_team_check"] = checks

print("\n========== IMPATTI RILEVATI ==========")
print(f"Impatti (dopo unione): {len(imp)}")
imp.to_csv("ball_impacts.csv", index=False)
print("\nFile creato: ball_impacts.csv")
print("========== COMPLETATO ==========")