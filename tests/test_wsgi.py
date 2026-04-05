import json
import re
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from main import (
    ALLOWED_ORIGINS_ENV_VAR,
    API_KEY_ENV_VAR,
    DEFAULT_SHELL_BALLISTIC_COEFFICIENT,
    ENABLE_CHALLENGE_ENV_VAR,
    FIXED_PLOT_BOUNDS,
    G,
    HISTORICAL_GUN_PLOT_BOUNDS,
    MAX_DT,
    MAX_REQUEST_BODY_BYTES,
    MAX_SPEED,
    MIN_DT,
    MIN_MATERIAL_DENSITY,
    MIN_PRESSURE_ATM,
    MIN_SPHERICITY,
    MIN_VOLUME_FACTOR,
    MIN_BALLISTIC_COEFFICIENT,
    PUBLIC_MODE_ENV_VAR,
    SESSION_COOKIE_NAME,
    SESSION_SECRET_ENV_VAR,
    application,
    analytical_metrics,
    challenge_answer_is_correct,
    material_density_from_mass_and_diameter,
    normalize_simulation_params,
    runtime_configuration_error,
    simulation_response,
    verify_signed_payload,
)


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
            "ballisticCoefficient": 0,
            "dragModel": "g1",
        })

        self.assertEqual(params["speed"], MAX_SPEED)
        self.assertEqual(params["pressure"], MIN_PRESSURE_ATM)
        self.assertEqual(params["dt"], MIN_DT)
        self.assertEqual(params["materialDensity"], MIN_MATERIAL_DENSITY)
        self.assertEqual(params["sphericity"], MIN_SPHERICITY)
        self.assertEqual(params["volumeFactor"], MIN_VOLUME_FACTOR)
        self.assertEqual(params["ballisticCoefficient"], MIN_BALLISTIC_COEFFICIENT)
        self.assertEqual(params["dragModel"], "g1")

    def test_non_shell_input_resets_ballistic_coefficient_fields(self) -> None:
        params = normalize_simulation_params({
            "projectileShape": "sphere",
            "ballisticCoefficient": 0.5,
            "dragModel": "g1",
        })
        self.assertEqual(params["ballisticCoefficient"], 0.0)
        self.assertEqual(params["dragModel"], "g1")

    def test_shell_defaults_to_generic_g7_ballistic_coefficient(self) -> None:
        params = normalize_simulation_params({"projectileShape": "shell"})
        self.assertEqual(params["dragModel"], "g7")
        self.assertEqual(params["ballisticCoefficient"], DEFAULT_SHELL_BALLISTIC_COEFFICIENT)

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
        self.assertIn("asset_path.is_relative_to(RESOLVED_ASSETS_DIR)", Path("ballistics/web/app.py").read_text())

    def test_api_body_size_limit_is_enforced_in_handler(self) -> None:
        self.assertIn("Request body too large.", Path("ballistics/web/app.py").read_text())
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

    def test_index_can_issue_session_immediately_when_challenge_disabled(self) -> None:
        with patch.dict("os.environ", {ENABLE_CHALLENGE_ENV_VAR: "0"}, clear=False):
            status, headers, body = self.wsgi_request(path="/", method="GET", body=b"")
        self.assertEqual(status, "200 OK")
        self.assertIn("Set-Cookie", headers)
        rendered = body.decode("utf-8")
        self.assertNotIn('const INITIAL_CSRF_TOKEN = "";', rendered)
        self.assertIn('const BOOTSTRAP_CHALLENGE = {"required":false};', rendered)

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

    def test_public_mode_requires_session_secret_and_allowed_origins(self) -> None:
        with patch.dict("os.environ", {PUBLIC_MODE_ENV_VAR: "1"}, clear=False):
            error = runtime_configuration_error() or ""
        self.assertIn(SESSION_SECRET_ENV_VAR, error)

        with patch.dict("os.environ", {PUBLIC_MODE_ENV_VAR: "1", SESSION_SECRET_ENV_VAR: "session-secret"}, clear=False):
            error = runtime_configuration_error() or ""
        self.assertIn(ALLOWED_ORIGINS_ENV_VAR, error)
