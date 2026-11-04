
import pandas as pd
import numpy as np

df = pd.read_csv("car_telemetry.csv")

df = df[df["pri"] != -1].copy()

df = df.sort_values(["pri", "time"])

df["dx"] = df.groupby("pri")["x"].diff()
df["dy"] = df.groupby("pri")["y"].diff()
df["dz"] = df.groupby("pri")["z"].diff()

df["distance"] = np.sqrt(
    df["dx"]**2 +
    df["dy"]**2 +
    df["dz"]**2
)

df["dt"] = df.groupby("pri")["time"].diff()

df["speed_from_position"] = (
    df["distance"] / df["dt"]
)

print("\n========== POSITION CHANGE ANALYSIS ==========")

for pri, player in df.groupby("pri"):

    valid = player.dropna(
        subset=["distance", "dt"]
    )

    print(f"\nPRI: {pri}")

    print("Campioni:", len(player))
    print(
        "Posizioni identiche:",
        (valid["distance"] == 0).sum()
    )
    print(
        "Posizioni cambiate:",
        (valid["distance"] > 0).sum()
    )
    print(
        "Distanza massima tra aggiornamenti:",
        round(valid["distance"].max(), 2)
    )
    print(
        "Velocità massima ricostruita:",
        round(valid["speed_from_position"].max(), 2)
    )

    print("\n10 maggiori spostamenti:")

    print(
        valid.nlargest(10, "distance")[
            ["frame", "time", "dt",
             "distance", "speed_from_position"]
        ].to_string(index=False)
    )
