
import json
from pathlib import Path

json_path = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

with json_path.open("r", encoding="utf-8") as file:
    data = json.load(file)


def inspect_value(name, value):
    print(f"\n--- {name} ---")
    print("Type:", type(value).__name__)

    if isinstance(value, dict):
        print("Keys:", list(value.keys())[:30])

        for key, item in list(value.items())[:5]:
            print(f"  {key}: {str(item)[:250]}")

    elif isinstance(value, list):
        print("Elements:", len(value))

        if value:
            print("First element type:", type(value[0]).__name__)

            if isinstance(value[0], dict):
                print("First element keys:", list(value[0].keys()))

                for key, item in list(value[0].items())[:5]:
                    print(f"  {key}: {str(item)[:250]}")
            else:
                print("First element:", str(value[0])[:500])


properties = data.get("Properties", {})

inspect_value("Goals", properties.get("Goals"))
inspect_value("Highlights", properties.get("Highlights"))
inspect_value("PlayerStats", properties.get("PlayerStats"))

frames = data.get("Frames", [])

if frames:
    inspect_value("First Frame", frames[0])

    actor_updates = frames[0].get("ActorUpdates", [])
    inspect_value("First Frame ActorUpdates", actor_updates)

    print("\n--- ACTOR UPDATE SAMPLE ---")

    if actor_updates:
        print(json.dumps(
            actor_updates[0],
            indent=2,
            ensure_ascii=False
        )[:3000])
