import argparse
import json
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description="Ispeziona gli aggiornamenti dei componenti.")
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
    updates = []
    for frame in data["Frames"]:
        for actor in frame.get("ActorUpdates", []):
            if actor.get("ObjectName") == component_name:
                updates.append({
                    "time": frame.get("Time"),
                    "state": actor.get("State"),
                    "actor_data": actor.get("ActorData", {})
                })

    print("\n" + "=" * 65)
    print(component_name)
    print("=" * 65)
    print("Totale aggiornamenti:", len(updates))
    print("Tipi di aggiornamento:")
    print(Counter(update["state"] for update in updates))

    print("\nPrime 15 occorrenze:")
    for update in updates[:15]:
        print(json.dumps(update, indent=2, ensure_ascii=False))

    print("\nUltime 5 occorrenze:")
    for update in updates[-5:]:
        print(json.dumps(update, indent=2, ensure_ascii=False))