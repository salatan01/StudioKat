// Isometric Picture Book — "The morning bus queue" (scaled up).
//
// One bus-stop shelter with a single-file queue lane. Commuters arrive one
// by one, in rule order (first come, first served), and each steps into the
// next free place back, so the line builds place by place. The camera hovers
// over the diorama and pushes in gently.
//
// Original StudioKat clip: the vendored demo (a boarding gate / aircraft) is a
// technique reference only; its place, people and narration are not reused.
//
// Deterministic: every value derives from `t`. No Math.random / Date.now.

import { Iso, tri, mix, hex, clamp, lerp, seg } from '/styles/isometric-picture-book/demo/engine.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const defW = (META.width | 0) || 1920;
const defH = (META.height | 0) || 1080;
// The render server sizes the viewport to --size; window.innerWidth/Height
// report it, so the canvas matches 16:9 and 9:16 renders alike.
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
const portrait = H > W;            // 9:16 runs the queue down the frame
const K = portrait ? 100 : 118;    // camera scale (screen px per world metre)
const PH = portrait ? 64 : 78;     // figure height in screen px

// ---- the place: one shelter, one single-file queue lane -------------------
const N_PLACES = 4;
// Queue places in world metres. Landscape: (1,-1) world direction -> screen
// horizontal (queue runs across the wide frame). Portrait: (1,1) world
// direction -> screen vertical (queue runs down the frame).
const PLACES = [];
for (let i = 0; i < N_PLACES; i++) {
  PLACES.push(portrait
    ? { x: -1.4 + i * 1.9, y: -3.0 + i * 1.9 }
    : { x: -3.2 + i * 2.0, y: 3.2 - i * 2.0 });
}
// camera centres on the place cluster so the diorama fills the frame
let cx = 0, cy = 0;
for (const p of PLACES) { cx += p.x; cy += p.y; }
cx /= N_PLACES; cy /= N_PLACES;
const cam = { x: cx, y: cy, z: portrait ? 1.8 : 1.5, k: K };

// 3 commuters arrive one by one and fill places 0, 1, 2 (place 3 stays empty,
// showing the rule continues). Each walks from a side entry point to their
// place, sampled every frame: a walk then a hold, never a teleport or a step.
const PAX = [];
{
  const enter0 = 0.7, gap = 1.0, walkDur = 1.0;
  const off = portrait ? { x: 0, y: 1.6 } : { x: 0, y: 1.4 };
  for (let i = 0; i < 3; i++) {
    const pl = PLACES[i];
    PAX.push({
      id: i,
      top: TOPS[i % TOPS.length], legs: LEGS[i % LEGS.length],
      sx: pl.x + off.x, sy: pl.y + off.y,   // entry point beside their place
      dx: pl.x, dy: pl.y,                   // destination place
      t0: enter0 + i * gap,                 // starts walking
      t1: enter0 + i * gap + walkDur,       // arrives and stands
    });
  }
}

function paxPos(p, t) {
  if (t <= p.t0) return { x: p.sx, y: p.sy, a: 0 };   // not entered yet
  if (t >= p.t1) return { x: p.dx, y: p.dy, a: 1 };   // standing at their place
  const f = seg(t, p.t0, p.t1);                       // 0 -> 1 while walking
  return { x: lerp(p.sx, p.dx, f), y: lerp(p.sy, p.dy, f), a: 1 };
}
function paxDepth(p, t) { const q = paxPos(p, t); return q.x + q.y; }

// ---- drawing ---------------------------------------------------------------
function drawFloor() {
  iso.add(-1e6, () => {
    iso.poly([
      iso.P(-60, -60, 0), iso.P(60, -60, 0),
      iso.P(60, 60, 0), iso.P(-60, 60, 0),
    ], C.floor);
  }, 0);
}

function drawShelter() {
  // back wall behind the queue + a roof slab, three flat tones, no outlines
  if (portrait) {
    // shelter to the screen-left of the vertical queue
    iso.box(cx - 2.7, cy - 0.3, 0, 1.6, 6.2, 3.0, C.wall);
    iso.box(cx - 3.1, cy - 0.7, 3.0, 2.4, 7.0, 0.5, C.roof);
  } else {
    // shelter screen-up (behind) the horizontal queue
    iso.box(cx - 3.3, cy - 2.9, 0, 7.6, 1.6, 3.0, C.wall);
    iso.box(cx - 3.7, cy - 3.3, 3.0, 8.4, 2.4, 0.5, C.roof);
  }
}

