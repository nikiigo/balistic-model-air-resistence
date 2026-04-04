import math
import unittest

from main import (
    AIR_GAS_CONSTANT,
    G,
    HTML_PAGE,
    SUTHERLAND_MU0,
    aerodynamic_state,
    air_density_from_conditions,
    analytical_metrics,
    drag_coefficient_nonspherical,
    drag_coefficient_sphere,
    dynamic_viscosity_air,
    kelvin_from_celsius,
    projectile_volume_from_diameter,
    pressure_atm_to_pa,
    reynolds_number,
    simulate_drag_reference,
    material_density_from_mass_and_diameter,
    mass_from_material_density,
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

    def test_dynamic_viscosity_matches_reference_value_at_zero_celsius(self) -> None:
        viscosity = dynamic_viscosity_air(0.0)
        self.assertAlmostEqual(viscosity, SUTHERLAND_MU0, places=9)

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
        self.assertGreater(aero["reynolds"], 0.0)
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

    def test_zero_pressure_reduces_drag_relative_to_standard_pressure(self) -> None:
        standard = simulate_drag_reference(self.base_params())
        vacuumish = simulate_drag_reference({**self.base_params(), "pressure": 0.0})
        ideal = analytical_metrics(speed=self.base_params()["speed"], angle_deg=self.base_params()["angle"])["range"]

        self.assertLess(standard["metrics"]["range"], ideal)
        self.assertGreater(vacuumish["metrics"]["range"], standard["metrics"]["range"])
        self.assertLess(vacuumish["aero"]["launch_drag_force"], 1e-9)

    def test_higher_pressure_increases_drag_and_reduces_range(self) -> None:
        low_pressure = simulate_drag_reference({**self.base_params(), "pressure": 0.8})
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


class FrontendContractTests(unittest.TestCase):
    def test_pressure_slider_allows_zero_for_validation_cue(self) -> None:
        self.assertIn('id="pressure" type="range" min="0" max="1.2"', HTML_PAGE)

    def test_material_density_control_can_expand_for_dense_historic_presets(self) -> None:
        self.assertIn("function syncMaterialDensityLimit(materialDensity)", HTML_PAGE)
        self.assertIn("Math.max(defaultMaterialDensityMax, roundedMax)", HTML_PAGE)

    def test_plot_bounds_keep_at_least_the_requested_axes_but_do_not_clip_presets_by_default(self) -> None:
        self.assertIn("FIXED_PLOT_BOUNDS.maxX = Math.max(2400, FIXED_PLOT_BOUNDS.maxX);", HTML_PAGE)
        self.assertIn("FIXED_PLOT_BOUNDS.maxY = Math.max(850, FIXED_PLOT_BOUNDS.maxY);", HTML_PAGE)

    def test_historic_guns_use_stable_per_gun_plot_bounds(self) -> None:
        self.assertIn("const HISTORICAL_GUN_PLOT_BOUNDS = Object.fromEntries(", HTML_PAGE)
        self.assertIn("function activePlotBounds()", HTML_PAGE)
        self.assertIn("function computeFocusedPlotBounds(params)", HTML_PAGE)
        self.assertIn("return state.currentGun ? HISTORICAL_GUN_PLOT_BOUNDS[state.currentGun] : FIXED_PLOT_BOUNDS;", HTML_PAGE)

    def test_selected_gun_can_be_customized_without_leaving_gun_context(self) -> None:
        self.assertIn("presetModified: false", HTML_PAGE)
        self.assertIn("state.presetModified = !paramsMatch(state.params, historicalGuns[state.currentGun].params);", HTML_PAGE)
        self.assertIn('historicalGuns[state.currentGun].name}${state.presetModified ? " custom" : ""}', HTML_PAGE)

    def test_resize_redraws_without_rerunning_physics(self) -> None:
        self.assertIn("function recalculatePhysics()", HTML_PAGE)
        self.assertIn("function redrawDisplay()", HTML_PAGE)
        self.assertIn('window.addEventListener("resize", redrawDisplay);', HTML_PAGE)

    def test_launch_controls_expose_projectile_shape_toggle(self) -> None:
        self.assertIn('id="shapeSphereBtn"', HTML_PAGE)
        self.assertIn('id="shapeShellBtn"', HTML_PAGE)
        self.assertIn("function setProjectileShape(shape, options = {})", HTML_PAGE)


if __name__ == "__main__":
    unittest.main()
