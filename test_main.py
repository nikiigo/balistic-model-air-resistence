import json
import math
import re
import unittest
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

from main import (
    ALLOWED_ORIGINS_ENV_VAR,
    API_KEY_ENV_VAR,
    PUBLIC_MODE_ENV_VAR,
    SESSION_COOKIE_NAME,
    SESSION_SECRET_ENV_VAR,
    AIR_GAS_CONSTANT,
    AIR_HEAT_CAPACITY_RATIO,
    FIXED_PLOT_BOUNDS,
    G,
    HISTORICAL_GUN_PLOT_BOUNDS,
    HTML_PAGE,
    MAX_DT,
    MAX_REQUEST_BODY_BYTES,
    MAX_SPEED,
    MIN_PRESSURE_ATM,
    MIN_DT,
    MIN_MATERIAL_DENSITY,
    MIN_SPHERICITY,
    MIN_VOLUME_FACTOR,
    SUTHERLAND_MU0,
    application,
    challenge_answer_is_correct,
    verify_signed_payload,
    runtime_configuration_error,
    normalize_simulation_params,
    aerodynamic_state,
    air_density_from_conditions,
    analytical_metrics,
    drag_coefficient_nonspherical,
    drag_coefficient_sphere,
    dynamic_viscosity_air,
    kelvin_from_celsius,
    mach_number,
    projectile_volume_from_diameter,
    pressure_atm_to_pa,
    reynolds_number,
    simulate_drag_reference,
    speed_of_sound_air,
    material_density_from_mass_and_diameter,
    mass_from_material_density,
    simulation_response,
    simulate_ideal_reference,
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

    def test_high_mach_flow_increases_drag_coefficient_above_base_reynolds_value(self) -> None:
        subsonic = aerodynamic_state(speed=200.0, temperature_c=15.0, pressure_atm=1.0, diameter=0.1)
        transonic = aerodynamic_state(speed=340.0, temperature_c=15.0, pressure_atm=1.0, diameter=0.1)

        self.assertLess(subsonic["mach"], 0.7)
        self.assertGreater(transonic["mach"], 0.95)
        self.assertAlmostEqual(subsonic["drag_coefficient"], subsonic["base_drag_coefficient"], places=9)
        self.assertGreater(transonic["drag_coefficient"], transonic["base_drag_coefficient"])
        self.assertGreater(transonic["drag_coefficient"], subsonic["drag_coefficient"])

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


class SimulationApiTests(unittest.TestCase):
    def test_normalize_simulation_params_clamps_untrusted_numeric_input(self) -> None:
        params = normalize_simulation_params({
            "speed": 100000,
            "pressure": -5,
            "dt": 0,
            "materialDensity": -20,
            "projectileShape": "shell",
            "sphericity": 0,
            "volumeFactor": -1,
        })

        self.assertEqual(params["speed"], MAX_SPEED)
        self.assertEqual(params["pressure"], MIN_PRESSURE_ATM)
        self.assertEqual(params["dt"], MIN_DT)
        self.assertEqual(params["materialDensity"], MIN_MATERIAL_DENSITY)
        self.assertEqual(params["sphericity"], MIN_SPHERICITY)
        self.assertEqual(params["volumeFactor"], MIN_VOLUME_FACTOR)

    def test_normalize_simulation_params_rejects_non_finite_values(self) -> None:
        with self.assertRaises(ValueError):
            normalize_simulation_params({"speed": float("inf")})

    def test_simulation_response_uses_python_reference_solver(self) -> None:
        params = {
            "angle": 35.0,
            "speed": 120.0,
            "materialDensity": material_density_from_mass_and_diameter(5.0, 0.1),
            "temperature": 15.0,
            "pressure": 1.0,
            "diameter": 0.1,
            "dt": 0.01,
        }
        response = simulation_response(params)

        self.assertIn("ideal", response)
        self.assertIn("drag", response)
        self.assertIn("focusedBounds", response)
        self.assertEqual(response["stableBounds"], FIXED_PLOT_BOUNDS)
        self.assertAlmostEqual(response["ideal"]["metrics"]["range"], analytical_metrics(120.0, 35.0)["range"], places=9)

    def test_simulation_response_uses_historical_stable_bounds_when_launcher_selected(self) -> None:
        response = simulation_response({"currentGun": "ballista"})
        self.assertEqual(response["stableBounds"], HISTORICAL_GUN_PLOT_BOUNDS["ballista"])


class ServerHardeningTests(unittest.TestCase):
    def wsgi_request(self, *, path: str = "/api/simulate", method: str = "POST", body: bytes = b"{}", extra_environ: dict | None = None):
        captured: dict[str, object] = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
        }
        if extra_environ:
            environ.update(extra_environ)
        response_body = b"".join(application(environ, start_response))
        return captured["status"], captured["headers"], response_body

    def bootstrap_browser_session(self) -> tuple[str, str]:
        status, _, body = self.wsgi_request(path="/", method="GET", body=b"")
        self.assertEqual(status, "200 OK")
        rendered = body.decode("utf-8")
        match = re.search(r"const BOOTSTRAP_CHALLENGE = (\{.*?\});", rendered)
        self.assertIsNotNone(match)
        challenge = json.loads(match.group(1))
        token_payload = verify_signed_payload(challenge["token"])
        self.assertIsNotNone(token_payload)
        if token_payload["kind"] == "vacuum_max_range_angle":
            answer = "45"
        elif token_payload["kind"] == "complementary_angle":
            answer = str(90 - token_payload["baseAngle"])
        else:
            answer = f"{round((2.0 * token_payload['speed']) / G, 1):.1f}"
        self.assertTrue(challenge_answer_is_correct(token_payload, answer))
        status, headers, body = self.wsgi_request(
            path="/session/bootstrap",
            body=json.dumps({"token": challenge["token"], "answer": answer}).encode("utf-8"),
        )
        self.assertEqual(status, "200 OK")
        payload = json.loads(body.decode("utf-8"))
        session_id = re.search(rf"{SESSION_COOKIE_NAME}=([^;]+)", headers["Set-Cookie"]).group(1)
        return session_id, payload["csrfToken"]

    def test_asset_path_containment_uses_resolved_relative_check(self) -> None:
        self.assertIn("asset_path.is_relative_to(RESOLVED_ASSETS_DIR)", Path("main.py").read_text())

    def test_api_body_size_limit_is_enforced_in_handler(self) -> None:
        self.assertIn("Request body too large.", Path("main.py").read_text())
        self.assertGreater(MAX_REQUEST_BODY_BYTES, 0)

    def test_wsgi_application_entrypoint_exists(self) -> None:
        self.assertTrue(callable(application))
        self.assertIn("make_server(args.host, args.port, application)", Path("main.py").read_text())

    def test_wsgi_sets_security_headers(self) -> None:
        status, headers, _ = self.wsgi_request(path="/", method="GET", body=b"")
        self.assertEqual(status, "200 OK")
        self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")

    def test_index_sets_session_cookie_and_renders_csrf_token(self) -> None:
        status, headers, body = self.wsgi_request(path="/", method="GET", body=b"")
        self.assertEqual(status, "200 OK")
        rendered = body.decode("utf-8")
        self.assertNotIn("__CSRF_TOKEN__", rendered)
        self.assertIn('const INITIAL_CSRF_TOKEN = "";', rendered)
        self.assertRegex(rendered, r'const BOOTSTRAP_CHALLENGE = \{.*"required":true.*\};')

    def test_browser_session_can_call_api_with_cookie_and_csrf(self) -> None:
        session_id, csrf = self.bootstrap_browser_session()
        status, _, body = self.wsgi_request(
            extra_environ={
                "HTTP_COOKIE": f"{SESSION_COOKIE_NAME}={session_id}",
                "HTTP_X_CSRF_TOKEN": csrf,
            }
        )
        self.assertEqual(status, "200 OK")
        self.assertIn(b'"ideal"', body)

    def test_browser_session_without_csrf_is_rejected(self) -> None:
        session_id, _ = self.bootstrap_browser_session()
        status, _, body = self.wsgi_request(extra_environ={"HTTP_COOKIE": f"{SESSION_COOKIE_NAME}={session_id}"})
        self.assertEqual(status, "401 Unauthorized")
        self.assertIn(b"Unauthorized", body)

    def test_api_key_is_required_when_configured(self) -> None:
        with patch.dict("os.environ", {API_KEY_ENV_VAR: "secret"}, clear=False):
            status, _, body = self.wsgi_request()
        self.assertEqual(status, "401 Unauthorized")
        self.assertIn(b"Unauthorized", body)

    def test_api_key_allows_request_when_header_matches(self) -> None:
        with patch.dict("os.environ", {API_KEY_ENV_VAR: "secret"}, clear=False):
            status, _, body = self.wsgi_request(extra_environ={"HTTP_X_API_KEY": "secret"})
        self.assertEqual(status, "200 OK")
        self.assertIn(b'"ideal"', body)

    def test_origin_is_rejected_when_not_allowlisted(self) -> None:
        with patch.dict("os.environ", {ALLOWED_ORIGINS_ENV_VAR: "https://example.com", API_KEY_ENV_VAR: "secret"}, clear=False):
            status, _, body = self.wsgi_request(extra_environ={"HTTP_ORIGIN": "https://evil.example", "HTTP_X_API_KEY": "secret"})
        self.assertEqual(status, "403 Forbidden")
        self.assertIn(b"Origin not allowed", body)

    def test_allowlisted_origin_is_accepted(self) -> None:
        with patch.dict("os.environ", {ALLOWED_ORIGINS_ENV_VAR: "https://example.com", API_KEY_ENV_VAR: "secret"}, clear=False):
            status, _, body = self.wsgi_request(extra_environ={"HTTP_ORIGIN": "https://example.com", "HTTP_X_API_KEY": "secret"})
        self.assertEqual(status, "200 OK")
        self.assertIn(b'"drag"', body)

    def test_public_mode_requires_api_key(self) -> None:
        with patch.dict("os.environ", {PUBLIC_MODE_ENV_VAR: "1"}, clear=False):
            self.assertIn(API_KEY_ENV_VAR, runtime_configuration_error() or "")
            status, _, body = self.wsgi_request()
        self.assertEqual(status, "503 Service Unavailable")
        self.assertIn(API_KEY_ENV_VAR.encode("utf-8"), body)

    def test_public_mode_requires_session_secret_and_allowed_origins(self) -> None:
        with patch.dict("os.environ", {PUBLIC_MODE_ENV_VAR: "1", API_KEY_ENV_VAR: "secret"}, clear=False):
            error = runtime_configuration_error() or ""
        self.assertIn(SESSION_SECRET_ENV_VAR, error)

        with patch.dict("os.environ", {PUBLIC_MODE_ENV_VAR: "1", API_KEY_ENV_VAR: "secret", SESSION_SECRET_ENV_VAR: "session-secret"}, clear=False):
            error = runtime_configuration_error() or ""
        self.assertIn(ALLOWED_ORIGINS_ENV_VAR, error)


