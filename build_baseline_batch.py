import os
import sys
import json
from pathlib import Path
import pandas as pd
import subprocess

# ==========================================
# CONFIGURAZIONE PERCORSI
# ==========================================
PROJECT_DIR = Path(__file__).resolve().parent
REPLAY_DIR = Path(r"C:\Users\kazam\Documents\My Games\Rocket League\TAGame\DemosEpic")
BATCH_PARSED_DIR = PROJECT_DIR / "parsed" / "batch_archive"
ROCKETRP_PATH = r"C:\Users\kazam\Downloads\RocketRP.CLI.1.2.19\RocketRP.CLI.exe"

MY_USERNAME = "Patrontex"
BATCH_PARSED_DIR.mkdir(parents=True, exist_ok=True)

def parse_replay_to_json(replay_path, output_dir):
    """Converte un replay in JSON usando RocketRP CLI se non esiste già."""
    json_path = output_dir / f"{replay_path.stem}.json"
    if json_path.exists():
        return json_path
    
    cmd = [ROCKETRP_PATH, "parse", "-r", str(replay_path), "-o", str(output_dir)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if json_path.exists():
            return json_path
    except subprocess.CalledProcessError:
        pass
    return None

def extract_match_metrics(json_path, username):
    """Estrae metriche chiave per l'utente da un singolo file JSON di replay."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # NOTA: Usiamo 'Properties' con la P maiuscola!
        properties = data.get("Properties", {})
        player_stats = properties.get("PlayerStats", [])
        
        user_stats = None
        for p in player_stats:
            # Di solito il nome del giocatore dentro PlayerStats si chiama "Name" o "PlayerName"
            p_name = p.get("Name", p.get("PlayerName", ""))
            if p_name.lower() == username.lower():
                user_stats = p
                break
        
        if not user_stats:
            return None 

        goals = user_stats.get("Goals", 0)
        assists = user_stats.get("Assists", 0)
        saves = user_stats.get("Saves", 0)
        score = user_stats.get("Score", 0)
        shots = user_stats.get("Shots", 0)

        return {
            "goals": goals,
            "assists": assists,
            "saves": saves,
            "score": score,
            "shots": shots
        }
    except Exception:
        return None

def main():
    print("=== AVVIO ANALISI BATCH ARCHIVIO REPLAY (BASELINE) ===")
    
    replay_files = list(REPLAY_DIR.glob("*.replay"))
    total_replays = len(replay_files)
    
    if total_replays == 0:
        print(f"❌ Nessun file .replay trovato in {REPLAY_DIR}")
        return

    print(f"📁 Trovati {total_replays} replay nell'archivio. Inizio elaborazione...")

    all_match_data = []
    processed_count = 0
    success_count = 0

    for idx, r_file in enumerate(replay_files, start=1):
        print(f"[{idx}/{total_replays}] Analisi: {r_file.name}...", end="\r")
        
        json_path = parse_replay_to_json(r_file, BATCH_PARSED_DIR)
        if not json_path:
            continue
        
        metrics = extract_match_metrics(json_path, MY_USERNAME)
        if metrics:
            all_match_data.append(metrics)
            success_count += 1
        
        processed_count += 1

    print(f"\n\n✨ Elaborazione completata! Replay analizzati con successo per '{MY_USERNAME}': {success_count}/{total_replays}")

    if not all_match_data:
        print("⚠️ Nessun dato valido estratto per l'utente specificato.")
        return

    # Calcoliamo le medie e le metriche di baseline
    df_baseline = pd.DataFrame(all_match_data)
    
    baseline_summary = {
        "total_matches_analyzed": success_count,
        "avg_score_per_match": float(df_baseline["score"].mean()),
        "avg_goals_per_match": float(df_baseline["goals"].mean()),
        "avg_assists_per_match": float(df_baseline["assists"].mean()),
        "avg_saves_per_match": float(df_baseline["saves"].mean()),
        "avg_shots_per_match": float(df_baseline["shots"].mean()),
        "max_score_recorded": int(df_baseline["score"].max()),
        "max_goals_recorded": int(df_baseline["goals"].max())
    }

    baseline_path = PROJECT_DIR / "player_baseline.json"
    with open(baseline_path, 'w', encoding='utf-8') as f:
        json.dump(baseline_summary, f, indent=4)

    print(f"\n📊 Baseline del giocatore salvata con successo in: {baseline_path}")
    print("--- RIEPILOGO STATISTICHE STORICHE ---")
    for k, v in baseline_summary.items():
        print(f"   - {k}: {v:.2f}" if isinstance(v, float) else f"   - {k}: {v}")

if __name__ == "__main__":
    main()