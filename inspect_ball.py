import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Ispeziona i movimenti della palla.")
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

ball_channel = None

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):
        if actor.get("ObjectName") == "TAGame.Ball_TA":
            ball_channel = actor.get("ChannelId")
            print("Ball Channel ID:", ball_channel)
            print("Initial actor information:")
            print(json.dumps(actor, indent=2)[:3000])
            break

    if ball_channel is not None:
        break

if ball_channel is None:
    print("Ball not found!")
    raise SystemExit

print("\n--- BALL UPDATES ---")
count = 0

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):
        if actor.get("ChannelId") == ball_channel:
            print("\nTime:", frame.get("Time"))
            print(json.dumps(actor, indent=2, ensure_ascii=False)[:3000])
            count += 1
            if count >= 5:
                break
    if count >= 5:
        break

print("\nUpdates displayed:", count)