import pandas as pd
from pathlib import Path

print("=== AVVIO RANKING INTELLIGENTE CON DEDUPLICATION ===")

csv_path = Path("highlight_events.csv")
if not csv_path.exists():
    print("Errore: highlight_events.csv non trovato.")
    exit()

df = pd.read_csv(csv_path)
print(f"Eventi totali letti nel CSV: {len(df)}")

# 1. Filtraggio base (escludiamo variazioni di velocità irrilevanti se presenti)
if "dv" in df.columns:
    filtered = df[df["dv"] >= 1000.0].copy()
else:
    filtered = df.copy()

# 2. Assegniamo un punteggio di spettacolarità
def calculate_score(row):
    score = row.get("dv", 1000.0)
    # Diamo un bonus extra se nel tipo evento c'è GOAL o SAVE
    event_type = str(row.get("type", "")).upper()
    if "GOAL" in event_type:
        score += 3000.0
    elif "SAVE" in event_type:
        score += 1500.0
    elif "SHOT" in event_type:
        score += 800.0
    return score

filtered["score"] = filtered.apply(calculate_score, axis=1)

# Ordiniamo per punteggio decrescente
filtered = filtered.sort_values(by="score", ascending=False).reset_index(drop=True)

# 3. FILTRO ANTI-CLONI / DEDUPLICATION TEMPORALE
# Rocket League gira a 60 fps. 5 secondi = circa 300 frame.
# Se due eventi avvengono a meno di 300 frame di distanza, evitiamo di prenderli entrambi.
MIN_FRAME_DISTANCE = 300 
selected_highlights = []

for _, row in filtered.iterrows():
    frame_col = "impact_frame" if "impact_frame" in row else "frame"
    curr_frame = row[frame_col]
    
    # Controlliamo se è troppo vicino a un evento già selezionato
    too_close = False
    for selected in selected_highlights:
        sel_frame = selected[frame_col]
        if abs(curr_frame - sel_frame) < MIN_FRAME_DISTANCE:
            too_close = False # Mettiamo True per scartarli, ma se vogliamo raggrupparli gestiamo così:
            too_close = True
            break
            
    if not too_close:
        selected_highlights.append(row)
        
    if len(selected_highlights) >= 10: # Vogliamo i top 10 ben distribuiti
        exit_loop = True

top_highlights = pd.DataFrame(selected_highlights)

# Riordiniamo cronologicamente per il montaggio video finale
frame_col = "impact_frame" if "impact_frame" in top_highlights.columns else "frame"
top_highlights = top_highlights.sort_values(by=frame_col).reset_index(drop=True)

output_path = Path("top_highlights_ranked.csv")
top_highlights.to_csv(output_path, index=False)

print(f"\nSelezionati i Top {len(top_highlights)} momenti unici e distanziati nel match.")
print(top_highlights[[frame_col, "player", "score"]].to_string(index=False))