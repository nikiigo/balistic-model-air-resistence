from __future__ import annotations

import json
import mimetypes
from typing import Any

from ballistics.config import bootstrap_challenge_enabled, emit_runtime_warnings, runtime_configuration_error
from ballistics.constants import ASSETS_DIR, MAX_REQUEST_BODY_BYTES, RESOLVED_ASSETS_DIR
from ballistics.schemas import simulation_response
from ballistics.web.auth import (
    browser_session_authorized,
    csrf_token_for_session,
    current_session_id,
    is_origin_allowed,
    is_request_authorized,
    log_simulation_request,
    new_session_id,
    session_cookie_header,
    verify_signed_payload,
)
from ballistics.web.challenge import BootstrapChallenge, challenge_answer_is_correct, challenge_is_expired, generate_bootstrap_challenge
from ballistics.web.pages import render_index_page


def wsgi_response(
    start_response,
    status: str,
    body: bytes,
    content_type: str,
    extra_headers: list[tuple[str, str]] | None = None,
    head_only: bool = False,
):
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "no-referrer"),
        ("Cross-Origin-Resource-Policy", "same-origin"),
        ("Cross-Origin-Opener-Policy", "same-origin"),
        ("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    start_response(status, headers)
    return [] if head_only else [body]


def json_error_response(start_response, status: str, message: str):
    return wsgi_response(
        start_response,
        status,
        json.dumps({"error": message}).encode("utf-8"),
        "application/json; charset=utf-8",
    )


def parse_json_object_body(environ, payload_name: str) -> dict[str, Any]:
    try:
        length = int(environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError as exc:
        raise ValueError("Invalid Content-Length.") from exc
    if length < 0:
        raise ValueError("Invalid Content-Length.")
    if length > MAX_REQUEST_BODY_BYTES:
        raise OverflowError("Request body too large.")

    payload = json.loads(environ["wsgi.input"].read(length) if length > 0 else b"{}")
    if not isinstance(payload, dict):
        raise ValueError(f"{payload_name} payload must be a JSON object.")
    return payload


def create_application(html_page: str):
    def application(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        head_only = method == "HEAD"
        config_error = runtime_configuration_error()
        if config_error is not None:
            return wsgi_response(
                start_response,
                "503 Service Unavailable",
                json.dumps({"error": config_error}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
        emit_runtime_warnings()

        if path.startswith("/assets/") and method in {"GET", "HEAD"}:
            relative = path.removeprefix("/assets/")
            asset_path = (ASSETS_DIR / relative).resolve()
            if not asset_path.is_relative_to(RESOLVED_ASSETS_DIR) or not asset_path.is_file():
                return wsgi_response(start_response, "404 Not Found", b"Not Found", "text/plain; charset=utf-8", head_only=head_only)

            content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
            return wsgi_response(
                start_response,
                "200 OK",
                asset_path.read_bytes(),
                content_type,
                extra_headers=[("Cache-Control", "public, max-age=31536000, immutable")],
                head_only=head_only,
            )

        if path in {"/", "/index.html"} and method in {"GET", "HEAD"}:
            session_id = current_session_id(environ)
            bootstrap_challenge: BootstrapChallenge | None = None
            extra_headers = None
            if session_id is None:
                if bootstrap_challenge_enabled():
                    challenge_payload = generate_bootstrap_challenge()
                    bootstrap_challenge = {**challenge_payload, "required": True}
                else:
                    session_id = new_session_id()
                    extra_headers = [session_cookie_header(session_id)]
            else:
                extra_headers = [session_cookie_header(session_id)]
            return wsgi_response(
                start_response,
                "200 OK",
                render_index_page(html_page, session_id, bootstrap_challenge),
                "text/html; charset=utf-8",
                extra_headers=extra_headers,
                head_only=head_only,
            )

        if path == "/session/bootstrap" and method == "POST":
            if not is_origin_allowed(environ):
                return json_error_response(start_response, "403 Forbidden", "Origin not allowed.")
            try:
                payload = parse_json_object_body(environ, "Bootstrap")
            except OverflowError as exc:
                return json_error_response(start_response, "413 Payload Too Large", str(exc))
            except ValueError as exc:
                return json_error_response(start_response, "400 Bad Request", str(exc))
            try:
                challenge_token = str(payload.get("token", ""))
                answer = str(payload.get("answer", ""))
                challenge = verify_signed_payload(challenge_token)
                if challenge is None:
                    raise ValueError("Challenge token is invalid.")
                issued_at = int(challenge.get("issuedAt", 0))
                if challenge_is_expired(issued_at):
                    raise ValueError("Challenge expired.")
                if not challenge_answer_is_correct(challenge, answer):
                    return json_error_response(start_response, "403 Forbidden", "Incorrect answer.")
                session_id = new_session_id()
                return wsgi_response(
                    start_response,
                    "200 OK",
                    json.dumps({"csrfToken": csrf_token_for_session(session_id)}).encode("utf-8"),
                    "application/json; charset=utf-8",
                    extra_headers=[session_cookie_header(session_id)],
                )
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                return json_error_response(start_response, "400 Bad Request", str(exc))

        if path == "/api/simulate" and method == "POST":
            if not (is_request_authorized(environ) or browser_session_authorized(environ)):
                status = "401 Unauthorized"
                log_simulation_request(environ, status)
                return json_error_response(start_response, status, "Unauthorized.")
            if not is_origin_allowed(environ):
                status = "403 Forbidden"
                log_simulation_request(environ, status)
                return json_error_response(start_response, status, "Origin not allowed.")
            try:
                payload = parse_json_object_body(environ, "Simulation")
            except OverflowError as exc:
                status = "413 Payload Too Large"
                log_simulation_request(environ, status)
                return json_error_response(start_response, status, str(exc))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                status = "400 Bad Request"
                log_simulation_request(environ, status)
                return json_error_response(start_response, status, str(exc))

            try:
                response_body = json.dumps(simulation_response(payload)).encode("utf-8")
                status = "200 OK"
                log_simulation_request(environ, status)
                return wsgi_response(start_response, status, response_body, "application/json; charset=utf-8")
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                status = "400 Bad Request"
                log_simulation_request(environ, status)
                return json_error_response(start_response, status, str(exc))

        return wsgi_response(start_response, "404 Not Found", b"Not Found", "text/plain; charset=utf-8", head_only=head_only)

    return application
