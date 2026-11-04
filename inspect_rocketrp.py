import json
from pathlib import Path

json_path = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

with json_path.open("r", encoding="utf-8") as file:
    data = json.load(file)

print("\n--- JSON STRUCTURE ---")
print("Root type:", type(data).__name__)

if isinstance(data, dict):
    print("\nTop-level keys:")

    for key, value in data.items():
        print(f"\n{key}: {type(value).__name__}")

        if isinstance(value, dict):
            print("  Keys:", list(value.keys())[:20])

        elif isinstance(value, list):
            print("  Elements:", len(value))

            if value and isinstance(value[0], dict):
                print("  First element keys:",
                      list(value[0].keys())[:20])

elif isinstance(data, list):
    print("Elements:", len(data))