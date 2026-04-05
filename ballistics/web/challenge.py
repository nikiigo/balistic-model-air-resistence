from __future__ import annotations

import secrets
import time
from typing import Dict

from ballistics.constants import BOOTSTRAP_CHALLENGE_TTL_SECONDS, G
from ballistics.web.auth import sign_payload


def generate_bootstrap_challenge() -> Dict[str, str]:
    challenge_id = secrets.randbelow(3)
    if challenge_id == 0:
        challenge = {
            "kind": "vacuum_max_range_angle",
            "prompt": "Ignoring drag, what launch angle gives maximum range in vacuum? Answer in degrees.",
        }
    elif challenge_id == 1:
        base_angle = 20 + (5 * secrets.randbelow(6))
        challenge = {
            "kind": "complementary_angle",
            "prompt": f"In vacuum, what complementary launch angle has the same range as {base_angle} degrees?",
            "baseAngle": base_angle,
        }
    else:
        speed = 10 + (5 * secrets.randbelow(5))
        challenge = {
            "kind": "vertical_flight_time",
            "prompt": f"Ignoring drag, if a projectile is launched straight up at {speed} m/s, what is the total flight time in seconds? Round to one decimal place.",
            "speed": speed,
        }
    challenge["issuedAt"] = int(time.time())
    challenge["token"] = sign_payload(challenge)
    return challenge


def challenge_answer_is_correct(challenge: Dict[str, object], answer: str) -> bool:
    normalized = answer.strip().lower()
    if not normalized:
        return False
    kind = challenge.get("kind")
    if kind == "vacuum_max_range_angle":
        try:
            return abs(float(normalized) - 45.0) <= 0.5
        except ValueError:
            return normalized in {"45", "45.0", "45 degrees"}
    if kind == "complementary_angle":
        try:
            expected = 90.0 - float(challenge.get("baseAngle", 0))
            return abs(float(normalized) - expected) <= 0.5
        except ValueError:
            return False
    if kind == "vertical_flight_time":
        try:
            speed = float(challenge.get("speed", 0))
            expected = round((2.0 * speed) / G, 1)
            return abs(float(normalized) - expected) <= 0.15
        except ValueError:
            return False
    return False


def challenge_is_expired(issued_at: int, now: float | None = None) -> bool:
    current_time = time.time() if now is None else now
    return current_time - issued_at > BOOTSTRAP_CHALLENGE_TTL_SECONDS
