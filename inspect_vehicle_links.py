import argparse
import json
from collections import defaultdict
from pathlib import Path

parser = argparse.ArgumentParser(description="Ispeziona i collegamenti dei veicoli.")
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

components = [
    "TAGame.CarComponent_Jump_TA",
    "TAGame.CarComponent_DoubleJump_TA",
    "TAGame.CarComponent_Dodge_TA",
    "TAGame.CarComponent_FlipCar_TA",
]

links = defaultdict(set)

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):
        if actor.get("ObjectName") not in components:
            continue

        actor_data = actor.get("ActorData", {})
        vehicle = actor_data.get("Vehicle")

        if vehicle:
            links[actor["ChannelId"]].add(
                vehicle.get("TargetIndex")
            )

print("\n=== COMPONENT → VEHICLE LINKS ===")
for channel, vehicles in sorted(links.items()):
    print(
        f"Component Channel {channel:4} "
        f"→ Vehicle TargetIndex: {sorted(vehicles)}"
    )

print("\n=== CAR ACTORS ===")
for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):
        if actor.get("ObjectName") == "TAGame.Car_TA":
            print(
                "Channel:", actor["ChannelId"],
                "| Name:", actor.get("Name"),
                "| ObjectId:", actor.get("ObjectId"),
                "| TargetIndex:", actor.get("TypeId", {}).get("TargetIndex")
            )
    break