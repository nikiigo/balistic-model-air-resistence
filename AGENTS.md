# Project Guidance

## Purpose

Interactive ballistics simulator for physics education. The Python server is the source of truth for both ideal and drag trajectory calculations; the browser renders server-computed results.

## Working Norms

- Prefer reviewing and modifying the Python simulation code before touching frontend behavior that depends on physics output.
- Keep the Python server and browser contract aligned. If API payloads or response fields change, update tests and the HTML template together.
- Preserve the existing WSGI architecture unless a task explicitly asks for a framework migration.
- Treat historical launcher presets as educational approximations, not source-of-truth scientific calibration.

## Run And Test

- Local app: `.venv/bin/gunicorn --bind 127.0.0.1:8000 main:application`
- WSGI entrypoint module: `main.py`
- Main test command in this repo: `python -m unittest -q`
- `pytest` may not be installed in the environment; prefer `python -m unittest -q` unless the repo is updated to depend on pytest explicitly.
- For browser testing, use Gunicorn so the WSGI deployment path is exercised.
- In this sandboxed environment, binding to `127.0.0.1:8000` may require escalated permissions.

## Code Map

- [`main.py`](/home/nikiigo/balistic-model-air-resistence/main.py): WSGI entrypoint and local server runner.
- [`ballistics/web/app.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/web/app.py): request routing, JSON parsing, session/bootstrap flow, API responses.
- [`ballistics/web/templates.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/web/templates.py): inline frontend app and UI contract.
- [`ballistics/web/pages.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/web/pages.py): injects CSRF token and bootstrap challenge into HTML.
- [`ballistics/web/auth.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/web/auth.py): API-key auth, signed browser session handling, CSRF derivation.
- [`ballistics/schemas.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/schemas.py): input normalization, plot bounds, API response serialization.
- [`ballistics/physics/ideal.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/physics/ideal.py): analytical ideal-motion solver.
- [`ballistics/physics/drag.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/physics/drag.py): aerodynamic helpers and RK4 drag solver.
- [`ballistics/presets.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/presets.py): default parameters and historical launcher presets.
- [`tests/test_physics.py`](/home/nikiigo/balistic-model-air-resistence/tests/test_physics.py): physics regression tests.
- [`tests/test_wsgi.py`](/home/nikiigo/balistic-model-air-resistence/tests/test_wsgi.py): API/auth/WSGI tests.
- [`tests/test_frontend.py`](/home/nikiigo/balistic-model-air-resistence/tests/test_frontend.py): frontend contract tests using string assertions against the HTML template.

## Physics Conventions

- Round-shot spheres use the Haider-Levenspiel Reynolds-side base drag correlation plus the current polynomial Mach correction.
- Shell-like projectiles use the `G1/G7 + ballistic coefficient` path rather than the sphere correlation.
- Shell drag is driven by drag function (`G1`/`G7`) and ballistic coefficient. `sphericity` may be carried in preset metadata, but it is not an independent driver in the current shell drag law.
- Shell `dragCoefficient` values returned by the API are equivalent coefficients derived from drag force, not direct `Cd(Re, Ma)` correlation outputs.
- Pressure is clamped to the supported floor `MIN_PRESSURE_ATM = 0.001`.
- When changing physics behavior, add or update regression tests in [`tests/test_physics.py`](/home/nikiigo/balistic-model-air-resistence/tests/test_physics.py).

## Review Hotspots

- Authentication and browser session handling in [`ballistics/web/auth.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/web/auth.py) and [`ballistics/web/app.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/web/app.py) need careful review for trust boundaries. Browser sessions are stateless signed cookies, not server-stored sessions.
- The frontend is embedded in one large HTML template. Small behavior changes can require both JS updates and contract-test updates.
- Plot-bounds behavior is partly precomputed in [`ballistics/schemas.py`](/home/nikiigo/balistic-model-air-resistence/ballistics/schemas.py); changes there can affect historical presets and graph scaling.

## Change Checklist

- Run `python -m unittest -q` after behavior changes.
- If changing API fields, update both backend serialization and frontend consumers.
- If changing preset semantics, check historical preset rendering and focused/stable plot bounds.
- If touching auth/session code, add a concrete WSGI test that reproduces the protected flow.
