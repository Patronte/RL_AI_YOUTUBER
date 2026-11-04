
import json
from pathlib import Path
from collections import defaultdict

path = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

with path.open("r", encoding="utf-8") as f:
    replay = json.load(f)

cars = {}
stats = defaultdict(lambda: {
    "updates": 0,
    "physics": 0,
    "position": 0,
    "velocity": 0
})

for frame_number, frame in enumerate(replay["Frames"]):

    for update in frame.get("ActorUpdates", []):

        channel = update.get("ChannelId")
        state = update.get("State")

        if state == "Close":
            cars.pop(channel, None)
            continue

        if state == "Open":
            if update.get("ObjectName") != "TAGame.Car_TA":
                continue

            cars[channel] = {
                "data": {}
            }

        if channel not in cars:
            continue

        if update.get("ObjectName") == "TAGame.Car_TA":
            cars[channel]["data"].update(
                update.get("ActorData", {})
            )

        data = update.get("ActorData", {})

        pri = cars[channel]["data"].get(
            "PlayerReplicationInfo", {}
        ).get("TargetIndex", -1)

        s = stats[pri]
        s["updates"] += 1

        rb = data.get("ReplicatedRBState")

        if isinstance(rb, dict):
            s["physics"] += 1

            if isinstance(rb.get("Position"), dict):
                s["position"] += 1

            if isinstance(rb.get("LinearVelocity"), dict):
                s["velocity"] += 1

print("\n========== PHYSICS UPDATES PER PLAYER ==========")

for pri, s in sorted(stats.items()):
    print(f"\nPRI: {pri}")
    for key, value in s.items():
        print(f"{key}: {value}")
