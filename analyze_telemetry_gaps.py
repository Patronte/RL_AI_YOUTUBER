
import pandas as pd
import numpy as np

df = pd.read_csv("car_telemetry.csv")

df = df[df["pri"] != -1].copy()
df = df.sort_values(["pri", "time"])

results = []

for pri, player in df.groupby("pri"):

    player = player.copy()

    player["dt"] = player["time"].diff()

    dx = player["x"].diff()
    dy = player["y"].diff()
    dz = player["z"].diff()

    player["distance"] = np.sqrt(
        dx**2 + dy**2 + dz**2
    )

    player["speed_position"] = (
        player["distance"] / player["dt"]
    )

    # Identifichiamo i campioni sospetti.
    suspicious = player[
        (player["dt"] > 0.2) |
        (player["distance"] > 1500) |
        (player["speed_position"] > 3000)
    ]

    print(f"\n========== PRI {pri} ==========")

    print(
        "Intervalli sospetti:",
        len(suspicious)
    )

    print(
        suspicious[
            [
                "frame",
                "time",
                "dt",
                "distance",
                "speed_position",
                "x",
                "y",
                "z"
            ]
        ].to_string(index=False)
    )

    results.append(suspicious)

all_results = pd.concat(results)

all_results.to_csv(
    "telemetry_discontinuities.csv",
    index=False
)

print("\n========== COMPLETATO ==========")
print("File creato: telemetry_discontinuities.csv")