function drawLane() {
  // centreline painted through the queue places
  iso.line3(PLACES.map(p => [p.x, p.y, 0.02]), C.lane, 2.6);
  // empty place markers waiting to be filled (the next free place back)
  for (let i = 0; i < N_PLACES; i++) {
    const s = PLACES[i];
    iso.add(6, () => {
      iso.poly([
        iso.P(s.x - 0.42, s.y - 0.42, 0.04),
        iso.P(s.x + 0.42, s.y - 0.42, 0.04),
        iso.P(s.x + 0.42, s.y + 0.42, 0.04),
        iso.P(s.x - 0.42, s.y + 0.42, 0.04),
      ], C.mark);
    }, 0);
  }
}

// screen-space commuter figure (feet at sx, sy, height PH px), drawn at the
// commuter's world position via iso.P, so size is fixed in screen px.
function drawPerson(sx, sy, topColor, legsColor) {
  const t3 = tri(topColor);
  const ld = hex(mix(legsColor, '#15171A', 0.25));
  ctx.save();
  ctx.translate(sx, sy);
  // feet
  ctx.fillStyle = C.legsDark;
  ctx.fillRect(-0.095 * PH, 0, 0.07 * PH, 0.13 * PH);
  ctx.fillRect(0.025 * PH, 0, 0.07 * PH, 0.13 * PH);
  // legs
  ctx.fillStyle = legsColor;
  ctx.fillRect(-0.09 * PH, -0.26 * PH, 0.07 * PH, 0.27 * PH);
  ctx.fillRect(0.02 * PH, -0.26 * PH, 0.07 * PH, 0.27 * PH);
  // body: tapered trapezoid, shirt colour mid-tone / dark side
  ctx.beginPath();
  ctx.moveTo(-0.17 * PH, -0.12 * PH);
  ctx.lineTo(-0.125 * PH, -0.68 * PH);
  ctx.lineTo(0.125 * PH, -0.68 * PH);
  ctx.lineTo(0.17 * PH, -0.12 * PH);
  ctx.closePath();
  ctx.fillStyle = t3[1];
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(0.03 * PH, -0.12 * PH);
  ctx.lineTo(0.03 * PH, -0.68 * PH);
  ctx.lineTo(0.125 * PH, -0.68 * PH);
  ctx.lineTo(0.17 * PH, -0.12 * PH);
  ctx.closePath();
  ctx.fillStyle = t3[2];
  ctx.fill();
  // head
  ctx.beginPath();
  ctx.arc(0, -0.84 * PH, 0.095 * PH, 0, Math.PI * 2);
  ctx.fillStyle = C.skin;
  ctx.fill();
  ctx.restore();
}

// route sign on the shelter wall; returns its screen box (viewport pixels)
const SIGN = { text: 'BUS 7' };

function signPoint() {
  if (portrait) return { x: cx - 1.9, y: cy + 2.8, z: 2.7 }; // on the shelter, screen-left
  return { x: cx - 0.6, y: cy - 3.3, z: 2.7 };
}

function signBox() {
  const sp = signPoint();
  iso.cam = cam;
  const [sx, sy] = iso.P(sp.x, sp.y, sp.z);
  ctx.font = '600 34px Newsreader';
  const mw = ctx.measureText(SIGN.text).width;
  const pad = 14;
  return {
    cx: sx, cy: sy, mw,
    x0: sx - mw / 2 - pad, x1: sx + mw / 2 + pad,
    y0: sy - 40, y1: sy + 12,
  };
}

function drawSign() {
  const b = signBox();
  ctx.save();
  ctx.translate(b.cx, b.cy);
  ctx.fillStyle = 'rgba(250,244,232,0.95)';
  ctx.beginPath(); ctx.roundRect(-b.mw / 2 - 14, -40, b.mw + 28, 54, 7); ctx.fill();
  ctx.strokeStyle = C.soft; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.fillStyle = C.ink;
  ctx.font = '600 34px Newsreader';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(SIGN.text, 0, 4);
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

  iso.cam = cam;
  drawFloor();
  drawShelter();
  drawLane();
  iso.flush();   // floor, shelter, lane, markers in depth order

  // commuters back-to-front by world depth (farther first, nearer on top)
  const ordered = [...PAX].sort((a, b) => paxDepth(a, t) - paxDepth(b, t));
  for (const p of ordered) {
    const pos = paxPos(p, t);
    if (pos.a <= 0) continue;          // not entered yet
    const [sx, sy] = iso.P(pos.x, pos.y, 0);
    drawPerson(sx, sy, p.top, p.legs);
    if (globalThis.__POS) {
      globalThis.__POS.push({ i: p.id, k: 'w', x: pos.x, y: pos.y, a: pos.a });
    }
  }

  drawSign();
}

window.render = t => draw(t);

// text the viewer must read: the route sign holds for the whole clip
window.TEXTS = () => {
  const b = signBox();
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
