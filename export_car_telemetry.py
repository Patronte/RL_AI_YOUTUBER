import argparse
import csv
import json
from pathlib import Path

# Configurazione argomenti da riga di comando
parser = argparse.ArgumentParser(description="Esporta la telemetria delle auto dal JSON del replay.")
parser.add_argument(
    "--json_path", 
    type=str, 
    default=str(Path("parsed") / "rocketrp_test" / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"),
    help="Percorso al file JSON del match da analizzare."
)
args = parser.parse_args()

path = Path(args.json_path)
print(f"🚗 Lettura file JSON per telemetria auto: {path}")

with path.open("r", encoding="utf-8") as f:
    replay = json.load(f)

cars = {}
output = []

# Ricostruzione dello stato delle automobili.
for frame_number, frame in enumerate(replay["Frames"]):

    frame_time = frame.get("Time")

    for update in frame.get("ActorUpdates", []):

        channel = update.get("ChannelId")
        state = update.get("State")
        obj = update.get("ObjectName")

        if state == "Close":
            cars.pop(channel, None)
            continue

        if state == "Open":

            if obj != "TAGame.Car_TA":
                continue

            cars[channel] = {
                "name": update.get("Name"),
                "data": {},
                "initial_position": update.get(
                    "InitialPosition"
                )
            }

        if channel not in cars:
            continue

        car = cars[channel]

        if obj == "TAGame.Car_TA":

            car["data"].update(
                update.get("ActorData", {})
            )

        data = car["data"]

        pri = data.get(
            "PlayerReplicationInfo", {}
        )

        pri_target = pri.get("TargetIndex")

        rb = data.get("ReplicatedRBState", {})

        pos = rb.get("Position", {})
        vel = rb.get("LinearVelocity", {})

        initial = car.get("initial_position") or {}

        # Manteniamo l'ultima posizione conosciuta.
        x = pos.get("X", initial.get("X"))
        y = pos.get("Y", initial.get("Y"))
        z = pos.get("Z", initial.get("Z"))

        output.append({
            "frame": frame_number,
            "time": frame_time,
            "delta": frame.get("Delta"),
            "channel": channel,
            "car": car["name"],
            "pri": pri_target if pri_target is not None else -1,
            "x": x,
            "y": y,
            "z": z,
            "vx": vel.get("X"),
            "vy": vel.get("Y"),
            "vz": vel.get("Z"),
            "throttle": data.get("ReplicatedThrottle"),
            "steer": data.get("ReplicatedSteer"),
            "driving": data.get("bDriving")
        })

output_path = Path("car_telemetry.csv")

with output_path.open(
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=output[0].keys()
    )

    writer.writeheader()
    writer.writerows(output)

print(f"Esportate {len(output)} righe.")
print(f"File: {output_path}")