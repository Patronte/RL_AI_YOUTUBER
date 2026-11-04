
import json
from pathlib import Path

json_path = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Manteniamo l'ultimo stato degli attori.
actors = {}

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):

        channel = actor.get("ChannelId")
        state = actor.get("State")

        if state == "Close":
            actors.pop(channel, None)
            continue

        if state == "Open":
            actors[channel] = {
                "name": actor.get("Name"),
                "object": actor.get("ObjectName"),
                "data": {}
            }

        if channel in actors:
            actors[channel]["data"].update(
                actor.get("ActorData", {})
            )

# Indicizza gli attori in base al Channel ID.
print("\n========== CAR → PLAYER ==========")

for channel, actor in actors.items():

    if actor["object"] != "TAGame.Car_TA":
        continue

    pri = actor["data"].get(
        "PlayerReplicationInfo", {}
    )

    pri_target = pri.get("TargetIndex")

    print(
        f"\nCar Channel: {channel}"
        f"\nCar Name: {actor['name']}"
        f"\nPRI TargetIndex: {pri_target}"
    )

    # Cerca gli attori PRI.
    for pri_channel, pri_actor in actors.items():

        if pri_actor["object"] != "TAGame.PRI_TA":
            continue

        # Mostriamo i dati per individuare
        # il collegamento corretto.
        print(
            f"  PRI Channel: {pri_channel}"
            f"\n  PRI Name: {pri_actor['name']}"
            f"\n  PRI Data: {pri_actor['data']}"
        )
