import json
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
BATCH_PARSED_DIR = PROJECT_DIR / "parsed" / "batch_archive"

def main():
    print("=== 🔍 DIAGNOSTICA MIRATA ARCHIVIO JSON REPLAY ===")
    
    json_files = list(BATCH_PARSED_DIR.glob("*.json"))
    if not json_files:
        print(f"❌ Nessun file JSON trovato in {BATCH_PARSED_DIR}.")
        return

    print(f"📁 Analisi in corso su {len(json_files)} file JSON...\n")

    match_durations = []
    anomalous_files = []

    for j_file in json_files:
        try:
            with open(j_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Usiamo 'Properties' con la P maiuscola
            properties = data.get("Properties", {})
            
            # Durata reale da TotalSecondsPlayed
            duration = properties.get("TotalSecondsPlayed", 0.0)
            duration_val = float(duration) if duration is not None else 0.0
            
            if duration_val > 0:
                match_durations.append(duration_val)
            else:
                anomalous_files.append((j_file.name, ["TotalSecondsPlayed pari a 0 o assente"]))

        except Exception as e:
            anomalous_files.append((j_file.name, [f"Errore di lettura: {str(e)}"]))

    print("--- 📊 RISULTATI DELLA DIAGNOSTICA ---")
    if match_durations:
        df_dur = pd.Series(match_durations)
        print(f"⏱️ Durata media delle partite: {df_dur.mean():.2f} secondi (~{df_dur.mean()/60:.1f} minuti)")
        print(f"⏱️ Durata minima: {df_dur.min():.2f}s | Massima: {df_dur.max():.2f}s")
    
    if anomalous_files:
        print(f"\n⚠️ Trovati {len(anomalous_files)} file anomali:")
        for fname, reasons in anomalous_files[:10]:
            print(f"  - ❌ {fname}: {', '.join(reasons)}")
    else:
        print("\n✨ Ottimo! Nessuna anomalia di durata riscontrata nei file.")

if __name__ == "__main__":
    main()