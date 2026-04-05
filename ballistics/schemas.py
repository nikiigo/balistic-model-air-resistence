from __future__ import annotations

import math
from typing import Any, TypedDict

from ballistics.constants import (
    DEFAULT_SHELL_BALLISTIC_COEFFICIENT,
    DEFAULT_SHELL_DRAG_MODEL,
    MAX_ANGLE_DEG,
    MAX_BALLISTIC_COEFFICIENT,
    MAX_DIAMETER_M,
    MAX_DT,
    MAX_MATERIAL_DENSITY,
    MAX_PRESSURE_ATM,
    MAX_SPEED,
    MAX_SPHERICITY,
    MAX_TEMPERATURE_C,
    MAX_VOLUME_FACTOR,
    MIN_ANGLE_DEG,
    MIN_BALLISTIC_COEFFICIENT,
    MIN_DIAMETER_M,
    MIN_DT,
    MIN_MATERIAL_DENSITY,
    MIN_PRESSURE_ATM,
    MIN_SPEED,
    MIN_SPHERICITY,
    MIN_TEMPERATURE_C,
    MIN_VOLUME_FACTOR,
)
from ballistics.physics.drag import simulate_drag_reference
from ballistics.physics.ideal import simulate_ideal_reference
from ballistics.presets import DEFAULT_SIMULATION_PARAMS, HISTORICAL_PLOT_REFERENCE_PARAMS, REFERENCE_PRESETS


class SimulationParams(TypedDict):
    angle: float
    speed: float
    materialDensity: float
    temperature: float
    pressure: float
    diameter: float
    dt: float
    projectileShape: str
    sphericity: float
    volumeFactor: float
    dragModel: str
    ballisticCoefficient: float


class PlotBounds(TypedDict):
    maxX: float
    maxY: float


class SerializedDragPoint(TypedDict):
    x: float
    y: float
    t: float
    vx: float
    vy: float
    airDensity: float
    viscosity: float
    speedOfSound: float
    area: float
    reynolds: float
    mach: float
    baseDragCoefficient: float
    dragCoefficient: float
    dragForce: float


class SerializedDragResult(TypedDict):
    points: list[SerializedDragPoint]
    metrics: dict[str, Any]
    aero: dict[str, Any]


class SimulationResponse(TypedDict):
    ideal: dict[str, Any]
    drag: SerializedDragResult
    focusedBounds: PlotBounds
    stableBounds: PlotBounds


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def compute_plot_bounds(params: SimulationParams) -> PlotBounds:
    sampled_angles = [5.0, 15.0, 25.0, 35.0, 45.0, 55.0, 65.0, 75.0, 85.0]
    max_x = 1.0
    max_y = 1.0

    for angle in sampled_angles:
        sample_params = {**params, "angle": angle}
        ideal = simulate_ideal_reference(sample_params)
        drag = simulate_drag_reference(sample_params)
        max_x = max(max_x, ideal["metrics"]["range"], drag["metrics"]["range"])
        max_y = max(max_y, ideal["metrics"]["maxHeight"], drag["metrics"]["max_height"])

    return {"maxX": max_x * 1.08, "maxY": max_y * 1.15}


def compute_focused_plot_bounds(params: SimulationParams) -> PlotBounds:
    sampled_angles = sorted({
        max(5.0, params["angle"] - 10.0),
        params["angle"],
        min(85.0, params["angle"] + 10.0),
    })
    max_x = 1.0
    max_y = 1.0

    for angle in sampled_angles:
        sample_params = {**params, "angle": angle}
        ideal = simulate_ideal_reference(sample_params)
        drag = simulate_drag_reference(sample_params)
        max_x = max(max_x, ideal["metrics"]["range"], drag["metrics"]["range"])
        max_y = max(max_y, ideal["metrics"]["maxHeight"], drag["metrics"]["max_height"])

    return {"maxX": max_x * 1.1, "maxY": max_y * 1.18}


def serialize_drag_result(result: dict[str, Any]) -> SerializedDragResult:
    points = [
        {
            "x": point["x"],
            "y": point["y"],
            "t": point["t"],
            "vx": point["vx"],
            "vy": point["vy"],
            "airDensity": point["air_density"],
            "viscosity": point["viscosity"],
            "speedOfSound": point["speed_of_sound"],
            "area": point["area"],
            "reynolds": point["reynolds"],
            "mach": point["mach"],
            "baseDragCoefficient": point["base_drag_coefficient"],
            "dragCoefficient": point["drag_coefficient"],
            "dragForce": point["drag_force"],
        }
        for point in result["points"]
    ]
    metrics = result["metrics"]
    aero = result["aero"]
    return {
        "points": points,
        "metrics": {
            "range": metrics["range"],
            "maxHeight": metrics["max_height"],
            "flightTime": metrics["flight_time"],
            "finalSpeed": metrics["final_speed"],
            "peak": metrics["peak"],
        },
        "aero": {
            "projectileMass": aero["projectile_mass"],
            "projectileShape": aero["projectile_shape"],
            "sphericity": aero["sphericity"],
            "dragModel": aero["drag_model"],
            "ballisticCoefficient": aero["ballistic_coefficient"],
            "airDensity": aero["air_density"],
            "viscosity": aero["viscosity"],
            "area": aero["area"],
            "launchReynolds": aero["launch_reynolds"],
            "launchDragCoefficient": aero["launch_drag_coefficient"],
            "launchDragForce": aero["launch_drag_force"],
            "impactReynolds": aero["impact_reynolds"],
            "impactDragCoefficient": aero["impact_drag_coefficient"],
            "impactDragForce": aero["impact_drag_force"],
        },
    }


