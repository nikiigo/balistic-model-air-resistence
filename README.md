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

- Adjustable launch angle, speed, mass, air temperature, air pressure, projectile diameter, and integration time step
- Simultaneous ideal and drag trajectories
- Comparison view with launch point, peak markers, and impact points
- Presets for ideal vacuum, high drag, heavy projectile, and long-range shots
- Historical gun library with image-backed presets for real 16th to 19th century artillery pieces
- Gun lock mode that freezes all ballistic parameters except launch angle
- Drag model derived from ideal-gas air density, Sutherland viscosity, Reynolds number, and sphere drag correlation
- Real-time metrics for range, maximum height, flight time, impact speed, air density, Reynolds number, and drag force
- Responsive single-page layout suitable for desktop and mobile widths

## Validation

Analytical helpers are covered with unit tests:

```bash
python3 -m unittest
```

The visual drag simulation can be checked against the ideal model by setting pressure to `0 atm`, which collapses drag toward vacuum behavior.
