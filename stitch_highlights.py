import os
import subprocess
from pathlib import Path
import pandas as pd

print("=== AVVIO COMPILAZIONE VIDEO PROFESSIONALE (STITCHING AVANZATO) ===")

# 1. Carichiamo i top highlights ordinati
ranked_csv = Path("top_highlights_ranked.csv")
if not ranked_csv.exists():
    print("Errore: top_highlights_ranked.csv non trovato. Esegui prima rank_highlights.py.")
    exit()

df_top = pd.read_csv(ranked_csv)

# 2. Troviamo la cartella dei match
batch_base = Path("recordings/highlights_batch")
if not batch_base.exists():
    print("Errore: La cartella recordings/highlights_batch/ non esiste.")
    exit()

match_dirs = [d for d in batch_base.iterdir() if d.is_dir()]
if not match_dirs:
    print("Errore: Nessuna cartella di match trovata.")
    exit()

latest_match_dir = max(match_dirs, key=os.path.getmtime)
print(f"Utilizzo la cartella match: {latest_match_dir.name}")

# 3. Raccogliamo i file in modo pulito e senza duplicati, basandoci sul ranking reale
video_files = []
for idx, row in df_top.iterrows():
    # Cerchiamo i file associati al ranking esatto (evitiamo doppioni)
    # Il nome salvato nel batch era highlight_<id>_<type>_<player>.mp4
    # Usiamo un pattern sicuro basato sull'indice della riga o sull'id se presente
    event_id = row.get("id", idx + 1)
    
    # Cerchiamo file che contengano l'identificativo esatto
    matches = list(latest_match_dir.glob(f"highlight_{idx+1}_*.mp4"))
    if not matches:
        # Fallback generico se il nome è diverso
        matches = list(latest_match_dir.glob("*.mp4"))
        if idx < len(matches):
            matches = [matches[idx]]
            
    if matches and matches[0] not in video_files:
        video_files.append(matches[0])

# Se per qualche motivo la lista è vuota o sballata, prendiamo i primi N unici
if not video_files:
    video_files = sorted(list(set(latest_match_dir.glob("*.mp4"))))

print(f"Trovati {len(video_files)} clip unici da montare nella compilation.")

if len(video_files) == 0:
    print("Errore: Nessun video da unire.")
    exit()

# 4. Creiamo la struttura per il filtro complesso di FFmpeg (concat filter)
# Questo ricodifica video e audio uniformemente, sistemando i problemi di audio e stacchi
input_args = []
filter_complex_parts = []

for i, v_file in enumerate(video_files):
    input_args.extend(["-i", str(v_file.resolve())])
    filter_complex_parts.append(f"[{i}:v][{i}:a]")

filter_complex_str = "".join(filter_complex_parts) + f"concat=n={len(video_files)}:v=1:a=1[outv][outa]"

# 5. Cartella di output finale
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)
final_output = output_dir / f"compilation_pro_{latest_match_dir.name}.mp4"

# 6. Comando FFmpeg con ricodifica (H.264 per il video e AAC per l'audio)
cmd = [
    "ffmpeg", "-y",
    *input_args,
    "-filter_complex", filter_complex_str,
    "-map", "[outv]",
    "-map", "[outa]",
    "-c:v", "libx264",
    "-crf", "23",
    "-preset", "fast",
    "-c:a", "aac",
    "-b:a", "192k",
    str(final_output)
]

print(f"Avvio del rendering video avanzato (potrebbe richiedere qualche minuto)...")
try:
    subprocess.run(cmd, check=True)
    print("\n=== COMPILAZIONE PROFESSIONALE COMPLETATA! ===")
    print(f"Il tuo video pulito è pronto in: {final_output}")
except subprocess.CalledProcessError as e:
    print(f"Errore critico durante il rendering FFmpeg: {e}")