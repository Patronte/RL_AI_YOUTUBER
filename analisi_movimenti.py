import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Percorsi dei file CSV
car_csv_path = "car_telemetry.csv"
events_csv_path = "match_events.csv"

if not os.path.exists(car_csv_path) or not os.path.exists(events_csv_path):
    print("Errore: Uno o entrambi i file di dati non sono stati trovati.")
    exit()

print("Caricamento dei dati di telemetria e degli eventi in corso...")
df_car = pd.read_csv(car_csv_path)
df_events = pd.read_csv(events_csv_path)

# Filtriamo i giocatori validi
df_players = df_car[df_car["pri"] != -1].copy()

print(f"\nTrovati {len(df_events)} eventi registrati in match_events.csv.")
print("\n========== DETTAGLIO EVENTI CHIAVE (GOL E TIRI) ==========")
df_goals = df_events[df_events["type"] == "goal"]
for _, g in df_goals.iterrows():
    print(f"[{g['time']:.2f}s] GOL segnato da {g['player']} (Team {g['team']}) al frame {g['frame']}")
print("==========================================================")

# Creazione della visualizzazione tattica
plt.figure(figsize=(10, 12))

# 1. Tracciamo le traiettorie di fondo dei giocatori in modo trasparente
for pri, player in df_players.groupby("pri"):
    plt.plot(
        player["x"],
        player["y"],
        label=f"Traiettoria (PRI: {pri})",
        alpha=0.25,
        linewidth=1
    )

# 2. Evidenziamo i punti in cui sono avvenuti i gol
# Cerchiamo le coordinate delle auto o della palla nei frame dei gol
for _, g in df_goals.iterrows():
    f_num = g["frame"]
    # Troviamo la posizione dei giocatori in quel frame specifico
    player_at_frame = df_players[df_players["frame"] == f_num]
    if not player_at_frame.empty:
        plt.scatter(
            player_at_frame["x"],
            player_at_frame["y"],
            color="red",
            s=120,
            marker="X",
            zorder=6,
            label="Posizione Gol" if _ == df_goals.index[0] else ""
        )

# Dimensioni standard del campo di Rocket League
plt.xlim(-4100, 4100)
plt.ylim(-6000, 6000)

plt.xlabel("Asse X (Larghezza Campo)")
plt.ylabel("Asse Y (Lunghezza Campo)")
plt.title("Analisi Tattica: Traiettorie e Posizioni dei Gol")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(loc="upper right")
plt.axis("equal")

print("\nGenerazione del grafico con la mappa dei gol...")
plt.show()