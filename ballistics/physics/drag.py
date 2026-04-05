from __future__ import annotations

import math
from typing import TypedDict

from ballistics.constants import (
    AIR_GAS_CONSTANT,
    AIR_HEAT_CAPACITY_RATIO,
    DEFAULT_SHELL_BALLISTIC_COEFFICIENT,
    DEFAULT_SHELL_DRAG_MODEL,
    G,
    MIN_PRESSURE_ATM,
    SUTHERLAND_MU0,
    SUTHERLAND_S,
    SUTHERLAND_T0,
)

STANDARD_AIR_DENSITY = 1.225
FPS_TO_MPS = 0.3048
MPS_TO_FPS = 1.0 / FPS_TO_MPS

G1_DRAG_TABLE = (
    (4230.0, 1.477404177730177e-04, 1.9565),
    (3680.0, 1.920339268755614e-04, 1.925),
    (3450.0, 2.894751026819746e-04, 1.875),
    (3295.0, 4.349905111115636e-04, 1.825),
    (3130.0, 6.520421871892662e-04, 1.775),
    (2960.0, 9.748073694078696e-04, 1.725),
    (2830.0, 1.453721560187286e-03, 1.675),
    (2680.0, 2.162887202930376e-03, 1.625),
    (2460.0, 3.209559783129881e-03, 1.575),
    (2225.0, 3.904368218691249e-03, 1.55),
    (2015.0, 3.222942271262336e-03, 1.575),
    (1890.0, 2.203329542297809e-03, 1.625),
    (1810.0, 1.511001028891904e-03, 1.675),
    (1730.0, 8.609957592468259e-04, 1.75),
    (1595.0, 4.086146797305117e-04, 1.85),
    (1520.0, 1.954473210037398e-04, 1.95),
    (1420.0, 5.431896266462351e-05, 2.125),
    (1360.0, 8.847742581674416e-06, 2.375),
    (1315.0, 1.456922328720298e-06, 2.625),
    (1280.0, 2.419485191895565e-07, 2.875),
    (1220.0, 1.657956321067612e-08, 3.25),
    (1185.0, 4.745469537157371e-10, 3.75),
    (1150.0, 1.379746590025088e-11, 4.25),
    (1100.0, 4.070157961147882e-13, 4.75),
    (1060.0, 2.938236954847331e-14, 5.125),
    (1025.0, 1.228597370774746e-14, 5.25),
    (980.0, 2.916938264100495e-14, 5.125),
    (945.0, 3.855099424807451e-13, 4.75),
    (905.0, 1.185097045689854e-11, 4.25),
    (860.0, 3.566129470974951e-10, 3.75),
    (810.0, 1.045513263966272e-08, 3.25),
    (780.0, 1.291159200846216e-07, 2.875),
    (750.0, 6.824429329105383e-07, 2.625),
    (700.0, 3.569169672385163e-06, 2.375),
    (640.0, 1.839015095899579e-05, 2.125),
    (600.0, 5.711174688734240e-05, 1.95),
    (550.0, 9.226557091973427e-05, 1.875),
    (250.0, 9.337991957131389e-05, 1.875),
    (100.0, 7.225247327590413e-05, 1.925),
    (65.0, 5.792684957074546e-05, 1.975),
    (0.0, 5.206214107320588e-05, 2.0),
)

G7_DRAG_TABLE = (
    (4200.0, 1.29081656775919e-09, 3.24121295355962),
    (3000.0, 1.71422231434847e-02, 1.27907168025204),
    (1470.0, 2.33355948302505e-03, 1.52693913274526),
    (1260.0, 7.97592111627665e-04, 1.67688974440324),
    (1110.0, 5.71086414289273e-12, 4.3212826264889),
    (960.0, 3.02865108244904e-17, 5.99074203776707),
    (670.0, 7.52285155782535e-06, 2.1738019851075),
    (540.0, 1.31766281225189e-05, 2.08774690257991),
    (0.0, 1.34504843776525e-05, 2.08702306738884),
)

