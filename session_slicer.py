from datetime import datetime
import os
from pathlib import Path
import subprocess

# Configurazione cartelle
RECORDINGS_DIR = Path("recordings/raw")
REPLAYS_DIR = Path("data/replays")  # o la cartella dove salvi i replay
OUTPUT_DIR = Path("recordings/sliced_matches")


def get_file_timestamps(folder: Path, extension: str):
  """Restituisce una lista di file ordinata per orario di creazione."""
  files = list(folder.glob(f"*{extension}"))
  # Ordina i file in base al timestamp di creazione su disco
  files.sort(key=lambda x: x.stat().st_ctime)
  return files


def slice_obs_recording():
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

  obs_videos = get_file_timestamps(RECORDINGS_DIR, ".mkv")  # o .mp4
  replays = get_file_timestamps(REPLAYS_DIR, ".replay")

  if not obs_videos:
    print("❌ Nessun video di OBS trovato in", RECORDINGS_DIR)
    return

  if not replays:
    print("❌ Nessun file .replay trovato in", REPLAYS_DIR)
    return

  # Prendiamo l'ultimo video registrato da OBS
  obs_video = obs_videos[-1]
  obs_start_time = obs_video.stat().st_ctime

  print(f"🎬 Video OBS trovato: {obs_video.name}")
  print(
      f"🕒 Inizio registrazione OBS: {datetime.fromtimestamp(obs_start_time)}"
  )

  # Supponiamo che i replay della sessione siano quelli creati dopo l'inizio della registrazione OBS
  session_replays = [
      r for r in replays if r.stat().st_ctime >= obs_start_time - 60
  ]  # tolleranza di 1 min

  if not session_replays:
    print("⚠️ Nessun replay trovato associato a questa sessione video.")
    return

  print(f"🎮 Trovati {len(session_replays)} replay in questa sessione.")

  # Calcolo dei tagli (nota: di default un match dura circa 5 minuti + tempi morti)
  # Qui usiamo un'approssimazione sicura basata sull'ordine cronologico dei replay
  current_offset = 0.0

  for i, replay in enumerate(session_replays, start=1):
    # Per ora stimiamo una durata standard di match (es. 330 secondi compresi i supplementari)
    # Successivamente leggeremo la durata esatta direttamente dal file JSON del replay!
    match_duration = 330.0

    output_file = OUTPUT_DIR / f"match_{i}_{replay.stem}.mp4"

    print(
        f"✂️ Taglio Partita {i}: da {current_offset}s a"
        f" {current_offset + match_duration}s -> {output_file.name}"
    )

    # Comando FFmpeg per tagliare il video senza ricodificare (veloce)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(current_offset),
        "-i",
        str(obs_video),
        "-t",
        str(match_duration),
        "-c",
        "copy",
        str(output_file),
    ]

    subprocess.run(cmd, stdout=subprocess.DEVONSET, stderr=subprocess.DEVONSET)
    current_offset += match_duration

  print("✅ Selzionamento e taglio della sessione completati con successo!")


if __name__ == "__main__":
  slice_obs_recording()