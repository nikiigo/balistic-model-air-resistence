from __future__ import annotations

import os

from ballistics.constants import (
    ALLOWED_ORIGINS_ENV_VAR,
    API_KEY_ENV_VAR,
    ENABLE_CHALLENGE_ENV_VAR,
    LOCAL_DEVELOPMENT_SESSION_SECRET,
    PUBLIC_MODE_ENV_VAR,
    SESSION_SECRET_ENV_VAR,
)


def configured_api_key() -> str | None:
    value = os.environ.get(API_KEY_ENV_VAR, "").strip()
    return value or None


def configured_session_secret() -> str:
    value = os.environ.get(SESSION_SECRET_ENV_VAR, "").strip()
    if value:
        return value
    api_key = configured_api_key()
    if api_key:
        return api_key
    return LOCAL_DEVELOPMENT_SESSION_SECRET


def configured_allowed_origins() -> set[str]:
    raw = os.environ.get(ALLOWED_ORIGINS_ENV_VAR, "")
    return {origin.strip() for origin in raw.split(",") if origin.strip()}


def public_mode_enabled() -> bool:
    return os.environ.get(PUBLIC_MODE_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "on"}


def bootstrap_challenge_enabled() -> bool:
    raw = os.environ.get(ENABLE_CHALLENGE_ENV_VAR, "").strip().lower()
    if not raw:
        return True
    return raw in {"1", "true", "yes", "on"}


_runtime_warning_flags = {
    "missing_allowed_origins": False,
}


def runtime_configuration_error() -> str | None:
    if public_mode_enabled() and not os.environ.get(SESSION_SECRET_ENV_VAR, "").strip():
        return f"{SESSION_SECRET_ENV_VAR} must be set when {PUBLIC_MODE_ENV_VAR}=1."
    if public_mode_enabled() and not configured_allowed_origins():
        return f"{ALLOWED_ORIGINS_ENV_VAR} must be set when {PUBLIC_MODE_ENV_VAR}=1."
    return None


def emit_runtime_warnings() -> None:
    if public_mode_enabled() and not configured_allowed_origins() and not _runtime_warning_flags["missing_allowed_origins"]:
        print(f"[ballistics] warning: {ALLOWED_ORIGINS_ENV_VAR} is unset while {PUBLIC_MODE_ENV_VAR}=1; Origin checks are disabled")
        _runtime_warning_flags["missing_allowed_origins"] = True
