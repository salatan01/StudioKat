// Isometric Picture Book — "The morning bus queue".
//
// One bus-stop shelter with a single painted queue lane. Commuters arrive one
// by one, in order, and each steps into the next free place back: first come,
// first served. The camera hovers over the diorama and pushes in gently.
//
// Original StudioKat clip: the vendored demo (a boarding gate / aircraft) is a
// technique reference only; its place, people and narration are not reused.
//
// Deterministic: every value derives from `t`. No Math.random / Date.now.

import { Iso, tri, mix, hex, clamp, lerp, seg, ss } from '/styles/isometric-picture-book/demo/engine.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const defW = (META.width | 0) || 1920;
const defH = (META.height | 0) || 1080;
// Match the actual render viewport (readcheck / stills pass --size for other
// aspects) so the clip draws correctly at 16:9 and 9:16 alike.
const vw = window.innerWidth || defW;
const vh = window.innerHeight || defH;
canvas.width = vw;
canvas.height = vh;
const W = canvas.width;
const H = canvas.height;

window.DUR = 6;

// ---- palette (warm paper world, one accent) -------------------------------
const C = {
  bg: '#F1E8D8', floor: '#EADAC0',
  wall: '#E8DECB', wallDark: '#C9B89E',
  roof: '#C9B89E', roofDark: '#A89478',
  ink: '#2A2E29', soft: '#7A7468',
  lane: '#D0573A', mark: '#F5E9CB',
  legs: '#4A4E4B', legsDark: '#2B2E2D',
  skin: '#D9A882', paper: '#FAF4E8',
};
// four muted shirt colours (the weave reads in these)
const TOPS = ['#B9824F', '#7F98AE', '#8C8199', '#D3C29E'];
const LEGS = ['#3E4450', '#59534A', '#3A3D42', '#4B4F5A'];

const iso = new Iso(ctx, W, H);

// ---- the place: one shelter, one queue lane -------------------------------
const SPOT_D = 3.0;        // metres between queue places
const N_PAX = 4;
// place i is at world (d, d) so the lane runs straight down the screen
// (screen x constant); larger d = nearer = front of the queue (bottom of screen)
const SPOTS = [];
for (let i = 0; i < N_PAX; i++) {
  const d = (N_PAX - 1 - i) * SPOT_D;   // place 0 = front (nearest, bottom)
  SPOTS.push({ x: d, y: d });
}
// commuters in arrival (rule) order; each steps into the next place back
const PAX = [];
{
  const enter0 = 0.7, gap = 1.0, walkDur = 0.9;
  for (let i = 0; i < N_PAX; i++) {
    const d = SPOTS[i].x;
    PAX.push({
      id: i,
      top: TOPS[i % TOPS.length], legs: LEGS[i % LEGS.length],
      dx: d, dy: d,                          // destination (their place)
      sx: d - 2.7, sy: d,                    // entry point, beside their place
      t0: enter0 + i * gap,                  // starts walking
      t1: enter0 + i * gap + walkDur,        // arrives and stands
    });
  }
}

// continuous world position of commuter p at time t (feet on the floor)
// sampled every frame: a walk then a hold, never a teleport or a step
function paxPos(p, t) {
  if (t <= p.t0) return { x: p.sx, y: p.sy, a: 0 };   // not entered yet
  if (t >= p.t1) return { x: p.dx, y: p.dy, a: 1 };   // standing at their place
  const f = seg(t, p.t0, p.t1);                       // 0 -> 1 while walking
  return { x: lerp(p.sx, p.dx, f), y: p.sy, a: 1 };   // walking beside the lane
}

function worldDepth(p, t) { const pos = paxPos(p, t); return pos.x + pos.y; }

// ---- camera: hover over the shelter, gentle push in -----------------------
function camAt(t) {
  const p = ss(seg(t, 0, 6));          // 0 -> 1 across the clip, smoothstep
  return {
    x: -0.4 + Math.sin(p * 0.5) * 0.12,
    y: 0.1 + Math.cos(p * 0.35) * 0.08,
    z: 1.0,
    k: 32 + p * 3,                     // slow push in
  };
}

// ---- drawing ---------------------------------------------------------------
function drawFloor() {
  iso.add(-1e6, () => {
    iso.poly([
      iso.P(-40, -40, 0), iso.P(40, -40, 0),
      iso.P(40, 40, 0), iso.P(-40, 40, 0),
    ], C.floor);
  }, 0);
}

function drawShelter() {
  // back wall behind the queue (top of the screen)
  iso.box(-2.9, -2.9, 0, 2.5, 2.5, 3.0, C.wall);
  // roof slab
  iso.box(-3.4, -3.4, 3.0, 3.5, 3.5, 0.5, C.roof);
}

function drawBench() {
  iso.box(-1.1, -1.1, 0, 2.2, 0.5, 0.45, C.wallDark);
}

