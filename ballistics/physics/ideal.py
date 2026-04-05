from __future__ import annotations

import math
from typing import Dict, TypedDict

from ballistics.constants import G


class IdealSimulationParams(TypedDict):
    angle: float
    speed: float
    dt: float


def analytical_metrics(speed: float, angle_deg: float, gravity: float = G) -> Dict[str, float]:
    angle_rad = math.radians(angle_deg)
    vx = speed * math.cos(angle_rad)
    vy = speed * math.sin(angle_rad)
    flight_time = 0.0 if gravity <= 0 else (2.0 * vy / gravity)
    max_height = 0.0 if gravity <= 0 else (vy * vy) / (2.0 * gravity)
    range_distance = vx * flight_time
    return {
        "flight_time": max(flight_time, 0.0),
        "max_height": max(max_height, 0.0),
        "range": max(range_distance, 0.0),
    }


def simulate_ideal_reference(params: IdealSimulationParams) -> Dict[str, object]:
    metrics = analytical_metrics(params["speed"], params["angle"])
    theta = math.radians(params["angle"])
    vx = params["speed"] * math.cos(theta)
    vy = params["speed"] * math.sin(theta)
    flight_time = metrics["flight_time"]
    step = max(params["dt"], (flight_time / 240.0) if flight_time > 0.0 else params["dt"])
    points: list[Dict[str, float]] = []
    t = 0.0

    while t <= flight_time:
        x = vx * t
        y = (vy * t) - (0.5 * G * t * t)
        points.append({"x": x, "y": max(0.0, y), "t": t, "vx": vx, "vy": vy - (G * t)})
        t += step

    peak_time = 0.0 if G <= 0.0 else max(vy / G, 0.0)
    if flight_time > 0.0:
        points.append({"x": metrics["range"], "y": 0.0, "t": flight_time, "vx": vx, "vy": -vy})
    return {
        "points": points,
        "metrics": {
            "range": metrics["range"],
            "maxHeight": metrics["max_height"],
            "flightTime": flight_time,
            "finalSpeed": math.hypot(vx, -vy),
            "peak": {"x": vx * peak_time, "y": metrics["max_height"]},
        },
    }
