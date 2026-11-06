import os
from pathlib import Path
from datetime import datetime

OBS_DIR = Path(r"C:\Users\kazam\Videos\Rocket Video")
REPLAY_DIR = Path(r"C:\Users\kazam\Documents\My Games\Rocket League\TAGame\DemosEpic")

def analyze_time_mapping():
    print("=== ANALISI DEI TIMESTAMP VIDEO VS REPLAY ===")
    
    # 1. Troviamo i file video in OBS
    video_files = list(OBS_DIR.glob("*.mp4")) + list(OBS_DIR.glob("*.mkv")) + list(OBS_DIR.glob("*.avi"))
    if not video_files:
        print(f"❌ Nessun video trovato in {OBS_DIR}")
        return

    for v_file in video_files:
        # Otteniamo l'orario di inizio (creazione/modifica) del file video di OBS
        v_stat = v_file.stat()
        v_start_time = v_stat.st_mtime # Timestamp di fine o creazione approssimativa
        # Nota: Di solito il mtime di un file OBS registrato indica la fine della registrazione, 
        # oppure possiamo stimare l'inizio sottraendo la durata se la calcoliamo.
        
        v_datetime = datetime.fromtimestamp(v_start_time)
        print(f"\n📹 Video trovato: {v_file.name}")
        print(f"   🕒 Timestamp file: {v_datetime} (Epoch: {v_start_time})")

        print("   🔎 Replays trovati nella stessa giornata/intorno a questo orario:")
        
        # 2. Cerchiamo i replay vicini (es. nel raggio di 2 ore prima del file)
        matched_replays = []
        for r_file in REPLAY_DIR.glob("*.replay"):
            r_time = r_file.stat().st_mtime
            # Se il replay è avvenuto nelle 2 ore precedenti alla fine del video di OBS
            if (v_start_time - 7200) <= r_time <= v_start_time:
                matched_replays.append((r_file, r_time))
                
        # Ordiniamo i replay dal più vecchio al più recente
        matched_replays.sort(key=lambda x: x[1])
        
        for r_file, r_time in matched_replays:
            r_datetime = datetime.fromtimestamp(r_time)
            diff_minutes = (v_start_time - r_time) / 60
            print(f"      - {r_file.name} | Orario: {r_datetime.strftime('%H:%M:%S')} | Circa {diff_minutes:.1f} min prima della fine del video")

if __name__ == "__main__":
    analyze_time_mapping()