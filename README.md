# Interactive Ballistics Simulator

Interactive web-based projectile simulator for physics education. The app compares ideal projectile motion with a drag model whose aerodynamic parameters are derived dynamically from atmospheric conditions and projectile geometry.

![Trajectory comparison](assets/screenshots/interactive-ballistics-simulator.png)

## Live Demo

https://funmechanics.net:8443/

## What the App Does

- draws ideal and drag trajectories side by side on the same graph
- recalculates the shot in real time as the controls change
- lets users explore historical artillery presets from the 16th to 19th centuries
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

Material density also has quick shortcuts:

- `S` stone
- `I` iron
- `B` bronze
- `U` uranium

## Historical Gun Library

The left-side gun library includes real artillery pieces with images, descriptive notes, and preset parameters. Selecting a gun applies its documented or inferred ballistic profile and switches the graph to a stable scale for that gun.

Included presets cover:

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

The historical presets are educational approximations. Some guns used rifled shells or lack directly documented muzzle velocity data, so the simulator uses either a spherical round-shot model or a simplified nonspherical shell model depending on the preset.

## Physics Model

The drag equation keeps the standard form:

`Fd = 0.5 * rho * Cd * A * v^2`

But the aerodynamic terms are derived dynamically:

- air density from the ideal gas law
- dynamic viscosity from Sutherland's law
- Reynolds number from instantaneous velocity, projectile diameter, density, and viscosity
- base drag coefficient from a piecewise sphere `Cd(Re)` correlation for round shot and a nonspherical `Cd(Re, sphericity)` correlation for elongated shell-like projectiles
- an approximate Mach-aware compressibility multiplier applied on top of that base drag coefficient for high-speed flow
- projectile area from diameter
- projectile mass from material density and a shape-aware projectile volume approximation

At each integration step, the drag solver iterates the velocity update several times to account for the coupling between speed, Reynolds number, drag coefficient, and drag force.

## Output Metrics

The current UI reports:

- ideal range
- ideal maximum height
- drag range
- drag maximum height
- range loss to drag
- time step

The graph also marks the peak and impact points for ideal and drag trajectories, shows the launch angle at the origin, and includes:

- header velocity indicators for ideal and drag impact speed
- a preset indicator showing the active gun or `Manual setup`
- a header-level scale toggle with `Stable` and `Fit shot` modes

## Assumptions and Limits

- round shot uses a spherical projectile model
- shell presets use a simplified elongated-projectile drag model
- pressure is clamped to a minimum supported value of `0.001 atm`
- compressibility is handled with an approximate Mach-aware drag correction, not a fitted `Cd(Re, Ma)` table or a full transonic/supersonic aerodynamic model
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
- set pressure to `0 atm` and verify drag behavior collapses toward the ideal case
- select a historical gun and confirm the graph switches to that gun's stable scale
- switch between `Stable` and `Fit shot` in the header and confirm the graph frame changes without changing the underlying trajectory
- edit a control after selecting a gun and confirm the gun stays selected but is marked as customized
- resize the browser window and confirm layout and graph remain usable

## Project Structure

- [main.py](main.py): HTTP server, HTML, CSS, JavaScript, and Python physics helpers
- [test_main.py](test_main.py): analytical and aerodynamic regression tests
- [assets/guns](assets/guns): bundled historical gun images used by the local library
- [assets/screenshots](assets/screenshots): README screenshot assets

## Future Work

- altitude-dependent atmosphere
- Mach-number corrections
- non-spherical projectiles
- wind and turbulence
- higher-order integration
- native Android port

## Author

Igor Nikitin