HL_SPHERE_A = math.exp(2.3288 - 6.4581 + 2.4486)
HL_SPHERE_B = 0.0964 + 0.5565
HL_SPHERE_C = math.exp(4.9050 - 13.8944 + 18.4222 - 10.2599)
HL_SPHERE_D = math.exp(1.4681 + 12.2584 - 20.7322 + 15.8855)


class AeroState(TypedDict):
    air_density: float
    viscosity: float
    speed_of_sound: float
    area: float
    reynolds: float
    mach: float
    base_drag_coefficient: float
    drag_coefficient: float
    drag_force: float
    projectile_shape: str
    sphericity: float
    drag_model: str
    ballistic_coefficient: float


class AccelerationState(TypedDict):
    ax: float
    ay: float
    aero: AeroState


def kelvin_from_celsius(temperature_c: float) -> float:
    return temperature_c + 273.15


def pressure_atm_to_pa(pressure_atm: float) -> float:
    return pressure_atm * 101325.0


def clamp_pressure_atm(pressure_atm: float) -> float:
    return max(pressure_atm, MIN_PRESSURE_ATM)


def air_density_from_conditions(temperature_c: float, pressure_atm: float) -> float:
    temperature_k = kelvin_from_celsius(temperature_c)
    if temperature_k <= 0:
        return 0.0
    return pressure_atm_to_pa(clamp_pressure_atm(pressure_atm)) / (AIR_GAS_CONSTANT * temperature_k)


def dynamic_viscosity_air(temperature_c: float) -> float:
    temperature_k = kelvin_from_celsius(temperature_c)
    if temperature_k <= 0:
        return 0.0
    return SUTHERLAND_MU0 * ((temperature_k / SUTHERLAND_T0) ** 1.5) * (
        (SUTHERLAND_T0 + SUTHERLAND_S) / (temperature_k + SUTHERLAND_S)
    )


def speed_of_sound_air(temperature_c: float) -> float:
    temperature_k = kelvin_from_celsius(temperature_c)
    if temperature_k <= 0:
        return 0.0
    return math.sqrt(AIR_HEAT_CAPACITY_RATIO * AIR_GAS_CONSTANT * temperature_k)


def mach_number(speed: float, temperature_c: float) -> float:
    sound_speed = speed_of_sound_air(temperature_c)
    if sound_speed <= 0 or speed <= 0:
        return 0.0
    return speed / sound_speed


def reynolds_number(density: float, speed: float, diameter: float, viscosity: float) -> float:
    if viscosity <= 0 or diameter <= 0 or density <= 0 or speed <= 0:
        return 0.0
    return density * speed * diameter / viscosity


def drag_coefficient_sphere(reynolds: float) -> float:
    if reynolds <= 0:
        return 0.0
    return (24.0 / reynolds) * (1.0 + HL_SPHERE_A * (reynolds**HL_SPHERE_B)) + (
        (HL_SPHERE_C * reynolds) / (HL_SPHERE_D + reynolds)
    )


def sphere_area_from_diameter(diameter: float) -> float:
    if diameter <= 0:
        return 0.0
    return math.pi * diameter * diameter / 4.0


def sphere_volume_from_diameter(diameter: float) -> float:
    if diameter <= 0:
        return 0.0
    return math.pi * diameter**3 / 6.0


def projectile_volume_from_diameter(diameter: float, volume_factor: float = 1.0) -> float:
    if volume_factor <= 0:
        return 0.0
    return sphere_volume_from_diameter(diameter) * volume_factor


def mass_from_material_density(material_density: float, diameter: float, volume_factor: float = 1.0) -> float:
    if material_density <= 0:
        return 0.0
    return material_density * projectile_volume_from_diameter(diameter, volume_factor)


def material_density_from_mass_and_diameter(mass: float, diameter: float, volume_factor: float = 1.0) -> float:
    volume = projectile_volume_from_diameter(diameter, volume_factor)
    if volume <= 0:
        return 0.0
    return mass / volume


