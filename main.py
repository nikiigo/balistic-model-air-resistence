from __future__ import annotations

import argparse
import html
import math
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict

G = 9.81
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


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
      --shell-width: min(1400px, calc(100vw - clamp(16px, 2vw, 32px)));
      --layout-gap: clamp(12px, 1.1vw, 18px);
      --card-radius: clamp(18px, 1.5vw, 24px);
      --card-padding: clamp(16px, 1.4vw, 22px);
      --hero-pad-y: clamp(10px, 0.9vw, 14px);
      --hero-pad-x: clamp(14px, 1.25vw, 20px);
      --guns-width: clamp(220px, 15.95vw, 255px);
      --main-panel-height: clamp(520px, 68vh, 620px);
      --canvas-height: clamp(340px, 45vh, 400px);
      --hero-stat-pad-y: clamp(4px, 0.45vw, 5px);
      --hero-stat-pad-x: clamp(6px, 0.65vw, 8px);
      --hero-stat-radius: clamp(14px, 1.1vw, 18px);
      --control-pop-width: clamp(270px, 20.5vw, 330px);
      --control-pop-offset: clamp(10px, 1.1vw, 18px);
      --control-pop-pad: clamp(8px, 0.75vw, 10px);
      --overlay-radius: clamp(14px, 1.1vw, 18px);
      --overlay-gap: clamp(8px, 0.9vw, 12px);
      --overlay-chip-pad-y: clamp(8px, 0.75vw, 10px);
      --overlay-chip-pad-x: clamp(10px, 0.95vw, 12px);
      --metric-pad: clamp(8px, 0.85vw, 10px);
      --gun-card-height: clamp(110px, 14vh, 132px);
      --gun-card-pad: clamp(6px, 0.7vw, 8px);
      --gun-hover-width: clamp(280px, 24vw, 340px);
      --gun-hover-pad: clamp(10px, 1vw, 14px);
      --caption-inset: clamp(10px, 1vw, 14px);
      --caption-pad-y: clamp(5px, 0.55vw, 6px);
      --caption-pad-x: clamp(6px, 0.65vw, 8px);
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
      width: var(--shell-width);
      margin: clamp(12px, 1.7vw, 24px) auto;
      display: grid;
      gap: var(--layout-gap);
      grid-template-columns: var(--guns-width) minmax(0, 1fr);
      grid-template-areas:
        "header header"
        "guns viz"
        "notes notes";
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--card-radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }

    .hero {
      grid-area: header;
      padding: var(--hero-pad-y) var(--hero-pad-x);
      display: grid;
      gap: clamp(8px, 0.8vw, 10px);
      grid-template-columns: minmax(0, 1.4fr) minmax(clamp(220px, 16vw, 260px), 0.8fr);
      align-items: end;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(1.4rem, 2.6vw, 2.4rem);
      line-height: 0.98;
      letter-spacing: -0.05em;
    }

    .hero p {
      margin: 0;
      color: var(--muted);
      font-size: 0.92rem;
      max-width: 58ch;
    }

    .stat-strip {
      display: grid;
      gap: clamp(8px, 0.9vw, 12px);
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .stat {
      background: linear-gradient(180deg, rgba(255,255,255,0.65), rgba(255,255,255,0.35));
      border-radius: var(--hero-stat-radius);
      padding: var(--hero-stat-pad-y) var(--hero-stat-pad-x);
      border: 1px solid rgba(255,255,255,0.5);
      font-size: 0.8rem;
    }

    .stat strong {
      display: block;
      font-size: 0.82rem;
      margin-top: 2px;
    }

    .guns {
      grid-area: guns;
      position: relative;
      z-index: 4;
      padding: var(--card-padding);
      display: grid;
      gap: var(--layout-gap);
      align-content: stretch;
      height: var(--main-panel-height);
    }

    .guns .section-stack {
      height: 100%;
      min-height: 0;
      display: grid;
      grid-template-rows: auto auto minmax(0, 1fr);
    }

    .guns h2,
    .viz h2,
    .notes h2 {
      margin: 0;
      font-size: 1.05rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .control-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: clamp(8px, 0.8vw, 10px);
    }

    label {
      display: grid;
      gap: clamp(4px, 0.45vw, 5px);
      font-size: 0.82rem;
      font-weight: 700;
    }

    .control-header {
      display: flex;
      justify-content: space-between;
      gap: var(--overlay-gap);
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
      border-radius: clamp(10px, 0.9vw, 12px);
      border: 1px solid var(--border);
      padding: clamp(8px, 0.85vw, 10px) clamp(10px, 0.95vw, 12px);
      background: rgba(255,255,255,0.85);
      font: inherit;
      color: var(--ink);
    }

    .toggle-row,
    .actions,
    .preset-list {
      display: flex;
      flex-wrap: wrap;
      gap: clamp(8px, 0.8vw, 10px);
    }

    .section-stack {
      display: grid;
      gap: var(--layout-gap);
    }

    .toggle {
      display: inline-flex;
      align-items: center;
      gap: clamp(5px, 0.55vw, 6px);
      background: rgba(255,255,255,0.7);
      border-radius: 999px;
      padding: clamp(4px, 0.45vw, 5px) clamp(8px, 0.75vw, 9px);
      border: 1px solid var(--border);
      font-weight: 600;
      font-size: 0.78rem;
    }

    button {
      border: none;
      border-radius: 999px;
      padding: clamp(6px, 0.65vw, 7px) clamp(9px, 0.9vw, 11px);
      font: inherit;
      font-weight: 700;
      font-size: 0.8rem;
      cursor: pointer;
      transition: transform 140ms ease, opacity 140ms ease, background 140ms ease;
    }

    button:hover { transform: translateY(-1px); }
    button.primary { background: var(--accent); color: white; }
    button.secondary { background: #eadfc8; color: var(--ink); }
    button.preset { background: rgba(255,255,255,0.75); color: var(--ink); border: 1px solid var(--border); }

    .viz {
      grid-area: viz;
      position: relative;
      z-index: 1;
      padding: var(--card-padding);
      display: grid;
      gap: var(--layout-gap);
      align-content: stretch;
      grid-template-rows: minmax(0, 1fr) auto;
      min-height: 0;
      height: var(--main-panel-height);
    }

    .canvas-wrap {
      position: relative;
      border-radius: var(--card-radius);
      overflow: hidden;
      border: 1px solid var(--border);
      background:
        linear-gradient(180deg, rgba(185, 215, 234, 0.95) 0%, rgba(225, 242, 251, 0.95) 48%, rgba(200, 217, 160, 0.95) 48%, rgba(183, 198, 134, 0.95) 100%);
      min-height: 0;
      height: 100%;
    }

    .control-pop {
      position: absolute;
      top: var(--control-pop-offset);
      right: var(--control-pop-offset);
      z-index: 3;
      width: min(var(--control-pop-width), calc(100% - (var(--control-pop-offset) * 2)));
      padding: var(--control-pop-pad);
      display: grid;
      gap: clamp(6px, 0.7vw, 8px);
      max-height: calc(100% - (var(--control-pop-offset) * 2));
      overflow: hidden;
      background: rgba(255, 248, 236, 0.92);
      border: 1px solid rgba(31, 31, 26, 0.12);
      border-radius: clamp(12px, 1vw, 16px);
      box-shadow: 0 18px 50px rgba(84, 56, 21, 0.22);
      backdrop-filter: blur(10px);
      grid-template-rows: auto minmax(0, 1fr);
    }

    .control-panel-head {
      display: flex;
      justify-content: space-between;
      gap: var(--overlay-gap);
      align-items: center;
    }

    .control-panel-head h3 {
      margin: 0;
      font-size: 0.84rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .control-scroll {
      display: grid;
      gap: clamp(6px, 0.7vw, 8px);
      overflow: auto;
      padding-right: 2px;
    }

    .control-scroll.hidden {
      display: none;
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
    }

    .legend {
      position: absolute;
      left: var(--control-pop-offset);
      top: var(--control-pop-offset);
      z-index: 2;
      display: flex;
      flex-wrap: wrap;
      gap: var(--overlay-gap);
      color: rgba(31, 31, 26, 0.86);
      font-size: 0.85rem;
      padding: var(--overlay-chip-pad-y) var(--overlay-chip-pad-x);
      border-radius: var(--overlay-radius);
      background: transparent;
      border: none;
      box-shadow: none;
      backdrop-filter: none;
    }

    .legend span {
      display: inline-flex;
      align-items: center;
      gap: clamp(6px, 0.7vw, 8px);
    }

    .legend i {
      width: 16px;
      height: 4px;
      border-radius: 999px;
      display: inline-block;
    }

    .metric-grid {
      display: grid;
      gap: clamp(6px, 0.7vw, 8px);
      grid-template-columns: repeat(3, minmax(0, 1fr));
      min-width: 0;
    }

    .metric {
      padding: var(--metric-pad);
      border-radius: clamp(12px, 1vw, 14px);
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--border);
      min-width: 0;
    }

    .metric .label {
      color: var(--muted);
      font-size: 0.76rem;
      margin-bottom: 6px;
    }

    .metric strong {
      display: block;
      font-size: 1rem;
      line-height: 1;
      word-break: break-word;
    }

    .metric small {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 0.72rem;
    }

    .notes {
      grid-area: notes;
      padding: var(--card-padding);
      display: grid;
      gap: clamp(10px, 1vw, 14px);
      align-content: start;
    }

    .note {
      background: rgba(255,255,255,0.72);
      border-radius: var(--overlay-radius);
      padding: clamp(10px, 1vw, 14px);
      border: 1px solid var(--border);
    }

    .note strong {
      display: block;
      margin-bottom: 6px;
    }

    .lock-note,
    .gun-card,
    .gun-hover {
      background: rgba(255,255,255,0.72);
      border-radius: var(--overlay-radius);
      border: 1px solid var(--border);
    }

    .lock-note {
      padding: clamp(6px, 0.7vw, 8px) clamp(8px, 0.85vw, 10px);
      font-size: 0.82rem;
      line-height: 1.1;
      border-radius: clamp(10px, 0.9vw, 12px);
    }

    .gun-library {
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      overflow-x: hidden;
      scroll-snap-type: y mandatory;
      gap: var(--overlay-gap);
      padding-right: 4px;
      min-height: 0;
      flex: 1 1 auto;
    }

    .gun-zone {
      position: relative;
      z-index: 6;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      gap: var(--overlay-gap);
      min-height: 0;
      height: 100%;
    }

    .gun-card {
      min-height: var(--gun-card-height);
      flex: 0 0 var(--gun-card-height);
      padding: var(--gun-card-pad);
      display: block;
      cursor: pointer;
      scroll-snap-align: start;
      position: relative;
    }

    .gun-card.active {
      border-color: rgba(182, 70, 42, 0.55);
      box-shadow: inset 0 0 0 1px rgba(182, 70, 42, 0.18);
    }

    .gun-card img,
    .gun-hover img {
      width: 100%;
      height: 100%;
      display: block;
      border-radius: clamp(12px, 1vw, 14px);
      object-fit: cover;
      background: rgba(0,0,0,0.06);
    }

    .gun-caption {
      position: absolute;
      left: var(--caption-inset);
      right: var(--caption-inset);
      bottom: var(--caption-inset);
      padding: var(--caption-pad-y) var(--caption-pad-x);
      text-align: center;
      font-size: 0.76rem;
      color: #fffaf0;
      font-weight: 800;
      border-radius: clamp(8px, 0.8vw, 10px);
      background: transparent;
      border: none;
      text-shadow: 0 1px 8px rgba(0, 0, 0, 0.72);
    }

    .gun-copy {
      display: grid;
      gap: clamp(5px, 0.55vw, 6px);
    }

    .gun-copy h3,
    .gun-hover h3 {
      margin: 0;
      font-size: 1.05rem;
    }

    .gun-specs {
      display: grid;
      gap: clamp(5px, 0.55vw, 6px);
      color: var(--muted);
      font-size: 0.92rem;
    }

    .gun-hover {
      position: absolute;
      top: 0;
      left: calc(100% + var(--overlay-gap));
      width: min(var(--gun-hover-width), 42vw);
      padding: var(--gun-hover-pad);
      display: grid;
      gap: var(--overlay-gap);
      background: rgba(255, 248, 236, 0.96);
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
      z-index: 5;
    }

    .gun-hover.hidden {
      display: none;
    }

    .gun-hover-head {
      display: flex;
      justify-content: space-between;
      gap: var(--overlay-gap);
      align-items: start;
    }

    .source-list {
      display: flex;
      flex-wrap: wrap;
      gap: clamp(6px, 0.7vw, 8px);
    }

    .source-list a {
      color: var(--accent);
      font-weight: 700;
      text-decoration: none;
    }

    .source-list a:hover {
      text-decoration: underline;
    }

    .muted {
      color: var(--muted);
    }

    @media (max-width: 1080px) {
      .shell {
        grid-template-columns: 1fr;
        grid-template-areas:
          "header"
          "guns"
          "viz"
          "notes";
      }

      .hero {
        grid-template-columns: 1fr;
      }

      .guns,
      .viz {
        height: auto;
      }

      .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 700px) {
      .shell {
        width: min(100vw - 16px, 1400px);
        margin: 8px auto 16px;
      }

      .hero,
      .guns,
      .viz,
      .notes {
        border-radius: 20px;
        padding: 18px;
      }

      .stat-strip,
      .metric-grid {
        grid-template-columns: 1fr;
      }

      .control-grid {
        grid-template-columns: 1fr;
      }

      .canvas-wrap,
      canvas {
        min-height: 320px;
        height: 320px;
      }

      .gun-library {
        gap: 10px;
      }

      .gun-hover {
        position: static;
        width: 100%;
      }

      .control-pop {
        top: 10px;
        right: 10px;
        width: calc(100% - 20px);
        padding: 10px;
        max-height: calc(100% - 20px);
      }

      .legend {
        left: 10px;
        right: 10px;
        top: 10px;
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

    <aside class="guns card">
      <div class="section-stack">
        <h2>Historic Gun Library</h2>
        <div class="lock-note" id="lockNote">
          select a real gun
        </div>
        <div class="gun-zone">
          <div class="gun-library" id="gunLibrary"></div>
          <div class="gun-hover hidden" id="gunHover">
            <div class="gun-hover-head">
              <div>
                <h3 id="gunHoverTitle">Historic gun</h3>
                <div class="muted" id="gunHoverSubtitle"></div>
              </div>
            </div>
            <img id="gunHoverImage" alt="" loading="lazy">
            <div class="gun-copy">
              <div class="gun-specs" id="gunHoverSpecs"></div>
              <div class="muted" id="gunHoverNote"></div>
              <div class="source-list" id="gunHoverSources"></div>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <section class="viz card">
      <div class="canvas-wrap">
        <div class="control-pop">
        <div class="control-panel-head">
          <h3>Launch Controls</h3>
          <button class="secondary" id="toggleControlsBtn">Hide</button>
        </div>
        <div class="control-scroll" id="controlScroll">
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

          <div class="actions">
            <button class="primary" id="launchBtn">Launch</button>
            <button class="secondary" id="replayBtn">Replay</button>
            <button class="secondary" id="resetBtn">Reset</button>
          </div>

          <div class="section-stack">
            <h3>Presets</h3>
            <div class="preset-list">
              <button class="preset" data-preset="vacuum">Ideal vacuum</button>
              <button class="preset" data-preset="highDrag">High drag</button>
              <button class="preset" data-preset="heavy">Heavy projectile</button>
              <button class="preset" data-preset="longRange">Long-range shot</button>
            </div>
          </div>
        </div>
        </div>
        <div class="legend">
          <span><i style="background: var(--ideal)"></i> Ideal analytical trajectory</span>
          <span><i style="background: var(--drag)"></i> Drag simulation trajectory</span>
          <span><i style="background: var(--compare)"></i> Active tracer / peak markers</span>
        </div>
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
      <div class="note">
        <strong>Historical preset caveat</strong>
        <span class="muted">Gun presets use documented bore, shot mass, and listed range or muzzle velocity. Drag coefficient and projectile area are simplified simulation inputs, and the Gribeauval launch speed is explicitly inferred from its reported maximum range.</span>
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
      dt: 0.016
    };

    const presets = {
      vacuum: { angle: 45, speed: 50, mass: 1, dragCoefficient: 0.47, airDensity: 0, area: 0.01, dt: 0.016 },
      highDrag: { angle: 42, speed: 48, mass: 0.45, dragCoefficient: 1.2, airDensity: 1.225, area: 0.045, dt: 0.012 },
      heavy: { angle: 45, speed: 55, mass: 8, dragCoefficient: 0.35, airDensity: 1.225, area: 0.012, dt: 0.016 },
      longRange: { angle: 34, speed: 120, mass: 5, dragCoefficient: 0.2, airDensity: 1.0, area: 0.008, dt: 0.01 }
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
    const toggleControlsBtn = document.getElementById("toggleControlsBtn");
    const controlScroll = document.getElementById("controlScroll");
    const gunLibraryEl = document.getElementById("gunLibrary");
    const lockNoteEl = document.getElementById("lockNote");
    const gunHover = document.getElementById("gunHover");
    const gunHoverTitle = document.getElementById("gunHoverTitle");
    const gunHoverSubtitle = document.getElementById("gunHoverSubtitle");
    const gunHoverImage = document.getElementById("gunHoverImage");
    const gunHoverSpecs = document.getElementById("gunHoverSpecs");
    const gunHoverNote = document.getElementById("gunHoverNote");
    const gunHoverSources = document.getElementById("gunHoverSources");

    const controls = {
      angle: document.getElementById("angle"),
      speed: document.getElementById("speed"),
      mass: document.getElementById("mass"),
      dragCoefficient: document.getElementById("dragCoefficient"),
      airDensity: document.getElementById("airDensity"),
      area: document.getElementById("area"),
      dt: document.getElementById("dt")
    };

    const historicalGuns = {
      basilisk: {
        name: "Queen Elizabeth's Pocket Pistol",
        subtitle: "Holy Roman Empire / England, 1544",
        image: "/assets/guns/queen-elizabeths-pocket-pistol.jpg",
        imageAlt: "Queen Elizabeth's Pocket Pistol at Dover Castle",
        imagePosition: "center center",
        caliber: "4.75 in (121 mm)",
        projectile: "10 lb shot (4.54 kg)",
        muzzleVelocity: "Estimated 134 m/s",
        range: "1,829 m test range",
        service: "Tudor coastal artillery",
        note: "This giant basilisk survives at Dover Castle. The simulator launch speed is inferred from the reported shot distance rather than a documented muzzle-velocity figure.",
        params: { angle: 16, speed: 134, mass: 4.54, dragCoefficient: 0.47, airDensity: 1.225, area: 0.0115, dt: 0.02 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Queen_Elizabeth%27s_Pocket_Pistol" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Queen_Elizabeth%27s_Pocket_Pistol.JPG" }
        ]
      },
      culverin: {
        name: "Culverin",
        subtitle: "France / England, 16th century",
        image: "/assets/guns/korean-culverin.jpg",
        imageAlt: "Korean culverin",
        imagePosition: "center center",
        caliber: "5.5 in (140 mm)",
        projectile: "17 lb shot (7.71 kg)",
        muzzleVelocity: "408 m/s",
        range: "Over 450 m at low elevation",
        service: "Renaissance field and siege artillery",
        note: "The speed figure comes from tests of a modern replica of an extraordinary culverin. Shot weight varied by pattern, so this preset uses a mid-range historical ball mass.",
        params: { angle: 9, speed: 408, mass: 7.71, dragCoefficient: 0.43, airDensity: 1.225, area: 0.0154, dt: 0.012 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Culverin" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Korean_culverin.jpg" }
        ]
      },
      demiCulverin: {
        name: "Demi-culverin",
        subtitle: "England / Europe, late 16th century",
        image: "/assets/guns/demi-culverin-mary-rose.jpg",
        imageAlt: "Demi-culverin from the Mary Rose collection",
        imagePosition: "center center",
        caliber: "4.0 in (102 mm)",
        projectile: "8 lb shot (3.63 kg)",
        muzzleVelocity: "Modeled 145 m/s",
        range: "549 m effective range",
        service: "Naval and field artillery",
        note: "The article provides shot class and effective range but not muzzle velocity. The simulator uses a conservative modeled launch speed consistent with a lighter long gun sitting between a saker and a culverin.",
        params: { angle: 14, speed: 145, mass: 3.63, dragCoefficient: 0.45, airDensity: 1.225, area: 0.0082, dt: 0.016 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Demi-culverin" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Demi_Culverin,_Mary_Rose_-_55130506883.jpg" }
        ]
      },
      saker: {
        name: "Saker",
        subtitle: "England, early 16th century",
        image: "/assets/guns/english-saker-fort-nelson.jpg",
        imageAlt: "English saker at Fort Nelson",
        imagePosition: "center center",
        caliber: "3.25 in (83 mm)",
        projectile: "5.25 lb shot (2.38 kg)",
        muzzleVelocity: "Estimated 164 m/s",
        range: "2,743 m maximum range",
        service: "Tudor and Stuart artillery",
        note: "The simulator launch speed is inferred from the reported maximum range. Real service loads varied substantially across foundries and periods.",
        params: { angle: 15, speed: 164, mass: 2.38, dragCoefficient: 0.46, airDensity: 1.225, area: 0.0054, dt: 0.016 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Saker" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:English_Saker,_Used_by_Chinese_and_Vietnamese,_Fort_Nelson,_Hampshire.jpg" }
        ]
      },
      falconet: {
        name: "Falconet",
        subtitle: "Europe, 16th to 17th century",
        image: "/assets/guns/falconet-wrought-iron-17th-century.jpg",
        imageAlt: "Wrought-iron falconet from the 17th century",
        imagePosition: "center center",
        caliber: "2.0 in (51 mm)",
        projectile: "1 lb shot (0.45 kg)",
        muzzleVelocity: "Estimated 122 m/s",
        range: "1,524 m maximum range",
        service: "Light field and fortress artillery",
        note: "This light piece is modeled from its reported maximum range rather than a preserved firing table, so the simulator value is an educational approximation.",
        params: { angle: 17, speed: 122, mass: 0.45, dragCoefficient: 0.47, airDensity: 1.225, area: 0.0020, dt: 0.018 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Falconet" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Falconet_wrought_iron_17th_century_(16424842933).jpg" }
        ]
      },
      demiCannon: {
        name: "Demi-cannon",
        subtitle: "England, early 17th century",
        image: "/assets/guns/32-pounder-naval-cannon-raleigh.jpg",
        imageAlt: "Large iron naval cannon used as a representative demi-cannon image",
        imagePosition: "center center",
        caliber: "6.25 in (159 mm)",
        projectile: "32 lb shot (14.5 kg)",
        muzzleVelocity: "Modeled 95 m/s",
        range: "488 m effective range",
        service: "Naval broadside artillery",
        note: "The article gives shot class and effective range rather than muzzle velocity. The simulator uses a conservative modeled launch speed and a representative heavy naval gun image.",
        params: { angle: 11, speed: 95, mass: 14.5, dragCoefficient: 0.44, airDensity: 1.225, area: 0.0198, dt: 0.02 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Demi-cannon" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:32-pounder_Naval_Cannon_(Raleigh,_NC)_-_DSC05867.JPG" }
        ]
      },
      gribeauval: {
        name: "Canon de 12 Gribeauval",
        subtitle: "France, 1765",
        image: "/assets/guns/gribeauval-cannon-de-12.jpg",
        imageAlt: "Canon de 12 Gribeauval at Les Invalides",
        imagePosition: "center center",
        caliber: "121 mm",
        projectile: "12 French livres round shot (~5.88 kg)",
        muzzleVelocity: "Estimated 133 m/s",
        range: "1,800 m max range",
        service: "American Revolutionary War, Napoleonic Wars",
        note: "The source used here gives range but not muzzle velocity. The simulator launch speed is inferred from the reported 1,800 m maximum range under an idealized 45° estimate.",
        params: { angle: 18, speed: 133, mass: 5.88, dragCoefficient: 0.47, airDensity: 1.225, area: 0.0115, dt: 0.02 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Canon_de_12_Gribeauval" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Gribeauval_cannon_de_12_An_2_de_la_Republique.jpg" }
        ]
      },
      napoleon: {
        name: "M1857 12-pounder Napoleon",
        subtitle: "United States, 1857",
        image: "/assets/guns/gettysburg-12-pounder-napoleon.jpg",
        imageAlt: "M1857 12-pounder Napoleon at Gettysburg",
        imagePosition: "center center",
        caliber: "4.62 in (117 mm)",
        projectile: "12 lb round shot (5.44 kg)",
        muzzleVelocity: "439 m/s",
        range: "1,480 m at 5°",
        service: "American Civil War",
        note: "This is a smoothbore gun-howitzer. The preset keeps the round-shot drag model used elsewhere in the simulator.",
        params: { angle: 12, speed: 439, mass: 5.44, dragCoefficient: 0.47, airDensity: 1.225, area: 0.0108, dt: 0.012 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/M1857_12-pounder_Napoleon" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Gettysburg,_12-pounder_Napoleon.jpg" }
        ]
      },
      ordnance: {
        name: "3-inch Ordnance Rifle",
        subtitle: "United States, 1861",
        image: "/assets/guns/cw-arty-3in-ordnance-front.jpg",
        imageAlt: "3-inch ordnance rifle at Gettysburg",
        imagePosition: "center center",
        caliber: "3.0 in (76 mm)",
        projectile: "9.5 lb shell (4.3 kg)",
        muzzleVelocity: "370 m/s",
        range: "1,673 m at 5°",
        service: "American Civil War",
        note: "This preset represents a rifled shell rather than a smooth round shot, so the drag coefficient is modeled lower.",
        params: { angle: 10, speed: 370, mass: 4.3, dragCoefficient: 0.32, airDensity: 1.225, area: 0.0045, dt: 0.01 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/3-inch_ordnance_rifle" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:CW_Arty_3in_Ordnance_front.jpg" }
        ]
      },
      armstrong: {
        name: "RBL 12-pounder 8 cwt Armstrong gun",
        subtitle: "United Kingdom, 1859",
        image: "/assets/guns/awm-armstrong-gun-1.jpg",
        imageAlt: "RBL 12-pounder Armstrong gun at the Australian War Memorial",
        imagePosition: "center center",
        caliber: "3.0 in (76.2 mm)",
        projectile: "11 lb 4 oz common shell (5.10 kg)",
        muzzleVelocity: "378 m/s",
        range: "3,109 m",
        service: "Second Opium War, New Zealand Wars",
        note: "This early breech-loader used rifled ammunition. The preset uses the listed common-shell weight and a lower drag coefficient than smoothbore round shot.",
        params: { angle: 8, speed: 378, mass: 5.1, dragCoefficient: 0.32, airDensity: 1.225, area: 0.0046, dt: 0.01 },
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/RBL_12-pounder_8_cwt_Armstrong_gun" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:AWM-Armstrong-gun-1.jpg" }
        ]
      }
    };

    const state = {
      params: { ...defaults },
      ideal: null,
      drag: null,
      currentGun: null,
      hoveredGun: null,
      controlsCollapsed: false,
      animationStart: 0,
      animating: false
    };

    function setControlsCollapsed(collapsed) {
      state.controlsCollapsed = collapsed;
      controlScroll.classList.toggle("hidden", collapsed);
      toggleControlsBtn.textContent = collapsed ? "Show" : "Hide";
      toggleControlsBtn.setAttribute("aria-expanded", String(!collapsed));
    }

    function readParams() {
      return {
        angle: Number(controls.angle.value),
        speed: Number(controls.speed.value),
        mass: Number(controls.mass.value),
        dragCoefficient: Number(controls.dragCoefficient.value),
        airDensity: Number(controls.airDensity.value),
        area: Number(controls.area.value),
        dt: Number(controls.dt.value)
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

    function setGunMode(gunKey) {
      state.currentGun = gunKey;
      syncControls(historicalGuns[gunKey].params);
      applyGunMode();
    }

    function clearGunMode() {
      state.currentGun = null;
      applyGunMode();
    }

    function applyGunMode() {
      const inGunMode = Boolean(state.currentGun);
      lockNoteEl.innerHTML = inGunMode
        ? `<strong>${historicalGuns[state.currentGun].name}</strong>`
        : `select a real gun`;
      renderGunLibrary();
    }

    function renderGunLibrary() {
      gunLibraryEl.innerHTML = Object.entries(historicalGuns).map(([key, gun]) => `
        <article class="gun-card ${state.currentGun === key ? "active" : ""}" data-gun="${key}">
          <img src="${gun.image}" alt="${gun.imageAlt}" loading="lazy" style="object-position: ${gun.imagePosition || "center center"}; transform: scale(${gun.imageScale || 1});">
          <div class="gun-caption">${gun.name}</div>
        </article>
      `).join("");

      gunLibraryEl.querySelectorAll("[data-gun]").forEach((card) => {
        card.addEventListener("mouseenter", () => {
          showGunHover(card.dataset.gun);
        });
        card.addEventListener("focusin", () => {
          showGunHover(card.dataset.gun);
        });
        card.addEventListener("mouseleave", () => {
          hideGunHover();
        });
        card.addEventListener("click", () => {
          setGunMode(card.dataset.gun);
          launch();
        });
      });
    }

    function showGunHover(gunKey) {
      state.hoveredGun = gunKey;
      const gun = historicalGuns[gunKey];
      gunHoverTitle.textContent = gun.name;
      gunHoverSubtitle.textContent = gun.subtitle;
      gunHoverImage.src = gun.image;
      gunHoverImage.alt = gun.imageAlt;
      gunHoverImage.style.objectPosition = gun.imagePosition || "center center";
      gunHoverImage.style.transform = `scale(${gun.imageScale || 1})`;
      gunHoverSpecs.innerHTML = `
        <span><strong>Caliber:</strong> ${gun.caliber}</span>
        <span><strong>Projectile:</strong> ${gun.projectile}</span>
        <span><strong>Muzzle velocity:</strong> ${gun.muzzleVelocity}</span>
        <span><strong>Service:</strong> ${gun.service}</span>
        <span><strong>Reported range:</strong> ${gun.range}</span>
      `;
      gunHoverNote.textContent = gun.note;
      gunHoverSources.innerHTML = gun.sources.map((source) => `<a href="${source.url}" target="_blank" rel="noreferrer">${source.label}</a>`).join("");
      gunHover.classList.remove("hidden");
    }

    function hideGunHover() {
      state.hoveredGun = null;
      gunHover.classList.add("hidden");
    }

    function updateLabels() {
      state.params = readParams();
      document.querySelectorAll("[data-out]").forEach((node) => {
        const key = node.dataset.out;
        node.textContent = formatters[key](state.params[key]);
      });
      document.getElementById("hero-angle").textContent = formatters.angle(state.params.angle);
      document.getElementById("hero-speed").textContent = formatters.speed(state.params.speed);
      document.getElementById("hero-mode").textContent = state.currentGun ? historicalGuns[state.currentGun].name : "Ideal + Drag";
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
      rows.push(metricCard("Ideal range", state.ideal.metrics.range, "m", `Time ${state.ideal.metrics.flightTime.toFixed(2)} s`));
      rows.push(metricCard("Ideal max height", state.ideal.metrics.maxHeight, "m", `Impact speed ${state.ideal.metrics.finalSpeed.toFixed(2)} m/s`));
      rows.push(metricCard("Drag range", state.drag.metrics.range, "m", `Time ${state.drag.metrics.flightTime.toFixed(2)} s`));
      rows.push(metricCard("Drag max height", state.drag.metrics.maxHeight, "m", `Impact speed ${state.drag.metrics.finalSpeed.toFixed(2)} m/s`));
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
      visible.push(...state.ideal.points);
      visible.push(...state.drag.points);
      const maxX = Math.max(1, ...visible.map((p) => p.x));
      const maxY = Math.max(1, ...visible.map((p) => p.y));
      return { maxX: maxX * 1.08, maxY: maxY * 1.15 };
    }

    function resizeCanvas() {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const cssWidth = Math.max(1, Math.round(rect.width));
      const cssHeight = Math.max(1, Math.round(rect.height));
      const pixelWidth = Math.max(1, Math.round(cssWidth * dpr));
      const pixelHeight = Math.max(1, Math.round(cssHeight * dpr));

      if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
        canvas.width = pixelWidth;
        canvas.height = pixelHeight;
      }

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return { width: cssWidth, height: cssHeight };
    }

    function getPlotGeometry(bounds) {
      const cssWidth = canvas.width / (window.devicePixelRatio || 1);
      const cssHeight = canvas.height / (window.devicePixelRatio || 1);
      const padLeft = 64;
      const padRight = 24;
      const padTop = 24;
      const padBottom = 44;
      const plotWidth = cssWidth - padLeft - padRight;
      const plotHeight = cssHeight - padTop - padBottom;
      const scale = Math.min(plotWidth / bounds.maxX, plotHeight / bounds.maxY);
      const usedWidth = bounds.maxX * scale;
      const usedHeight = bounds.maxY * scale;
      const offsetX = padLeft + ((plotWidth - usedWidth) / 2);
      const offsetY = cssHeight - padBottom;
      return { padLeft, padRight, padTop, padBottom, plotWidth, plotHeight, scale, offsetX, offsetY, usedWidth, usedHeight };
    }

    function toCanvas(x, y, bounds) {
      const geometry = getPlotGeometry(bounds);
      return {
        x: geometry.offsetX + (x * geometry.scale),
        y: geometry.offsetY - (y * geometry.scale)
      };
    }

    function drawGrid(bounds) {
      const viewport = resizeCanvas();
      const geometry = getPlotGeometry(bounds);
      ctx.clearRect(0, 0, viewport.width, viewport.height);
      ctx.lineWidth = 1;
      ctx.strokeStyle = "rgba(0,0,0,0.08)";
      ctx.fillStyle = "rgba(31,31,26,0.72)";
      ctx.font = "12px Trebuchet MS";

      for (let i = 0; i <= 6; i += 1) {
        const worldX = (bounds.maxX * i) / 6;
        const x = geometry.offsetX + (worldX * geometry.scale);
        ctx.beginPath();
        ctx.moveTo(x, geometry.padTop);
        ctx.lineTo(x, geometry.offsetY);
        ctx.stroke();
        ctx.fillText(`${worldX.toFixed(0)} m`, x - 16, viewport.height - 18);
      }

      for (let i = 0; i <= 5; i += 1) {
        const worldY = bounds.maxY - (bounds.maxY * i) / 5;
        const y = geometry.offsetY - (worldY * geometry.scale);
        ctx.beginPath();
        ctx.moveTo(geometry.offsetX, y);
        ctx.lineTo(geometry.offsetX + geometry.usedWidth, y);
        ctx.stroke();
        ctx.fillText(`${worldY.toFixed(0)} m`, 12, y + 4);
      }

      ctx.strokeStyle = "rgba(31,31,26,0.24)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(geometry.offsetX, geometry.offsetY);
      ctx.lineTo(geometry.offsetX + geometry.usedWidth, geometry.offsetY);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(geometry.offsetX, geometry.offsetY);
      ctx.lineTo(geometry.offsetX, geometry.offsetY - geometry.usedHeight);
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

    function drawLaunchAngle(bounds) {
      const origin = toCanvas(0, 0, bounds);
      const angleRad = state.params.angle * Math.PI / 180;
      const radius = 34;

      ctx.strokeStyle = "rgba(31,31,26,0.6)";
      ctx.lineWidth = 1.5;

      ctx.beginPath();
      ctx.moveTo(origin.x, origin.y);
      ctx.lineTo(origin.x + radius + 12, origin.y);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(origin.x, origin.y);
      ctx.lineTo(origin.x + Math.cos(angleRad) * (radius + 12), origin.y - Math.sin(angleRad) * (radius + 12));
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(origin.x, origin.y, radius, 0, -angleRad, true);
      ctx.stroke();

      ctx.fillStyle = "rgba(31,31,26,0.86)";
      const labelRadius = radius + 18;
      const labelAngle = angleRad / 2;
      ctx.fillText(
        `${state.params.angle.toFixed(1)}°`,
        origin.x + Math.cos(labelAngle) * labelRadius - 8,
        origin.y - Math.sin(labelAngle) * labelRadius - 4
      );
    }

    function drawScene(progress) {
      const bounds = worldBounds();
      drawGrid(bounds);

      drawPath(state.ideal.points, getComputedStyle(document.documentElement).getPropertyValue("--ideal").trim(), bounds, progress);
      drawMarker(state.ideal.metrics.peak, bounds, getComputedStyle(document.documentElement).getPropertyValue("--compare").trim(), "Ideal peak");
      drawMarker({ x: state.ideal.metrics.range, y: 0 }, bounds, getComputedStyle(document.documentElement).getPropertyValue("--ideal").trim(), "Ideal impact");

      drawPath(state.drag.points, getComputedStyle(document.documentElement).getPropertyValue("--drag").trim(), bounds, progress);
      drawMarker(state.drag.metrics.peak, bounds, getComputedStyle(document.documentElement).getPropertyValue("--compare").trim(), "Drag peak");
      drawMarker({ x: state.drag.metrics.range, y: 0 }, bounds, getComputedStyle(document.documentElement).getPropertyValue("--drag").trim(), "Drag impact");

      const origin = toCanvas(0, 0, bounds);
      drawLaunchAngle(bounds);
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
      clearGunMode();
      syncControls(defaults);
      recompute();
    });
    toggleControlsBtn.addEventListener("click", () => {
      setControlsCollapsed(!state.controlsCollapsed);
    });
    document.querySelectorAll("[data-preset]").forEach((button) => {
      button.addEventListener("click", () => {
        clearGunMode();
        syncControls(presets[button.dataset.preset]);
        launch();
      });
    });
    window.addEventListener("resize", recompute);

    renderGunLibrary();
    hideGunHover();
    setControlsCollapsed(false);
    syncControls(defaults);
    applyGunMode();
    recompute();
    launch();
  </script>
</body>
</html>
"""


class SimulatorHandler(BaseHTTPRequestHandler):
    def _send_asset(self) -> bool:
        if not self.path.startswith("/assets/"):
            return False

        relative = self.path.removeprefix("/assets/")
        asset_path = (ASSETS_DIR / relative).resolve()
        if not str(asset_path).startswith(str(ASSETS_DIR.resolve())) or not asset_path.is_file():
            self.send_error(404, "Not Found")
            return True

        content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
        content = asset_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)
        return True

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
        if self._send_asset():
            return
        self._send_index_headers()

    def do_GET(self) -> None:
        if self._send_asset():
            return
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
