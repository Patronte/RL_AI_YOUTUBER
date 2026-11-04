import os
import json
import subprocess
from pathlib import Path

# Percorsi
metadata_path = "highlights_metadata.json"
output_dir = Path("recordings/highlights")
output_dir.mkdir(parents=True, exist_ok=True)

if not os.path.exists(metadata_path):
    print(f"Errore: Il file {metadata_path} non esiste. Esegui prima generate_highlights_metadata.py.")
    exit()

print("Caricamento dei metadati degli highlights...")
with open(metadata_path, "r", encoding="utf-8") as f:
    highlights = json.load(f)

print(f"Trovati {len(highlights)} highlight configurati.")

# NOTA: Per il test iniziale, cerchiamo un file video OBS disponibile nella cartella raw o specifica
# In base al tuo settings.py, le registrazioni OBS si trovano solitamente in C:\Users\kazam\Videos\Rocket Video o in recordings/raw
obs_dir = Path(r"C:\Users\kazam\Videos\Rocket Video")

if not obs_dir.exists():
    # Fallback alla cartella locale del progetto se esiste
    obs_dir = Path("recordings/raw")

video_files = list(obs_dir.glob("*.mp4")) + list(obs_dir.glob("*.mkv")) + list(obs_dir.glob("*.avi"))

if not video_files:
    print(f"\n[ATTENZIONE] Nessun file video di registrazione trovato in: {obs_dir}")
    print("Metti una registrazione video di prova nella cartella delle registrazioni OBS o in 'recordings/raw/' per procedere al taglio effettivo.")
    exit()

# Prendiamo la prima registrazione disponibile per il test
source_video = video_files[0]
print(f"Video sorgente selezionato per il taglio: {source_video.name}")

# Funzione per tagliare il video usando FFmpeg
def cut_clip(input_video, start_time, end_time, output_filename):
    duration = end_time - start_time
    cmd = [
        "ffmpeg",
        "-y",                 # Sovrascrivi file esistenti
        "-ss", str(start_time),# Tempo di inizio
        "-i", str(input_video),
        "-t", str(duration),   # Durata del clip
        "-c:v", "copy",        # Copia diretta del codec video (velocissimo, senza ricodifica)
        "-c:a", "copy",        # Copia diretta del codec audio
        str(output_filename)
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError as e:
        # Se la copia diretta fallisce (es. problemi di keyframe), proviamo con la ricodifica standard
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
        except Exception as err:
            print(f"Errore FFmpeg nel taglio: {err}")
            return False

print("\nAvvio del processo di taglio dei clip...")
success_count = 0

# Per evitare di generarne troppi tutti insieme durante i test, tagliamo ad esempio i primi 3 o tutti
for h in highlights[:5]:  # Limitiamo ai primi 5 per un test rapido
    h_id = h["id"]
    h_type = h["type"].upper()
    player = h["player"]
    start = h["clip_start_time"]
    end = h["clip_end_time"]
    
    out_name = output_dir / f"highlight_{h_id}_{h_type}_{player}.mp4"
    
    print(f"Taglio clip #{h_id} ({h_type} di {player}): da {start}s a {end}s...")
    success = cut_clip(source_video, start, end, out_name)
    if success:
        success_count += 1

print(f"\nProcesso completato! Generati con successo {success_count} clip video nella cartella: {output_dir.resolve()}")