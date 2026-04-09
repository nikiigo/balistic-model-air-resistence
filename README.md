# Interactive Ballistics Simulator

Interactive web-based projectile simulator for physics education. The app compares two trajectory solvers:

- an ideal solver for vacuum projectile motion
- a drag solver for atmosphere-aware projectile motion

The browser UI renders trajectories computed by the Python server.

![Trajectory comparison](assets/screenshots/interactive-ballistics-simulator.png)

## Live Demo

https://funmechanics.net:8443/

## What the App Does

- draws ideal and drag trajectories side by side on the same graph
- recalculates the shot in real time as the controls change
- lets users explore historical launcher presets spanning siege engines and artillery
- shows core flight metrics for ideal and drag cases
- includes short educational notes about drag, optimal angle, and model assumptions

## Launch Controls

The simulator UI exposes:

- launch angle
- initial velocity
- projectile shape (`Round shot` or `Shell`)
- projectile material density
- air temperature
- air pressure
- projectile diameter
- integration time step

The air-pressure control is limited to `0.001 atm` through `2.0 atm`, matching the browser and server-side validation range while respecting the low-pressure floor used by the drag solver.

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

The simulator uses a 2D point-mass flight model in horizontal distance and height.

### Two Solvers

#### Ideal solver

The ideal solver is an analytical vacuum solution. It computes:

- range
- maximum height
- flight time
- peak location

It uses only launch angle, launch speed, gravity, and the display time step used for sampling the analytical curve.

#### Drag solver

The drag solver is a numerical solver that integrates projectile motion through an atmosphere. It includes:

- air density from the ideal gas law
- dynamic viscosity from Sutherland's law
- speed of sound from the ideal-gas relation for air
- Reynolds number from instantaneous velocity, air density, diameter, and viscosity
- Mach number from instantaneous speed and local speed of sound
- projectile area from diameter
- projectile mass from material density and projectile volume

The drag solver advances the trajectory with a classical fourth-order Runge-Kutta (RK4) integrator.

- round shot
- shell

These families share the same atmospheric state calculation and the same RK4 motion integrator, but they use different drag laws.

#### Round-shot family

Round shot uses a sphere-based drag model grounded in two parts:

1. Reynolds-side base drag:
   the base drag coefficient is computed from the Haider-Levenspiel sphere correlation

2. Compressibility correction:
   that base coefficient is multiplied by a polynomial Mach correction

In code, the round-shot family follows:

`Cd_base(Re) = (24/Re) * (1 + A * Re^B) + (C * Re) / (D + Re)`

with:

- `A = 0.18624356`
- `B = 0.6529`
- `C = 0.43731566`
- `D = 7185.3535`

`Cd = Cd_base(Re) * (1 + Ma^2/4 + Ma^4/40)`

The drag force then uses the standard quadratic form:

`Fd = 0.5 * rho * Cd * A * v^2`

This family is used for cannon balls, stones, and other near-spherical projectiles.

Grounding references:

- A. Haider, O. Levenspiel, *Drag Coefficient and Terminal Velocity of Spherical and Non-Spherical Particles*, Powder Technology 58 (1989) 63-70. DOI: https://doi.org/10.1016/0032-5910(89)80008-7
- Eric Loth, *Drag of Non-Spherical Solid Particles of Regular and Irregular Shape*, Powder Technology 182 (2008) 342-353. DOI: https://doi.org/10.1016/j.powtec.2007.06.001

#### Shell family

Shell projectiles use a drag-function plus ballistic-coefficient model rather than the sphere `Cd(Re, Ma)` path.

In this family:

- the drag law uses `G1` or `G7` tables plus ballistic coefficient
- atmospheric density affects drag through density scaling
- Reynolds number and Mach number are computed and reported as diagnostics
- the reported shell drag coefficient is an equivalent coefficient derived from the computed drag force, not a directly correlated sphere-style `Cd(Re, Ma)`

In implementation terms, the shell path uses:

`R_std = (C * v_fps^n) / BC`

where:

- `C, n` come from the active row of the `G1` or `G7` drag table for the current velocity band
- `v_fps` is projectile speed in feet per second
- `BC` is ballistic coefficient

That standard retardation is then density-scaled:

`a_drag = R_std * (rho / rho_std) * FPS_TO_MPS`

Drag force magnitude is then:

`Fd = m * a_drag`

The reported shell drag coefficient is back-computed afterward as an equivalent coefficient:

`Cd_equivalent = 2 * Fd / (rho * A * v^2)`

The UI defaults manual shell mode to:

- `dragModel: "g7"`
- `ballisticCoefficient: 0.22`

Historical shell presets also use the shell family and are configured on `G7`.

Shell preset metadata may include descriptors such as `sphericity`, but in the shell solver those values do not independently drive drag beyond the selected drag function and ballistic coefficient.

### Practical Difference Between The Drag Families

- round shot: atmosphere changes drag through `Re`, `Ma`, `rho`, and `mu`, with drag coefficient built from a sphere correlation and Mach correction
- shell: atmosphere still changes drag through density, but the primary aerodynamic law is the `G1/G7 + BC` model instead of a direct sphere `Cd(Re, Ma)` correlation

## Validation Snapshot

The table below compares the model against a few historical artillery reference points that are close to presets in the simulator. These are spot checks, not a full firing-table calibration. The listed model ranges are covered by regression tests so the documented snapshot stays aligned with the solver.

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
- some preset muzzle velocities and BC values are modeled approximations, so this should be treated as a first-pass validation check rather than a final calibration
- at the moment, the simulator is noticeably better validated for round-shot sphere projectiles than for elongated shell projectiles

## Output Metrics

The UI reports:

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
- ideal solver uses vacuum projectile motion
- drag solver uses either the round-shot sphere family or the shell `G1/G7 + BC` family
- historical shell presets are configured on `G7`
- shell ballistic-coefficient values are approximate modeling inputs, not a complete historical firing-table dataset
- shell `sphericity` is descriptive preset metadata rather than an independent shell drag input
- pressure is clamped to a minimum supported value of `0.001 atm`
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

The WSGI entrypoint is exposed through [`main.py`](main.py), and Gunicorn is the recommended local run path because it matches the deployment path more closely. Application-layer protections include browser sessions, CSRF checks, origin allowlists, and an optional bootstrap challenge. It is not a complete standalone internet edge service: TLS, throttling, and network exposure controls should remain at the proxy and host layers.

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

This is basic application-layer hardening, not full production security by itself. If the service is internet-facing, TLS, request throttling, and network exposure controls should be enforced by the reverse proxy and host environment.

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
