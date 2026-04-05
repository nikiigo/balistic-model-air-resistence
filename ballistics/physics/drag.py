from __future__ import annotations

import math
from typing import Dict

from ballistics.constants import (
    AIR_GAS_CONSTANT,
    AIR_HEAT_CAPACITY_RATIO,
    G,
    MIN_PRESSURE_ATM,
    SUTHERLAND_MU0,
    SUTHERLAND_S,
    SUTHERLAND_T0,
)


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


def smoothstep(value: float, edge0: float, edge1: float) -> float:
    if edge1 <= edge0:
        return 0.0
    scaled = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return scaled * scaled * (3.0 - (2.0 * scaled))


def interpolate(value: float, edge0: float, edge1: float, start: float, end: float) -> float:
    return start + ((end - start) * smoothstep(value, edge0, edge1))


def drag_coefficient_sphere(reynolds: float) -> float:
    if reynolds <= 0:
        return 0.0
    if reynolds < 0.1:
        return 24.0 / reynolds
    if reynolds < 1000.0:
        return (24.0 / reynolds) * (1.0 + 0.15 * (reynolds ** 0.687))
    return 0.44


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


def drag_coefficient_nonspherical(reynolds: float, sphericity: float) -> float:
    if reynolds <= 0 or sphericity <= 0 or sphericity > 1:
        return 0.0
    # The old Haider-Levenspiel particle correlation drastically overpredicted
    # drag for streamlined artillery-style projectiles at high Reynolds number.
    # For this simulator, the "shell" branch is intended to represent elongated,
    # relatively streamlined projectiles, so use the spherical base correlation
    # with a bounded streamlining factor instead.
    sphere_base_drag = drag_coefficient_sphere(reynolds)
    streamlining_factor = interpolate(sphericity, 0.35, 1.0, 0.38, 1.0)
    return sphere_base_drag * streamlining_factor


def compressibility_drag_multiplier_shell(mach: float) -> float:
    if mach <= 0.7:
        return 1.0
    if mach < 0.95:
        return interpolate(mach, 0.7, 0.95, 1.0, 1.18)
    if mach < 1.1:
        return interpolate(mach, 0.95, 1.1, 1.18, 1.55)
    if mach < 1.5:
        return interpolate(mach, 1.1, 1.5, 1.55, 1.35)
    return 1.35


def compressibility_drag_multiplier(mach: float) -> float:
    if mach <= 0.6:
        return 1.0
    if mach < 0.9:
        return interpolate(mach, 0.6, 0.9, 1.0, 1.35)
    if mach < 1.1:
        return interpolate(mach, 0.9, 1.1, 1.35, 2.15)
    if mach < 1.5:
        return interpolate(mach, 1.1, 1.5, 2.15, 2.0)
    return 2.0


def aerodynamic_state(
    speed: float,
    temperature_c: float,
    pressure_atm: float,
    diameter: float,
    projectile_shape: str = "sphere",
    sphericity: float = 1.0,
) -> Dict[str, float]:
    density = air_density_from_conditions(temperature_c, pressure_atm)
    viscosity = dynamic_viscosity_air(temperature_c)
    sound_speed = speed_of_sound_air(temperature_c)
    area = sphere_area_from_diameter(diameter)
    reynolds = reynolds_number(density, speed, diameter, viscosity)
    mach = mach_number(speed, temperature_c)
    if projectile_shape == "shell":
        base_drag_coefficient = drag_coefficient_nonspherical(reynolds, sphericity)
        drag_coefficient = base_drag_coefficient * compressibility_drag_multiplier_shell(mach)
    else:
        base_drag_coefficient = drag_coefficient_sphere(reynolds)
        drag_coefficient = base_drag_coefficient * compressibility_drag_multiplier(mach)
    drag_force = 0.5 * density * drag_coefficient * area * speed * speed
    return {
        "air_density": density,
        "viscosity": viscosity,
        "speed_of_sound": sound_speed,
        "area": area,
        "reynolds": reynolds,
        "mach": mach,
        "base_drag_coefficient": base_drag_coefficient,
        "drag_coefficient": drag_coefficient,
        "drag_force": drag_force,
        "projectile_shape": projectile_shape,
        "sphericity": sphericity,
    }


def drag_acceleration(
    vx: float,
    vy: float,
    projectile_mass: float,
    temperature_c: float,
    pressure_atm: float,
    diameter: float,
    projectile_shape: str,
    sphericity: float,
) -> Dict[str, float]:
    speed = math.hypot(vx, vy)
    aero = aerodynamic_state(
        speed,
        temperature_c,
        pressure_atm,
        diameter,
        projectile_shape=projectile_shape,
        sphericity=sphericity,
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
    projectile_mass = mass_from_material_density(params["materialDensity"], params["diameter"], volume_factor)
    aero = aerodynamic_state(
        math.hypot(vx, vy),
        params["temperature"],
        params["pressure"],
        params["diameter"],
        projectile_shape=projectile_shape,
        sphericity=sphericity,
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