function drawLane() {
  const L = SPOT_D * (N_PAX - 1);
  iso.add(5, () => {
    // painted lane strip along the queue line
    iso.poly([
      iso.P(-0.16, -0.16, 0.02), iso.P(0.16, -0.16, 0.02),
      iso.P(L + 0.16, L + 0.16, 0.02), iso.P(L - 0.16, L + 0.16, 0.02),
    ], C.lane);
  }, 0);
  // empty place markers waiting to be filled
  for (let i = 0; i < N_PAX; i++) {
    const s = SPOTS[i];
    iso.add(6, () => {
      iso.poly([
        iso.P(s.x - 0.34, s.y - 0.34, 0.04),
        iso.P(s.x + 0.34, s.y - 0.34, 0.04),
        iso.P(s.x + 0.34, s.y + 0.34, 0.04),
        iso.P(s.x - 0.34, s.y + 0.34, 0.04),
      ], C.mark);
    }, 0);
  }
}

// simple screen-space commuter figure (feet at sx, sy, height h px)
function drawPerson(sx, sy, h, topColor, legsColor) {
  const t3 = tri(topColor);
  const ld = hex(mix(legsColor, '#15171A', 0.25));
  ctx.save();
  ctx.translate(sx, sy);
  // feet
  ctx.fillStyle = C.legsDark;
  ctx.fillRect(-0.095 * h, 0, 0.07 * h, 0.13 * h);
  ctx.fillRect(0.025 * h, 0, 0.07 * h, 0.13 * h);
  // legs
  ctx.fillStyle = legsColor;
  ctx.fillRect(-0.09 * h, -0.26 * h, 0.07 * h, 0.27 * h);
  ctx.fillRect(0.02 * h, -0.26 * h, 0.07 * h, 0.27 * h);
  // body: tapered trapezoid, shirt colour mid-tone / dark side
  ctx.beginPath();
  ctx.moveTo(-0.17 * h, -0.12 * h);
  ctx.lineTo(-0.125 * h, -0.68 * h);
  ctx.lineTo(0.125 * h, -0.68 * h);
  ctx.lineTo(0.17 * h, -0.12 * h);
  ctx.closePath();
  ctx.fillStyle = t3[1];
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(0.03 * h, -0.12 * h);
  ctx.lineTo(0.03 * h, -0.68 * h);
  ctx.lineTo(0.125 * h, -0.68 * h);
  ctx.lineTo(0.17 * h, -0.12 * h);
  ctx.closePath();
  ctx.fillStyle = t3[2];
  ctx.fill();
  // head
  ctx.beginPath();
  ctx.arc(0, -0.84 * h, 0.095 * h, 0, Math.PI * 2);
  ctx.fillStyle = C.skin;
  ctx.fill();
  ctx.restore();
}

// route sign on the shelter wall; returns its screen box (viewport pixels)
const SIGN = { x: -1.5, y: -1.5, z: 2.6, text: 'BUS 7' };

function signBox(t) {
  iso.cam = camAt(t);
  const [sx, sy] = iso.P(SIGN.x, SIGN.y, SIGN.z);
  ctx.font = '600 28px Newsreader';
  const mw = ctx.measureText(SIGN.text).width;
  const pad = 12;
  return {
    cx: sx, cy: sy, mw,
    x0: sx - mw / 2 - pad, x1: sx + mw / 2 + pad,
    y0: sy - 32, y1: sy + 10,
  };
}

function drawSign(t) {
  const b = signBox(t);
  ctx.save();
  ctx.translate(b.cx, b.cy);
  ctx.fillStyle = 'rgba(250,244,232,0.94)';
  ctx.beginPath(); ctx.roundRect(-b.mw / 2 - 12, -32, b.mw + 24, 44, 6); ctx.fill();
  ctx.strokeStyle = C.soft; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.fillStyle = C.ink;
  ctx.font = '600 28px Newsreader';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(SIGN.text, 0, 2);
  ctx.restore();
}

function draw(t) {
  t = clamp(t, 0, window.DUR);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, W, H);

  iso.cam = camAt(t);
  drawFloor();
  drawShelter();
  drawBench();
  drawLane();
  iso.flush();

  // commuters back-to-front: farther world depth drawn first (nearer on top)
  const ordered = [...PAX].sort((a, b) => worldDepth(a, t) - worldDepth(b, t));
  for (const p of ordered) {
    const pos = paxPos(p, t);
    if (pos.a <= 0) continue;          // not entered yet
    const [sx, sy] = iso.P(pos.x, pos.y, 0);
    drawPerson(sx, sy, 36, p.top, p.legs);
    if (globalThis.__POS) {
      globalThis.__POS.push({ i: p.id, k: 'w', x: pos.x, y: pos.y, a: pos.a });
    }
  }

  drawSign(t);
}

window.render = t => draw(t);

// text the viewer must read: the route sign holds for the whole clip
window.TEXTS = () => {
  const b = signBox(0);
  return [{
    id: 'sign', text: SIGN.text,
    x0: b.x0, y0: b.y0, x1: b.x1, y1: b.y1,
  }];
};

await Promise.all([
  document.fonts.load('600 40px Newsreader', 'BUS 7 0123456789'),
]);
await document.fonts.ready;

draw(0);
window.READY = true;
