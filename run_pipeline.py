import os
import glob
import sys
import subprocess
from pathlib import Path
import pandas as pd

# ==========================================
# CONFIGURAZIONE PERCORSI E DIRECTORY
# ==========================================
PROJECT_DIR = Path(__file__).resolve().parent
REPLAY_DIR = r"C:\Users\kazam\Documents\My Games\Rocket League\TAGame\DemosEpic"
PARSED_DIR = PROJECT_DIR / "parsed" / "rocketrp_test"
OBS_DIR = Path(r"C:\Users\kazam\Videos\Rocket Video")
OUTPUT_BASE_DIR = PROJECT_DIR / "recordings" / "highlights_batch"

PARSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

def run_step(description, command_list):
    """Esegue un comando della pipeline mostrando l'output in tempo reale."""
    print(f"\n⚡ {description}...")
    try:
        subprocess.run(command_list, check=True)
        print(f"✅ {description} completato con successo.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante: {description}\n{e}")
        return False

def get_latest_replay(replay_dir):
    search_path = os.path.join(replay_dir, "*.replay")
    list_of_files = glob.glob(search_path)
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getmtime)

print("=== AVVIO MASTER PIPELINE END-TO-END ===")

# ==========================================
# FASE 1: CONVERSIONE REPLAY -> JSON
# ==========================================
latest_replay_path = get_latest_replay(REPLAY_DIR)
if not latest_replay_path:
    print(f"❌ Nessun file .replay trovato in {REPLAY_DIR}")
    exit()

replay_name = Path(latest_replay_path).stem
output_json_path = PARSED_DIR / f"{replay_name}.json"

rocketrp_path = r"C:\Users\kazam\Downloads\RocketRP.CLI.1.2.19\RocketRP.CLI.exe"
conv_cmd = [
    rocketrp_path, "parse",
    "-r", latest_replay_path,
    "-o", str(PARSED_DIR),
    "-p"
]

if not run_step(f"Conversione replay ({Path(latest_replay_path).name})", conv_cmd):
    exit()

# Verifichiamo che il JSON esista e sia pronto
if not output_json_path.exists():
    json_candidates = list(PARSED_DIR.glob("*.json"))
    if json_candidates:
        output_json_path = max(json_candidates, key=os.path.getmtime)
    else:
        print("❌ File JSON di output non trovato nella cartella parsed.")
        exit()

print(f"📂 File JSON di lavoro: {output_json_path}")
json_arg = str(output_json_path)

# ==========================================
# FASE 2: ESTRAZIONE E ANALISI DATI (Pipeline Dinamica)
# ==========================================
data_steps = [
    ("Estrazione Telemetria Auto", [sys.executable, "export_car_telemetry.py", "--json_path", json_arg]),
    ("Estrazione Telemetria Palla", [sys.executable, "export_ball_telemetry.py", "--json_path", json_arg]),
    ("Rilevamento Impatti Palla", [sys.executable, "detect_ball_impacts.py", "--json_path", json_arg]),
    ("Costruzione Eventi Match", [sys.executable, "build_match_events.py", "--json_path", json_arg]),
    ("Raffinamento Tocchi Palla", [sys.executable, "refine_ball_touches.py", "--json_path", json_arg]),
    ("Ranking Highlights", [sys.executable, "rank_highlights.py"])
]

for desc, cmd in data_steps:
    if not run_step(desc, cmd):
        print("⚠️ Interruzione della pipeline per errore in un passaggio dati.")
        exit()

# ==========================================
# FASE 3: TAGLIO VIDEO HIGHLIGHTS CON FFMEG
# ==========================================
print("\n=== AVVIO TAGLIO DEI TOP HIGHLIGHTS ===")

csv_path = Path("top_highlights_ranked.csv")
if not csv_path.exists():
    print("❌ Errore: top_highlights_ranked.csv non trovato dopo il ranking.")
    exit()

df_highlights = pd.read_csv(csv_path)

highlights = []
for idx, row in df_highlights.iterrows():
    event_time = float(row["time"]) if "time" in row and not pd.isna(row["time"]) else 0.0
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

if not OBS_DIR.exists():
    OBS_DIR = Path("recordings/raw")
    OBS_DIR.mkdir(parents=True, exist_ok=True)

video_files = list(OBS_DIR.glob("*.mp4")) + list(OBS_DIR.glob("*.mkv")) + list(OBS_DIR.glob("*.avi"))
if not video_files:
    print(f"⚠️ Nessun video trovato in {OBS_DIR}. Saltato il taglio video.")
    exit()

def cut_clip(input_video, start_time, end_time, output_filename):
    duration = max(1.0, end_time - start_time)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", str(input_video),
        "-t", str(duration),
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "ultrafast",
        "-c:a", "aac",
        str(output_filename)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Errore FFmpeg nel taglio: {e}")
        return False

for idx, video_path in enumerate(video_files, start=1):
    match_output_dir = OUTPUT_BASE_DIR / f"match_{idx}_{video_path.stem}"
    match_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n--- Taglio Clip per Match [{idx}/{len(video_files)}]: {video_path.name} ---")
    success_count = 0
    for h in highlights:
        out_name = match_output_dir / f"highlight_{h['id']}_{str(h['type']).upper()}_{h['player']}.mp4"
        if cut_clip(video_path, h["clip_start_time"], h["clip_end_time"], out_name):
            success_count += 1

    print(f"Completato! Estratti {success_count}/{len(highlights)} clip nella cartella: {match_output_dir}")

print("\n=== 🎉 MASTER PIPELINE COMPLETATA CON SUCCESSO ===")