def ballistic_drag_retardation_fps_s(speed_mps: float, drag_model: str, ballistic_coefficient: float) -> float:
    if speed_mps <= 0 or ballistic_coefficient <= 0:
        return 0.0
    speed_fps = speed_mps * MPS_TO_FPS
    drag_table = G1_DRAG_TABLE if drag_model == "g1" else G7_DRAG_TABLE
    for minimum_speed_fps, coefficient, exponent in drag_table:
        if speed_fps > minimum_speed_fps:
            return (coefficient * (speed_fps**exponent)) / ballistic_coefficient
    return 0.0


def ballistic_drag_acceleration(speed_mps: float, density: float, drag_model: str, ballistic_coefficient: float) -> float:
    if density <= 0:
        return 0.0
    standard_retardation_fps_s = ballistic_drag_retardation_fps_s(speed_mps, drag_model, ballistic_coefficient)
    density_ratio = density / STANDARD_AIR_DENSITY
    return standard_retardation_fps_s * density_ratio * FPS_TO_MPS


def compressibility_drag_multiplier(mach: float) -> float:
    if mach <= 0:
        return 1.0
    return 1.0 + ((mach * mach) / 4.0) + ((mach**4) / 40.0)


def _shared_aerodynamic_state(
    speed: float,
    temperature_c: float,
    pressure_atm: float,
    diameter: float,
    projectile_shape: str,
    sphericity: float,
    drag_model: str,
    ballistic_coefficient: float,
) -> AeroState:
    density = air_density_from_conditions(temperature_c, pressure_atm)
    viscosity = dynamic_viscosity_air(temperature_c)
    sound_speed = speed_of_sound_air(temperature_c)
    area = sphere_area_from_diameter(diameter)
    reynolds = reynolds_number(density, speed, diameter, viscosity)
    mach = mach_number(speed, temperature_c)
    normalized_drag_model = "g1" if drag_model == "g1" else DEFAULT_SHELL_DRAG_MODEL
    return {
        "air_density": density,
        "viscosity": viscosity,
        "speed_of_sound": sound_speed,
        "area": area,
        "reynolds": reynolds,
        "mach": mach,
        "base_drag_coefficient": 0.0,
        "drag_coefficient": 0.0,
        "drag_force": 0.0,
        "projectile_shape": projectile_shape,
        "sphericity": sphericity,
        "drag_model": normalized_drag_model,
        "ballistic_coefficient": ballistic_coefficient,
    }


def _sphere_aerodynamic_state(base_state: AeroState, speed: float) -> AeroState:
    base_drag_coefficient = drag_coefficient_sphere(base_state["reynolds"])
    drag_coefficient = base_drag_coefficient * compressibility_drag_multiplier(base_state["mach"])
    drag_force = 0.5 * base_state["air_density"] * drag_coefficient * base_state["area"] * speed * speed
    return {
        **base_state,
        "base_drag_coefficient": base_drag_coefficient,
        "drag_coefficient": drag_coefficient,
        "drag_force": drag_force,
        "ballistic_coefficient": 0.0,
    }


def _shell_aerodynamic_state(base_state: AeroState, speed: float, projectile_mass: float) -> AeroState:
    effective_ballistic_coefficient = (
        base_state["ballistic_coefficient"]
        if base_state["ballistic_coefficient"] > 0
        else DEFAULT_SHELL_BALLISTIC_COEFFICIENT
    )
    drag_accel = ballistic_drag_acceleration(
        speed,
        base_state["air_density"],
        base_state["drag_model"],
        effective_ballistic_coefficient,
    )
    drag_force = projectile_mass * drag_accel if projectile_mass > 0 else 0.0
    if base_state["air_density"] > 0 and base_state["area"] > 0 and speed > 0 and drag_force > 0:
        drag_coefficient = (2.0 * drag_force) / (
            base_state["air_density"] * base_state["area"] * speed * speed
        )
    else:
        drag_coefficient = 0.0
    return {
        **base_state,
        "base_drag_coefficient": drag_coefficient,
        "drag_coefficient": drag_coefficient,
        "drag_force": drag_force,
        "ballistic_coefficient": effective_ballistic_coefficient,
    }


