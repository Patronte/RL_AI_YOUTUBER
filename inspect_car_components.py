import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Ispeziona i componenti dell'auto.")
parser.add_argument(
    "--json_path", 
    type=str, 
    default=str(Path("parsed") / "rocketrp_test" / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"),
    help="Percorso al file JSON del match da analizzare."
)
args = parser.parse_args()
json_path = Path(args.json_path)

with json_path.open("r", encoding="utf-8") as file:
    data = json.load(file)

components = [
    "TAGame.CarComponent_Jump_TA",
    "TAGame.CarComponent_DoubleJump_TA",
    "TAGame.CarComponent_Dodge_TA",
    "TAGame.CarComponent_FlipCar_TA",
]

for component_name in components:
    print("\n" + "=" * 65)
    print(component_name)
    print("=" * 65)

    found = 0
    for frame in data["Frames"]:
        for actor in frame.get("ActorUpdates", []):
            if actor.get("ObjectName") == component_name:
                print("\nTime:", frame.get("Time"))
                print("Channel:", actor.get("ChannelId"))
                print(json.dumps(actor, indent=2, ensure_ascii=False)[:2500])
                found += 1
                if found >= 3:
                    break
        if found >= 3:
            break
    print("\nUpdates displayed:", found)