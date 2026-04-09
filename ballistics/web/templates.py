from __future__ import annotations

import json

from ballistics.presets import HISTORICAL_PLOT_REFERENCE_PARAMS, REFERENCE_PRESETS


HTML_TEMPLATE = """<!DOCTYPE html>
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
      grid-template-columns: minmax(260px, 1.05fr) minmax(0, 2fr);
      align-items: end;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(1.4rem, 2.6vw, 2.4rem);
      line-height: 0.98;
      letter-spacing: -0.05em;
    }

    .hero-title {
      display: flex;
      align-items: center;
      gap: clamp(8px, 0.8vw, 10px);
      flex-wrap: nowrap;
    }

    .help-trigger {
      min-width: 34px;
      min-height: 34px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: var(--hero-stat-pad-y) var(--hero-stat-pad-x);
      border-radius: var(--hero-stat-radius);
      border: 1px solid rgba(255,255,255,0.5);
      background: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(255,255,255,0.4));
    }

    .help-glyph {
      display: block;
      color: var(--accent);
      font-size: 2.45rem;
      font-weight: 950;
      line-height: 0.78;
      transform: translateY(-1px) scale(1.08);
      transform-origin: center;
    }

    .help-trigger:hover {
      border-color: rgba(182, 70, 42, 0.18);
      background: linear-gradient(180deg, #c95236, #a73c23);
    }

    .help-trigger:hover .help-glyph {
      color: #fff7f0;
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
      grid-template-columns: repeat(9, minmax(0, 1fr));
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

    .scale-stat {
      display: grid;
      gap: 6px;
    }

    .scale-toggle {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }

    .scale-toggle button {
      padding: 5px 9px;
      font-size: 0.74rem;
      background: rgba(255,255,255,0.75);
      color: var(--ink);
      border: 1px solid var(--border);
    }

    .scale-toggle button.active {
      background: var(--accent);
      color: #fff;
      border-color: transparent;
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
      align-items: start;
    }

    label {
      display: grid;
      gap: clamp(4px, 0.45vw, 5px);
      font-size: 0.82rem;
      font-weight: 700;
      align-content: start;
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
      touch-action: pan-x;
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

    .material-presets {
      display: flex;
      flex-wrap: wrap;
      gap: clamp(4px, 0.45vw, 6px);
      margin-top: 4px;
    }

    .calc-status {
      position: absolute;
      left: 50%;
      top: 54%;
      transform: translate(-50%, -50%);
      z-index: 3;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.94);
      color: var(--ink);
      font-size: 0.8rem;
      font-weight: 700;
      box-shadow: 0 12px 28px rgba(31,31,26,0.18);
      opacity: 0;
      visibility: hidden;
      transition: opacity 120ms ease, visibility 120ms ease;
      pointer-events: none;
    }

    .calc-status.visible {
      opacity: 1;
      visibility: visible;
    }

    .calc-status::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: rgba(31,31,26,0.3);
      transition: background 120ms ease;
    }

    .calc-status.busy::before {
      background: var(--accent);
      box-shadow: 0 0 0 5px rgba(182, 70, 42, 0.12);
    }

    .calc-status.ready::before {
      background: #2d7a46;
    }

    .calc-status.blocked::before {
      background: #8c6b1f;
    }

    .calc-status.error::before {
      background: #9c2f1f;
    }

    .material-chip {
      padding: 4px 7px;
      font-size: 0.72rem;
      line-height: 1;
    }

    .shape-toggle {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: clamp(6px, 0.7vw, 8px);
      margin-top: 4px;
    }

    .shape-card {
      border-radius: 14px;
      padding: 8px 6px 7px;
      background: rgba(255,255,255,0.78);
      color: var(--ink);
      border: 1px solid var(--border);
      display: grid;
      justify-items: center;
      gap: 6px;
    }

    .shape-card.active {
      background: rgba(182, 70, 42, 0.12);
      border-color: rgba(182, 70, 42, 0.45);
      box-shadow: inset 0 0 0 1px rgba(182, 70, 42, 0.18);
    }

    .shape-icon {
      width: 100%;
      height: 36px;
      display: block;
    }

    .shape-card span {
      font-size: 0.72rem;
      line-height: 1;
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
      display: block;
      color: var(--text);
    }

    .gun-copy h3,
    .gun-hover h3 {
      margin: 0;
      font-size: 1.05rem;
    }

    .gun-specs {
      display: block;
      margin-top: clamp(5px, 0.55vw, 6px);
      color: var(--muted);
      font-size: 0.92rem;
    }

    .gun-specs span,
    .gun-copy .muted,
    .gun-copy p {
      display: block;
      margin-top: clamp(5px, 0.55vw, 6px);
    }

    .gun-hover {
      position: absolute;
      top: clamp(-120px, -10vh, -56px);
      left: calc(100% + var(--overlay-gap));
      width: min(var(--gun-hover-width), 42vw);
      padding: var(--gun-hover-pad);
      display: grid;
      gap: var(--overlay-gap);
      background: rgba(255, 248, 236, 0.96);
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
      z-index: 5;
    }

    .gun-hover-body {
      display: block;
    }

    .gun-hover-media {
      width: 100%;
      aspect-ratio: 4 / 3;
      overflow: hidden;
      margin-bottom: var(--overlay-gap);
    }

    .gun-hover.hidden {
      display: none;
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

    .bootstrap-gate {
      position: fixed;
      inset: 0;
      z-index: 20;
      display: grid;
      place-items: center;
      padding: 20px;
      background: rgba(31, 31, 26, 0.46);
      backdrop-filter: blur(6px);
    }

    .bootstrap-gate.hidden {
      display: none;
    }

    .bootstrap-card {
      width: min(520px, 100%);
      padding: 24px;
      border-radius: 22px;
      background: rgba(255, 248, 236, 0.98);
      border: 1px solid var(--border);
      box-shadow: 0 24px 70px rgba(0, 0, 0, 0.24);
      display: grid;
      gap: 14px;
    }

    .bootstrap-card h2 {
      margin: 0;
      font-size: 1.2rem;
    }

    .bootstrap-form {
      display: grid;
      gap: 10px;
    }

    .bootstrap-error {
      min-height: 1.2em;
      color: var(--accent);
      font-size: 0.88rem;
      font-weight: 700;
    }

    .guide-overlay {
      position: fixed;
      inset: 0;
      z-index: 25;
      display: grid;
      place-items: center;
      padding: 20px;
      background: rgba(31, 31, 26, 0.42);
      backdrop-filter: blur(6px);
    }

    .guide-overlay.hidden {
      display: none;
    }

    .guide-card {
      width: min(760px, 100%);
      max-height: min(78vh, 760px);
      overflow: auto;
      padding: clamp(18px, 1.8vw, 24px);
      border-radius: 22px;
      background: rgba(255, 248, 236, 0.98);
      border: 1px solid var(--border);
      box-shadow: 0 24px 70px rgba(0, 0, 0, 0.24);
      display: grid;
      gap: 14px;
    }

    .guide-head {
      display: flex;
      justify-content: space-between;
      align-items: start;
      gap: 12px;
    }

    .guide-head h2 {
      margin: 0;
      font-size: clamp(1.2rem, 2vw, 1.5rem);
      letter-spacing: -0.03em;
    }

    .guide-close {
      min-width: 34px;
      min-height: 34px;
      padding: 0;
      border-radius: 999px;
      background: rgba(255,255,255,0.82);
      color: var(--ink);
      border: 1px solid var(--border);
      font-size: 1.05rem;
      line-height: 1;
    }

    .guide-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: clamp(10px, 1vw, 14px);
    }

    .guide-section {
      background: rgba(255, 255, 255, 0.58);
      border: 1px solid rgba(31, 31, 26, 0.08);
      border-radius: 18px;
      padding: 14px;
      display: grid;
      gap: 8px;
    }

    .guide-section h3 {
      margin: 0;
      font-size: 0.95rem;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }

    .guide-section p,
    .guide-section li {
      margin: 0;
      color: var(--muted);
      font-size: 0.93rem;
      line-height: 1.45;
    }

    .guide-section ul {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 7px;
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

      .guide-grid {
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

      .hero h1 {
        font-size: 1.8rem;
      }

      .stat {
        font-size: 0.74rem;
      }

      .stat strong {
        font-size: 0.8rem;
      }

      .canvas-wrap {
        min-height: 0;
        height: auto;
        padding-top: 210px;
      }

      canvas {
        min-height: 300px;
        height: 300px;
      }

      .gun-library {
        flex-direction: row;
        overflow-x: auto;
        overflow-y: hidden;
        scroll-snap-type: x mandatory;
        gap: 10px;
        padding-bottom: 6px;
        padding-right: 0;
      }

      .gun-card {
        min-height: 150px;
        flex: 0 0 180px;
      }

      .gun-hover {
        position: static;
        width: 100%;
      }

      .gun-hover-body {
        display: block;
      }

      .gun-hover-media {
        width: 100%;
        aspect-ratio: 4 / 3;
      }

      .control-pop {
        top: 10px;
        left: 10px;
        right: 10px;
        width: auto;
        padding: 10px;
        max-height: 190px;
      }

      .control-panel-head h3 {
        font-size: 0.8rem;
      }

      .control-scroll {
        gap: 10px;
      }

      .actions {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .material-presets {
        gap: 8px;
      }

      .material-chip {
        min-width: 34px;
        min-height: 34px;
        padding: 0;
      }

      .legend {
        left: 10px;
        right: 10px;
        top: 220px;
        font-size: 0.72rem;
        gap: 8px;
        padding: 6px 0;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero card">
      <div>
        <p class="muted">Physics Education Sandbox</p>
        <div class="hero-title">
          <h1>Interactive Ballistics Simulator</h1>
        </div>
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
          Drag V
          <strong id="hero-drag-speed">55.0 m/s</strong>
        </div>
        <div class="stat">
          Ideal T
          <strong id="hero-ideal-time">0.00 s</strong>
        </div>
        <div class="stat">
          Drag T
          <strong id="hero-drag-time">0.00 s</strong>
        </div>
        <div class="stat">
          Re end
          <strong id="hero-impact-reynolds">0</strong>
        </div>
        <div class="stat">
          Preset
          <strong id="hero-mode">Manual setup</strong>
        </div>
        <div class="stat scale-stat">
          Scale
          <div class="scale-toggle">
            <button type="button" class="active" id="scaleStableBtn">Stable</button>
            <button type="button" id="scaleFitBtn">Fit shot</button>
          </div>
        </div>
        <button type="button" class="stat help-trigger" id="guideBtn" aria-haspopup="dialog" aria-controls="guideOverlay" aria-label="Open quick guide"><span class="help-glyph">?</span></button>
      </div>
    </section>

    <div class="guide-overlay hidden" id="guideOverlay" role="dialog" aria-modal="true" aria-labelledby="guideTitle">
      <div class="guide-card">
        <div class="guide-head">
          <div>
            <h2 id="guideTitle">Quick Guide</h2>
            <p class="muted">What this simulator does, how to use it, and what the current physics models mean.</p>
          </div>
          <button type="button" class="guide-close" id="guideCloseBtn" aria-label="Close quick guide">×</button>
        </div>
        <div class="guide-grid">
          <section class="guide-section">
            <h3>Purpose</h3>
            <p>The goal of this project is to demonstrate how real-world physical factors affect ballistic modeling results.</p>
            <p>Use the controls to change launch angle, muzzle velocity, projectile diameter, material density, air temperature, air pressure, and integration time step.</p>
            <p>The simulator goes beyond vacuum-based equations and includes drag coefficient dependence on Reynolds number, compressibility effects via Mach number, and atmospheric conditions such as temperature and pressure.</p>
            <p>It highlights how environmental variables can significantly change projectile trajectory, even under otherwise identical initial conditions.</p>
          </section>
          <section class="guide-section">
            <h3>Quick Start</h3>
            <ul>
              <li>Start by choosing a historic launcher on the left or stay in manual setup if you want to build a shot from scratch.</li>
              <li>Watch the graph update and compare the ideal vacuum curve against the drag curve for the same launch conditions.</li>
              <li>Use the indicators under the graph to compare range, maximum height, time step, and the range lost to drag.</li>
              <li>Try changing only one environmental parameter at a time, such as air pressure or temperature, to see how strongly the trajectory responds.</li>
              <li>As a simple experiment, try to find the launch angle that gives the longest drag-limited range in a real atmosphere, then compare it with the ideal vacuum case.</li>
            </ul>
          </section>
          <section class="guide-section">
            <h3>Round Shot Model</h3>
            <p>Sphere projectiles use a Reynolds-based round-shot drag law with a Mach correction. Use this for cannon balls, stones, and other near-spherical shot.</p>
          </section>
          <section class="guide-section">
            <h3>Shell Model</h3>
            <p>Shell projectiles use a G7 ballistic-coefficient model with density-scaled drag. It does not use the round-shot sphere `Cd(Re, Ma)` law as the primary shell drag model.</p>
          </section>
        </div>
      </div>
    </div>

    <aside class="guns card">
      <div class="section-stack">
        <h2>Historic Launcher Library</h2>
        <div class="lock-note" id="lockNote">
          select a real launcher
        </div>
        <div class="gun-zone">
          <div class="gun-library" id="gunLibrary"></div>
          <div class="gun-hover hidden" id="gunHover">
            <div class="gun-hover-body">
              <div class="gun-copy">
                <div class="gun-hover-media">
                  <img id="gunHoverImage" alt="" loading="lazy">
                </div>
                <h3 id="gunHoverTitle">Historic launcher</h3>
                <div class="muted" id="gunHoverSubtitle"></div>
                <div class="gun-specs" id="gunHoverSpecs"></div>
                <div class="source-list" id="gunHoverSources"></div>
              </div>
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
              <input id="speed" type="range" min="5" max="600" step="1" value="55">
            </label>
            <label>
              <span class="control-header"><span>Air pressure</span><span class="value" data-out="pressure">1.00 atm</span></span>
              <input id="pressure" type="range" min="0.001" max="2.0" step="0.001" value="1">
            </label>
            <label>
              <span class="control-header"><span>Air temperature</span><span class="value" data-out="temperature">15.0 °C</span></span>
              <input id="temperature" type="range" min="-30" max="45" step="1" value="15">
            </label>
            <label>
              <span class="control-header"><span>Material density</span><span class="value" data-out="materialDensity">1324 kg/m³</span></span>
              <input id="materialDensity" type="range" min="50" max="19500" step="10" value="1324">
              <div class="material-presets">
                <button class="secondary material-chip" type="button" data-density="2600" title="Stone">S</button>
                <button class="secondary material-chip" type="button" data-density="7870" title="Iron">I</button>
                <button class="secondary material-chip" type="button" data-density="8800" title="Bronze">B</button>
                <button class="secondary material-chip" type="button" data-density="19050" title="Uranium">U</button>
              </div>
            </label>
            <label>
              <span class="control-header"><span>Projectile diameter</span><span class="value" data-out="diameter">0.113 m</span></span>
              <input id="diameter" type="range" min="0.01" max="0.30" step="0.001" value="0.113">
            </label>
            <label>
              <div class="shape-toggle">
                <button type="button" class="shape-card active" id="shapeSphereBtn" aria-label="Round shot">
                  <svg class="shape-icon" viewBox="0 0 72 36" aria-hidden="true">
                    <circle cx="36" cy="18" r="11" fill="rgba(31,31,26,0.78)"/>
                    <ellipse cx="31" cy="14" rx="4.2" ry="2.8" fill="rgba(255,255,255,0.28)"/>
                  </svg>
                  <span>Round shot</span>
                </button>
                <button type="button" class="shape-card" id="shapeShellBtn" aria-label="Shell">
                  <svg class="shape-icon" viewBox="0 0 72 36" aria-hidden="true">
                    <path d="M18 25 L27 13 Q36 6 45 13 L54 25 Q36 30 18 25 Z" fill="rgba(31,31,26,0.78)"/>
                    <path d="M28 12 L36 8 L44 12" fill="none" stroke="rgba(255,255,255,0.28)" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  <span>Shell</span>
                </button>
              </div>
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
        </div>
        </div>
        <div class="legend">
          <span><i style="background: var(--ideal)"></i> Ideal analytical trajectory</span>
          <span><i style="background: var(--drag)"></i> Drag simulation trajectory</span>
          <span><i style="background: var(--compare)"></i> Active tracer / peak markers</span>
        </div>
        <div class="calc-status" id="calcStatus" aria-live="polite">Recalculating trajectory...</div>
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
        <span class="muted">The drag correlations are clamped to a minimum of 0.001 atm, so treat that as the lowest supported pressure.</span>
      </div>
      <div class="note">
        <strong>Historical preset caveat</strong>
        <span class="muted">Gun presets use documented bore, shot mass, and listed range or muzzle velocity. The simulator derives projectile mass from diameter and material density, while drag is derived from temperature, pressure, projectile diameter, and Reynolds number.</span>
      </div>
    </aside>
  </main>
  <div class="bootstrap-gate hidden" id="bootstrapGate">
    <div class="bootstrap-card">
      <p class="muted">Verification step</p>
      <h2>Answer One Physics Question</h2>
      <div class="muted" id="bootstrapPrompt"></div>
      <div class="bootstrap-form">
        <input id="bootstrapAnswer" type="text" inputmode="decimal" autocomplete="off" placeholder="Enter your answer">
        <button type="button" class="primary" id="bootstrapSubmitBtn">Unlock simulator</button>
        <div class="bootstrap-error" id="bootstrapError"></div>
      </div>
    </div>
  </div>
  <script>
    const INITIAL_CSRF_TOKEN = "__CSRF_TOKEN__";
    const BOOTSTRAP_CHALLENGE = __BOOTSTRAP_CHALLENGE__;

    function sphereVolumeFromDiameter(diameter) {
      if (diameter <= 0) {
        return 0;
      }
      return Math.PI * diameter ** 3 / 6;
    }

    function projectileVolumeFromDiameter(diameter, volumeFactor = 1) {
      if (volumeFactor <= 0) {
        return 0;
      }
      return sphereVolumeFromDiameter(diameter) * volumeFactor;
    }

    function materialDensityFromMassAndDiameter(mass, diameter, volumeFactor = 1) {
      const volume = projectileVolumeFromDiameter(diameter, volumeFactor);
      if (volume <= 0) {
        return 0;
      }
      return mass / volume;
    }

    function massFromMaterialDensity(materialDensity, diameter, volumeFactor = 1) {
      if (materialDensity <= 0) {
        return 0;
      }
      return materialDensity * projectileVolumeFromDiameter(diameter, volumeFactor);
    }

    const defaults = {
      angle: 12,
      speed: 439,
      materialDensity: materialDensityFromMassAndDiameter(5.44, 0.117),
      temperature: 15,
      pressure: 1,
      diameter: 0.117,
      dt: 0.012,
      projectileShape: "sphere",
      sphericity: 1,
      volumeFactor: 1,
      dragModel: "g7",
      ballisticCoefficient: 0
    };
    const MIN_PRESSURE = 0.001;

    const presets = __REFERENCE_PRESETS_JSON__;
    const historicalGunParams = __HISTORICAL_GUN_PARAMS_JSON__;

    const formatters = {
      angle: (v) => `${Number(v).toFixed(1)}°`,
      speed: (v) => `${Number(v).toFixed(1)} m/s`,
      materialDensity: (v) => `${Number(v).toFixed(0)} kg/m³`,
      temperature: (v) => `${Number(v).toFixed(1)} °C`,
      pressure: (v) => `${Number(v) < 0.01 ? Number(v).toFixed(3) : Number(v).toFixed(2)} atm`,
      diameter: (v) => `${Number(v).toFixed(3)} m`,
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
    const calcStatusEl = document.getElementById("calcStatus");
    const gunLibraryEl = document.getElementById("gunLibrary");
    const lockNoteEl = document.getElementById("lockNote");
    const gunHover = document.getElementById("gunHover");
    const gunHoverTitle = document.getElementById("gunHoverTitle");
    const gunHoverSubtitle = document.getElementById("gunHoverSubtitle");
    const gunHoverImage = document.getElementById("gunHoverImage");
    const gunHoverSpecs = document.getElementById("gunHoverSpecs");
    const gunHoverSources = document.getElementById("gunHoverSources");
    const guideBtn = document.getElementById("guideBtn");
    const guideOverlay = document.getElementById("guideOverlay");
    const guideCloseBtn = document.getElementById("guideCloseBtn");
    const bootstrapGate = document.getElementById("bootstrapGate");
    const bootstrapPrompt = document.getElementById("bootstrapPrompt");
    const bootstrapAnswer = document.getElementById("bootstrapAnswer");
    const bootstrapSubmitBtn = document.getElementById("bootstrapSubmitBtn");
    const bootstrapError = document.getElementById("bootstrapError");

    const controls = {
      angle: document.getElementById("angle"),
      speed: document.getElementById("speed"),
      materialDensity: document.getElementById("materialDensity"),
      temperature: document.getElementById("temperature"),
      pressure: document.getElementById("pressure"),
      diameter: document.getElementById("diameter"),
      dt: document.getElementById("dt")
    };
    const shapeSphereBtn = document.getElementById("shapeSphereBtn");
    const shapeShellBtn = document.getElementById("shapeShellBtn");
    const defaultMaterialDensityMax = Number(controls.materialDensity.max);
    const CUSTOM_SHELL_SPHERICITY = 0.68;
    const CUSTOM_SHELL_VOLUME_FACTOR = 2.2;
    const CUSTOM_SHELL_DRAG_MODEL = "g7";
    const CUSTOM_SHELL_BALLISTIC_COEFFICIENT = 0.22;
    const historicalGuns = {
      ballista: {
        name: "Ballista",
        subtitle: "Ancient Mediterranean to medieval period",
        image: "/assets/guns/roman-ballista-alesia.jpg",
        imageAlt: "Roman ballista reproduction displayed at Alesia",
        imagePosition: "center center",
        diameterLabel: "50 mm bolt body",
        projectile: "0.85 kg bolt",
        muzzleVelocity: "Modeled 70 m/s release",
        range: "Direct-fire anti-personnel / anti-material shot",
        service: "Ancient and medieval siege warfare",
        note: "The ballista preset uses the simulator's G7 ballistic-coefficient shell path to approximate a large bolt rather than a stone sphere. It remains a point-mass flight approximation after release.",
        params: historicalGunParams.ballista,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Ballista" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Reproduction_of_Roman_Ballista_-_Al%C3%A9sia_2015.jpg" }
        ]
      },
      mangonel: {
        name: "Mangonel / traction catapult",
        subtitle: "Late antiquity to medieval period",
        image: "/assets/guns/mauvezin-mangonel.jpg",
        imageAlt: "Medieval catapult displayed inside the courtyard of Mauvezin Castle",
        imagePosition: "center center",
        diameterLabel: "180 mm stone",
        projectile: "12 kg stone shot",
        muzzleVelocity: "Modeled 42 m/s release",
        range: "Short-range bombardment",
        service: "Late antique and medieval siege warfare",
        note: "This preset represents a lighter torsion or traction-style engine. Its lower release speed and heavier launch angle make it useful for comparing pre-gunpowder trajectories against cannons.",
        params: historicalGunParams.mangonel,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Mangonel" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:The_medieval_catapult,_inside_the_courtyard_of_Mauvezin_Castle.jpg" }
        ]
      },
      trebuchet: {
        name: "Counterweight trebuchet",
        subtitle: "Mediterranean / Europe, 12th to 15th century",
        image: "/assets/guns/warwick-castle-trebuchet.jpg",
        imageAlt: "Large counterweight trebuchet at Warwick Castle",
        imagePosition: "center center",
        diameterLabel: "280 mm stone",
        projectile: "30 kg stone shot",
        muzzleVelocity: "Modeled 55 m/s release",
        range: "Heavy siege bombardment",
        service: "Medieval siege warfare",
        note: "This preset approximates a large counterweight trebuchet with a heavy stone release. The simulator starts at projectile release rather than modeling sling and arm dynamics.",
        params: historicalGunParams.trebuchet,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Trebuchet" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Warwick_Castle_trebuchet.jpg" }
        ]
      },
      saker: {
        name: "Saker",
        subtitle: "England, early 16th century",
        image: "/assets/guns/english-saker-fort-nelson.jpg",
        imageAlt: "English saker at Fort Nelson",
        imagePosition: "center center",
        diameterLabel: "83 mm",
        projectile: "5.25 lb shot (2.38 kg)",
        muzzleVelocity: "Estimated 164 m/s",
        range: "2,743 m maximum range",
        service: "Tudor and Stuart field artillery",
        note: "The simulator launch speed is inferred from the reported maximum range. Real service loads varied substantially across foundries and periods.",
        params: historicalGunParams.saker,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Saker" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:English_Saker,_Used_by_Chinese_and_Vietnamese,_Fort_Nelson,_Hampshire.jpg" }
        ]
      },
      basilisk: {
        name: "Queen Elizabeth's Pocket Pistol",
        subtitle: "Holy Roman Empire / England, 1544",
        image: "/assets/guns/queen-elizabeths-pocket-pistol.jpg",
        imageAlt: "Queen Elizabeth's Pocket Pistol at Dover Castle",
        imagePosition: "center center",
        diameterLabel: "121 mm",
        projectile: "10 lb shot (4.54 kg)",
        muzzleVelocity: "Estimated 134 m/s",
        range: "1,829 m test range",
        service: "Tudor coastal artillery",
        note: "This giant basilisk survives at Dover Castle. The simulator launch speed is inferred from the reported shot distance rather than a documented muzzle-velocity figure.",
        params: historicalGunParams.basilisk,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Queen_Elizabeth%27s_Pocket_Pistol" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Queen_Elizabeth%27s_Pocket_Pistol.JPG" }
        ]
      },
      culverin: {
        name: "Culverin extraordinary",
        subtitle: "France / England, 16th century",
        image: "/assets/guns/korean-culverin.jpg",
        imageAlt: "Korean culverin",
        imagePosition: "center center",
        diameterLabel: "140 mm",
        projectile: "20 lb shot (9.07 kg)",
        muzzleVelocity: "408 m/s",
        range: "Over 450 m at low elevation",
        service: "Renaissance field and siege artillery",
        note: "This preset follows the extraordinary culverin class, matching the reported modern-replica velocity with a heavier 20-pound shot rather than the lighter ordinary culverin ball.",
        params: historicalGunParams.culverin,
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
        diameterLabel: "102 mm",
        projectile: "8 lb shot (3.63 kg)",
        muzzleVelocity: "Modeled 145 m/s",
        range: "549 m effective range",
        service: "Naval and field artillery",
        note: "The article provides shot class and effective range but not muzzle velocity. The simulator uses a conservative modeled launch speed consistent with a lighter long gun sitting between a saker and a culverin.",
        params: historicalGunParams.demiCulverin,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Demi-culverin" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Demi_Culverin,_Mary_Rose_-_55130506883.jpg" }
        ]
      },
      falconet: {
        name: "Falconet",
        subtitle: "Europe, 16th to 17th century",
        image: "/assets/guns/falconet-wrought-iron-17th-century.jpg",
        imageAlt: "Wrought-iron falconet from the 17th century",
        imagePosition: "center center",
        diameterLabel: "51 mm",
        projectile: "1 lb shot (0.45 kg)",
        muzzleVelocity: "Estimated 122 m/s",
        range: "1,524 m maximum range",
        service: "Light field and fortress artillery",
        note: "This light piece is modeled from its reported maximum range rather than a preserved firing table, so the simulator value is an educational approximation.",
        params: historicalGunParams.falconet,
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
        diameterLabel: "159 mm",
        projectile: "32 lb shot (14.5 kg)",
        muzzleVelocity: "Modeled 95 m/s",
        range: "488 m effective range",
        service: "Naval broadside artillery",
        note: "The article gives shot class and effective range rather than muzzle velocity. The simulator uses a conservative modeled launch speed and a representative heavy naval gun image.",
        params: historicalGunParams.demiCannon,
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
        diameterLabel: "121 mm",
        projectile: "12 French livres round shot (~5.88 kg)",
        muzzleVelocity: "Estimated 133 m/s",
        range: "1,800 m max range",
        service: "Revolutionary and Napoleonic field artillery",
        note: "The source used here gives range but not muzzle velocity. The simulator launch speed is inferred from the reported 1,800 m maximum range under an idealized 45° estimate.",
        params: historicalGunParams.gribeauval,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Canon_de_12_Gribeauval" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Gribeauval_cannon_de_12_An_2_de_la_Republique.jpg" }
        ]
      },
      m1841SixPounder: {
        name: "M1841 6-pounder gun",
        subtitle: "United States, 1841",
        image: "/assets/guns/english-saker-fort-nelson.jpg",
        imageAlt: "Representative light field gun used as an image stand-in for the M1841 6-pounder",
        imagePosition: "center center",
        diameterLabel: "93.2 mm",
        projectile: "6 lb round shot (2.72 kg)",
        muzzleVelocity: "1,450 ft/s (442 m/s)",
        range: "1,451 yd at 5°",
        service: "Mexican-American War, early American Civil War field artillery",
        note: "This preset follows the historical comparison setup used in the validation snapshot: a 6-pound round shot at 5 degrees elevation and 1,450 ft/s. The repository does not include a dedicated M1841 image, so this entry uses a representative light field gun image.",
        params: historicalGunParams.m1841SixPounder,
        sources: [
          { label: "Specs", url: "https://antietam.aotw.org/weapons.php?weapon_id=12" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:English_Saker_at_Fort_Nelson.jpg" }
        ]
      },
      paixhans: {
        name: "Paixhans gun",
        subtitle: "France, 1823",
        image: "/assets/guns/paixhans-shell-gun.jpg",
        imageAlt: "Paixhans shell gun on display at Le Port, Reunion",
        imagePosition: "center center",
        diameterLabel: "220 mm",
        projectile: "30 kg shell",
        muzzleVelocity: "400 m/s",
        range: "Shell-gun naval artillery",
        service: "Explosive-shell naval warfare",
        note: "The Paixhans gun was designed for explosive shells fired on a flatter trajectory than older shell artillery. This preset uses the simulator's G7 ballistic-coefficient shell model with an effective shell-density approximation.",
        params: historicalGunParams.paixhans,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/Paixhans_gun" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Canon-Obusier-80lbs-22cm-Paixhans-No.4621.jpg" }
        ]
      },
      armstrong: {
        name: "RBL 12-pounder 8 cwt Armstrong gun",
        subtitle: "United Kingdom, 1859",
        image: "/assets/guns/awm-armstrong-gun-1.jpg",
        imageAlt: "RBL 12-pounder Armstrong gun at the Australian War Memorial",
        imagePosition: "center center",
        diameterLabel: "76.2 mm",
        projectile: "11 lb 4 oz common shell (5.10 kg)",
        muzzleVelocity: "378 m/s",
        range: "3,109 m",
        service: "Second Opium War and New Zealand Wars field artillery",
        note: "This early breech-loader used rifled ammunition. The preset uses the listed common-shell weight with the simulator's G7 ballistic-coefficient shell model.",
        params: historicalGunParams.armstrong,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/RBL_12-pounder_8_cwt_Armstrong_gun" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:AWM-Armstrong-gun-1.jpg" }
        ]
      },
      ordnance: {
        name: "3-inch Ordnance Rifle",
        subtitle: "United States, 1861",
        image: "/assets/guns/cw-arty-3in-ordnance-front.jpg",
        imageAlt: "3-inch ordnance rifle at Gettysburg",
        imagePosition: "center center",
        diameterLabel: "76 mm",
        projectile: "9.5 lb shell (4.3 kg)",
        muzzleVelocity: "370 m/s",
        range: "1,673 m at 5°",
        service: "American Civil War field artillery",
        note: "This preset represents a rifled shell rather than a smooth round shot. It uses the simulator's G7 ballistic-coefficient shell model.",
        params: historicalGunParams.ordnance,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/3-inch_ordnance_rifle" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:CW_Arty_3in_Ordnance_front.jpg" }
        ]
      },
      napoleon: {
        name: "M1857 12-pounder Napoleon",
        subtitle: "United States, 1857",
        image: "/assets/guns/gettysburg-12-pounder-napoleon.jpg",
        imageAlt: "M1857 12-pounder Napoleon at Gettysburg",
        imagePosition: "center center",
        diameterLabel: "117 mm",
        projectile: "12 lb round shot (5.44 kg)",
        muzzleVelocity: "439 m/s",
        range: "1,480 m at 5°",
        service: "American Civil War field artillery",
        note: "This is a smoothbore gun-howitzer. The preset keeps the round-shot drag model used elsewhere in the simulator.",
        params: historicalGunParams.napoleon,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/M1857_12-pounder_Napoleon" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Gettysburg,_12-pounder_Napoleon.jpg" }
        ]
      },
      parrott: {
        name: "10-pounder Parrott rifle",
        subtitle: "United States, 1861",
        image: "/assets/guns/10-pounder-parrott-rifle-chickamauga.jpg",
        imageAlt: "10-pounder Parrott rifle at Chickamauga Battlefield Visitors Center",
        imagePosition: "center center",
        diameterLabel: "74 mm",
        projectile: "9.5 lb shell (4.30 kg)",
        muzzleVelocity: "375 m/s",
        range: "1,692 m at 5°",
        service: "American Civil War field artillery",
        note: "This preset follows the documented 2.9-inch Parrott rifle figures and uses the simulator's G7 ballistic-coefficient shell model for its elongated projectile.",
        params: historicalGunParams.parrott,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/10-pounder_Parrott_rifle" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:10_Pounder_Parrott_Rifle,_Chickamauga_Battlefield_Visitors_Center.jpg" }
        ]
      },
      longGun24: {
        name: "24-pounder long gun",
        subtitle: "France / Britain / United States, 18th to 19th century",
        image: "/assets/guns/24-pounder-long-gun-isla-mancera.jpg",
        imageAlt: "24-pounder long gun on Isla Mancera, Chile",
        imagePosition: "center center",
        diameterLabel: "152.2 mm",
        projectile: "24 lb shot (10.89 kg)",
        muzzleVelocity: "Modeled 450 m/s",
        range: "Naval long-range battery class",
        service: "Age-of-Sail naval artillery",
        note: "The source identifies the gun class, caliber, and shot weight, but muzzle velocity varied by navy, barrel pattern, and powder charge. This preset uses a representative modeled launch speed for a heavy long gun rather than one universal historical firing table.",
        params: historicalGunParams.longGun24,
        sources: [
          { label: "Specs", url: "https://en.wikipedia.org/wiki/24-pounder_long_gun" },
          { label: "Image", url: "https://commons.wikimedia.org/wiki/File:Ca%C3%B1%C3%B3n_de_a_24_libras_en_Isla_Mancera,_Chile.jpg" }
        ]
      }
    };

    const state = {
      params: { ...defaults },
      ideal: null,
      drag: null,
      focusedBounds: null,
      stableBounds: null,
      csrfToken: INITIAL_CSRF_TOKEN,
      bootstrapChallenge: BOOTSTRAP_CHALLENGE,
      currentGun: "napoleon",
      presetModified: false,
      scaleMode: "stable",
      hoveredGun: null,
      hoverHideTimer: null,
      controlsCollapsed: false,
      animationStart: 0,
      animating: false,
      requestSerial: 0,
      requestController: null
    };

    function activePlotBounds() {
      if (state.scaleMode === "fit" && state.focusedBounds) {
        return state.focusedBounds;
      }
      return state.stableBounds || state.focusedBounds || { maxX: 2400, maxY: 850 };
    }

    function updateScaleButtons() {
      const stableBtn = document.getElementById("scaleStableBtn");
      const fitBtn = document.getElementById("scaleFitBtn");
      stableBtn.classList.toggle("active", state.scaleMode === "stable");
      fitBtn.classList.toggle("active", state.scaleMode === "fit");
    }

    function setScaleMode(mode) {
      state.scaleMode = mode;
      updateScaleButtons();
      redrawDisplay();
    }

    function setProjectileShape(shape, options = {}) {
      state.params.projectileShape = shape;
      if (shape === "shell") {
        state.params.sphericity = options.sphericity ?? state.params.sphericity ?? CUSTOM_SHELL_SPHERICITY;
        state.params.volumeFactor = options.volumeFactor ?? state.params.volumeFactor ?? CUSTOM_SHELL_VOLUME_FACTOR;
        state.params.dragModel = options.dragModel ?? state.params.dragModel ?? CUSTOM_SHELL_DRAG_MODEL;
        state.params.ballisticCoefficient = options.ballisticCoefficient ?? state.params.ballisticCoefficient ?? CUSTOM_SHELL_BALLISTIC_COEFFICIENT;
      } else {
        state.params.sphericity = 1;
        state.params.volumeFactor = 1;
        state.params.dragModel = CUSTOM_SHELL_DRAG_MODEL;
        state.params.ballisticCoefficient = 0;
      }
      updateShapeControls();
    }

    function updateShapeControls() {
      const isShell = state.params.projectileShape === "shell";
      shapeSphereBtn.classList.toggle("active", !isShell);
      shapeShellBtn.classList.toggle("active", isShell);
      controls.materialDensity.disabled = isShell;
      controls.diameter.disabled = isShell;
    }

    function syncMaterialDensityLimit(materialDensity) {
      const roundedMax = Math.ceil(materialDensity / 10) * 10;
      controls.materialDensity.max = String(Math.max(defaultMaterialDensityMax, roundedMax));
    }

    function setControlsCollapsed(collapsed) {
      state.controlsCollapsed = collapsed;
      controlScroll.classList.toggle("hidden", collapsed);
      toggleControlsBtn.textContent = collapsed ? "Show" : "Hide";
      toggleControlsBtn.setAttribute("aria-expanded", String(!collapsed));
    }

    function readParams() {
      return {
        ...state.params,
        angle: Number(controls.angle.value),
        speed: Number(controls.speed.value),
        materialDensity: Number(controls.materialDensity.value),
        temperature: Number(controls.temperature.value),
        pressure: clampPressure(Number(controls.pressure.value)),
        diameter: Number(controls.diameter.value),
        dt: Number(controls.dt.value)
      };
    }

    function syncControls(params) {
      if (typeof params.materialDensity === "number") {
        syncMaterialDensityLimit(params.materialDensity);
      }
      state.params = { ...state.params, ...params };
      Object.entries(params).forEach(([key, value]) => {
        const control = controls[key];
        if (!control) {
          return;
        }
        if (control.type === "checkbox") {
          control.checked = Boolean(value);
        } else {
          control.value = String(key === "pressure" ? clampPressure(Number(value)) : value);
        }
      });
      updateShapeControls();
      updateLabels();
    }

    function paramsMatch(left, right) {
      const keys = ["angle", "speed", "materialDensity", "temperature", "pressure", "diameter", "dt", "projectileShape", "sphericity", "volumeFactor", "dragModel", "ballisticCoefficient"];
      return keys.every((key) => {
        if (typeof left[key] === "string" || typeof right[key] === "string") {
          return left[key] === right[key];
        }
        return Math.abs(left[key] - right[key]) < 1e-9;
      });
    }

    function setGunMode(gunKey) {
      const gunParams = historicalGuns[gunKey].params;
      const normalizedParams = gunParams.projectileShape === "shell"
        ? gunParams
        : {
            ...gunParams,
            projectileShape: "sphere",
            sphericity: 1,
            volumeFactor: 1,
            dragModel: CUSTOM_SHELL_DRAG_MODEL,
            ballisticCoefficient: 0
          };
      state.currentGun = gunKey;
      state.presetModified = false;
      syncControls(normalizedParams);
      applyGunMode();
    }

    function clearGunMode() {
      state.currentGun = null;
      state.presetModified = false;
      applyGunMode();
    }

    function applyGunMode() {
      const inGunMode = Boolean(state.currentGun);
      lockNoteEl.innerHTML = inGunMode
        ? `<strong>${historicalGuns[state.currentGun].name}</strong>${state.presetModified ? ' <span class="muted">(customized)</span>' : ""}`
        : `select a real launcher`;
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
          scheduleHideGunHover();
        });
        card.addEventListener("click", () => {
          showGunHover(card.dataset.gun);
          setGunMode(card.dataset.gun);
          launch();
        });
      });
    }

    function showGunHover(gunKey) {
      clearTimeout(state.hoverHideTimer);
      state.hoverHideTimer = null;
      state.hoveredGun = gunKey;
      const gun = historicalGuns[gunKey];
      gunHoverTitle.textContent = gun.name;
      gunHoverSubtitle.textContent = gun.subtitle;
      gunHoverImage.src = gun.image;
      gunHoverImage.alt = gun.imageAlt;
      gunHoverImage.style.objectPosition = gun.imagePosition || "center center";
      gunHoverImage.style.transform = `scale(${gun.imageScale || 1})`;
      const densityLabel = gun.params.projectileShape === "shell" ? "Effective projectile density" : "Material density";
      const shapeLabel = gun.params.projectileShape === "shell" ? `${String((gun.params.dragModel || "g7")).toUpperCase()} BC shell` : "Round shot sphere";
      gunHoverSpecs.innerHTML = `
        <span><strong>Diameter:</strong> ${gun.diameterLabel}</span>
        <span><strong>Shape model:</strong> ${shapeLabel}</span>
        <span><strong>${densityLabel}:</strong> ${Math.round(gun.params.materialDensity)} kg/m³</span>
        ${gun.params.projectileShape === "shell" ? `<span><strong>Ballistic coefficient:</strong> ${Number(gun.params.ballisticCoefficient || 0).toFixed(2)}</span>` : ""}
        <span><strong>Projectile:</strong> ${gun.projectile}</span>
        <span><strong>Muzzle velocity:</strong> ${gun.muzzleVelocity}</span>
        <span><strong>Service:</strong> ${gun.service}</span>
      `;
      gunHoverSources.innerHTML = gun.sources.map((source) => `<a href="${source.url}" target="_blank" rel="noreferrer">${source.label}</a>`).join("");
      gunHover.classList.remove("hidden");
    }

    function hideGunHover() {
      clearTimeout(state.hoverHideTimer);
      state.hoverHideTimer = null;
      state.hoveredGun = null;
      gunHover.classList.add("hidden");
    }

    function scheduleHideGunHover() {
      clearTimeout(state.hoverHideTimer);
      state.hoverHideTimer = window.setTimeout(() => {
        hideGunHover();
      }, 160);
    }

    function updateLabels() {
      state.params = readParams();
      syncMaterialDensityLimit(state.params.materialDensity);
      if (state.currentGun) {
        state.presetModified = !paramsMatch(state.params, historicalGuns[state.currentGun].params);
        applyGunMode();
      }
      document.querySelectorAll("[data-out]").forEach((node) => {
        const key = node.dataset.out;
        node.textContent = formatters[key](state.params[key]);
      });
      document.getElementById("hero-angle").textContent = formatters.angle(state.params.angle);
      document.getElementById("hero-speed").textContent = formatters.speed(state.params.speed);
      document.getElementById("hero-mode").textContent = state.currentGun
        ? `${historicalGuns[state.currentGun].name}${state.presetModified ? " custom" : ""}`
        : "Manual setup";
    }

    function clampPressure(pressureAtm) {
      return Math.max(pressureAtm, MIN_PRESSURE);
    }

    function updateCalculationStatus(label, tone) {
      calcStatusEl.textContent = label;
      calcStatusEl.classList.remove("busy", "ready", "blocked", "error");
      calcStatusEl.classList.add(tone);
      calcStatusEl.classList.add("visible");
    }

    function hideCalculationStatus() {
      calcStatusEl.classList.remove("visible", "busy", "ready", "blocked", "error");
    }

    function openGuide() {
      guideOverlay.classList.remove("hidden");
    }

    function closeGuide() {
      guideOverlay.classList.add("hidden");
    }

    function bootstrapRequired() {
      return !state.csrfToken;
    }

    function updateBootstrapGate() {
      const challengeRequired = state.bootstrapChallenge && state.bootstrapChallenge.required !== false;
      bootstrapGate.classList.toggle("hidden", !challengeRequired || !bootstrapRequired());
      if (challengeRequired && bootstrapRequired()) {
        bootstrapPrompt.textContent = state.bootstrapChallenge.prompt;
      }
    }

    async function bootstrapSession() {
      bootstrapError.textContent = "";
      bootstrapSubmitBtn.disabled = true;
      try {
        const response = await fetch("/session/bootstrap", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            token: state.bootstrapChallenge.token,
            answer: bootstrapAnswer.value,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          bootstrapError.textContent = payload.error || "Verification failed.";
          return false;
        }
        state.csrfToken = payload.csrfToken;
        state.bootstrapChallenge = { required: false };
        bootstrapAnswer.value = "";
        updateBootstrapGate();
        return true;
      } finally {
        bootstrapSubmitBtn.disabled = false;
      }
    }

    async function recalculatePhysics() {
      if (bootstrapRequired()) {
        updateCalculationStatus("Unlock simulator to calculate", "blocked");
        updateBootstrapGate();
        return false;
      }
      const requestSerial = state.requestSerial + 1;
      state.requestSerial = requestSerial;
      if (state.requestController) {
        state.requestController.abort();
      }
      const controller = new AbortController();
      state.requestController = controller;
      updateCalculationStatus("Recalculating trajectory...", "busy");

      try {
        const response = await fetch("/api/simulate", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrfToken },
          body: JSON.stringify({ ...state.params, currentGun: state.currentGun }),
          signal: controller.signal
        });
        if (!response.ok) {
          throw new Error(`Simulation request failed with ${response.status}`);
        }
        const payload = await response.json();
        if (requestSerial !== state.requestSerial) {
          return false;
        }
        state.ideal = payload.ideal;
        state.drag = payload.drag;
        state.focusedBounds = payload.focusedBounds;
        state.stableBounds = payload.stableBounds;
        state.requestController = null;
        return true;
      } catch (error) {
        if (error.name === "AbortError") {
          return false;
        }
        updateCalculationStatus("Trajectory update failed", "error");
        throw error;
      }
    }

    function redrawDisplay() {
      if (!state.ideal || !state.drag) {
        return;
      }
      document.getElementById("hero-drag-speed").textContent = `${state.drag.metrics.finalSpeed.toFixed(1)} m/s`;
      document.getElementById("hero-ideal-time").textContent = `${state.ideal.metrics.flightTime.toFixed(2)} s`;
      document.getElementById("hero-drag-time").textContent = `${state.drag.metrics.flightTime.toFixed(2)} s`;
      document.getElementById("hero-impact-reynolds").textContent = `${state.drag.aero.impactReynolds.toFixed(0)}`;
      renderMetrics();
      drawScene(1);
      hideCalculationStatus();
    }

    async function recompute() {
      updateLabels();
      const applied = await recalculatePhysics();
      if (!applied) {
        return false;
      }
      redrawDisplay();
      return true;
    }

    function renderMetrics() {
      const rows = [];
      const dragAero = state.drag.aero;
      rows.push(metricCard("Ideal range", state.ideal.metrics.range, "m", `Time ${state.ideal.metrics.flightTime.toFixed(2)} s`));
      rows.push(metricCard("Ideal max height", state.ideal.metrics.maxHeight, "m", `Impact speed ${state.ideal.metrics.finalSpeed.toFixed(2)} m/s`));
      rows.push(metricCard("Time step", state.params.dt, "s", "Smaller steps improve stability but cost more frames."));
      rows.push(metricCard("Drag range", state.drag.metrics.range, "m", `Time ${state.drag.metrics.flightTime.toFixed(2)} s`));
      rows.push(metricCard("Drag max height", state.drag.metrics.maxHeight, "m", `Impact speed ${state.drag.metrics.finalSpeed.toFixed(2)} m/s`));
      const deltaRange = state.ideal.metrics.range - state.drag.metrics.range;
      const angleHint = dragAero.airDensity > 0 ? "Lower angles often win with drag." : "Vacuum restores the 45° symmetry.";
      rows.push(metricCard("Range loss to drag", deltaRange, "m", angleHint));
      metricsEl.innerHTML = rows.join("");
    }

    function metricCard(label, value, unit, note) {
      const suffix = unit ? ` ${unit}` : "";
      return `
        <article class="metric">
          <div class="label">${label}</div>
          <strong>${value.toFixed(2)}${suffix}</strong>
          <small>${note}</small>
        </article>
      `;
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
      const xScale = plotWidth / bounds.maxX;
      const yScale = plotHeight / bounds.maxY;
      const usedWidth = plotWidth;
      const usedHeight = plotHeight;
      const offsetX = padLeft;
      const offsetY = cssHeight - padBottom;
      return { padLeft, padRight, padTop, padBottom, plotWidth, plotHeight, xScale, yScale, offsetX, offsetY, usedWidth, usedHeight };
    }

    function toCanvas(x, y, bounds) {
      const geometry = getPlotGeometry(bounds);
      return {
        x: geometry.offsetX + (x * geometry.xScale),
        y: geometry.offsetY - (y * geometry.yScale)
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
        const x = geometry.offsetX + (worldX * geometry.xScale);
        ctx.beginPath();
        ctx.moveTo(x, geometry.padTop);
        ctx.lineTo(x, geometry.offsetY);
        ctx.stroke();
        ctx.fillText(`${worldX.toFixed(0)} m`, x - 16, viewport.height - 18);
      }

      for (let i = 0; i <= 5; i += 1) {
        const worldY = bounds.maxY - (bounds.maxY * i) / 5;
        const y = geometry.offsetY - (worldY * geometry.yScale);
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

      drawScaleReferences(bounds);
    }

    function drawScaleReferences(bounds) {
      const references = [
        {
          name: "Football field",
          x: 36,
          width: 109.7,
          height: 48.8,
          draw() {
            const bottomLeft = toCanvas(this.x, 0, bounds);
            const topRight = toCanvas(this.x + this.width, this.height, bounds);
            const widthPx = topRight.x - bottomLeft.x;
            const heightPx = bottomLeft.y - topRight.y;
            if (widthPx < 36 || heightPx < 14) {
              return false;
            }
            ctx.save();
            ctx.strokeStyle = "rgba(31,31,26,0.12)";
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.strokeRect(bottomLeft.x, topRight.y, widthPx, heightPx);
            ctx.beginPath();
            ctx.moveTo(bottomLeft.x + widthPx / 2, topRight.y);
            ctx.lineTo(bottomLeft.x + widthPx / 2, bottomLeft.y);
            ctx.stroke();
            ctx.restore();
            labelReference(this.name, bottomLeft.x, topRight.y - 6);
            return true;
          }
        },
        {
          name: "Eiffel Tower",
          x: 190,
          width: 125,
          height: 330,
          draw() {
            const baseLeft = toCanvas(this.x, 0, bounds);
            const baseRight = toCanvas(this.x + this.width, 0, bounds);
            const apex = toCanvas(this.x + (this.width / 2), this.height, bounds);
            const towerHeightPx = baseLeft.y - apex.y;
            const towerWidthPx = baseRight.x - baseLeft.x;
            if (towerHeightPx < 24) {
              return false;
            }
            const legInset = towerWidthPx * 0.18;
            const archHeight = towerHeightPx * 0.16;
            const midY = baseLeft.y - (towerHeightPx * 0.48);
            const topY = baseLeft.y - (towerHeightPx * 0.78);
            const midInset = towerWidthPx * 0.29;
            const topInset = towerWidthPx * 0.4;
            ctx.save();
            ctx.strokeStyle = "rgba(31,31,26,0.14)";
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(baseLeft.x, baseLeft.y);
            ctx.lineTo(apex.x, apex.y);
            ctx.lineTo(baseRight.x, baseRight.y);
            ctx.moveTo(baseLeft.x + legInset, baseLeft.y);
            ctx.quadraticCurveTo(apex.x, baseLeft.y - archHeight, baseRight.x - legInset, baseRight.y);
            ctx.moveTo(baseLeft.x + midInset, midY);
            ctx.lineTo(baseRight.x - midInset, midY);
            ctx.moveTo(baseLeft.x + topInset, topY);
            ctx.lineTo(baseRight.x - topInset, topY);
            ctx.stroke();
            ctx.restore();
            labelReference(this.name, apex.x - 24, apex.y - 6);
            return true;
          }
        }
      ];

      references.forEach((reference) => {
        reference.draw();
      });
    }

    function labelReference(text, x, y) {
      ctx.save();
      ctx.fillStyle = "rgba(31,31,26,0.42)";
      ctx.font = "11px Trebuchet MS";
      ctx.fillText(text, x, y);
      ctx.restore();
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

    function drawMarker(point, bounds, color) {
      const p = toCanvas(point.x, point.y, bounds);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    function drawLaunchAngle(bounds) {
      const origin = toCanvas(0, 0, bounds);
      const geometry = getPlotGeometry(bounds);
      const angleRad = state.params.angle * Math.PI / 180;
      const displayAngle = Math.atan2(Math.sin(angleRad) * geometry.yScale, Math.cos(angleRad) * geometry.xScale);
      const radius = 34;

      ctx.strokeStyle = "rgba(31,31,26,0.6)";
      ctx.lineWidth = 1.5;

      ctx.beginPath();
      ctx.moveTo(origin.x, origin.y);
      ctx.lineTo(origin.x + radius + 12, origin.y);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(origin.x, origin.y);
      ctx.lineTo(origin.x + Math.cos(displayAngle) * (radius + 12), origin.y - Math.sin(displayAngle) * (radius + 12));
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(origin.x, origin.y, radius, 0, -displayAngle, true);
      ctx.stroke();

      ctx.fillStyle = "rgba(31,31,26,0.86)";
      const labelRadius = radius + 18;
      const labelAngle = displayAngle / 2;
      ctx.fillText(
        `${state.params.angle.toFixed(1)}°`,
        origin.x + Math.cos(labelAngle) * labelRadius - 8,
        origin.y - Math.sin(labelAngle) * labelRadius - 4
      );
    }

    function drawScene(progress) {
      const bounds = activePlotBounds();
      drawGrid(bounds);

      drawPath(state.ideal.points, getComputedStyle(document.documentElement).getPropertyValue("--ideal").trim(), bounds, progress);
      drawMarker(state.ideal.metrics.peak, bounds, getComputedStyle(document.documentElement).getPropertyValue("--compare").trim());
      drawMarker({ x: state.ideal.metrics.range, y: 0 }, bounds, getComputedStyle(document.documentElement).getPropertyValue("--ideal").trim());

      drawPath(state.drag.points, getComputedStyle(document.documentElement).getPropertyValue("--drag").trim(), bounds, progress);
      drawMarker(state.drag.metrics.peak, bounds, getComputedStyle(document.documentElement).getPropertyValue("--compare").trim());
      drawMarker({ x: state.drag.metrics.range, y: 0 }, bounds, getComputedStyle(document.documentElement).getPropertyValue("--drag").trim());

      const origin = toCanvas(0, 0, bounds);
      drawLaunchAngle(bounds);
      ctx.fillStyle = "#111";
      ctx.beginPath();
      ctx.arc(origin.x, origin.y, 5, 0, Math.PI * 2);
      ctx.fill();
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

    async function launch() {
      const applied = await recompute();
      if (!applied) {
        return;
      }
      state.animating = true;
      state.animationStart = 0;
      requestAnimationFrame(animate);
    }

    Object.values(controls).forEach((control) => {
      control.addEventListener("input", recompute);
      control.addEventListener("change", recompute);
    });

    launchBtn.addEventListener("click", launch);
    bootstrapSubmitBtn.addEventListener("click", async () => {
      const unlocked = await bootstrapSession();
      if (unlocked) {
        launch();
      }
    });
    bootstrapAnswer.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        const unlocked = await bootstrapSession();
        if (unlocked) {
          launch();
        }
      }
    });
    replayBtn.addEventListener("click", () => {
      state.animating = true;
      state.animationStart = 0;
      requestAnimationFrame(animate);
    });
    resetBtn.addEventListener("click", () => {
      setGunMode("napoleon");
      recompute();
    });
    toggleControlsBtn.addEventListener("click", () => {
      setControlsCollapsed(!state.controlsCollapsed);
    });
    guideBtn.addEventListener("click", openGuide);
    guideCloseBtn.addEventListener("click", closeGuide);
    guideOverlay.addEventListener("click", (event) => {
      if (event.target === guideOverlay) {
        closeGuide();
      }
    });
    document.getElementById("scaleStableBtn").addEventListener("click", () => {
      setScaleMode("stable");
    });
    document.getElementById("scaleFitBtn").addEventListener("click", () => {
      setScaleMode("fit");
    });
    shapeSphereBtn.addEventListener("click", () => {
      setProjectileShape("sphere");
      recompute();
    });
    shapeShellBtn.addEventListener("click", () => {
      setProjectileShape("shell", {
        sphericity: state.params.projectileShape === "shell" ? state.params.sphericity : CUSTOM_SHELL_SPHERICITY,
        volumeFactor: state.params.projectileShape === "shell" ? state.params.volumeFactor : CUSTOM_SHELL_VOLUME_FACTOR,
        dragModel: state.params.projectileShape === "shell" ? state.params.dragModel : CUSTOM_SHELL_DRAG_MODEL,
        ballisticCoefficient: state.params.projectileShape === "shell" ? state.params.ballisticCoefficient : CUSTOM_SHELL_BALLISTIC_COEFFICIENT
      });
      recompute();
    });
    gunHover.addEventListener("mouseenter", () => {
      clearTimeout(state.hoverHideTimer);
      state.hoverHideTimer = null;
    });
    gunHover.addEventListener("mouseleave", () => {
      scheduleHideGunHover();
    });
    document.querySelectorAll("[data-density]").forEach((button) => {
      button.addEventListener("click", () => {
        controls.materialDensity.value = button.dataset.density;
        recompute();
      });
    });
    window.addEventListener("resize", () => {
      redrawDisplay();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !guideOverlay.classList.contains("hidden")) {
        closeGuide();
      }
    });

    renderGunLibrary();
    hideGunHover();
    setControlsCollapsed(false);
    updateScaleButtons();
    updateShapeControls();
    updateBootstrapGate();
    setGunMode("napoleon");
    if (!bootstrapRequired()) {
      launch();
    }
  </script>
</body>
</html>
"""

HTML_PAGE = (
    HTML_TEMPLATE
    .replace("__REFERENCE_PRESETS_JSON__", json.dumps(REFERENCE_PRESETS, separators=(",", ":")))
    .replace("__HISTORICAL_GUN_PARAMS_JSON__", json.dumps(HISTORICAL_PLOT_REFERENCE_PARAMS, separators=(",", ":")))
)
