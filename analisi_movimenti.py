
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("car_telemetry.csv")

plt.figure(figsize=(12, 12))

for pri, player in df[df["pri"] != -1].groupby("pri"):
    plt.plot(
        player["x"],
        player["y"],
        label=f"Giocatore {pri}",
        alpha=0.8
    )

plt.xlim(-4500, 4500)
plt.ylim(-6000, 6000)

plt.xlabel("X")
plt.ylabel("Y")
plt.title("Traiettorie dei quattro giocatori")
plt.legend()
plt.grid()
plt.axis("equal")

plt.show()
