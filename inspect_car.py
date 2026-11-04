import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Ispeziona l'auto nel replay.")
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

car_channel = None

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):
        if actor.get("ObjectName") == "TAGame.Car_TA":
            car_channel = actor.get("ChannelId")
            print("Car Channel ID:", car_channel)
            print("\nInitial actor information:")
            print(json.dumps(actor, indent=2)[:3000])
            break
    if car_channel is not None:
        break

if car_channel is None:
    print("Car not found!")
    raise SystemExit

print("\n--- CAR UPDATES ---")
count = 0

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):
        if actor.get("ChannelId") == car_channel:
            print("\nTime:", frame.get("Time"))
            print(json.dumps(actor, indent=2, ensure_ascii=False)[:4000])
            count += 1
            if count >= 6:
                break
    if count >= 6:
        break

print("\nUpdates displayed:", count)