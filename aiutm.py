import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
BATCH_PARSED_DIR = PROJECT_DIR / "parsed" / "batch_archive"

def check_existing_json():
    json_files = list(BATCH_PARSED_DIR.glob("*.json"))
    if not json_files:
        print("❌ Nessun file JSON trovato.")
        return

    sample_file = json_files[0]
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    properties = data.get("properties", {})
    print(f"File analizzato: {sample_file.name}")
    print("Chiavi disponibili in properties:", list(properties.keys()))
    
    if "ReplayDuration" in properties:
        print("ReplayDuration:", properties["ReplayDuration"])
    elif "MatchDuration" in properties:
        print("MatchDuration:", properties["MatchDuration"])
    else:
        print("⚠️ Nessuna chiave 'Duration' standard trovata in properties con il parsing attuale (-p).")

if __name__ == "__main__":
    check_existing_json()