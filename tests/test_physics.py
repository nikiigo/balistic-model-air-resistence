import math
import unittest

from main import (
    AIR_GAS_CONSTANT,
    AIR_HEAT_CAPACITY_RATIO,
    G,
    MIN_PRESSURE_ATM,
    SUTHERLAND_MU0,
    aerodynamic_state,
    air_density_from_conditions,
    analytical_metrics,
    drag_coefficient_nonspherical,
    drag_coefficient_sphere,
    dynamic_viscosity_air,
    kelvin_from_celsius,
    mach_number,
    mass_from_material_density,
    material_density_from_mass_and_diameter,
    pressure_atm_to_pa,
    projectile_volume_from_diameter,
    reynolds_number,
    simulate_drag_reference,
    simulate_ideal_reference,
    speed_of_sound_air,
    sphere_area_from_diameter,
)


class AnalyticalMetricsTests(unittest.TestCase):
    def test_zero_angle_has_zero_height_and_time(self) -> None:
        metrics = analytical_metrics(speed=20, angle_deg=0)
        self.assertAlmostEqual(metrics["flight_time"], 0.0)
        self.assertAlmostEqual(metrics["max_height"], 0.0)
        self.assertAlmostEqual(metrics["range"], 0.0)

    def test_forty_five_degree_solution_matches_closed_form(self) -> None:
        speed = 30
        metrics = analytical_metrics(speed=speed, angle_deg=45)
        expected_range = (speed * speed) / G
        expected_height = (speed * speed) / (4 * G)
        expected_time = (2 * speed * math.sin(math.pi / 4)) / G

        self.assertAlmostEqual(metrics["range"], expected_range, places=6)
        self.assertAlmostEqual(metrics["max_height"], expected_height, places=6)
        self.assertAlmostEqual(metrics["flight_time"], expected_time, places=6)

    def test_complementary_angles_share_the_same_range(self) -> None:
        speed = 42
        lower = analytical_metrics(speed=speed, angle_deg=30)
        higher = analytical_metrics(speed=speed, angle_deg=60)
        self.assertAlmostEqual(lower["range"], higher["range"], places=6)


class AerodynamicHelpersTests(unittest.TestCase):
    def test_air_density_matches_ideal_gas_law_at_standard_conditions(self) -> None:
        density = air_density_from_conditions(temperature_c=15.0, pressure_atm=1.0)
        expected = pressure_atm_to_pa(1.0) / (AIR_GAS_CONSTANT * kelvin_from_celsius(15.0))
        self.assertAlmostEqual(density, expected, places=9)
        self.assertAlmostEqual(density, 1.225, places=3)

    def test_air_density_clamps_pressure_to_supported_floor(self) -> None:
        clamped = air_density_from_conditions(temperature_c=15.0, pressure_atm=0.0)
        minimum = air_density_from_conditions(temperature_c=15.0, pressure_atm=MIN_PRESSURE_ATM)
        self.assertAlmostEqual(clamped, minimum, places=9)

    def test_dynamic_viscosity_matches_reference_value_at_zero_celsius(self) -> None:
        viscosity = dynamic_viscosity_air(0.0)
        self.assertAlmostEqual(viscosity, SUTHERLAND_MU0, places=9)

    def test_speed_of_sound_matches_ideal_gas_relation(self) -> None:
        speed = speed_of_sound_air(15.0)
        expected = math.sqrt(AIR_HEAT_CAPACITY_RATIO * AIR_GAS_CONSTANT * kelvin_from_celsius(15.0))
        self.assertAlmostEqual(speed, expected, places=9)

    def test_mach_number_matches_speed_ratio(self) -> None:
        speed = speed_of_sound_air(15.0) * 0.75
        self.assertAlmostEqual(mach_number(speed, 15.0), 0.75, places=9)

    def test_sphere_area_from_diameter(self) -> None:
        self.assertAlmostEqual(sphere_area_from_diameter(0.1), math.pi * 0.01 / 4.0, places=9)

    def test_drag_coefficient_piecewise_regimes(self) -> None:
        self.assertAlmostEqual(drag_coefficient_sphere(0.05), 480.0, places=6)
        transitional = drag_coefficient_sphere(100.0)
        expected = (24.0 / 100.0) * (1.0 + 0.15 * (100.0 ** 0.687))
        self.assertAlmostEqual(transitional, expected, places=9)
        self.assertAlmostEqual(drag_coefficient_sphere(5000.0), 0.44, places=9)

    def test_nonspherical_drag_correlation_differs_from_sphere(self) -> None:
        shell_cd = drag_coefficient_nonspherical(5000.0, 0.65)
        sphere_cd = drag_coefficient_sphere(5000.0)
        self.assertGreater(shell_cd, 0.0)
        self.assertNotAlmostEqual(shell_cd, sphere_cd, places=6)

    def test_reynolds_number_zeroes_for_non_physical_inputs(self) -> None:
        self.assertEqual(reynolds_number(0.0, 10.0, 0.1, 1.8e-5), 0.0)
        self.assertEqual(reynolds_number(1.2, 0.0, 0.1, 1.8e-5), 0.0)
        self.assertEqual(reynolds_number(1.2, 10.0, 0.0, 1.8e-5), 0.0)
        self.assertEqual(reynolds_number(1.2, 10.0, 0.1, 0.0), 0.0)

    def test_material_density_round_trip_matches_mass(self) -> None:
        density = material_density_from_mass_and_diameter(5.0, 0.1)
        self.assertAlmostEqual(mass_from_material_density(density, 0.1), 5.0, places=9)

    def test_shape_volume_factor_changes_mass_consistently(self) -> None:
        elongated_volume = projectile_volume_from_diameter(0.1, 2.5)
        spherical_volume = projectile_volume_from_diameter(0.1, 1.0)
        self.assertGreater(elongated_volume, spherical_volume)
        self.assertAlmostEqual(
            mass_from_material_density(7800.0, 0.1, 2.5),
            7800.0 * elongated_volume,
            places=9,
        )

    def test_aerodynamic_state_consistency(self) -> None:
        aero = aerodynamic_state(speed=100.0, temperature_c=15.0, pressure_atm=1.0, diameter=0.1)
        self.assertAlmostEqual(aero["area"], sphere_area_from_diameter(0.1), places=9)
        self.assertGreater(aero["air_density"], 1.0)
        self.assertGreater(aero["viscosity"], 0.0)
        self.assertGreater(aero["speed_of_sound"], 300.0)
        self.assertGreater(aero["reynolds"], 0.0)
        self.assertGreater(aero["mach"], 0.0)
        self.assertGreater(aero["base_drag_coefficient"], 0.0)
        self.assertGreater(aero["drag_coefficient"], 0.0)
        self.assertGreater(aero["drag_force"], 0.0)


