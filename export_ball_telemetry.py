import csv
import json
from pathlib import Path

JSON_PATH = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)
OUTPUT_PATH = Path("ball_telemetry.csv")

with JSON_PATH.open("r", encoding="utf-8") as f:
    replay = json.load(f)

# channel -> stato corrente della palla (il channel può cambiare
# dopo ogni gol, quando la palla viene chiusa e riaperta).
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
            # Se la palla è ferma (Sleeping) non c'è velocità: la azzeriamo.
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
print(f"Channel palla usati: {sorted({r['channel'] for r in rows})}")
print(f"Aggiornamenti di tocco (HitTeamNum): {sum(r['is_hit_update'] for r in rows)}")
print(f"File: {OUTPUT_PATH}")