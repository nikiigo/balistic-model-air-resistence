# Interactive Ballistics Simulator

Interactive web-based projectile simulator for physics education. The app compares ideal projectile motion with a drag model whose aerodynamic parameters are derived dynamically from atmospheric conditions and projectile geometry.

The browser UI renders trajectories computed by the Python server, so the simulation logic now lives in one place rather than being duplicated in both Python and JavaScript.

![Trajectory comparison](assets/screenshots/interactive-ballistics-simulator.png)

## Live Demo

https://funmechanics.net:8443/

## What the App Does

- draws ideal and drag trajectories side by side on the same graph
- recalculates the shot in real time as the controls change
- lets users explore historical launcher presets spanning siege engines and artillery
- shows core flight metrics for ideal and drag cases
- includes short educational notes about drag, optimal angle, and model assumptions

## Current Launch Controls

The simulator UI currently exposes:

- launch angle
- initial velocity
- projectile shape (`Round shot` or `Shell`)
- projectile material density
- air temperature
- air pressure
- projectile diameter
- integration time step

The air-pressure control is limited to `0.001 atm` through `2.0 atm`, matching the current browser and server-side validation range while still respecting the low-pressure floor used by the drag solver.

Material density also has quick shortcuts:

- `S` stone
- `I` iron
- `B` bronze
- `U` uranium

## Historical Launcher Library

<!--suppress GrazieInspection -->
The left-side historic launcher library includes siege engines and artillery pieces with images, descriptive notes, and preset parameters. Selecting a launcher applies its documented or inferred ballistic profile and switches the graph to a stable scale for that launcher.

Included presets cover:

- Counterweight trebuchet
- Mangonel / traction catapult
- Ballista
- Queen Elizabeth's Pocket Pistol
- Culverin extraordinary
- Demi-culverin
- Saker
- Falconet
- Demi-cannon
- Canon de 12 Gribeauval
- M1841 6-pounder gun
- M1857 12-pounder Napoleon
- 3-inch Ordnance Rifle
- RBL 12-pounder 8 cwt Armstrong gun
- 10-pounder Parrott rifle
- 24-pounder long gun
- Paixhans gun

The historical presets are educational approximations. Some launchers lack directly documented release velocity data, so the simulator uses either a spherical shot model or a simplified streamlined-projectile model depending on the preset.

## Physics Model

<!--suppress GrazieInspection -->
The drag equation keeps the standard form:

`Fd = 0.5 * rho * Cd * A * v^2`

But the aerodynamic terms are derived dynamically:

- air density from the ideal gas law
- dynamic viscosity from Sutherland's law
- speed of sound from the ideal-gas relation for air
- Mach number from instantaneous projectile speed and local speed of sound
- Reynolds number from instantaneous velocity, projectile diameter, density, and viscosity
- base drag coefficient from the Haider-Levenspiel sphere-limit correlation for round shot
- a polynomial sphere Mach correction from `Eric Loth` applied as `Cd = Cd_base(Re) * (1 + Ma^2/4 + Ma^4/40)`
- shell-like projectiles can use a standard drag-function plus ballistic-coefficient path (`G1` or `G7`), with the current historical shell presets using `G7`
- projectile area from diameter
- projectile mass from material density and a shape-aware projectile volume approximation

In implementation terms, the two projectile families work differently:

- round shot spheres: compute a base `Cd(Re)` from the Haider-Levenspiel sphere-limit correlation, then scale that base value with the Mach correction `1 + Ma^2/4 + Ma^4/40`
- shell-like projectiles: compute drag directly from the standard `G1/G7` drag-function plus ballistic coefficient (`BC`)
- shell preset metadata may still include geometric descriptors such as `sphericity`, but in the current shell solver those descriptors do not independently modify drag beyond what is already represented by the chosen drag function and ballistic coefficient

If the user manually switches the UI to `Shell`, the current default shell path is `G7` with ballistic coefficient `0.22` unless a historical shell preset supplies different shell parameters.

For shell-like projectiles, Reynolds number and Mach number are still reported as diagnostics, but they are not the primary inputs to the shell drag law. The displayed shell drag coefficient is an equivalent `Cd` derived afterward from the computed drag force:

- `Cd_equivalent = 2 * Fd / (rho * A * v^2)`

So for shells, the aerodynamic driver is the `G1/G7 + BC` model, not a direct `Cd(Re, Ma)` correlation.

The shell drag-function shape is data-fitted through the standard `G1/G7` model, but the preset ballistic-coefficient values remain approximate tuning inputs rather than source-verified firing-table BCs for each historical round. In the current repository comparisons for the 3-inch Ordnance Rifle and 10-pounder Parrott, `G7` produces materially smaller range error than `G1`, which is why the historical shell presets are configured on `G7`.

For round shot, the base Reynolds-side correlation is the Haider-Levenspiel sphere-limit form:

- A. Haider, O. Levenspiel, *Drag Coefficient and Terminal Velocity of Spherical and Non-Spherical Particles*, Powder Technology 58 (1989) 63-70. DOI: https://doi.org/10.1016/0032-5910(89)80008-7

This correlation is also widely adopted in engineering software and multiphase-flow practice, including implementations in Fluent, OpenFOAM, and EDEM. In the software documentation checked for this project, we did not find a prominently stated hard Reynolds-number cutoff for the Haider-Levenspiel model of the kind explicitly stated in Morrison's 2016 sphere note. Even so, using it as the Reynolds-side base drag law for historical round-shot ballistics remains a modeling choice rather than a direct validation of full compressible artillery flight by Haider and Levenspiel themselves.

For round-shot compressibility, the simulator uses the polynomial Mach correction requested from Eric Loth's review of drag correlations for non-spherical particles:

- Eric Loth, *Drag of Non-Spherical Solid Particles of Regular and Irregular Shape*, Powder Technology 182 (2008) 342-353. DOI: https://doi.org/10.1016/j.powtec.2007.06.001

The flight model is a 2D point-mass model in horizontal distance and height.

At each integration step, the drag solver advances the trajectory with a classical fourth-order Runge-Kutta (RK4) method.

RK4 is used here because the drag trajectory is governed by nonlinear ordinary differential equations: drag depends on speed, while the effective aerodynamic terms depend on the current Mach number and Reynolds number. For this kind of smooth nonlinear point-mass flight problem, RK4 gives a good practical balance between accuracy, stability, and implementation simplicity without requiring extremely small time steps.

## Validation Snapshot

The table below compares the current model against a few historical artillery reference points that are close to presets in the simulator. These are spot checks, not a full firing-table calibration. The listed model ranges are also covered by regression tests so the documented snapshot stays aligned with the solver.

| Launcher | Comparison setup | Model range | Historical reference | Error |
| --- | --- | ---: | ---: | ---: |
| M1841 6-pounder gun | `5°` elevation, round shot | `1451 yd` | `1523 yd` | `-4.7%` |
| M1857 12-pounder Napoleon | `5°` elevation, round shot | `1622 yd` | `1680 yd` | `-3.4%` |
| 3-inch Ordnance Rifle | `5°` elevation, shell preset | `1539 yd` | `1800 yd` effective range | `-14.5%` |
| 10-pounder Parrott rifle | `5°` elevation, shell preset | `1528 yd` | `1800 yd` effective range | `-15.1%` |

Reference sources:

- Vicksburg National Military Park, table of fire for the Light 12-Pounder Gun, Model 1857: https://www.nps.gov/vick/learn/education/mathematics-range-chart.htm
- Antietam on the Web, Model 1841 6-pounder gun data (`5°`, `1450 ft/s`, `1523 yd`): https://antietam.aotw.org/weapons.php?weapon_id=12
- NPS Shenandoah artillery overview with effective-range summaries for the 3-inch Ordnance Rifle and 10-pounder Parrott: https://www.nps.gov/articles/000/civil-war-weapons-in-the-shenandoah-valley.htm

Caveat:

- the Napoleon comparison uses an explicit table-of-fire entry, while the Ordnance and Parrott values above are NPS effective-range summaries rather than one matching firing table
- some preset muzzle velocities and BC values are still modeled approximations, so this should be treated as a first-pass validation check rather than a final calibration
- at the moment, the simulator is noticeably better validated for round-shot sphere projectiles than for elongated shell projectiles

## Output Metrics

The current UI reports:

- ideal range
- ideal maximum height
- time step
- drag range
- drag maximum height
- range loss to drag

The graph also marks the peak and impact points for ideal and drag trajectories, shows the launch angle at the origin, and includes:

- a temporary overlay that appears on the graph while the trajectory is being recalculated
- a header velocity indicator for drag impact speed
- header flight-time indicators for ideal and drag solutions
- a header Reynolds-number indicator for the drag solution at impact
- a preset indicator showing the active launcher or `Manual setup`
- a header-level scale toggle with `Stable` and `Fit shot` modes

## Assumptions and Limits

- 2D planar point-mass motion only
- round shot uses a spherical projectile model with a Haider-Levenspiel Reynolds-side base drag correlation and a separate Mach correction
- shell presets now use a `G7` ballistic-coefficient model by default; the backend can still calculate `G1`, but the current historical shell presets remain on `G7`
- the `G1/G7` drag-function shapes are standard fitted curves, but the preset ballistic-coefficient values are still approximate and not all tied to historical firing tables
- shell `sphericity` is currently descriptive metadata for presets rather than an extra correction layered on top of the `G1/G7 + BC` law
- pressure is clamped to a minimum supported value of `0.001 atm`
- sphere compressibility uses a polynomial Mach correction on top of the Reynolds-based base drag, not a full `Cd(Re, Ma)` surface
- no wind
- no spin or Magnus effect
- no terrain modeling
- constant gravity
- ideal-gas atmosphere

## Run Locally

Install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Start the local app with Gunicorn:

```bash
.venv/bin/gunicorn --bind 127.0.0.1:8000 main:application
```

Then open:

```text
http://127.0.0.1:8000
```

You can also bind a different interface or port:

```bash
.venv/bin/gunicorn --bind 127.0.0.1:8888 main:application
```

The application still exposes the same WSGI entrypoint through [`main.py`](main.py), but Gunicorn is the recommended local run path because it matches the deployment path more closely. Application-layer protections include browser sessions, CSRF checks, origin allowlists, and an optional bootstrap challenge. It is still not a complete standalone internet edge service: TLS, throttling, and network exposure controls should remain at the proxy and host layers.
For browser-testing the deployment path locally, run:

```bash
.venv/bin/gunicorn --bind 127.0.0.1:8000 main:application
```

For deployment behind Caddy or another reverse proxy, run the WSGI app with a production server such as Gunicorn:

```bash
.venv/bin/gunicorn main:application
```

Install Gunicorn into the project virtualenv:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Example production-style Gunicorn command bound to localhost:

```bash
BALLISTICS_PUBLIC_MODE=1 \
BALLISTICS_SESSION_SECRET=change-this-too \
BALLISTICS_ALLOWED_ORIGINS=https://your-domain.example \
# Optional:
# BALLISTICS_ENABLE_CHALLENGE=0 \
.venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 30 main:application
```

To run it as a systemd service, create `/etc/systemd/system/ballistics.service`:

```ini
[Unit]
Description=Interactive Ballistics Simulator
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/absolute/path/to/balistic-model-air-resistence
Environment=BALLISTICS_PUBLIC_MODE=1
Environment=BALLISTICS_SESSION_SECRET=change-this-too
Environment=BALLISTICS_ALLOWED_ORIGINS=https://your-domain.example
# Optional:
# Environment=BALLISTICS_ENABLE_CHALLENGE=0
# Optional:
# Environment=BALLISTICS_API_KEY=change-me
ExecStart=/absolute/path/to/balistic-model-air-resistence/.venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 --timeout 30 main:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ballistics.service
sudo systemctl status ballistics.service
```