def aerodynamic_state(
    speed: float,
    temperature_c: float,
    pressure_atm: float,
    diameter: float,
    projectile_shape: str = "sphere",
    sphericity: float = 1.0,
    projectile_mass: float = 0.0,
    drag_model: str = DEFAULT_SHELL_DRAG_MODEL,
    ballistic_coefficient: float = 0.0,
) -> AeroState:
    base_state = _shared_aerodynamic_state(
        speed,
        temperature_c,
        pressure_atm,
        diameter,
        projectile_shape,
        sphericity,
        drag_model,
        ballistic_coefficient,
    )
    if projectile_shape == "shell":
        return _shell_aerodynamic_state(base_state, speed, projectile_mass)
    return _sphere_aerodynamic_state(base_state, speed)


def drag_acceleration(
    vx: float,
    vy: float,
    projectile_mass: float,
    temperature_c: float,
    pressure_atm: float,
    diameter: float,
    projectile_shape: str,
    sphericity: float,
    drag_model: str,
    ballistic_coefficient: float,
) -> Dict[str, float]:
    speed = math.hypot(vx, vy)
    aero = aerodynamic_state(
        speed,
        temperature_c,
        pressure_atm,
        diameter,
        projectile_shape=projectile_shape,
        sphericity=sphericity,
        projectile_mass=projectile_mass,
        drag_model=drag_model,
        ballistic_coefficient=ballistic_coefficient,
    )
    drag_accel_scale = 0.0 if speed == 0.0 or projectile_mass <= 0.0 else aero["drag_force"] / (projectile_mass * speed)
    return {
        "ax": -drag_accel_scale * vx,
        "ay": -G - (drag_accel_scale * vy),
        "aero": aero,
    }


