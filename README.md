# Interactive Ballistics Simulator

Interactive 2D projectile-motion simulator for physics education. The application compares an ideal analytical trajectory with a numerically integrated trajectory that includes aerodynamic drag derived from environmental conditions and projectile size.

The app is dependency-free: a single Python server in `main.py` serves the entire UI, JavaScript simulator, and local historical gun images.

## What It Does

- Simulates ideal projectile motion from the closed-form solution
- Simulates drag-affected motion with time-stepped numerical integration
- Computes drag dynamically from:
  - air temperature
  - air pressure
  - projectile diameter
  - instantaneous velocity
- Displays both ideal and drag trajectories together
- Includes historical artillery presets from the 16th to 19th centuries

## Run

Start the local server:

```bash
python3 main.py
```

Then open:

```text
http://127.0.0.1:8000
```

Optional host and port:

```bash
python3 main.py --host 0.0.0.0 --port 9000
```

## Controls

The simulator parameters come from the launch-control panel:

- Launch angle
- Initial velocity
- Projectile material density
- Air temperature
- Air pressure
- Projectile diameter
- Integration time step

Historical gun presets populate those same controls with gun-specific values.

## Historical Gun Library

The left-side gun library includes real artillery pieces from the 16th to 19th centuries with local images and hover details. Selecting a gun fills the simulator with that gun's ballistic inputs, including projectile diameter in millimeters.

These presets are educational approximations. Documented shot size, projectile mass, and listed ranges or muzzle velocities were used where available. The simulator derives projectile mass from diameter and material density while still assuming a spherical projectile.

## Drag Model

The drag-force equation remains:

```text
Fd = 1/2 * rho * Cd * A * v^2
```

The difference is that the aerodynamic terms are now derived rather than entered directly.

### Air Density

Air density is computed from the ideal gas law:

```text
rho = p / (R * T)
```

- `T` is taken from the UI in Celsius and converted to Kelvin
- `p` is taken from the UI in atm and converted to pascals
- `R = 287.05 J/(kg*K)`

### Dynamic Viscosity

Dynamic viscosity is computed with Sutherland's law:

```text
mu(T) = mu0 * (T / T0)^(3/2) * (T0 + S) / (T + S)
```

Constants used:

- `mu0 = 1.716e-5 Pa*s`
- `T0 = 273.15 K`
- `S = 111 K`

### Reynolds Number

```text
Re = rho * v * d / mu
```

### Sphere Drag Coefficient

The simulator uses the standard piecewise sphere correlation:

```text
Cd = 24 / Re                         for Re < 0.1
Cd = (24 / Re) * (1 + 0.15 Re^0.687) for 0.1 <= Re < 1000
Cd = 0.44                             for Re >= 1000
```

### Cross-Sectional Area

Area is derived from projectile diameter:

```text
A = pi * d^2 / 4
```

### Iterative Step Update

At each drag-integration step, the simulator:

1. estimates speed from the current velocity
2. computes `rho`, `mu`, `Re`, `Cd`, and drag force
3. updates velocity
4. applies relaxation over several internal iterations for stability

## Metrics

The UI reports:

- Ideal range
- Ideal maximum height
- Drag range
- Drag maximum height
- Range loss to drag
- Air density
- Launch Reynolds number
- Launch drag coefficient
- Launch drag force
- Time step

## Validation

Run the tests with:

```bash
python3 -m unittest
```

Syntax check:

```bash
python3 -m py_compile main.py test_main.py
```

The tests currently cover:

- analytical projectile-motion helpers
- ideal gas density conversion
- Sutherland viscosity
- Reynolds number
- sphere drag coefficient regimes
- sphere area calculation
- reference drag-stepper regression behavior for pressure, temperature, and diameter changes

## Manual Checks

Useful manual checks in the browser:

- Set pressure to `0 atm` and verify the drag trajectory moves toward vacuum behavior.
- Increase pressure and verify range decreases.
- Increase projectile diameter and verify drag force increases and range decreases.
- Increase temperature at fixed pressure and verify reported air density decreases.
- Select historical guns and confirm the diameter shown in the hover card matches the loaded control value.

## Deployment

The app can run behind Caddy or any reverse proxy because the backend only serves static HTML and local asset files.

Example Caddy reverse proxy:

```caddy
example.com {
    reverse_proxy 127.0.0.1:8000
}
```