PLOT_REFERENCE_SCENARIOS: list[SimulationParams] = [
    DEFAULT_SIMULATION_PARAMS,
    *REFERENCE_PRESETS.values(),
    *HISTORICAL_PLOT_REFERENCE_PARAMS.values(),
    {**DEFAULT_SIMULATION_PARAMS, "angle": 45.0, "speed": 440.0, "pressure": MIN_PRESSURE_ATM},
    {**DEFAULT_SIMULATION_PARAMS, "angle": 85.0, "speed": 440.0, "pressure": MIN_PRESSURE_ATM},
    {
        **DEFAULT_SIMULATION_PARAMS,
        "angle": 45.0,
        "speed": 440.0,
        "materialDensity": 12000.0,
        "temperature": -10.0,
        "pressure": 1.2,
        "diameter": 0.01,
    },
]

FIXED_PLOT_BOUNDS: PlotBounds = {"maxX": 1.0, "maxY": 1.0}
for _plot_params in PLOT_REFERENCE_SCENARIOS:
    _sample_bounds = compute_plot_bounds(_plot_params)
    FIXED_PLOT_BOUNDS["maxX"] = max(FIXED_PLOT_BOUNDS["maxX"], _sample_bounds["maxX"])
    FIXED_PLOT_BOUNDS["maxY"] = max(FIXED_PLOT_BOUNDS["maxY"], _sample_bounds["maxY"])
FIXED_PLOT_BOUNDS["maxX"] = max(2400.0, FIXED_PLOT_BOUNDS["maxX"])
FIXED_PLOT_BOUNDS["maxY"] = max(850.0, FIXED_PLOT_BOUNDS["maxY"])

HISTORICAL_GUN_PLOT_BOUNDS: dict[str, PlotBounds] = {}
for _gun_key, _gun_params in HISTORICAL_PLOT_REFERENCE_PARAMS.items():
    _gun_bounds = compute_focused_plot_bounds(_gun_params)
    HISTORICAL_GUN_PLOT_BOUNDS[_gun_key] = {
        "maxX": max(200.0, _gun_bounds["maxX"]),
        "maxY": max(80.0, _gun_bounds["maxY"]),
    }


def normalize_simulation_params(payload: dict[str, object]) -> SimulationParams:
    params: SimulationParams = {**DEFAULT_SIMULATION_PARAMS}
    numeric_fields = (
        "angle",
        "speed",
        "materialDensity",
        "temperature",
        "pressure",
        "diameter",
        "dt",
        "sphericity",
        "volumeFactor",
        "ballisticCoefficient",
    )
    for field in numeric_fields:
        if field in payload:
            candidate = float(payload[field])
            if not math.isfinite(candidate):
                raise ValueError(f"{field} must be finite.")
            params[field] = candidate

    projectile_shape = str(payload.get("projectileShape", params["projectileShape"]))
    params["projectileShape"] = "shell" if projectile_shape == "shell" else "sphere"
    drag_model = str(payload.get("dragModel", params.get("dragModel", DEFAULT_SHELL_DRAG_MODEL))).lower()
    params["dragModel"] = "g1" if drag_model == "g1" else DEFAULT_SHELL_DRAG_MODEL
    params["angle"] = clamp(float(params["angle"]), MIN_ANGLE_DEG, MAX_ANGLE_DEG)
    params["speed"] = clamp(float(params["speed"]), MIN_SPEED, MAX_SPEED)
    params["materialDensity"] = clamp(float(params["materialDensity"]), MIN_MATERIAL_DENSITY, MAX_MATERIAL_DENSITY)
    params["temperature"] = clamp(float(params["temperature"]), MIN_TEMPERATURE_C, MAX_TEMPERATURE_C)
    params["pressure"] = clamp(float(params["pressure"]), MIN_PRESSURE_ATM, MAX_PRESSURE_ATM)
    params["diameter"] = clamp(float(params["diameter"]), MIN_DIAMETER_M, MAX_DIAMETER_M)
    params["dt"] = clamp(float(params["dt"]), MIN_DT, MAX_DT)
    if params["projectileShape"] != "shell":
        params["sphericity"] = 1.0
        params["volumeFactor"] = 1.0
        params["ballisticCoefficient"] = 0.0
    else:
        params["sphericity"] = clamp(float(params["sphericity"]), MIN_SPHERICITY, MAX_SPHERICITY)
        params["volumeFactor"] = clamp(float(params["volumeFactor"]), MIN_VOLUME_FACTOR, MAX_VOLUME_FACTOR)
        if "ballisticCoefficient" not in payload:
            params["ballisticCoefficient"] = DEFAULT_SHELL_BALLISTIC_COEFFICIENT
        params["ballisticCoefficient"] = clamp(
            float(params.get("ballisticCoefficient", DEFAULT_SHELL_BALLISTIC_COEFFICIENT)),
            MIN_BALLISTIC_COEFFICIENT,
            MAX_BALLISTIC_COEFFICIENT,
        )
    return params


def simulation_response(payload: dict[str, object]) -> SimulationResponse:
    params = normalize_simulation_params(payload)
    current_gun = payload.get("currentGun")
    ideal = simulate_ideal_reference(params)
    drag = serialize_drag_result(simulate_drag_reference(params))
    focused_bounds = compute_focused_plot_bounds(params)
    stable_bounds = HISTORICAL_GUN_PLOT_BOUNDS.get(str(current_gun), FIXED_PLOT_BOUNDS)
    return {
        "ideal": ideal,
        "drag": drag,
        "focusedBounds": focused_bounds,
        "stableBounds": stable_bounds,
    }
