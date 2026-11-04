import os
import json
import subprocess
from pathlib import Path
import pandas as pd

# Definiamo le cartelle principali
OBS_DIR = Path(r"C:\Users\kazam\Videos\Rocket Video")
OUTPUT_BASE_DIR = Path("recordings/highlights_batch")
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

print("=== AVVIO PIPELINE AUTOMATICA MASSIVA (BATCH) ===")

# 1. Carichiamo gli eventi filtrati direttamente da highlight_events.csv
csv_path = Path("highlight_events.csv")
if not csv_path.exists():
    print("Errore: highlight_events.csv non trovato. Esegui prima build_match_events.py.")
    exit()

df_highlights = pd.read_csv(csv_path)

# Convertiamo il DataFrame in una lista di dizionari per il taglio video
highlights = []
for idx, row in df_highlights.iterrows():
    event_time = float(row["time"]) if not pd.isna(row["time"]) else 0.0
    
    # Finestra temporale del clip: 4 secondi prima dell'evento, 3 secondi dopo
    start_time = max(0.0, event_time - 4.0)
    end_time = event_time + 3.0
    
    highlights.append({
        "id": idx + 1,
        "type": row["type"],
        "player": row["player"] if not pd.isna(row["player"]) else "Unknown",
        "clip_start_time": start_time,
        "clip_end_time": end_time
    })

print(f"Trovati {len(highlights)} eventi filtrati in highlight_events.csv da elaborare.")

# 2. Cerchiamo tutti i video di OBS disponibili nella cartella
if not OBS_DIR.exists():
    OBS_DIR = Path("recordings/raw")
    OBS_DIR.mkdir(parents=True, exist_ok=True)

video_files = list(OBS_DIR.glob("*.mp4")) + list(OBS_DIR.glob("*.mkv")) + list(OBS_DIR.glob("*.avi"))

if not video_files:
    print(f"Nessun video trovato in {OBS_DIR}. Aggiungi le registrazioni per procedere.")
    exit()

print(f"Trovati {len(video_files)} file video di registrazione OBS da processare in blocco.")

# 3. Funzione di taglio ffmpeg
def cut_clip(input_video, start_time, end_time, output_filename):
    duration = max(1.0, end_time - start_time)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", str(input_video),
        "-t", str(duration),
        "-c:v", "copy",
        "-c:a", "copy",
        str(output_filename)
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError:
        try:
            cmd_recode = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-i", str(input_video),
                "-t", str(duration),
                str(output_filename)
            ]
            subprocess.run(cmd_recode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except Exception as e:
            print(f"Errore critico FFmpeg: {e}")
            return False

# 4. Elaborazione batch di ogni video trovato
for idx, video_path in enumerate(video_files, start=1):
    match_output_dir = OUTPUT_BASE_DIR / f"match_{idx}_{video_path.stem}"
    match_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n--- Elaborazione Match [{idx}/{len(video_files)}]: {video_path.name} ---")
    
    success_count = 0
    for h in highlights:
        h_id = h["id"]
        h_type = h["type"].upper()
        player = str(h["player"]).replace(" ", "_")
        start = h["clip_start_time"]
        end = h["clip_end_time"]
        
        out_name = match_output_dir / f"highlight_{h_id}_{h_type}_{player}.mp4"
        
        success = cut_clip(video_path, start, end, out_name)
        if success:
            success_count += 1

    print(f"Completato! Estratti {success_count}/{len(highlights)} clip nella cartella: {match_output_dir}")

print("\n=== ELABORAZIONE BATCH COMPLETATA CON SUCCESSO ===")