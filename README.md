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

The air-pressure control is limited to `0.001 atm` through `1.2 atm` because the current drag correlations are not treated as valid below that floor.

Material density also has quick shortcuts:

- `S` stone
- `I` iron
- `B` bronze
- `U` uranium

## Historical Launcher Library

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
- M1857 12-pounder Napoleon
- 3-inch Ordnance Rifle
- RBL 12-pounder 8 cwt Armstrong gun
- 10-pounder Parrott rifle
- 24-pounder long gun
- Paixhans gun

The historical presets are educational approximations. Some launchers lack directly documented release velocity data, so the simulator uses either a spherical shot model or a simplified streamlined-projectile model depending on the preset.

## Physics Model

The drag equation keeps the standard form:

`Fd = 0.5 * rho * Cd * A * v^2`

But the aerodynamic terms are derived dynamically:

- air density from the ideal gas law
- dynamic viscosity from Sutherland's law
- speed of sound from the ideal-gas relation for air
- Mach number from instantaneous projectile speed and local speed of sound
- Reynolds number from instantaneous velocity, projectile diameter, density, and viscosity
- base drag coefficient from a piecewise sphere `Cd(Re)` correlation for round shot and a bounded streamlined-shell form factor for elongated shell-like projectiles
- an approximate Mach-aware compressibility multiplier applied on top of that base drag coefficient for high-speed flow, with a milder transonic rise for shell-like projectiles than for spheres
- projectile area from diameter
- projectile mass from material density and a shape-aware projectile volume approximation

The flight model is a 2D point-mass model in horizontal distance and height.

At each integration step, the drag solver advances the trajectory with a classical fourth-order Runge-Kutta (RK4) method.

## Output Metrics

The current UI reports:

- ideal range
- ideal maximum height
- drag range
- drag maximum height
- range loss to drag
- time step

The graph also marks the peak and impact points for ideal and drag trajectories, shows the launch angle at the origin, and includes:

- a header velocity indicator for drag impact speed
- header flight-time indicators for ideal and drag solutions
- a header Reynolds-number indicator for the drag solution at impact
- a preset indicator showing the active launcher or `Manual setup`
- a header-level scale toggle with `Stable` and `Fit shot` modes

## Assumptions and Limits

- 2D planar point-mass motion only
- round shot uses a spherical projectile model
- shell presets use a simplified elongated-projectile drag model tuned to avoid the unrealistically large drag penalties produced by generic nonspherical particle correlations
- pressure is clamped to a minimum supported value of `0.001 atm`
- compressibility is handled with an approximate Mach-aware drag correction, not a fitted `Cd(Re, Ma)` table or a full transonic/supersonic aerodynamic model
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

Start the local web server:

```bash
python3 main.py
```

Then open:

```text
http://127.0.0.1:8000
```

You can also bind a different interface or port:

```bash
python3 main.py --host 127.0.0.1 --port 8888
```

This server is still suitable for local use, but it now also supports a basic internet-facing browser deployment model behind a reverse proxy. Application-layer protections include browser sessions, CSRF checks, origin allowlists, and an optional bootstrap challenge. It is still not a complete standalone internet edge service: TLS, throttling, and network exposure controls should remain at the proxy and host layers.
For browser-testing the deployment path locally, you can also run:

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
- better shell-specific aerodynamic data or ballistic-coefficient models
- non-spherical projectiles
- wind and turbulence
- adaptive time stepping
- native Android port

## Author

Igor Nikitin
