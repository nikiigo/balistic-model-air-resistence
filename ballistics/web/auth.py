from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from http.cookies import SimpleCookie
from typing import Any

from ballistics.config import configured_allowed_origins, configured_api_key, configured_session_secret, public_mode_enabled
from ballistics.constants import SESSION_COOKIE_NAME

SESSION_PAYLOAD_KIND = "browser_session"


def is_request_authorized(environ) -> bool:
    expected = configured_api_key()
    if expected is None:
        return False
    return hmac.compare_digest(environ.get("HTTP_X_API_KEY", ""), expected)


def is_origin_allowed(environ) -> bool:
    allowed = configured_allowed_origins()
    if not allowed:
        return True
    origin = environ.get("HTTP_ORIGIN", "")
    if not origin:
        return True
    return origin in allowed


def log_simulation_request(environ, status: str) -> None:
    remote_addr = environ.get("HTTP_X_FORWARDED_FOR", environ.get("REMOTE_ADDR", "-"))
    origin = environ.get("HTTP_ORIGIN", "-")
    print(f"[ballistics] {environ.get('REQUEST_METHOD', 'POST')} {environ.get('PATH_INFO', '')} {status} remote={remote_addr} origin={origin}")


def parse_request_cookies(environ) -> SimpleCookie:
    cookie = SimpleCookie()
    raw_cookie = environ.get("HTTP_COOKIE", "")
    if raw_cookie:
        cookie.load(raw_cookie)
    return cookie


def current_session_id(environ) -> str | None:
    session_payload = current_session_payload(environ)
    if session_payload is None:
        return None
    session_id = session_payload.get("sid")
    if not isinstance(session_id, str) or not session_id:
        return None
    return session_id


def current_session_payload(environ) -> dict[str, Any] | None:
    cookies = parse_request_cookies(environ)
    morsel = cookies.get(SESSION_COOKIE_NAME)
    if morsel is None:
        return None
    payload = verify_signed_payload(morsel.value)
    if payload is None:
        return None
    if payload.get("kind") != SESSION_PAYLOAD_KIND:
        return None
    return payload


def csrf_token_for_session(session_id: str) -> str:
    return hmac.new(configured_session_secret().encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256).hexdigest()


def new_session_id() -> str:
    return secrets.token_urlsafe(32)


def session_cookie_header(session_id: str) -> tuple[str, str]:
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE_NAME] = sign_browser_session(session_id)
    cookie[SESSION_COOKIE_NAME]["path"] = "/"
    cookie[SESSION_COOKIE_NAME]["httponly"] = True
    cookie[SESSION_COOKIE_NAME]["samesite"] = "Lax"
    if public_mode_enabled():
        cookie[SESSION_COOKIE_NAME]["secure"] = True
    return "Set-Cookie", cookie.output(header="").strip()


def sign_browser_session(session_id: str) -> str:
    return sign_payload({
        "kind": SESSION_PAYLOAD_KIND,
        "sid": session_id,
        "issuedAt": int(time.time()),
    })


def sign_payload(payload: dict[str, Any]) -> str:
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    signature = hmac.new(configured_session_secret().encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def verify_signed_payload(token: str) -> dict[str, Any] | None:
    try:
        encoded_payload, signature = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(configured_session_secret().encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(encoded_payload.encode("ascii")))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def browser_session_authorized(environ) -> bool:
    session_id = current_session_id(environ)
    if not session_id:
        return False
    origin = environ.get("HTTP_ORIGIN", "")
    allowed_origins = configured_allowed_origins()
    if allowed_origins and origin not in allowed_origins:
        return False
    provided_csrf = environ.get("HTTP_X_CSRF_TOKEN", "")
    if not provided_csrf:
        return False
    expected_csrf = csrf_token_for_session(session_id)
    return hmac.compare_digest(provided_csrf, expected_csrf)