class DragSimulationRegressionTests(unittest.TestCase):
    def base_params(self) -> dict[str, float]:
        return {
            "angle": 35.0,
            "speed": 120.0,
            "materialDensity": material_density_from_mass_and_diameter(5.0, 0.1),
            "temperature": 15.0,
            "pressure": 1.0,
            "diameter": 0.1,
            "dt": 0.01,
        }

    def test_pressure_below_supported_floor_clamps_to_minimum(self) -> None:
        clamped = simulate_drag_reference({**self.base_params(), "pressure": 0.0})
        minimum = simulate_drag_reference({**self.base_params(), "pressure": MIN_PRESSURE_ATM})
        self.assertAlmostEqual(clamped["metrics"]["range"], minimum["metrics"]["range"], places=9)
        self.assertAlmostEqual(clamped["aero"]["launch_drag_force"], minimum["aero"]["launch_drag_force"], places=9)

    def test_higher_pressure_increases_drag_and_reduces_range(self) -> None:
        low_pressure = simulate_drag_reference({**self.base_params(), "pressure": MIN_PRESSURE_ATM})
        high_pressure = simulate_drag_reference({**self.base_params(), "pressure": 1.2})

        self.assertGreater(high_pressure["aero"]["launch_drag_force"], low_pressure["aero"]["launch_drag_force"])
        self.assertLess(high_pressure["metrics"]["range"], low_pressure["metrics"]["range"])

    def test_larger_diameter_increases_drag_and_reduces_range(self) -> None:
        small = simulate_drag_reference({**self.base_params(), "diameter": 0.05})
        large = simulate_drag_reference({**self.base_params(), "diameter": 0.2})

        self.assertGreater(large["aero"]["area"], small["aero"]["area"])
        self.assertGreater(large["aero"]["projectile_mass"], small["aero"]["projectile_mass"])
        self.assertGreater(large["aero"]["launch_drag_force"], small["aero"]["launch_drag_force"])

    def test_higher_temperature_reduces_density(self) -> None:
        cold = aerodynamic_state(speed=120.0, temperature_c=-10.0, pressure_atm=1.0, diameter=0.1)
        warm = aerodynamic_state(speed=120.0, temperature_c=30.0, pressure_atm=1.0, diameter=0.1)

        self.assertLess(warm["air_density"], cold["air_density"])

    def test_shell_shape_uses_nonspherical_drag_model(self) -> None:
        sphere = aerodynamic_state(speed=200.0, temperature_c=15.0, pressure_atm=1.0, diameter=0.076)
        shell = aerodynamic_state(
            speed=200.0,
            temperature_c=15.0,
            pressure_atm=1.0,
            diameter=0.076,
            projectile_shape="shell",
            sphericity=0.65,
        )
        self.assertNotAlmostEqual(shell["drag_coefficient"], sphere["drag_coefficient"], places=6)
        self.assertLess(shell["drag_coefficient"], sphere["drag_coefficient"])

    def test_high_mach_flow_increases_drag_coefficient_above_base_reynolds_value(self) -> None:
        subsonic = aerodynamic_state(speed=200.0, temperature_c=15.0, pressure_atm=1.0, diameter=0.1)
        transonic = aerodynamic_state(speed=340.0, temperature_c=15.0, pressure_atm=1.0, diameter=0.1)

        self.assertLess(subsonic["mach"], 0.7)
        self.assertGreater(transonic["mach"], 0.95)
        self.assertAlmostEqual(subsonic["drag_coefficient"], subsonic["base_drag_coefficient"], places=9)
        self.assertGreater(transonic["drag_coefficient"], transonic["base_drag_coefficient"])
        self.assertGreater(transonic["drag_coefficient"], subsonic["drag_coefficient"])

    def test_artillery_shell_launch_drag_coefficient_stays_in_reasonable_range(self) -> None:
        shell = aerodynamic_state(
            speed=370.0,
            temperature_c=15.0,
            pressure_atm=1.0,
            diameter=0.076,
            projectile_shape="shell",
            sphericity=0.66,
        )
        self.assertGreater(shell["mach"], 1.0)
        self.assertLess(shell["drag_coefficient"], 1.0)

    def test_rk4_solution_converges_as_time_step_shrinks(self) -> None:
        coarse = simulate_drag_reference({**self.base_params(), "dt": 0.02})
        medium = simulate_drag_reference({**self.base_params(), "dt": 0.01})
        fine = simulate_drag_reference({**self.base_params(), "dt": 0.005})
        reference = simulate_drag_reference({**self.base_params(), "dt": 0.0025})

        coarse_error = abs(coarse["metrics"]["range"] - reference["metrics"]["range"])
        medium_error = abs(medium["metrics"]["range"] - reference["metrics"]["range"])
        fine_error = abs(fine["metrics"]["range"] - reference["metrics"]["range"])

        self.assertGreater(coarse_error, medium_error)
        self.assertGreater(medium_error, fine_error)
        self.assertLess(fine_error, 0.05)

    def test_impact_metrics_match_interpolated_final_point_state(self) -> None:
        result = simulate_drag_reference({**self.base_params(), "dt": 0.02})
        final_point = result["points"][-1]

        self.assertEqual(final_point["y"], 0.0)
        self.assertAlmostEqual(result["metrics"]["final_speed"], math.hypot(final_point["vx"], final_point["vy"]), places=9)
        self.assertAlmostEqual(result["aero"]["impact_reynolds"], final_point["reynolds"], places=9)
        self.assertAlmostEqual(result["aero"]["impact_drag_coefficient"], final_point["drag_coefficient"], places=9)
        self.assertAlmostEqual(result["aero"]["impact_drag_force"], final_point["drag_force"], places=9)

    def test_ideal_reference_matches_closed_form_metrics(self) -> None:
        params = self.base_params()
        ideal = simulate_ideal_reference(params)
        analytical = analytical_metrics(params["speed"], params["angle"])

        self.assertAlmostEqual(ideal["metrics"]["range"], analytical["range"], places=9)
        self.assertAlmostEqual(ideal["metrics"]["maxHeight"], analytical["max_height"], places=9)
        self.assertAlmostEqual(ideal["metrics"]["flightTime"], analytical["flight_time"], places=9)

    def test_streamlined_shell_range_is_not_crushed_by_particle_drag_correlation(self) -> None:
        params = {
            "angle": 10.0,
            "speed": 370.0,
            "materialDensity": material_density_from_mass_and_diameter(4.3, 0.076, 2.4),
            "temperature": 15.0,
            "pressure": 1.0,
            "diameter": 0.076,
            "dt": 0.01,
            "projectileShape": "shell",
            "sphericity": 0.66,
            "volumeFactor": 2.4,
        }
        drag = simulate_drag_reference(params)
        ideal = simulate_ideal_reference(params)
        self.assertGreater(drag["metrics"]["range"], 1500.0)
        self.assertGreater(drag["metrics"]["range"] / ideal["metrics"]["range"], 0.3)
