import argparse
import csv
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Esporta la telemetria della palla dal JSON del replay.")
parser.add_argument(
    "--json_path", 
    type=str, 
    default=str(Path("parsed") / "rocketrp_test" / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"),
    help="Percorso al file JSON del match da analizzare."
)
args = parser.parse_args()

JSON_PATH = Path(args.json_path)
OUTPUT_PATH = Path("ball_telemetry.csv")

print(f"⚽ Lettura file JSON per telemetria palla: {JSON_PATH}")

with JSON_PATH.open("r", encoding="utf-8") as f:
    replay = json.load(f)

balls = {}
rows = []

for frame_number, frame in enumerate(replay["Frames"]):
    frame_time = frame.get("Time")

    for update in frame.get("ActorUpdates", []):
        channel = update.get("ChannelId")
        state = update.get("State")
        obj = update.get("ObjectName")

        if state == "Close":
            balls.pop(channel, None)
            continue

        if state == "Open" and obj == "TAGame.Ball_TA":
            initial = update.get("InitialPosition") or {}
            balls[channel] = {
                "x": initial.get("X"),
                "y": initial.get("Y"),
                "z": initial.get("Z"),
                "vx": None, "vy": None, "vz": None,
                "hit_team": None,
            }

        if channel not in balls:
            continue

        ball = balls[channel]
        data = update.get("ActorData") or {}

        rb = data.get("ReplicatedRBState")
        if isinstance(rb, dict):
            pos = rb.get("Position") or {}
            vel = rb.get("LinearVelocity") or {}
            ball["x"] = pos.get("X", ball["x"])
            ball["y"] = pos.get("Y", ball["y"])
            ball["z"] = pos.get("Z", ball["z"])
            ball["vx"] = vel.get("X", 0 if rb.get("Sleeping") else ball["vx"])
            ball["vy"] = vel.get("Y", 0 if rb.get("Sleeping") else ball["vy"])
            ball["vz"] = vel.get("Z", 0 if rb.get("Sleeping") else ball["vz"])

        if "HitTeamNum" in data:
            ball["hit_team"] = data["HitTeamNum"]

        rows.append({
            "frame": frame_number,
            "time": frame_time,
            "channel": channel,
            "x": ball["x"], "y": ball["y"], "z": ball["z"],
            "vx": ball["vx"], "vy": ball["vy"], "vz": ball["vz"],
            "hit_team": ball["hit_team"],
            "is_physics_update": isinstance(rb, dict),
            "is_hit_update": "HitTeamNum" in data,
        })

with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Esportate {len(rows)} righe.")
print(f"File: {OUTPUT_PATH}")