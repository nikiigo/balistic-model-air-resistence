from __future__ import annotations

import json

from ballistics.web.auth import csrf_token_for_session
from ballistics.web.challenge import BootstrapChallenge


def render_index_page(html_page: str, session_id: str | None, bootstrap_challenge: BootstrapChallenge | None) -> bytes:
    csrf_token = csrf_token_for_session(session_id) if session_id else ""
    challenge_json = json.dumps(bootstrap_challenge or {"required": False}, separators=(",", ":"))
    return (
        html_page
        .replace("__CSRF_TOKEN__", csrf_token)
        .replace("__BOOTSTRAP_CHALLENGE__", challenge_json)
    ).encode("utf-8")
