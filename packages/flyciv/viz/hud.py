from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HUD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>flyciv watch</title>
<style>
  :root { --bg:#100e0c; --ink:#e6dcc8; --dim:#8a7f6a; --road:#c9b896; --wear:#c47a2c; --food:#6fbf73; --hero:#f3f0a8; --crowd:#7a6a55; --spike:#7ed0c6; --line:#2a2620; }
  * { box-sizing: border-box; }
  html, body { margin:0; height:100%; background:var(--bg); color:var(--ink); font: 13px/1.4 "IBM Plex Mono", ui-monospace, Menlo, monospace; }
  header { display:flex; justify-content:space-between; gap:16px; padding:12px 16px; border-bottom:1px solid var(--line); }
  header strong { letter-spacing:.12em; font-weight:600; }
  header .honest { color:var(--dim); max-width:52ch; }
  main { display:grid; grid-template-columns: 1fr 280px; grid-template-rows: 1fr 120px; height: calc(100% - 108px); }
  #map { grid-row:1; grid-column:1; border-right:1px solid var(--line); }
  #spikes { grid-row:1; grid-column:2; padding:12px; }
  #timeline { grid-column:1 / -1; border-top:1px solid var(--line); padding:10px 16px; }
  canvas { width:100%; height:100%; display:block; image-rendering: pixelated; }
  .row { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
  button, input[type=range] { accent-color: var(--wear); }
  button { background:#1c1916; color:var(--ink); border:1px solid #3a342c; padding:6px 10px; cursor:pointer; }
  button:hover { border-color:var(--road); }
  #stats span { margin-right:14px; color:var(--dim); }
  #stats b { color:var(--ink); font-weight:500; }
  .dot { display:inline-block; width:8px; height:8px; margin-right:4px; }
  #eventlog { color:var(--dim); min-height:1.4em; }
  h2 { font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--dim); margin:0 0 8px; }
</style>
</head>
<body>
<header>
  <div>
    <strong>FLYCIV</strong>
    <div class="honest">Not a living fly. Frozen connectome. Only adapters evolve. Roads and trainer are designed rules.</div>
  </div>
  <div id="stats"></div>
</header>
<main>
  <canvas id="map"></canvas>
  <aside id="spikes">
    <h2>Hero 0 spikes</h2>
    <canvas id="raster" width="260" height="420"></canvas>
    <div style="margin-top:8px;color:var(--dim)">
      <span class="dot" style="background:var(--hero)"></span>hero
      <span class="dot" style="background:var(--crowd)"></span>crowd
      <span class="dot" style="background:var(--road)"></span>road
      <span class="dot" style="background:var(--wear)"></span>wear
      <span class="dot" style="background:var(--food)"></span>food
    </div>
  </aside>
  <section id="timeline">
    <div class="row">
      <button id="play">pause</button>
      <input id="scrub" type="range" min="0" max="0" value="0" style="flex:1"/>
      <label>speed <input id="speed" type="range" min="1" max="12" value="4"/></label>
    </div>
    <div id="eventlog"></div>
  </section>
</main>
<script>
const DATA = __FRAMES__;
const frames = DATA.frames;
const map = document.getElementById('map');
const ctx = map.getContext('2d');
const raster = document.getElementById('raster');
const rctx = raster.getContext('2d');
const scrub = document.getElementById('scrub');
const playBtn = document.getElementById('play');
const speed = document.getElementById('speed');
const stats = document.getElementById('stats');
const eventlog = document.getElementById('eventlog');
let i = 0, playing = true, acc = 0, last = performance.now();
let spikeHist = [];
scrub.max = Math.max(0, frames.length - 1);

function resize() {
  const dpr = window.devicePixelRatio || 1;
  map.width = map.clientWidth * dpr;
  map.height = map.clientHeight * dpr;
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
window.addEventListener('resize', () => { resize(); draw(frames[i]); });
resize();

function cell(grid, y, x) {
  const row = grid[y|0];
  return row ? (row[x|0] || 0) : 0;
}

function draw(f) {
  if (!f) return;
  const W = map.clientWidth, H = map.clientHeight;
  const n = f.res;
  const s = Math.floor(Math.min(W, H) / n);
  const ox = Math.floor((W - s*n)/2), oy = Math.floor((H - s*n)/2);
  ctx.fillStyle = '#161310';
  ctx.fillRect(0,0,W,H);
  for (let y=0;y<n;y++) for (let x=0;x<n;x++) {
    const wear = cell(f.wear,y,x);
    const road = cell(f.roads,y,x);
    const trail = cell(f.trails,y,x);
    const food = cell(f.food,y,x);
    const brood = cell(f.brood,y,x);
    const store = cell(f.store,y,x);
    let col = null;
    if (road) col = '#c9b896';
    else if (trail) col = '#a36b2a';
    else if (wear > 0) {
      const t = Math.min(1, wear/12);
      col = `rgb(${40+t*160},${28+t*70},${16})`;
    }
    if (col) { ctx.fillStyle = col; ctx.fillRect(ox+x*s, oy+y*s, s, s); }
    if (food > 0) { ctx.fillStyle = '#6fbf73'; ctx.fillRect(ox+x*s+s*0.25, oy+y*s+s*0.25, Math.max(1,s*0.5), Math.max(1,s*0.5)); }
    if (brood) { ctx.fillStyle = '#7aa0c4'; ctx.fillRect(ox+x*s, oy+y*s, Math.max(1,s*0.35), Math.max(1,s*0.35)); }
    if (store) { ctx.fillStyle = '#e8d27a'; ctx.fillRect(ox+x*s, oy+y*s, s, Math.max(1,s*0.2)); }
  }
  const ny = f.nest[0], nx = f.nest[1];
  ctx.strokeStyle = '#e6dcc8';
  ctx.strokeRect(ox+nx*s-1, oy+ny*s-1, s+2, s+2);
  for (const a of f.agents) {
    ctx.fillStyle = a.k === 'H' ? '#f3f0a8' : '#7a6a55';
    const r = a.k === 'H' ? Math.max(2, s*0.45) : Math.max(1, s*0.28);
    ctx.beginPath();
    ctx.arc(ox+a.x*s + s/2, oy+a.y*s + s/2, r, 0, Math.PI*2);
    ctx.fill();
  }
  stats.innerHTML = `<span>g<b>${f.generation}</b> step <b>${f.step}</b></span>
    <span>cal <b>${f.calories.toFixed(1)}</b></span>
    <span>trainer <b>${f.trainer ? 'live' : 'off'}</b></span>
    <span>flies <b>${f.agents.length}</b></span>
    <span>frame <b>${i+1}/${frames.length}</b></span>`;
  const ev = (f.events||[]).map(e => e.name+'@g'+e.generation).join(' · ') || '(no civilization events yet)';
  eventlog.textContent = ev;
  drawRaster(f);
}

function drawRaster(f) {
  const w = raster.width, h = raster.height;
  rctx.fillStyle = '#100e0c';
  rctx.fillRect(0,0,w,h);
  const n = (f.spikes||[]).length || 20;
  spikeHist.push(f.spikes || []);
  if (spikeHist.length > 80) spikeHist.shift();
  const cw = w / 80, ch = h / n;
  for (let t=0;t<spikeHist.length;t++) {
    const col = spikeHist[t];
    for (let k=0;k<n;k++) {
      if (col[k]) {
        rctx.fillStyle = '#7ed0c6';
        rctx.fillRect(t*cw, k*ch, Math.max(1,cw-0.4), Math.max(1,ch-0.6));
      }
    }
  }
  rctx.fillStyle = '#8a7f6a';
  rctx.font = '10px ui-monospace';
  (f.names||[]).forEach((name,k) => {
    if (k % 2 === 0) rctx.fillText(name, 2, k*ch + 9);
  });
}

playBtn.onclick = () => { playing = !playing; playBtn.textContent = playing ? 'pause' : 'play'; };
scrub.oninput = () => { i = +scrub.value; spikeHist = []; draw(frames[i]); };
function tick(now) {
  const dt = now - last; last = now;
  if (playing && frames.length) {
    acc += dt * (0.5 + +speed.value);
    const stepMs = 80;
    while (acc >= stepMs) {
      acc -= stepMs;
      i = (i + 1) % frames.length;
      if (i === 0) spikeHist = [];
      scrub.value = i;
      draw(frames[i]);
    }
  }
  requestAnimationFrame(tick);
}
draw(frames[0]);
requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def write_hud(path: Path, frames: list[dict[str, Any]], meta: dict[str, Any] | None = None) -> Path:
    path = Path(path)
    payload = {"meta": meta or {}, "frames": frames}
    html = HUD_HTML.replace("__FRAMES__", json.dumps(payload, separators=(",", ":")))
    path.write_text(html, encoding="utf-8")
    return path
