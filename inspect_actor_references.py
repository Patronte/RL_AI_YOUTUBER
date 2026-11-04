
import json
from pathlib import Path

json_path = (
    Path("parsed")
    / "rocketrp_test"
    / "3D37EE4411F1D7AB02548DB2DDA89CDC.json"
)

with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Indice degli attori aperti.
actors = {}

for frame in data["Frames"]:
    for actor in frame.get("ActorUpdates", []):

        channel = actor.get("ChannelId")
        state = actor.get("State")

        if state == "Close":
            actors.pop(channel, None)
            continue

        if state == "Open":
            actors[channel] = {
                "name": actor.get("Name"),
                "object": actor.get("ObjectName"),
                "target": actor.get("TypeId", {}).get("TargetIndex"),
                "data": {}
            }

        if channel in actors:
            actors[channel]["data"].update(
                actor.get("ActorData", {})
            )

print("\n========== CAR ACTORS ==========")

cars = {}

for channel, actor in actors.items():
    if actor["object"] == "TAGame.Car_TA":
        cars[channel] = actor
        print(
            f"Channel={channel} "
            f"Name={actor['name']} "
            f"Target={actor['target']}"
        )

print("\n========== COMPONENT REFERENCES ==========")

for channel, actor in actors.items():

    if actor["object"] not in [
        "TAGame.CarComponent_Jump_TA",
        "TAGame.CarComponent_DoubleJump_TA",
        "TAGame.CarComponent_Dodge_TA",
        "TAGame.CarComponent_FlipCar_TA"
    ]:
        continue

    vehicle = actor["data"].get("Vehicle", {})

    target = vehicle.get("TargetIndex")

    matching_cars = [
    (car_channel, car)
    for car_channel, car in cars.items()
    if car_channel == target
]

    print(
        f"\nComponent Channel={channel}"
        f"\nType={actor['object']}"
        f"\nVehicle Target={target}"
        f"\nMatching Cars={[(c, x['name']) for c, x in matching_cars]}"
    )
