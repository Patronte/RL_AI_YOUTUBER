import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Ispeziona le associazioni auto-giocatore.")
parser.add_argument(
    "--json_path", 
    type=str, 
    default=str(Path("parsed") / "rocketrp_test" / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"),
    help="Percorso al file JSON del match da analizzare."
)
args = parser.parse_args()
json_path = Path(args.json_path)

with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

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

print("\n========== CAR → PLAYER ==========")

for channel, actor in actors.items():
    if actor["object"] != "TAGame.Car_TA":
        continue

    pri = actor["data"].get("PlayerReplicationInfo", {})
    pri_target = pri.get("TargetIndex")

    print(
        f"\nCar Channel: {channel}"
        f"\nCar Name: {actor['name']}"
        f"\nPRI TargetIndex: {pri_target}"
    )

    for pri_channel, pri_actor in actors.items():
        if pri_actor["object"] != "TAGame.PRI_TA":
            continue
        print(
            f"  PRI Channel: {pri_channel}"
            f"\n  PRI Name: {pri_actor['name']}"
            f"\n  PRI Data: {pri_actor['data']}"
        )