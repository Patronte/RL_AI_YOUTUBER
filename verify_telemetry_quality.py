
import pandas as pd
import numpy as np

df = pd.read_csv("car_telemetry.csv")

df = df[df["pri"] != -1].copy()

df = df.sort_values(["pri", "frame"])

print("\n========== TELEMETRY QUALITY ==========")

for pri, player in df.groupby("pri"):

    player = player.copy()

    dt = player["time"].diff()

    dx = player["x"].diff()
    dy = player["y"].diff()
    dz = player["z"].diff()

    distance = np.sqrt(dx**2 + dy**2 + dz**2)

    print(f"\nPRI: {pri}")

    print("Campioni:", len(player))
    print("Intervallo mediano:", round(dt.median(), 5))
    print("Intervalli > 0.2s:", int((dt > 0.2).sum()))
    print("Intervalli > 1s:", int((dt > 1).sum()))

    print(
        "Posizioni identiche:",
        int((distance == 0).sum())
    )

    print(
        "Distanza mediana:",
        round(distance.median(), 2)
    )

    print(
        "Distanza massima:",
        round(distance.max(), 2)
    )

    print(
        "Aggiornamenti senza velocità:",
        int(player["vx"].isna().sum())
    )

print("\n========== COMPLETATO ==========")