def simulate_drag_reference(params: Dict[str, float], max_steps: int = 25000) -> Dict[str, object]:
    theta = math.radians(params["angle"])
    x = 0.0
    y = 0.0
    vx = params["speed"] * math.cos(theta)
    vy = params["speed"] * math.sin(theta)
    dt = params["dt"]
    projectile_shape = params.get("projectileShape", "sphere")
    sphericity = params.get("sphericity", 1.0)
    volume_factor = params.get("volumeFactor", 1.0)
    drag_model = params.get("dragModel", DEFAULT_SHELL_DRAG_MODEL)
    ballistic_coefficient = params.get("ballisticCoefficient", 0.0)
    projectile_mass = mass_from_material_density(params["materialDensity"], params["diameter"], volume_factor)
    aero = aerodynamic_state(
        math.hypot(vx, vy),
        params["temperature"],
        params["pressure"],
        params["diameter"],
        projectile_shape=projectile_shape,
        sphericity=sphericity,
        projectile_mass=projectile_mass,
        drag_model=drag_model,
        ballistic_coefficient=ballistic_coefficient,
    )
    points = [{"x": x, "y": y, "t": 0.0, "vx": vx, "vy": vy, **aero}]
    t = 0.0
    max_height = 0.0
    peak = {"x": 0.0, "y": 0.0}

    for _ in range(max_steps):
        k1 = drag_acceleration(
            vx,
            vy,
            projectile_mass,
            params["temperature"],
            params["pressure"],
            params["diameter"],
            projectile_shape,
            sphericity,
            drag_model,
            ballistic_coefficient,
        )
        k2 = drag_acceleration(
            vx + (k1["ax"] * dt / 2.0),
            vy + (k1["ay"] * dt / 2.0),
            projectile_mass,
            params["temperature"],
            params["pressure"],
            params["diameter"],
            projectile_shape,
            sphericity,
            drag_model,
            ballistic_coefficient,
        )
        k3 = drag_acceleration(
            vx + (k2["ax"] * dt / 2.0),
            vy + (k2["ay"] * dt / 2.0),
            projectile_mass,
            params["temperature"],
            params["pressure"],
            params["diameter"],
            projectile_shape,
            sphericity,
            drag_model,
            ballistic_coefficient,
        )
        k4 = drag_acceleration(
            vx + (k3["ax"] * dt),
            vy + (k3["ay"] * dt),
            projectile_mass,
            params["temperature"],
            params["pressure"],
            params["diameter"],
            projectile_shape,
            sphericity,
            drag_model,
            ballistic_coefficient,
        )

        x += dt * (vx + 2.0 * (vx + (k1["ax"] * dt / 2.0)) + 2.0 * (vx + (k2["ax"] * dt / 2.0)) + (vx + (k3["ax"] * dt))) / 6.0
        y += dt * (vy + 2.0 * (vy + (k1["ay"] * dt / 2.0)) + 2.0 * (vy + (k2["ay"] * dt / 2.0)) + (vy + (k3["ay"] * dt))) / 6.0
        vx += dt * (k1["ax"] + (2.0 * k2["ax"]) + (2.0 * k3["ax"]) + k4["ax"]) / 6.0
        vy += dt * (k1["ay"] + (2.0 * k2["ay"]) + (2.0 * k3["ay"]) + k4["ay"]) / 6.0
        aero = aerodynamic_state(
            math.hypot(vx, vy),
            params["temperature"],
            params["pressure"],
            params["diameter"],
            projectile_shape=projectile_shape,
            sphericity=sphericity,
            projectile_mass=projectile_mass,
            drag_model=drag_model,
            ballistic_coefficient=ballistic_coefficient,
        )
        t += dt

        if y > max_height:
            max_height = y
            peak = {"x": x, "y": y}

        if y <= 0.0 and t > 0.0:
            prev = points[-1]
            ratio = prev["y"] / (prev["y"] - y) if prev["y"] != y else 1.0
            impact_x = prev["x"] + (x - prev["x"]) * ratio
            impact_t = prev["t"] + (t - prev["t"]) * ratio
            impact_vx = prev["vx"] + (vx - prev["vx"]) * ratio
            impact_vy = prev["vy"] + (vy - prev["vy"]) * ratio
            impact_aero = aerodynamic_state(
                math.hypot(impact_vx, impact_vy),
                params["temperature"],
                params["pressure"],
                params["diameter"],
                projectile_shape=projectile_shape,
                sphericity=sphericity,
                projectile_mass=projectile_mass,
                drag_model=drag_model,
                ballistic_coefficient=ballistic_coefficient,
            )
            points.append({"x": impact_x, "y": 0.0, "t": impact_t, "vx": impact_vx, "vy": impact_vy, **impact_aero})
            return {
                "points": points,
                "metrics": {
                    "range": impact_x,
                    "max_height": max_height,
                    "flight_time": impact_t,
                    "final_speed": math.hypot(impact_vx, impact_vy),
                    "peak": peak,
                },
                "aero": {
                    "projectile_mass": projectile_mass,
                    "projectile_shape": projectile_shape,
                    "sphericity": sphericity,
                    "drag_model": drag_model,
                    "ballistic_coefficient": ballistic_coefficient,
                    "air_density": impact_aero["air_density"],
                    "viscosity": impact_aero["viscosity"],
                    "area": impact_aero["area"],
                    "launch_reynolds": points[0]["reynolds"],
                    "launch_drag_coefficient": points[0]["drag_coefficient"],
                    "launch_drag_force": points[0]["drag_force"],
                    "impact_reynolds": impact_aero["reynolds"],
                    "impact_drag_coefficient": impact_aero["drag_coefficient"],
                    "impact_drag_force": impact_aero["drag_force"],
                },
            }

        points.append({"x": x, "y": y, "t": t, "vx": vx, "vy": vy, **aero})

    return {
        "points": points,
        "metrics": {
            "range": x,
            "max_height": max_height,
            "flight_time": t,
            "final_speed": math.hypot(vx, vy),
            "peak": peak,
        },
        "aero": {
            "projectile_mass": projectile_mass,
            "projectile_shape": projectile_shape,
            "sphericity": sphericity,
            "drag_model": drag_model,
            "ballistic_coefficient": ballistic_coefficient,
            "air_density": aero["air_density"],
            "viscosity": aero["viscosity"],
            "area": aero["area"],
            "launch_reynolds": points[0]["reynolds"],
            "launch_drag_coefficient": points[0]["drag_coefficient"],
            "launch_drag_force": points[0]["drag_force"],
            "impact_reynolds": aero["reynolds"],
            "impact_drag_coefficient": aero["drag_coefficient"],
            "impact_drag_force": aero["drag_force"],
        },
    }
