
import json
from pathlib import Path

path = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

with path.open("r", encoding="utf-8") as f:
    data = json.load(f)

print("ROOT KEYS:")
print(data.keys())

print("\nFIRST FRAME:")
print(json.dumps(
    data["Frames"][0],
    indent=2,
    ensure_ascii=False
)[:5000])

print("\nSECOND FRAME:")
print(json.dumps(
    data["Frames"][1],
    indent=2,
    ensure_ascii=False
)[:2000])
