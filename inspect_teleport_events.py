
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

df["speed_position"] = (
    df["distance"] / df["dt"]
)

# Individuiamo gli spostamenti anomali.
events = df[df["distance"] > 1500].copy()

print("\n========== ANOMALOUS MOVEMENTS ==========")

print(
    events[
        ["frame", "time", "pri",
         "x", "y", "z",
         "distance", "dt",
         "speed_position"]
    ].sort_values("frame").to_string(index=False)
)

print("\n========== EVENT FRAME SUMMARY ==========")

summary = (
    events.groupby("frame")
    .agg(
        players=("pri", "count"),
        max_distance=("distance", "max"),
        players_involved=("pri", lambda x: list(x))
    )
    .sort_index()
)

print(summary.to_string())
