import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
BATCH_PARSED_DIR = PROJECT_DIR / "parsed" / "batch_archive"

def inspect_properties():
    json_files = list(BATCH_PARSED_DIR.glob("*.json"))
    if not json_files:
        return

    with open(json_files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    props = data.get("Properties", {})
    print("Chiavi all'interno di 'Properties':", list(props.keys()))
    
    # Cerchiamo se c'è PlayerStats o simili dentro Properties
    for k in props.keys():
        if "player" in k.lower() or "stat" in k.lower() or "duration" in k.lower() or "match" in k.lower():
            print(f"Trovata chiave rilevante in Properties: {k} -> Tipo: {type(props[k])}")

if __name__ == "__main__":
    inspect_properties()