from __future__ import annotations

import argparse
import html
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict

G = 9.81


def analytical_metrics(speed: float, angle_deg: float, gravity: float = G) -> Dict[str, float]:
    angle_rad = math.radians(angle_deg)
    vx = speed * math.cos(angle_rad)
    vy = speed * math.sin(angle_rad)
    flight_time = 0.0 if gravity <= 0 else (2.0 * vy / gravity)
    max_height = 0.0 if gravity <= 0 else (vy * vy) / (2.0 * gravity)
    range_distance = vx * flight_time
    return {
        "flight_time": max(flight_time, 0.0),
        "max_height": max(max_height, 0.0),
        "range": max(range_distance, 0.0),
    }


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Interactive Ballistics Simulator</title>
  <style>
    :root {
      --bg: #f4efe6;
      --panel: rgba(255, 249, 240, 0.86);
      --panel-strong: #fff7ea;
      --ink: #1f1f1a;
      --muted: #5c594f;
      --accent: #b6462a;
      --accent-soft: #de8f49;
      --sky: #b9d7ea;
      --field: #c8d9a0;
      --ideal: #2459d3;
      --drag: #d54b37;
      --compare: #3f8a47;
      --border: rgba(31, 31, 26, 0.12);
      --shadow: 0 20px 60px rgba(84, 56, 21, 0.16);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255, 226, 183, 0.85), transparent 32%),
        radial-gradient(circle at top right, rgba(185, 215, 234, 0.95), transparent 28%),
        linear-gradient(180deg, #f7f2e7 0%, var(--bg) 55%, #ece2cf 100%);
      min-height: 100vh;
    }

    .shell {
      width: min(1400px, calc(100vw - 32px));
      margin: 24px auto;
      display: grid;
      gap: 18px;
      grid-template-columns: 340px minmax(0, 1fr);
      grid-template-areas:
        "header header"
        "controls viz"
        "notes viz";
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }

    .hero {
      grid-area: header;
      padding: 28px;
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.8fr);
      align-items: end;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 4rem);
      line-height: 0.95;
      letter-spacing: -0.05em;
    }

    .hero p {
      margin: 0;
      color: var(--muted);
      font-size: 1.02rem;
      max-width: 58ch;
    }

    .stat-strip {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .stat {
      background: linear-gradient(180deg, rgba(255,255,255,0.65), rgba(255,255,255,0.35));
      border-radius: 18px;
      padding: 14px;
      border: 1px solid rgba(255,255,255,0.5);
    }

    .stat strong {
      display: block;
      font-size: 1.35rem;
      margin-top: 6px;
    }

    .controls {
      grid-area: controls;
      padding: 22px;
      display: grid;
      gap: 16px;
      align-content: start;
    }

    .controls h2,
    .viz h2,
    .notes h2 {
      margin: 0;
      font-size: 1.05rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .control-grid {
      display: grid;
      gap: 14px;
    }

    label {
      display: grid;
      gap: 8px;
      font-size: 0.95rem;
      font-weight: 700;
    }

    .control-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
    }

    .value {
      font-weight: 800;
      color: var(--accent);
    }

    input[type="range"] {
      width: 100%;
      accent-color: var(--accent);
    }

    input[type="number"] {
      width: 100%;
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 10px 12px;
      background: rgba(255,255,255,0.85);
      font: inherit;
      color: var(--ink);
    }

    .toggle-row,
    .actions,
    .preset-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .toggle {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255,255,255,0.7);
      border-radius: 999px;
      padding: 8px 12px;
      border: 1px solid var(--border);
      font-weight: 600;
    }

    button {
      border: none;
      border-radius: 999px;
      padding: 11px 16px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 140ms ease, opacity 140ms ease, background 140ms ease;
    }

    button:hover { transform: translateY(-1px); }
    button.primary { background: var(--accent); color: white; }
    button.secondary { background: #eadfc8; color: var(--ink); }
    button.preset { background: rgba(255,255,255,0.75); color: var(--ink); border: 1px solid var(--border); }

    .viz {
      grid-area: viz;
      padding: 22px;
      display: grid;
      gap: 16px;
      align-content: start;
    }

    .canvas-wrap {
      position: relative;
      border-radius: 24px;
      overflow: hidden;
      border: 1px solid var(--border);
      background:
        linear-gradient(180deg, rgba(185, 215, 234, 0.95) 0%, rgba(225, 242, 251, 0.95) 48%, rgba(200, 217, 160, 0.95) 48%, rgba(183, 198, 134, 0.95) 100%);
      min-height: 520px;
    }

    canvas {
      display: block;
      width: 100%;
      height: 520px;
    }

    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      color: var(--muted);
      font-size: 0.93rem;
    }

    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .legend i {
      width: 16px;
      height: 4px;
      border-radius: 999px;
      display: inline-block;
    }

    .metric-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .metric {
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--border);
    }

    .metric .label {
      color: var(--muted);
      font-size: 0.9rem;
      margin-bottom: 8px;
    }

    .metric strong {
      display: block;
      font-size: 1.3rem;
      line-height: 1;
    }

    .metric small {
      display: block;
      margin-top: 6px;
      color: var(--muted);
    }

    .notes {
      grid-area: notes;
      padding: 22px;
      display: grid;
      gap: 14px;
      align-content: start;
    }

    .note {
      background: rgba(255,255,255,0.72);
      border-radius: 18px;
      padding: 14px;
      border: 1px solid var(--border);
    }

    .note strong {
      display: block;
      margin-bottom: 6px;
    }

    .muted {
      color: var(--muted);
    }

    @media (max-width: 1080px) {
      .shell {
        grid-template-columns: 1fr;
        grid-template-areas:
          "header"
          "controls"
          "viz"
          "notes";
      }

      .hero {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 700px) {
      .shell {
        width: min(100vw - 16px, 1400px);
        margin: 8px auto 16px;
      }

      .hero,
      .controls,
      .viz,
      .notes {
        border-radius: 20px;
        padding: 18px;
      }

      .stat-strip,
      .metric-grid {
        grid-template-columns: 1fr;
      }

      .canvas-wrap,
      canvas {
        min-height: 380px;
        height: 380px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero card">
      <div>
        <p class="muted">Physics Education Sandbox</p>
        <h1>Interactive Ballistics Simulator</h1>
        <p>
          Explore how launch angle, velocity, mass, and drag reshape projectile motion.
          Compare ideal vacuum motion against a numerical air-resistance model in real time.
        </p>
      </div>
      <div class="stat-strip">
        <div class="stat">
          Angle
          <strong id="hero-angle">45.0°</strong>
        </div>
        <div class="stat">
          Speed
          <strong id="hero-speed">55.0 m/s</strong>
        </div>
        <div class="stat">
          Mode
          <strong id="hero-mode">Compare</strong>
        </div>
      </div>
    </section>

    <aside class="controls card">
      <h2>Launch Controls</h2>
      <div class="control-grid">
        <label>
          <span class="control-header"><span>Launch angle</span><span class="value" data-out="angle">45.0°</span></span>
          <input id="angle" type="range" min="0" max="90" step="0.5" value="45">
        </label>
        <label>
          <span class="control-header"><span>Initial velocity</span><span class="value" data-out="speed">55.0 m/s</span></span>
          <input id="speed" type="range" min="5" max="180" step="1" value="55">
        </label>
        <label>
          <span class="control-header"><span>Projectile mass</span><span class="value" data-out="mass">1.00 kg</span></span>
          <input id="mass" type="range" min="0.1" max="20" step="0.1" value="1">
        </label>
        <label>
          <span class="control-header"><span>Drag coefficient (Cd)</span><span class="value" data-out="dragCoefficient">0.47</span></span>
          <input id="dragCoefficient" type="range" min="0.05" max="1.5" step="0.01" value="0.47">
        </label>
        <label>
          <span class="control-header"><span>Air density</span><span class="value" data-out="airDensity">1.225 kg/m³</span></span>
          <input id="airDensity" type="range" min="0" max="1.5" step="0.01" value="1.225">
        </label>
        <label>
          <span class="control-header"><span>Cross-sectional area</span><span class="value" data-out="area">0.010 m²</span></span>
          <input id="area" type="range" min="0.001" max="0.08" step="0.001" value="0.01">
        </label>
        <label>
          <span class="control-header"><span>Time step</span><span class="value" data-out="dt">0.016 s</span></span>
          <input id="dt" type="range" min="0.005" max="0.05" step="0.001" value="0.016">
        </label>
      </div>

      <div class="toggle-row">
        <label class="toggle"><input id="showIdeal" type="checkbox" checked> Ideal</label>
        <label class="toggle"><input id="showDrag" type="checkbox" checked> With drag</label>
        <label class="toggle"><input id="compareMode" type="checkbox" checked> Compare side by side</label>
      </div>

      <div class="actions">
        <button class="primary" id="launchBtn">Launch</button>
        <button class="secondary" id="replayBtn">Replay</button>
        <button class="secondary" id="resetBtn">Reset</button>
      </div>

      <div>
        <h2>Presets</h2>
        <div class="preset-list">
          <button class="preset" data-preset="vacuum">Ideal vacuum</button>
          <button class="preset" data-preset="highDrag">High drag</button>
          <button class="preset" data-preset="heavy">Heavy projectile</button>
          <button class="preset" data-preset="longRange">Long-range shot</button>
        </div>
      </div>
    </aside>

    <section class="viz card">
      <h2>Trajectory Visualization</h2>
      <div class="legend">
        <span><i style="background: var(--ideal)"></i> Ideal analytical trajectory</span>
        <span><i style="background: var(--drag)"></i> Drag simulation trajectory</span>
        <span><i style="background: var(--compare)"></i> Active tracer / peak markers</span>
      </div>
      <div class="canvas-wrap">
        <canvas id="simCanvas" width="960" height="520"></canvas>
      </div>
      <div class="metric-grid" id="metrics"></div>
    </section>

    <aside class="notes card">
      <h2>Why It Behaves This Way</h2>
      <div class="note">
        <strong>Why drag reduces range</strong>
        <span class="muted">Air resistance continuously opposes velocity, so the projectile loses horizontal speed and reaches the ground sooner.</span>
      </div>
      <div class="note">
        <strong>Why the optimal angle shifts</strong>
        <span class="muted">In vacuum the classic optimum is 45°, but drag penalizes long airtime, so lower launch angles often travel farther.</span>
      </div>
      <div class="note">
        <strong>Ideal vs. real motion</strong>
        <span class="muted">The ideal model is symmetric and exactly solvable. The drag model is not symmetric and needs step-by-step numerical integration.</span>
      </div>
      <div class="note">
        <strong>Validation cue</strong>
        <span class="muted">Set air density to zero or disable drag to make the simulated path collapse toward the analytical ideal solution.</span>
      </div>
    </aside>
  </main>

  <script>
    const defaults = {
      angle: 45,
      speed: 55,
      mass: 1,
      dragCoefficient: 0.47,
      airDensity: 1.225,
      area: 0.01,
      dt: 0.016,
      showIdeal: true,
      showDrag: true,
      compareMode: true
    };

    const presets = {
      vacuum: { angle: 45, speed: 50, mass: 1, dragCoefficient: 0.47, airDensity: 0, area: 0.01, dt: 0.016, showIdeal: true, showDrag: true, compareMode: true },
      highDrag: { angle: 42, speed: 48, mass: 0.45, dragCoefficient: 1.2, airDensity: 1.225, area: 0.045, dt: 0.012, showIdeal: true, showDrag: true, compareMode: true },
      heavy: { angle: 45, speed: 55, mass: 8, dragCoefficient: 0.35, airDensity: 1.225, area: 0.012, dt: 0.016, showIdeal: true, showDrag: true, compareMode: true },
      longRange: { angle: 34, speed: 120, mass: 5, dragCoefficient: 0.2, airDensity: 1.0, area: 0.008, dt: 0.01, showIdeal: true, showDrag: true, compareMode: true }
    };

    const formatters = {
      angle: (v) => `${Number(v).toFixed(1)}°`,
      speed: (v) => `${Number(v).toFixed(1)} m/s`,
      mass: (v) => `${Number(v).toFixed(2)} kg`,
      dragCoefficient: (v) => Number(v).toFixed(2),
      airDensity: (v) => `${Number(v).toFixed(3)} kg/m³`,
      area: (v) => `${Number(v).toFixed(3)} m²`,
      dt: (v) => `${Number(v).toFixed(3)} s`,
    };

    const canvas = document.getElementById("simCanvas");
    const ctx = canvas.getContext("2d");
    const metricsEl = document.getElementById("metrics");
    const launchBtn = document.getElementById("launchBtn");
    const replayBtn = document.getElementById("replayBtn");
    const resetBtn = document.getElementById("resetBtn");

    const controls = {
      angle: document.getElementById("angle"),
      speed: document.getElementById("speed"),
      mass: document.getElementById("mass"),
      dragCoefficient: document.getElementById("dragCoefficient"),
      airDensity: document.getElementById("airDensity"),
      area: document.getElementById("area"),
      dt: document.getElementById("dt"),
      showIdeal: document.getElementById("showIdeal"),
      showDrag: document.getElementById("showDrag"),
      compareMode: document.getElementById("compareMode"),
    };

    const state = {
      params: { ...defaults },
      ideal: null,
      drag: null,
      animationStart: 0,
      animating: false
    };

    function readParams() {
      return {
        angle: Number(controls.angle.value),
        speed: Number(controls.speed.value),
        mass: Number(controls.mass.value),
        dragCoefficient: Number(controls.dragCoefficient.value),
        airDensity: Number(controls.airDensity.value),
        area: Number(controls.area.value),
        dt: Number(controls.dt.value),
        showIdeal: controls.showIdeal.checked,
        showDrag: controls.showDrag.checked,
        compareMode: controls.compareMode.checked
      };
    }

    function syncControls(params) {
      Object.entries(params).forEach(([key, value]) => {
        const control = controls[key];
        if (!control) {
          return;
        }
        if (control.type === "checkbox") {
          control.checked = Boolean(value);
        } else {
          control.value = String(value);
        }
      });
      updateLabels();
    }

    function updateLabels() {
      state.params = readParams();
      document.querySelectorAll("[data-out]").forEach((node) => {
        const key = node.dataset.out;
        node.textContent = formatters[key](state.params[key]);
      });
      document.getElementById("hero-angle").textContent = formatters.angle(state.params.angle);
      document.getElementById("hero-speed").textContent = formatters.speed(state.params.speed);
      document.getElementById("hero-mode").textContent = state.params.compareMode ? "Compare" : "Single";
    }

    function simulateIdeal(params) {
      const theta = params.angle * Math.PI / 180;
      const vx = params.speed * Math.cos(theta);
      const vy = params.speed * Math.sin(theta);
      const flightTime = (2 * vy) / 9.81;
      const points = [];
      const step = Math.max(params.dt, flightTime / 240 || params.dt);
      let maxHeight = 0;

      for (let t = 0; t <= flightTime; t += step) {
        const x = vx * t;
        const y = (vy * t) - (0.5 * 9.81 * t * t);
        points.push({ x, y: Math.max(0, y), t, vx, vy: vy - 9.81 * t });
        maxHeight = Math.max(maxHeight, y);
      }

      const range = vx * flightTime;
      points.push({ x: range, y: 0, t: flightTime, vx, vy: -vy });
      return {
        points,
        metrics: {
          range,
          maxHeight,
          flightTime,
          finalSpeed: Math.hypot(vx, -vy),
          peak: { x: vx * (vy / 9.81), y: maxHeight }
        }
      };
    }

    function simulateDrag(params) {
      const theta = params.angle * Math.PI / 180;
      let x = 0;
      let y = 0;
      let vx = params.speed * Math.cos(theta);
      let vy = params.speed * Math.sin(theta);
      const dt = params.dt;
      const points = [{ x, y, t: 0, vx, vy }];
      let t = 0;
      let maxHeight = 0;
      let peak = { x: 0, y: 0 };
      const dragConstant = 0.5 * params.airDensity * params.dragCoefficient * params.area / params.mass;

      for (let i = 0; i < 25000; i += 1) {
        const speed = Math.hypot(vx, vy);
        const ax = speed === 0 ? 0 : -dragConstant * speed * vx;
        const ay = -9.81 - (speed === 0 ? 0 : dragConstant * speed * vy);

        vx += ax * dt;
        vy += ay * dt;
        x += vx * dt;
        y += vy * dt;
        t += dt;

        if (y > maxHeight) {
          maxHeight = y;
          peak = { x, y };
        }

        if (y <= 0 && t > 0) {
          const prev = points[points.length - 1];
          const ratio = prev.y / (prev.y - y || 1);
          const impactX = prev.x + (x - prev.x) * ratio;
          const impactT = prev.t + (t - prev.t) * ratio;
          points.push({ x: impactX, y: 0, t: impactT, vx, vy });
          return {
            points,
            metrics: {
              range: impactX,
              maxHeight,
              flightTime: impactT,
              finalSpeed: Math.hypot(vx, vy),
              peak
            }
          };
        }

        points.push({ x, y, t, vx, vy });
      }

      return {
        points,
        metrics: {
          range: x,
          maxHeight,
          flightTime: t,
          finalSpeed: Math.hypot(vx, vy),
          peak
        }
      };
    }

    function recompute() {
      updateLabels();
      state.ideal = simulateIdeal(state.params);
      state.drag = simulateDrag(state.params);
      renderMetrics();
      drawScene(1);
    }

    function renderMetrics() {
      const rows = [];
      if (state.params.showIdeal) {
        rows.push(metricCard("Ideal range", state.ideal.metrics.range, "m", `Time ${state.ideal.metrics.flightTime.toFixed(2)} s`));
        rows.push(metricCard("Ideal max height", state.ideal.metrics.maxHeight, "m", `Impact speed ${state.ideal.metrics.finalSpeed.toFixed(2)} m/s`));
      }
      if (state.params.showDrag) {
        rows.push(metricCard("Drag range", state.drag.metrics.range, "m", `Time ${state.drag.metrics.flightTime.toFixed(2)} s`));
        rows.push(metricCard("Drag max height", state.drag.metrics.maxHeight, "m", `Impact speed ${state.drag.metrics.finalSpeed.toFixed(2)} m/s`));
      }
      const deltaRange = state.ideal.metrics.range - state.drag.metrics.range;
      const angleHint = state.params.airDensity > 0 ? "Lower angles often win with drag." : "Vacuum restores the 45° symmetry.";
      rows.push(metricCard("Range loss to drag", deltaRange, "m", angleHint));
      rows.push(metricCard("Time step", state.params.dt, "s", "Smaller steps improve stability but cost more frames."));
      metricsEl.innerHTML = rows.join("");
    }

    function metricCard(label, value, unit, note) {
      return `
        <article class="metric">
          <div class="label">${label}</div>
          <strong>${value.toFixed(2)} ${unit}</strong>
          <small>${note}</small>
        </article>
      `;
    }

    function worldBounds() {
      const visible = [];
      if (state.params.showIdeal) {
        visible.push(...state.ideal.points);
      }
      if (state.params.showDrag) {
        visible.push(...state.drag.points);
      }
      const maxX = Math.max(1, ...visible.map((p) => p.x));
      const maxY = Math.max(1, ...visible.map((p) => p.y));
      return { maxX: maxX * 1.08, maxY: maxY * 1.15 };
    }

    function toCanvas(x, y, bounds) {
      const padLeft = 64;
      const padRight = 24;
      const padTop = 24;
      const padBottom = 44;
      const width = canvas.width - padLeft - padRight;
      const height = canvas.height - padTop - padBottom;
      return {
        x: padLeft + (x / bounds.maxX) * width,
        y: canvas.height - padBottom - (y / bounds.maxY) * height
      };
    }

    function drawGrid(bounds) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 1;
      ctx.strokeStyle = "rgba(0,0,0,0.08)";
      ctx.fillStyle = "rgba(31,31,26,0.72)";
      ctx.font = "12px Trebuchet MS";

      for (let i = 0; i <= 6; i += 1) {
        const x = (canvas.width - 88) * (i / 6) + 64;
        ctx.beginPath();
        ctx.moveTo(x, 24);
        ctx.lineTo(x, canvas.height - 44);
        ctx.stroke();
        const worldX = (bounds.maxX * i) / 6;
        ctx.fillText(`${worldX.toFixed(0)} m`, x - 16, canvas.height - 18);
      }

      for (let i = 0; i <= 5; i += 1) {
        const y = (canvas.height - 68) * (i / 5) + 24;
        ctx.beginPath();
        ctx.moveTo(64, y);
        ctx.lineTo(canvas.width - 24, y);
        ctx.stroke();
        const worldY = bounds.maxY - (bounds.maxY * i) / 5;
        ctx.fillText(`${worldY.toFixed(0)} m`, 12, y + 4);
      }

      ctx.strokeStyle = "rgba(31,31,26,0.24)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(64, canvas.height - 44);
      ctx.lineTo(canvas.width - 24, canvas.height - 44);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(64, canvas.height - 44);
      ctx.lineTo(64, 24);
      ctx.stroke();
    }

    function drawPath(points, color, bounds, progress) {
      const limit = Math.max(1, Math.floor(points.length * progress));
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.beginPath();
      points.slice(0, limit).forEach((point, index) => {
        const c = toCanvas(point.x, point.y, bounds);
        if (index === 0) {
          ctx.moveTo(c.x, c.y);
        } else {
          ctx.lineTo(c.x, c.y);
        }
      });
      ctx.stroke();

      const tracer = points[Math.min(limit - 1, points.length - 1)];
      const tracerCanvas = toCanvas(tracer.x, tracer.y, bounds);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(tracerCanvas.x, tracerCanvas.y, 5, 0, Math.PI * 2);
      ctx.fill();
    }

    function drawMarker(point, bounds, color, label) {
      const p = toCanvas(point.x, point.y, bounds);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "rgba(31,31,26,0.86)";
      ctx.fillText(label, p.x + 8, p.y - 8);
    }

    function drawScene(progress) {
      const bounds = worldBounds();
      drawGrid(bounds);

      if (state.params.showIdeal) {
        drawPath(state.ideal.points, getComputedStyle(document.documentElement).getPropertyValue("--ideal").trim(), bounds, progress);
        drawMarker(state.ideal.metrics.peak, bounds, getComputedStyle(document.documentElement).getPropertyValue("--compare").trim(), "Ideal peak");
        drawMarker({ x: state.ideal.metrics.range, y: 0 }, bounds, getComputedStyle(document.documentElement).getPropertyValue("--ideal").trim(), "Ideal impact");
      }

      if (state.params.showDrag) {
        drawPath(state.drag.points, getComputedStyle(document.documentElement).getPropertyValue("--drag").trim(), bounds, progress);
        drawMarker(state.drag.metrics.peak, bounds, getComputedStyle(document.documentElement).getPropertyValue("--compare").trim(), "Drag peak");
        drawMarker({ x: state.drag.metrics.range, y: 0 }, bounds, getComputedStyle(document.documentElement).getPropertyValue("--drag").trim(), "Drag impact");
      }

      const origin = toCanvas(0, 0, bounds);
      ctx.fillStyle = "#111";
      ctx.beginPath();
      ctx.arc(origin.x, origin.y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillText("Launch point", origin.x + 8, origin.y - 8);
    }

    function animate(timestamp) {
      if (!state.animating) {
        return;
      }
      if (!state.animationStart) {
        state.animationStart = timestamp;
      }
      const elapsed = timestamp - state.animationStart;
      const progress = Math.min(1, elapsed / 2200);
      drawScene(progress);
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        state.animating = false;
        state.animationStart = 0;
      }
    }

    function launch() {
      recompute();
      state.animating = true;
      state.animationStart = 0;
      requestAnimationFrame(animate);
    }

    Object.values(controls).forEach((control) => {
      control.addEventListener("input", recompute);
      control.addEventListener("change", recompute);
    });

    launchBtn.addEventListener("click", launch);
    replayBtn.addEventListener("click", () => {
      state.animating = true;
      state.animationStart = 0;
      requestAnimationFrame(animate);
    });
    resetBtn.addEventListener("click", () => {
      syncControls(defaults);
      recompute();
    });

    document.querySelectorAll("[data-preset]").forEach((button) => {
      button.addEventListener("click", () => {
        syncControls(presets[button.dataset.preset]);
        launch();
      });
    });

    syncControls(defaults);
    recompute();
    launch();
  </script>
</body>
</html>
"""


class SimulatorHandler(BaseHTTPRequestHandler):
    def _send_index_headers(self) -> bytes | None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404, "Not Found")
            return None

        content = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        return content

    def do_HEAD(self) -> None:
        self._send_index_headers()

    def do_GET(self) -> None:
        content = self._send_index_headers()
        if content is None:
            return
        self.wfile.write(content)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        escaped = html.escape(format % args)
        print(f"[ballistics] {escaped}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the interactive ballistics simulator.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with ThreadingHTTPServer((args.host, args.port), SimulatorHandler) as server:
        print(f"Serving ballistics simulator at http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
