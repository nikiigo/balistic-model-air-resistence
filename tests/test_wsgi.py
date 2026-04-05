import json
import re
import unittest
from http.cookies import SimpleCookie
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from ballistics.config import runtime_configuration_error
from ballistics.constants import (
    ALLOWED_ORIGINS_ENV_VAR,
    API_KEY_ENV_VAR,
    DEFAULT_SHELL_BALLISTIC_COEFFICIENT,
    ENABLE_CHALLENGE_ENV_VAR,
    G,
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
)
from ballistics.physics.drag import material_density_from_mass_and_diameter
from ballistics.physics.ideal import analytical_metrics
from ballistics.schemas import (
    FIXED_PLOT_BOUNDS,
    HISTORICAL_GUN_PLOT_BOUNDS,
    normalize_simulation_params,
    simulation_response,
)
from ballistics.web.app import create_application
from ballistics.web.auth import csrf_token_for_session, verify_signed_payload
from ballistics.web.challenge import challenge_answer_is_correct
from ballistics.web.templates import HTML_PAGE

application = create_application(HTML_PAGE)


def cookie_value_from_set_cookie(header: str, name: str) -> str | None:
    cookie = SimpleCookie()
    cookie.load(header)
    morsel = cookie.get(name)
    if morsel is None:
        return None
    return morsel.value


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
    @staticmethod
    def wsgi_request(
        *,
        path: str = "/api/simulate",
        method: str = "POST",
        body: bytes = b"{}",
        extra_environ: dict[str, str | BytesIO] | None = None,
    ) -> tuple[str, dict[str, str], bytes]:
        captured_status = ""
        captured_headers: dict[str, str] = {}

        def start_response(status, headers):
            nonlocal captured_status, captured_headers
            captured_status = status
            captured_headers = dict(headers)

        environ: dict[str, str | BytesIO] = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
        }
        if extra_environ:
            environ.update(extra_environ)
        response_body = b"".join(application(environ, start_response))
        return captured_status, captured_headers, response_body

    def bootstrap_browser_session(self) -> tuple[str, str, str]:
        status, _, body = self.wsgi_request(path="/", method="GET", body=b"")
        self.assertEqual(status, "200 OK")
        rendered = body.decode("utf-8")
        match = re.search(r"const BOOTSTRAP_CHALLENGE = (\{.*?\});", rendered)
        self.assertIsNotNone(match)
        assert match is not None
        challenge_data = json.loads(match.group(1))
        self.assertIsInstance(challenge_data, dict)
        challenge = challenge_data
        token_payload = verify_signed_payload(str(challenge["token"]))
        self.assertIsNotNone(token_payload)
        assert token_payload is not None
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
        payload_data = json.loads(body.decode("utf-8"))
        self.assertIsInstance(payload_data, dict)
        payload = payload_data
        session_token = cookie_value_from_set_cookie(headers["Set-Cookie"], SESSION_COOKIE_NAME)
        self.assertIsNotNone(session_token)
        assert session_token is not None
        session_payload = verify_signed_payload(session_token)
        self.assertIsNotNone(session_payload)
        assert session_payload is not None
        self.assertEqual(session_payload["kind"], "browser_session")
        session_id = str(session_payload["sid"])
        return session_token, session_id, str(payload["csrfToken"])

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
        session_token = cookie_value_from_set_cookie(headers["Set-Cookie"], SESSION_COOKIE_NAME)
        self.assertIsNotNone(session_token)
        assert session_token is not None
        session_payload = verify_signed_payload(session_token)
        self.assertIsNotNone(session_payload)
        assert session_payload is not None
        self.assertEqual(session_payload["kind"], "browser_session")
        self.assertIn(f'const INITIAL_CSRF_TOKEN = "{csrf_token_for_session(str(session_payload["sid"]))}";', rendered)

    def test_browser_session_can_call_api_with_cookie_and_csrf(self) -> None:
        session_token, _, csrf = self.bootstrap_browser_session()
        status, _, body = self.wsgi_request(
            extra_environ={
                "HTTP_COOKIE": f"{SESSION_COOKIE_NAME}={session_token}",
                "HTTP_X_CSRF_TOKEN": csrf,
            }
        )
        self.assertEqual(status, "200 OK")
        self.assertIn(b'"ideal"', body)

    def test_browser_session_without_csrf_is_rejected(self) -> None:
        session_token, _, _ = self.bootstrap_browser_session()
        status, _, body = self.wsgi_request(extra_environ={"HTTP_COOKIE": f"{SESSION_COOKIE_NAME}={session_token}"})
        self.assertEqual(status, "401 Unauthorized")
        self.assertIn(b"Unauthorized", body)

    def test_forged_cookie_does_not_render_csrf_token(self) -> None:
        forged_cookie = "attacker"
        status, headers, body = self.wsgi_request(
            path="/",
            method="GET",
            body=b"",
            extra_environ={"HTTP_COOKIE": f"{SESSION_COOKIE_NAME}={forged_cookie}"},
        )
        self.assertEqual(status, "200 OK")
        self.assertNotIn("Set-Cookie", headers)
        rendered = body.decode("utf-8")
        self.assertIn('const INITIAL_CSRF_TOKEN = "";', rendered)
        self.assertNotIn(csrf_token_for_session(forged_cookie), rendered)

    def test_forged_cookie_and_derived_csrf_are_rejected(self) -> None:
        forged_cookie = "attacker"
        status, _, body = self.wsgi_request(
            extra_environ={
                "HTTP_COOKIE": f"{SESSION_COOKIE_NAME}={forged_cookie}",
                "HTTP_X_CSRF_TOKEN": csrf_token_for_session(forged_cookie),
            }
        )
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
