import argparse
import json
from collections import defaultdict
from pathlib import Path

parser = argparse.ArgumentParser(description="Ispeziona gli eventi dei componenti.")
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

targets = {
    "TAGame.CarComponent_Jump_TA",
    "TAGame.CarComponent_DoubleJump_TA",
    "TAGame.CarComponent_Dodge_TA",
}

events = defaultdict(list)

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):
        name = actor.get("ObjectName")
        if name not in targets:
            continue

        actor_data = actor.get("ActorData", {})
        if not actor_data or "Vehicle" in actor_data:
            continue

        events[name].append({
            "time": frame.get("Time"),
            "channel": actor.get("ChannelId"),
            "data": actor_data
        })

for name, records in events.items():
    print("\n" + "=" * 65)
    print(name)
    print("Eventi:", len(records))
    print("=" * 65)

    for event in records[:30]:
        print(
            f"Time: {event['time']:.3f} | "
            f"Channel: {event['channel']} | "
            f"Data: {json.dumps(event['data'])}"
        )