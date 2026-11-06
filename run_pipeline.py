import os
import sys
import glob
import subprocess
import re
from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
REPLAY_DIR = Path(r"C:\Users\kazam\Documents\My Games\Rocket League\TAGame\DemosEpic")
PARSED_DIR = PROJECT_DIR / "parsed" / "rocketrp_test"
OBS_DIR = Path(r"C:\Users\kazam\Videos\Rocket Video")
OUTPUT_BASE_DIR = PROJECT_DIR / "recordings" / "highlights_batch"
ROCKETRP_PATH = r"C:\Users\kazam\Downloads\RocketRP.CLI.1.2.19\RocketRP.CLI.exe"

MY_USERNAME = "Patrontex"

PARSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(name):
    clean_name = re.sub(r'[^\w\-]', '_', str(name))
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    return clean_name if clean_name else "Unknown"

def run_step(description, command_list):
    print(f"\n⚡ {description}...")
    try:
        subprocess.run(command_list, check=True)
        print(f"✅ {description} completato.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante {description}: {e}")
        return False

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    try:
        res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"⚠️ Impossibile leggere durata con ffprobe: {e}")
        return None

def cut_clip(input_video, start_time, end_time, output_filename):
    duration = max(1.0, end_time - start_time)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_time:.2f}",
        "-i", str(input_video),
        "-t", f"{duration:.2f}",
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
        print(f"❌ Errore FFmpeg durante il taglio: {e}")
        return False

print("=== AVVIO PIPELINE CON CATENA CAUSALE & BLOCCO ANTI-LOBBY RIGIDO ===")

video_files = list(OBS_DIR.glob("*.mp4")) + list(OBS_DIR.glob("*.mkv")) + list(OBS_DIR.glob("*.avi"))
if not video_files:
    print(f"❌ Nessun video trovato in {OBS_DIR}")
    sys.exit(1)

latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
v_end_time = latest_video.stat().st_mtime
v_duration = get_video_duration(latest_video)

if not v_duration:
    print("❌ Durata video non leggibile.")
    sys.exit(1)

v_start_time = v_end_time - v_duration

matched_replays = []
for r_file in REPLAY_DIR.glob("*.replay"):
    r_time = r_file.stat().st_mtime
    if v_start_time <= r_time <= (v_end_time + 30):
        matched_replays.append((r_file, r_time))

matched_replays.sort(key=lambda x: x[1])

if not matched_replays:
    print("❌ Nessun replay trovato per questo video.")
    sys.exit(1)

for match_idx, (r_file, r_end_time) in enumerate(matched_replays, start=1):
    print(f"\n==========================================")
    print(f"🎮 ELABORAZIONE MATCH [{match_idx}/{len(matched_replays)}]: {r_file.name}")
    print(f"==========================================")
    
    conv_cmd = [ROCKETRP_PATH, "parse", "-r", str(r_file), "-o", str(PARSED_DIR), "-p"]
    if not run_step(f"Conversione {r_file.name}", conv_cmd):
        continue

    output_json_path = PARSED_DIR / f"{r_file.stem}.json"
    if not output_json_path.exists():
        json_candidates = list(PARSED_DIR.glob("*.json"))
        output_json_path = max(json_candidates, key=os.path.getmtime)

    json_arg = str(output_json_path)

    data_steps = [
        ("Estrazione Telemetria Auto", [sys.executable, "export_car_telemetry.py", "--json_path", json_arg]),
        ("Estrazione Telemetria Palla", [sys.executable, "export_ball_telemetry.py", "--json_path", json_arg]),
        ("Rilevamento Impatti Palla", [sys.executable, "detect_ball_impacts.py", "--json_path", json_arg]),
        ("Costruzione Eventi Match", [sys.executable, "build_match_events.py", "--json_path", json_arg]),
        ("Raffinamento Tocchi Palla", [sys.executable, "refine_ball_touches.py", "--json_path", json_arg]),
        ("Ranking Highlights", [sys.executable, "rank_highlights.py", "--username", MY_USERNAME, "--json_path", json_arg])
    ]

    failed = False
    for desc, cmd in data_steps:
        if not run_step(desc, cmd):
            failed = True
            break
    if failed:
        continue

    # CALCOLO DURATA MATCH EFETTIVA (Stop prima della lobby)
    events_csv_path = Path("match_events.csv")
    if events_csv_path.exists():
        df_events = pd.read_csv(events_csv_path)
        match_duration_seconds = df_events["time"].max() if "time" in df_events.columns and not df_events["time"].isna().all() else 300.0
    else:
        df_ball = pd.read_csv("ball_telemetry.csv")
        match_duration_seconds = df_ball["time"].max() if "time" in df_ball.columns else 300.0

    match_start_real_time = r_end_time - match_duration_seconds
    match_offset_in_video = max(0.0, match_start_real_time - v_start_time)

    csv_path = Path("top_highlights_ranked.csv")
    if not csv_path.exists():
        continue

    df_highlights = pd.read_csv(csv_path)
    match_output_dir = OUTPUT_BASE_DIR / f"match_{match_idx}_{r_file.stem}"
    match_output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for idx, row in df_highlights.iterrows():
        rel_start = float(row["start_time"]) if "start_time" in row else float(row.get("time", 0)) - 5.0
        rel_end = float(row["end_time"]) if "end_time" in row else float(row.get("time", 0)) + 3.5

        # 🛑 BLOCCO ANTI-LOBBY RIGIDO: Nessun taglio può superare la durata reale della partita
        rel_end_clamped = min(match_duration_seconds, rel_end)
        
        # Se lo start cade oltre la fine o il clip è troppo corto a causa del clamp, ignoriamo
        if rel_start >= match_duration_seconds or (rel_end_clamped - rel_start) < 1.0:
            print(f"🛡️ Clip {idx+1} bloccata dal filtro Anti-Lobby (Sforava nel post-game).")
            continue

        abs_start = match_offset_in_video + rel_start
        abs_end = match_offset_in_video + rel_end_clamped
        
        h_id = idx + 1
        h_type = sanitize_filename(row.get("type", "highlight")).lower()
        player = sanitize_filename(row.get("player", "Unknown"))
        
        out_name = match_output_dir / f"highlight_{h_id}_{h_type}_{player}.mp4"
        if cut_clip(latest_video, abs_start, abs_end, out_name):
            success_count += 1

    print(f"✨ Estratti {success_count} clip nella cartella: {match_output_dir}")

print("\n=== 🎉 PIPELINE MULTI-MATCH COMPLETATA ===")