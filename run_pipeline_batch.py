import os
import json
import subprocess
from pathlib import Path
import pandas as pd

# Definiamo le cartelle principali
OBS_DIR = Path(r"C:\Users\kazam\Videos\Rocket Video")
OUTPUT_BASE_DIR = Path("recordings/highlights_batch")
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

print("=== AVVIO PIPELINE DI TAGLIO DEI TOP HIGHLIGHTS ===")

# 1. Carichiamo direttamente il file dei Top 10 rankati (e non più quelli grezzi)
csv_path = Path("top_highlights_ranked.csv")
if not csv_path.exists():
    print("Errore: top_highlights_ranked.csv non trovato. Esegui prima rank_highlights.py.")
    exit()

df_highlights = pd.read_csv(csv_path)

# Convertiamo il DataFrame in una lista di dizionari per il taglio video
highlights = []
for idx, row in df_highlights.iterrows():
    event_time = float(row["time"]) if "time" in row and not pd.isna(row["time"]) else 0.0
    
    # Finestra temporale più ampia: 5 secondi prima dell'evento, 5 secondi dopo
    start_time = max(0.0, event_time - 5.0)
    end_time = event_time + 5.0
    
    highlights.append({
        "id": idx + 1,
        "type": row.get("type", "HIGHLIGHT"),
        "player": str(row.get("player", "Unknown")).replace(" ", "_"),
        "clip_start_time": start_time,
        "clip_end_time": end_time
    })

print(f"Trovati {len(highlights)} top highlights da tagliare.")

# 2. Cerchiamo i video di OBS disponibili
if not OBS_DIR.exists():
    OBS_DIR = Path("recordings/raw")
    OBS_DIR.mkdir(parents=True, exist_ok=True)

video_files = list(OBS_DIR.glob("*.mp4")) + list(OBS_DIR.glob("*.mkv")) + list(OBS_DIR.glob("*.avi"))

if not video_files:
    print(f"Nessun video trovato in {OBS_DIR}. Aggiungi le registrazioni per procedere.")
    exit()

print(f"Trovati {len(video_files)} file video di registrazione OBS da processare.")

# 3. Funzione di taglio ffmpeg ultra-veloce con preset ultrafast e feedback visivo in tempo reale
def cut_clip(input_video, start_time, end_time, output_filename):
    duration = max(1.0, end_time - start_time)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", str(input_video),
        "-t", str(duration),
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "ultrafast",  # <-- Rendering super accelerato
        "-c:a", "aac",
        str(output_filename)
    ]
    try:
        # Senza PIPE silenziose: vedrai eventuali log direttamente nel terminale
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Errore critico FFmpeg nel taglio: {e}")
        return False

# 4. Elaborazione batch limitata ai video del match corrente
for idx, video_path in enumerate(video_files, start=1):
    match_output_dir = OUTPUT_BASE_DIR / f"match_{idx}_{video_path.stem}"
    match_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n--- Taglio Clip per Match [{idx}/{len(video_files)}]: {video_path.name} ---")
    
    success_count = 0
    for h in highlights:
        h_id = h["id"]
        h_type = str(h["type"]).upper()
        player = h["player"]
        start = h["clip_start_time"]
        end = h["clip_end_time"]
        
        out_name = match_output_dir / f"highlight_{h_id}_{h_type}_{player}.mp4"
        
        success = cut_clip(video_path, start, end, out_name)
        if success:
            success_count += 1

    print(f"Completato! Estratti {success_count}/{len(highlights)} clip puliti nella cartella: {match_output_dir}")

print("\n=== TAGLIO BATCH COMPLETATO CON SUCCESSO ===")