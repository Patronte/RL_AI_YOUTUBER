
import json
from pathlib import Path
from collections import Counter

json_path = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

with json_path.open("r", encoding="utf-8") as file:
    data = json.load(file)

frames = data.get("Frames", [])

print("Frames analizzati:", len(frames))

actor_types = Counter()
interesting_actors = []

keywords = ("ball", "car", "vehicle", "boost")

for frame_index, frame in enumerate(frames):
    for actor in frame.get("ActorUpdates", []):
        object_name = str(actor.get("ObjectName", ""))
        type_name = str(actor.get("TypeName", ""))
        actor_name = str(actor.get("Name", ""))

        combined = (
            object_name + " " + type_name + " " + actor_name
        ).lower()

        actor_types[object_name] += 1

        if any(word in combined for word in keywords):
            interesting_actors.append(
                (frame_index, frame.get("Time"), actor)
            )

print("\n--- CLASSI PIU' FREQUENTI ---")

for name, count in actor_types.most_common(25):
    print(f"{count:6} | {name}")

print("\n--- ATTORI INTERESSANTI ---")
print("Aggiornamenti trovati:", len(interesting_actors))

shown = set()

for frame_index, timestamp, actor in interesting_actors:
    identity = (
        actor.get("ObjectName"),
        actor.get("TypeName"),
        actor.get("Name")
    )

    if identity in shown:
        continue

    shown.add(identity)

    print(f"\nFrame: {frame_index} | Time: {timestamp}")
    print(json.dumps(
        actor,
        indent=2,
        ensure_ascii=False
    )[:2200])

    if len(shown) >= 12:
        break