class FrontendContractTests(unittest.TestCase):
    def test_pressure_slider_enforces_supported_minimum(self) -> None:
        self.assertIn(f'id="pressure" type="range" min="{MIN_PRESSURE_ATM}" max="1.2"', HTML_PAGE)
        self.assertIn("const MIN_PRESSURE = 0.001;", HTML_PAGE)
        self.assertIn("function clampPressure(pressureAtm)", HTML_PAGE)
        self.assertIn("Number(v) < 0.01 ? Number(v).toFixed(3) : Number(v).toFixed(2)", HTML_PAGE)

    def test_material_density_control_can_expand_for_dense_historic_presets(self) -> None:
        self.assertIn("function syncMaterialDensityLimit(materialDensity)", HTML_PAGE)
        self.assertIn("Math.max(defaultMaterialDensityMax, roundedMax)", HTML_PAGE)

    def test_plot_bounds_keep_at_least_the_requested_axes_but_do_not_clip_presets_by_default(self) -> None:
        self.assertIn("return state.stableBounds || state.focusedBounds || { maxX: 2400, maxY: 850 };", HTML_PAGE)

    def test_historic_guns_use_stable_per_gun_plot_bounds(self) -> None:
        self.assertIn("function activePlotBounds()", HTML_PAGE)
        self.assertIn('body: JSON.stringify({ ...state.params, currentGun: state.currentGun })', HTML_PAGE)

    def test_selected_gun_can_be_customized_without_leaving_gun_context(self) -> None:
        self.assertIn("presetModified: false", HTML_PAGE)
        self.assertIn("state.presetModified = !paramsMatch(state.params, historicalGuns[state.currentGun].params);", HTML_PAGE)
        self.assertIn('historicalGuns[state.currentGun].name}${state.presetModified ? " custom" : ""}', HTML_PAGE)

    def test_resize_redraws_without_rerunning_physics(self) -> None:
        self.assertIn("async function recalculatePhysics()", HTML_PAGE)
        self.assertIn("function redrawDisplay()", HTML_PAGE)
        self.assertIn('window.addEventListener("resize", () => {', HTML_PAGE)

    def test_launch_controls_expose_projectile_shape_toggle(self) -> None:
        self.assertIn('id="shapeSphereBtn"', HTML_PAGE)
        self.assertIn('id="shapeShellBtn"', HTML_PAGE)
        self.assertIn("function setProjectileShape(shape, options = {})", HTML_PAGE)

    def test_header_exposes_flight_time_indicators(self) -> None:
        self.assertIn('id="hero-ideal-time"', HTML_PAGE)
        self.assertIn('id="hero-drag-time"', HTML_PAGE)
        self.assertIn('state.ideal.metrics.flightTime.toFixed(2)', HTML_PAGE)
        self.assertIn('state.drag.metrics.flightTime.toFixed(2)', HTML_PAGE)
        self.assertIn('id="hero-impact-reynolds"', HTML_PAGE)
        self.assertIn('state.drag.aero.impactReynolds.toFixed(0)', HTML_PAGE)
        self.assertNotIn('id="hero-ideal-speed"', HTML_PAGE)

    def test_frontend_uses_python_simulation_endpoint(self) -> None:
        self.assertIn('fetch("/api/simulate"', HTML_PAGE)
        self.assertIn('"X-CSRF-Token": state.csrfToken', HTML_PAGE)
        self.assertIn('fetch("/session/bootstrap"', HTML_PAGE)
        self.assertIn("const BOOTSTRAP_CHALLENGE = __BOOTSTRAP_CHALLENGE__;", HTML_PAGE)
        self.assertNotIn("function simulateDrag(params)", HTML_PAGE)
        self.assertNotIn("function simulateIdeal(params)", HTML_PAGE)

    def test_historic_library_includes_siege_engines(self) -> None:
        self.assertIn("Counterweight trebuchet", HTML_PAGE)
        self.assertIn("Mangonel / traction catapult", HTML_PAGE)
        self.assertIn("Ballista", HTML_PAGE)
        self.assertIn("Historic Launcher Library", HTML_PAGE)


if __name__ == "__main__":
    unittest.main()
