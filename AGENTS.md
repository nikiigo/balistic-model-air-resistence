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

- [`main.py`](main.py): WSGI entrypoint and local server runner.
- [`ballistics/web/app.py`](ballistics/web/app.py): request routing, JSON parsing, session/bootstrap flow, API responses.
- [`ballistics/web/templates.py`](ballistics/web/templates.py): inline frontend app and UI contract.
- [`ballistics/web/pages.py`](ballistics/web/pages.py): injects CSRF token and bootstrap challenge into HTML.
- [`ballistics/web/auth.py`](ballistics/web/auth.py): API-key auth, signed browser session handling, CSRF derivation.
- [`ballistics/schemas.py`](ballistics/schemas.py): input normalization, plot bounds, API response serialization.
- [`ballistics/physics/ideal.py`](ballistics/physics/ideal.py): analytical ideal-motion solver.
- [`ballistics/physics/drag.py`](ballistics/physics/drag.py): aerodynamic helpers and RK4 drag solver.
- [`ballistics/presets.py`](ballistics/presets.py): default parameters and historical launcher presets.
- [`docs/api.md`](docs/api.md): browser-facing API contract for bootstrap/session flow and `POST /api/simulate`.
- [`tests/test_physics.py`](tests/test_physics.py): physics regression tests.
- [`tests/test_wsgi.py`](tests/test_wsgi.py): API/auth/WSGI tests.
- [`tests/test_frontend.py`](tests/test_frontend.py): frontend contract tests using string assertions against the HTML template.

## Physics Conventions

- Round-shot spheres use the Haider-Levenspiel Reynolds-side base drag correlation plus the current polynomial Mach correction.
- Shell-like projectiles use the `G1/G7 + ballistic coefficient` path rather than the sphere correlation.
- Both drag families use the same RK4 trajectory integrator; what changes between them is the drag-law submodel used to compute acceleration inside each step.
- Shell drag is driven by drag function (`G1`/`G7`) and ballistic coefficient. `sphericity` may be carried in preset metadata, but it is not an independent driver in the current shell drag law.
- In the current shell implementation, the `G1/G7` lookup is velocity-banded in `ft/s` and then scaled by actual air density. Mach and Reynolds are still computed and reported for shell shots, but they are not the primary shell drag-law inputs.
- Shell `dragCoefficient` values returned by the API are equivalent coefficients derived from drag force, not direct `Cd(Re, Ma)` correlation outputs.
- Keep preset families explicit: round-shot presets should carry `projectileShape: "sphere"` with `sphericity = 1`, `volumeFactor = 1`, and `ballisticCoefficient = 0`, while shell presets should carry their shell-specific `volumeFactor`, `dragModel`, and positive `ballisticCoefficient`.
- Pressure is clamped to the supported floor `MIN_PRESSURE_ATM = 0.001`.
- When changing physics behavior, add or update regression tests in [`tests/test_physics.py`](tests/test_physics.py).

## Preset Architecture

- Backend physics presets live in [`ballistics/presets.py`](ballistics/presets.py). Treat that file as the source of truth for simulation parameters.
- Frontend generic presets and historical launcher params are serialized from the backend into [`ballistics/web/templates.py`](ballistics/web/templates.py) as `presets` and `historicalGunParams`.
- The frontend `historicalGuns` object in [`ballistics/web/templates.py`](ballistics/web/templates.py) should mainly add presentation metadata such as names, notes, images, and sources while reusing `historicalGunParams.<key>` for physics.
- Keep preset families explicit in backend preset data. Do not rely on inherited or partially merged state in the frontend to imply sphere-vs-shell behavior.
- When a preset changes, verify all of: backend params in [`ballistics/presets.py`](ballistics/presets.py), frontend launcher metadata in [`ballistics/web/templates.py`](ballistics/web/templates.py), launcher hover copy, tests, and README references that mention the preset.
- Launcher images are local assets under `assets/guns/`. The hover panel now uses a fixed `4:3` media frame in [`ballistics/web/templates.py`](ballistics/web/templates.py), so new images should be chosen or prepared to read well in that crop.

