# Interactive Ballistics Simulator

Interactive web-based projectile simulator for physics education. The app compares ideal projectile motion with a drag model whose aerodynamic parameters are derived dynamically from atmospheric conditions and projectile geometry.

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

The historical presets are educational approximations. Some launchers lack directly documented release velocity data, so the simulator uses either a spherical shot model or a simplified nonspherical projectile model depending on the preset.

## Physics Model

The drag equation keeps the standard form:

`Fd = 0.5 * rho * Cd * A * v^2`

But the aerodynamic terms are derived dynamically:

- air density from the ideal gas law
- dynamic viscosity from Sutherland's law
- speed of sound from the ideal-gas relation for air
- Mach number from instantaneous projectile speed and local speed of sound
- Reynolds number from instantaneous velocity, projectile diameter, density, and viscosity
- drag coefficient from a Reynolds-based base correlation plus a Mach-aware compressibility multiplier for high-speed flow
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
- shell presets use a simplified elongated-projectile drag model
- pressure is clamped to a minimum supported value of `0.001 atm`
- compressibility is handled with an approximate Mach-aware drag correction, not a full transonic/supersonic aerodynamic model
- no wind
- no spin or Magnus effect
- no terrain modeling
- constant gravity
- ideal-gas atmosphere

## Run Locally

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

## Validation

Run the automated checks:

```bash
python3 -m unittest
python3 -m py_compile main.py test_main.py
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

- [main.py](main.py): HTTP server, HTML, CSS, JavaScript, and Python physics helpers
- [test_main.py](test_main.py): analytical and aerodynamic regression tests
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
