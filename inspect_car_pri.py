import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Verifica PRI delle auto.")
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
                "target": actor.get("TypeId", {}).get("TargetIndex"),
                "data": {}
            }

        if channel in actors:
            actors[channel]["data"].update(
                actor.get("ActorData", {})
            )

print("\n========== CAR → PLAYER VERIFICATION ==========")

for car_channel, car in actors.items():
    if car["object"] != "TAGame.Car_TA":
        continue

    pri_target = car["data"].get("PlayerReplicationInfo", {}).get("TargetIndex")

    print(f"\nCAR: {car['name']}")
    print(f"Car Channel: {car_channel}")
    print(f"PRI TargetIndex: {pri_target}")

    pri = actors.get(pri_target)
    if pri and pri["object"] == "TAGame.PRI_TA":
        player = pri["data"]
        print(f"PRI Channel: {pri_target}")
        print(f"Player Name: {player.get('PlayerName')}")
        print(f"Player ID: {player.get('PlayerID')}")
    else:
        print("PRI NOT FOUND")