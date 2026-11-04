import os
import json
import pandas as pd

# Percorsi dei file
events_csv_path = "match_events.csv"
output_json_path = "highlights_metadata.json"

if not os.path.exists(events_csv_path):
    print(f"Errore: Il file {events_csv_path} non esiste. Esegui prima build_match_events.py.")
    exit()

print("Caricamento degli eventi di match in corso...")
df_events = pd.read_csv(events_csv_path)

# Filtriamo gli eventi che ci interessano per gli highlights (es. gol, parate, tiri importanti)
# Vogliamo catturare i gol come eventi principali
target_types = ["goal", "save", "shot"]
df_highlights_raw = df_events[df_events["type"].isin(target_types)].copy()

print(f"Trovati {len(df_highlights_raw)} eventi potenziali per gli highlights.")

# Parametri di finestra temporale per il clip video (in secondi)
# Es: vogliamo un clip che parta 6 secondi PRIMA dell'evento e finisca 3 secondi DOPO
PRE_EVENT_BUFFER = 6.0
POST_EVENT_BUFFER = 3.0

highlights_list = []

for idx, row in df_highlights_raw.iterrows():
    event_time = row["time"]
    event_type = row["type"]
    player = row["player"]
    team = row["team"]
    frame = row["frame"]
    
    # Calcolo dei timestamp di inizio e fine clip
    start_time = max(0.0, event_time - PRE_EVENT_BUFFER)
    end_time = event_time + POST_EVENT_BUFFER
    
    highlight_item = {
        "id": int(idx),
        "type": event_type,
        "player": player,
        "team": int(team),
        "frame": int(frame),
        "exact_event_time": round(float(event_time), 2),
        "clip_start_time": round(float(start_time), 2),
        "clip_end_time": round(float(end_time), 2),
        "duration": round(float(end_time - start_time), 2)
    }
    
    highlights_list.append(highlight_item)

# Salvataggio in formato JSON (struttura pronta per futuri script di video editing)
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(highlights_list, f, indent=4, ensure_ascii=False)

print(front := f"\nFile generato con successo: {output_json_path}")
print(f"Totale clip di highlight configurate: {len(highlights_list)}")

# Mostriamo un'anteprima dei primi 3 highlights generati
print("\nAnteprima primi highlights:")
for h in highlights_list[:3]:
    print(f" - [{h['type'].upper()}] Giocatore: {h['player']} | Da {h['clip_start_time']}s a {h['clip_end_time']}s (Evento a {h['exact_event_time']}s)")