To update environment variables later, edit the unit file and reload it:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ballistics.service
```

Example Caddy site block:

```caddy
your-domain.example {
	encode gzip zstd

	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
		X-Content-Type-Options "nosniff"
		Referrer-Policy "no-referrer"
	}

	log {
		output file /var/log/caddy/ballistics-access.log
		format console
	}

	reverse_proxy 127.0.0.1:8000
}
```

Deployment notes:

- keep Gunicorn bound to `127.0.0.1:8000`
- expose only Caddy publicly
- set `BALLISTICS_ALLOWED_ORIGINS` to your exact HTTPS origin
- keep the browser on the session-cookie + CSRF path; do not blindly inject `X-API-Key` on the public browser route unless you explicitly want every public request proxied upstream as trusted
- keep TLS termination in Caddy; if you want rate limiting, add it with the mechanism you already use in your Caddy deployment

Optional hardening environment variables:

- `BALLISTICS_PUBLIC_MODE`: set to `1` to enable internet-facing safety checks; in this mode the app refuses to serve unless `BALLISTICS_SESSION_SECRET` and `BALLISTICS_ALLOWED_ORIGINS` are configured
- `BALLISTICS_API_KEY`: optional shared secret for trusted non-browser or upstream callers; it is not required for the public browser-session flow
- `BALLISTICS_SESSION_SECRET`: HMAC secret used to issue browser session cookies and CSRF tokens
- `BALLISTICS_ALLOWED_ORIGINS`: comma-separated browser origins allowed to call `/api/simulate` when an `Origin` header is present
- `BALLISTICS_ENABLE_CHALLENGE`: set to `0` to disable the browser bootstrap question gate; defaults to enabled, and when disabled the server issues the browser session immediately on `GET /`

Example:

```bash
BALLISTICS_PUBLIC_MODE=1 \
BALLISTICS_SESSION_SECRET=change-this-too \
BALLISTICS_ALLOWED_ORIGINS=https://your-domain.example \
# Optional:
# BALLISTICS_ENABLE_CHALLENGE=0 \
# Optional:
# BALLISTICS_API_KEY=change-me \
.venv/bin/gunicorn main:application
```

Browser requests use a server-issued session cookie plus a CSRF token injected into the HTML page.

With the default challenge-enabled mode, a new browser visit first presents a lightweight physics challenge. A correct answer upgrades the browser into a real simulation session and enables `/api/simulate`.

If `BALLISTICS_ENABLE_CHALLENGE=0`, the browser skips that question gate and receives the session immediately.

This is basic application-layer hardening, not full production security by itself. If the service is internet-facing, TLS, request throttling, and network exposure controls should still be enforced by the reverse proxy and host environment.

## Validation

Run the automated checks:

```bash
python3 -m unittest
python3 -m py_compile main.py tests/test_physics.py tests/test_wsgi.py tests/test_frontend.py
```

Useful manual checks:

- change angle and confirm the trajectory is recomputed rather than only visually rescaled
- switch projectile shape between `Round shot` and `Shell` in custom mode and confirm the trajectory changes
- set pressure to `0.001 atm` and verify drag is reduced relative to standard pressure without collapsing fully to the ideal case
- select a historical launcher and confirm the graph switches to that launcher's stable scale
- switch between `Stable` and `Fit shot` in the header and confirm the graph frame changes without changing the underlying trajectory
- edit a control after selecting a launcher and confirm the launcher stays selected but is marked as customized
- resize the browser window and confirm layout and graph remain usable

## Project Structure

- [main.py](main.py): thin local entrypoint and compatibility import surface
- [ballistics/physics](ballistics/physics): ideal-flight and drag/atmosphere physics helpers
- [ballistics/web](ballistics/web): WSGI routing, auth, challenge, page rendering, and embedded template
- [ballistics/schemas.py](ballistics/schemas.py): simulation request normalization and response shaping
- [ballistics/presets.py](ballistics/presets.py): preset and plot-reference data
- [requirements.txt](requirements.txt): runtime Python dependency pins
- browser rendering calls the local `/api/simulate` endpoint for ideal and drag trajectories
- [tests/test_physics.py](tests/test_physics.py): analytical and aerodynamic regression tests
- [tests/test_wsgi.py](tests/test_wsgi.py): WSGI, auth, and hardening tests
- [tests/test_frontend.py](tests/test_frontend.py): embedded frontend contract checks
- [assets/guns](assets/guns): bundled historical launcher images used by the local library
- [assets/screenshots](assets/screenshots): README screenshot assets

## Future Work

- altitude-dependent atmosphere
- sphere drag tables fitted directly over `Re` and `Ma`
- better historical ballistic-coefficient data for the shell presets
- non-spherical projectiles
- wind and turbulence
- adaptive time stepping
- native Android port

## Author

<!--suppress GrazieInspection -->
Igor Nikitin