## Validation Snapshot

- The README's `Validation Snapshot` table is backed by regression tests in [`tests/test_physics.py`](tests/test_physics.py) under `ValidationSnapshotRegressionTests`.
- The Napoleon, Ordnance, and Parrott snapshot checks are created by copying the corresponding entries from `HISTORICAL_PLOT_REFERENCE_PARAMS` and overriding only the comparison angle to `5.0` degrees.
- The M1841 6-pounder snapshot now uses the named preset key `m1841SixPounder` directly. That preset is the documented `5°`, `1450 ft/s`, `6 lb` round-shot case with diameter `0.093218 m` and mass `2.72155 kg`.
- Snapshot assertions currently compare modeled range in yards after converting from meters with `1.0936132983377078`.
- If physics changes move one of these ranges, update both the regression test and the README table in the same change. Do not leave the README snapshot as a stale hand-maintained number.
- When adding a historical launcher preset, update all of: [`ballistics/presets.py`](ballistics/presets.py), [`ballistics/web/templates.py`](ballistics/web/templates.py), [`tests/test_frontend.py`](tests/test_frontend.py), and any backend stable-bounds coverage in [`tests/test_wsgi.py`](tests/test_wsgi.py). If the preset is part of the documented list, update the README too.

## Model Validation Guidance

- Historical shell presets are currently configured on `G7`.
- The backend can calculate `G1` for shell projectiles, but the current repository comparisons for the 3-inch Ordnance Rifle and 10-pounder Parrott favor `G7` over `G1`.
- The validation snapshot is a partial historical comparison, not a full ballistic calibration. Do not overstate it in code comments or docs.
- If shell drag law or shell preset parameters change, compare the updated results against the validation snapshot tests before changing README claims.

## Review Hotspots

- Authentication and browser session handling in [`ballistics/web/auth.py`](ballistics/web/auth.py) and [`ballistics/web/app.py`](ballistics/web/app.py) need careful review for trust boundaries. Browser sessions are stateless signed cookies, not server-stored sessions.
- The frontend is embedded in one large HTML template. Small behavior changes can require both JS updates and contract-test updates.
- The header quick-guide dialog is also defined inside [`ballistics/web/templates.py`](ballistics/web/templates.py). If its wording or sections change, update [`tests/test_frontend.py`](tests/test_frontend.py) in the same change.
- The homepage default shot and the metric-card ordering under the graph are hardcoded in [`ballistics/web/templates.py`](ballistics/web/templates.py), not derived from backend presets automatically. The relevant places are the `defaults` object / initial state wiring and `renderMetrics()`.
- The shell/sphere UI mode can regress if preset params are partial or merged carelessly. Preserve explicit `projectileShape`, shell BC params, and sphere zero-BC params when editing presets or selection logic.
- In the current UI, shell mode locks the `materialDensity` and `diameter` controls because shell trajectory is driven by `G1/G7 + BC`; those controls only affect shell diagnostics in the current model.
- The Launch Controls panel now exposes a manual `bc` slider for shell mode only. It sits above `Time step` in [`ballistics/web/templates.py`](ballistics/web/templates.py) and feeds `state.params.ballisticCoefficient` during manual shell setup.
- The graph recalculation overlay is driven by `updateCalculationStatus()` inside `recalculatePhysics()` and hidden from `redrawDisplay()`. If the overlay behavior changes, update the frontend contract tests too.
- Plot-bounds behavior is partly precomputed in [`ballistics/schemas.py`](ballistics/schemas.py); changes there can affect historical presets and graph scaling.

## Change Checklist

- Run `python -m unittest -q` after behavior changes.
- If changing API fields, update both backend serialization and frontend consumers.
- If changing preset semantics, check historical preset rendering and focused/stable plot bounds.
- If touching auth/session code, add a concrete WSGI test that reproduces the protected flow.
