import pandas as pd
import json
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Rank highlights with causal chain and strict team filtering.")
    parser.add_argument("--username", type=str, default="Patrontex", help="Il tuo nickname in-game")
    parser.add_argument("--json_path", type=str, default="", help="Percorso al file JSON del replay")
    return parser.parse_known_args()

def get_my_team_and_teammates(json_path, username):
    """Estrae il team index (0 o 1) e i nomi di tutti i compagni di squadra dal JSON."""
    if not json_path or not Path(json_path).exists():
        return None, []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        properties = data.get("properties", {})
        player_stats = properties.get("PlayerStats", [])
        
        my_team = None
        for p in player_stats:
            p_name = p.get("Name", "")
            if p_name.lower() == username.lower():
                my_team = p.get("Team", p.get("TeamNum", None))
                break

        if my_team is None:
            return None, []

        teammates = [
            p.get("Name") for p in player_stats 
            if p.get("Team", p.get("TeamNum", None)) == my_team and p.get("Name")
        ]
        return my_team, teammates
    except Exception as e:
        print(f"⚠️ Errore lettura team da JSON: {e}")
        return None, []

def find_causal_start_time(events_df, event_time, player_name, teammates, max_lookback=12.0):
    """
    True Start a Catena Causale:
    Risale a ritroso nel CSV degli eventi/tocchi fino a trovare il primo tocco utile 
    della squadra (o intercettazione) che ha dato origine all'azione.
    """
    if "time" not in events_df.columns:
        return max(0.0, event_time - 5.0)

    # Eventi/tocchi precedenti all'evento clou entro una finestra massima di lookback
    prior_events = events_df[
        (events_df["time"] <= event_time) & 
        (events_df["time"] >= max(0.0, event_time - max_lookback))
    ].sort_values(by="time", ascending=False)

    if prior_events.empty:
        return max(0.0, event_time - 5.0)

    chain_start = event_time - 3.0  # Fallback minimo per contestualizzare
    last_valid_time = event_time

    for _, row in prior_events.iterrows():
        p = str(row.get("player", ""))
        t = float(row.get("time", 0.0))
        
        # Interruzione catena se c'è una pausa di gioco troppo lunga (>4.5s senza tocchi)
        if (last_valid_time - t) > 4.5:
            break

        # Se il tocco appartiene alla squadra o è un tocco chiave correlato
        if any(mate.lower() in p.lower() for mate in teammates) or p == player_name:
            chain_start = t
            last_valid_time = t
        else:
            # Tocco avversario: se è vicino all'azione (es. rimpallo o parata subita), lo includiamo ma non estendiamo a ritroso oltre
            chain_start = min(chain_start, t)
            break

    # Margine di respiro pre-azione (1.5s prima del tocco iniziale)
    return max(0.0, chain_start - 1.5)

def main():
    args, _ = parse_args()
    username = args.username
    json_path = args.json_path

    print("=== RANKING INTELLIGENTE: CATENA CAUSALE & FILTRO RIGOROSO SQUADRA ===")
    
    events_file = Path("highlight_events.csv")
    if not events_file.exists():
        events_file = Path("match_events.csv")
        if not events_file.exists():
            print("❌ Nessun file di eventi trovato per il ranking.")
            return

    df_events = pd.read_csv(events_file)
    touches_file = Path("ball_touches.csv")
    df_touches = pd.read_csv(touches_file) if touches_file.exists() else df_events

    my_team, teammates = get_my_team_and_teammates(json_path, username)

    # Filtro di squadra rigoroso: manteniamo gli eventi dove il protagonista o chi subisce l'azione è del tuo team
    if teammates:
        pattern = "|".join([re_escape(m) for m in teammates])
        df_filtered = df_events[df_events["player"].astype(str).str.contains(pattern, case=False, na=False)].copy()
        if not df_filtered.empty:
            df_events = df_filtered
            print(f"🛡️ Filtro squadra applicato con successo. Compagni: {teammates}")
        else:
            print("⚠️ Nessun evento trovato esclusivamente per il team, uso eventi generali.")

    if 'score' not in df_events.columns:
        df_events['score'] = 1000.0

    df_events = df_events.sort_values(by="score", ascending=False)
    
    selected_highlights = []
    min_time_gap = 8.0

    for _, row in df_events.iterrows():
        event_t = float(row.get("time", 0.0))
        p_name = str(row.get("player", username))
        
        if all(abs(event_t - h["event_time"]) >= min_time_gap for h in selected_highlights):
            # Calcolo dinamico del True Start tramite la Catena Causale
            start_t = find_causal_start_time(df_touches, event_t, p_name, teammates)
            # Fine azione: +3.5s per celebrazione/esplosione gol
            end_t = event_t + 3.5

            selected_highlights.append({
                "time": event_t,
                "event_time": event_t,
                "start_time": start_t,
                "end_time": end_t,
                "type": row.get("type", "highlight"),
                "player": p_name,
                "score": row.get("score", 1000.0)
            })

            if len(selected_highlights) >= 15:
                break

    df_ranked = pd.DataFrame(selected_highlights).sort_values(by="start_time")

    print(f"\nSelezionati i Top {len(df_ranked)} momenti con durata e start dinamici.")
    print(df_ranked[['start_time', 'event_time', 'end_time', 'player', 'type']].to_string(index=False))

    df_ranked.to_csv("top_highlights_ranked.csv", index=False)
    print("✅ Ranking Highlights con Catena Causale completato.")

def re_escape(text):
    import re
    return re.escape(text)

if __name__ == "__main__":
    main()