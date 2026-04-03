# Interactive Ballistics Simulator

This project is a dependency-free web app for exploring 2D projectile motion in two modes:

- Ideal motion using the analytical solution
- Motion with air resistance using numerical time-stepping

The simulator includes live controls, preset scenarios, trajectory comparison, and educational notes explaining how drag changes range, flight time, and maximum height.

## Run

```bash
python3 main.py
```

Then open `http://127.0.0.1:8000`.

Optional flags:

```bash
python3 main.py --host 0.0.0.0 --port 9000
```

## Features

- Adjustable launch angle, speed, mass, drag coefficient, air density, cross-sectional area, and integration time step
- Toggleable ideal and drag trajectories
- Comparison view with launch point, peak markers, and impact points
- Presets for ideal vacuum, high drag, heavy projectile, and long-range shots
- Real-time metrics for range, maximum height, flight time, and impact speed
- Responsive single-page layout suitable for desktop and mobile widths

## Validation

Analytical helpers are covered with unit tests:

```bash
python3 -m unittest
```

The visual drag simulation can be checked against the ideal model by setting air density to `0` or disabling drag.
