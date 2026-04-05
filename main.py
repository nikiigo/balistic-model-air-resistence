from __future__ import annotations

import argparse
import math
from wsgiref.simple_server import make_server

from ballistics.config import (
    configured_allowed_origins,
    configured_api_key,
    configured_session_secret,
    emit_runtime_warnings,
    public_mode_enabled,
    runtime_configuration_error,
)
from ballistics.constants import (
    ALLOWED_ORIGINS_ENV_VAR,
    API_KEY_ENV_VAR,
    AIR_GAS_CONSTANT,
    AIR_HEAT_CAPACITY_RATIO,
    ASSETS_DIR,
    BASE_DIR,
    BOOTSTRAP_CHALLENGE_TTL_SECONDS,
    G,
    MAX_ANGLE_DEG,
    MAX_DIAMETER_M,
    MAX_DT,
    MAX_MATERIAL_DENSITY,
    MAX_PRESSURE_ATM,
    MAX_REQUEST_BODY_BYTES,
    MAX_SPEED,
    MAX_SPHERICITY,
    MAX_TEMPERATURE_C,
    MAX_VOLUME_FACTOR,
    MIN_ANGLE_DEG,
    MIN_DIAMETER_M,
    MIN_DT,
    MIN_MATERIAL_DENSITY,
    MIN_PRESSURE_ATM,
    MIN_SPEED,
    MIN_SPHERICITY,
    MIN_TEMPERATURE_C,
    MIN_VOLUME_FACTOR,
    PUBLIC_MODE_ENV_VAR,
    RESOLVED_ASSETS_DIR,
    SESSION_COOKIE_NAME,
    SESSION_SECRET_ENV_VAR,
    SUTHERLAND_MU0,
)
from ballistics.physics.drag import (
    aerodynamic_state,
    air_density_from_conditions,
    clamp_pressure_atm,
    compressibility_drag_multiplier,
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
    speed_of_sound_air,
    sphere_area_from_diameter,
    sphere_volume_from_diameter,
)
from ballistics.physics.ideal import analytical_metrics, simulate_ideal_reference
from ballistics.schemas import (
    FIXED_PLOT_BOUNDS,
    HISTORICAL_GUN_PLOT_BOUNDS,
    compute_focused_plot_bounds,
    compute_plot_bounds,
    normalize_simulation_params,
    serialize_drag_result,
    simulation_response,
)
from ballistics.web.app import create_application
from ballistics.web.auth import csrf_token_for_session, verify_signed_payload
from ballistics.web.challenge import challenge_answer_is_correct, challenge_is_expired, generate_bootstrap_challenge
from ballistics.web.pages import render_index_page
from ballistics.web.templates import HTML_PAGE

application = create_application(HTML_PAGE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the interactive ballistics simulator.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with make_server(args.host, args.port, application) as server:
        print(f"Serving ballistics simulator at http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
