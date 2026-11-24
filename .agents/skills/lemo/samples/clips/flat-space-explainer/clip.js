// Flat Space Explainer — "From a teacup to a galaxy".
// One continuous zoom out: a teacup resolves into a house, a city, Earth and
// finally the Milky Way, with a live scale readout naming the scale at each
// step. Original StudioKat clip; the vendored flat-space-explainer demo is a
// technique reference only (its story, guide and labels are not reused).
// Deterministic: every value derives from `t`; the starfield is seeded.
// No clock, no unseeded randomness.

import { clamp, seg, eio, mulberry, TAU } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
canvas.width = W;
canvas.height = H;
const S0 = [W / 2, H / 2];
const MW = Math.min(W, H);
const M = Math.round(MW * 0.04);
const portrait = H > W;

window.DUR = 8;

// ---- palette (flat space): deep nights, mist, blue, mint, coral, sun, cream ----
const C = {
  night: '#161933', n2: '#22274a', n3: '#353d6f', mist: '#8f96c9',
  blue: '#4d7cfe', blueD: '#3a5fd9',
  mint: '#3fd8ae', mintD: '#22b38c',
  coral: '#ff6b5e', coralD: '#e14b45',
  sun: '#ffc84a', sunD: '#f2a12f',
  cream: '#fff4e2', creamD: '#f0dcc0',
};

const TITLE = 'From a teacup to a galaxy';

function F(c) { ctx.fillStyle = c; }
function ellipse(x, y, rx, ry) { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, TAU); ctx.fill(); }
function circle(x, y, r) { ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); }
function rect(x, y, w, h) { ctx.beginPath(); ctx.rect(x, y, w, h); ctx.fill(); }

// deterministic starfield (seeded, never Math.random)
const R = mulberry(0xC0FFEE);
const STARS = [];
for (let i = 0; i < (portrait ? 300 : 420); i++) {
  STARS.push({ x: R() * W, y: R() * H, r: 1.1 + R() * 2.2,
    c: R() < 0.55 ? C.mist : R() < 0.88 ? C.cream : C.sun });
}

// ---- subjects -----------------------------------------------------------
// stop: the second at which the subject fills the frame.
// scale() returns 0.06 (a dot) .. 1 (fills the frame).
const SUBJECTS = [
  { stop: 0.0, label: '\u2248 15 cm',     name: 'a teacup' },
  { stop: 2.0, label: '\u2248 3 m',       name: 'a house' },
  { stop: 4.0, label: '\u2248 15 km',     name: 'a city' },
  { stop: 6.0, label: '\u2248 12 000 km', name: 'Earth' },
  { stop: 8.0, label: '\u2248 100 000 ly', name: 'the Milky Way' },
];

const PEAK = 0.22 * MW;   // screen radius when a subject fills the frame

function bump(t, a, b, c, d) { return seg(t, a, b) * (1 - seg(t, c, d)); }
function rise(t, a, b) { return eio(clamp(seg(t, a, b))); }

function subjectScale(sub, t) {
  const s = sub.stop;
  if (s === 0.0) return 0.06 + 0.94 * (1 - eio(seg(t, 0, 1.1))); // teacup: full, then shrinks
  if (s === 2.0) return 0.06 + 0.94 * bump(t, 1.3, 2.0, 2.0, 3.1);
  if (s === 4.0) return 0.06 + 0.94 * bump(t, 3.3, 4.0, 4.0, 5.1);
  if (s === 6.0) return 0.06 + 0.94 * bump(t, 5.3, 6.0, 6.0, 7.1);
  return 0.06 + 0.94 * rise(t, 7.3, 8.0); // galaxy: grows to the end
}

// the subject largest on screen at `t` — the readout is tied to the camera
function dominant(t) {
  let best = SUBJECTS[0]; let bs = -1;
  for (let i = 0; i < SUBJECTS.length; i++) {
    const sc = subjectScale(SUBJECTS[i], t);
    if (sc > bs) { bs = sc; best = SUBJECTS[i]; }
  }
  return best;
}

// ---- two-tone helpers (base + one shade step, no stroke) ----------------
function twoToneEllipse(x, y, rx, ry, base, shade, dx, dy) {
  F(shade); ellipse(x + dx, y + dy, rx, ry);
  F(base);  ellipse(x, y, rx, ry);
}
function twoToneRect(x, y, w, h, base, shade, dx, dy) {
  F(shade); rect(x + dx, y + dy, w, h);
  F(base);  rect(x, y, w, h);
}
function twoToneCircle(x, y, rad, base, shade, dx, dy) {
  F(shade); circle(x + dx, y + dy, rad);
  F(base);  circle(x, y, rad);
}

// ---- subject drawings (screen radius r, centre x, y) --------------------
function drawTeacup(r, x, y) {
  twoToneEllipse(x, y + r * 0.14, r * 0.9, r * 0.18, C.cream, C.creamD, r * 0.04, r * 0.05); // saucer
  twoToneEllipse(x, y - r * 0.08, r * 0.5, r * 0.72, C.cream, C.creamD, r * 0.04, r * 0.06); // cup
  F(C.mint); ellipse(x, y - r * 0.44, r * 0.42, r * 0.1);                                       // tea
  F(C.creamD); rect(x + r * 0.33, y - r * 0.26, r * 0.1, r * 0.42);                             // handle
  F(C.mist);
  circle(x - r * 0.14, y - r * 0.62, r * 0.05);                                                 // steam
  circle(x + r * 0.06, y - r * 0.84, r * 0.05);
}
function drawHouse(r, x, y) {
  twoToneRect(x - r * 0.5, y - r * 0.22, r, r * 0.62, C.sun, C.sunD, r * 0.05, r * 0.06);   // building
  F(C.sunD);
  ctx.beginPath(); ctx.moveTo(x, y - r * 0.56); ctx.lineTo(x - r * 0.62, y - r * 0.12); ctx.lineTo(x + r * 0.62, y - r * 0.12); ctx.closePath(); ctx.fill(); // roof
  F(C.n2); rect(x - r * 0.1, y - r * 0.02, r * 0.16, r * 0.22);                               // door
  rect(x + r * 0.22, y - r * 0.18, r * 0.14, r * 0.14);                                       // window
}
function drawCity(r, x, y) {
  const ground = y + r * 0.28;
  for (let i = -4; i <= 4; i++) {                                                             // deterministic skyline
    const bx = x + i * r * 0.22;
    const bh = r * (0.35 + 0.55 * ((i * 37 + 11) % 100) / 100);
    twoToneRect(bx - r * 0.085, ground - bh, r * 0.17, bh, C.blue, C.blueD, r * 0.02, r * 0.025);
  }
}
function drawEarth(r, x, y) {
  twoToneCircle(x, y, r * 0.5, C.blue, C.blueD, r * 0.04, r * 0.05);                         // planet
  F(C.mint); circle(x - r * 0.11, y - r * 0.09, r * 0.11);                                    // continent
}
function drawGalaxy(r, x, y) {
  F(C.cream); circle(x, y, r * 0.13);                                                         // core
  for (let arm = 0; arm < 3; arm++) {                                                         // spiral arms (dotted, flat)
    const a0 = arm * TAU / 3;
    for (let k = 0; k <= 26; k++) {
      const f = k / 26;
      const ang = a0 + f * TAU * 1.5;
      const rad = f * r * 0.92;
      F(C.mist); circle(x + Math.cos(ang) * rad, y + Math.sin(ang) * rad * 0.5, r * 0.022);
    }
  }
}

// ---- camera: one continuous pull-back with a little drift ---------------
function camAt(t) {
  const z = 1 - 0.09 * seg(t, 0, 8);
  const cx = 0.025 * MW * Math.sin(t * 1.1);
  const cy = 0.018 * MW * Math.cos(t * 0.8);
  return { z, c: [cx, cy] };
}

// ---- type ---------------------------------------------------------------
function setFont(weight, size) {
  ctx.font = `${weight} ${Math.round(size)}px "Jost"`;
  ctx.letterSpacing = size >= 90 ? `${(-size * 0.02).toFixed(2)}px` : '0px';
}
function measure(text, weight, size) { setFont(weight, size); return ctx.measureText(text); }
function fitSize(text, maxW, start, weight) {
  let s = start;
  for (let i = 0; i < 60 && s > 8; i++) {
    if (measure(text, weight, s).width <= maxW) break;
    s *= 0.93;
  }
  return s;
}

// a run of text wiped in horizontally (never a fade)
function wipeText(text, x, y, size, weight, p, color) {
  if (p <= 0) return;
  setFont(weight, size);
  F(color);
  const w = measure(text, weight, size).width + size * 0.12;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x - 2, y - size * 1.04, w * p + 4, size * 1.34);
  ctx.clip();
  ctx.fillText(text, x, y);
  ctx.restore();
}

function draw(t) {
  t = clamp(t, 0, window.DUR);

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic';

  F(C.night); ctx.fillRect(0, 0, W, H);

  // starfield (fixed screen space — deep space behind the travel)
  for (const s of STARS) { F(s.c); circle(s.x, s.y, s.r); }

  const cam = camAt(t);
  const dom = dominant(t);
  const sx = S0[0] - cam.c[0] * cam.z;
  const sy = S0[1] - cam.c[1] * cam.z;

  // subjects back-to-front so the current one sits on top (nesting)
  const scales = [subjectScale(SUBJECTS[4], t), subjectScale(SUBJECTS[3], t),
                  subjectScale(SUBJECTS[2], t), subjectScale(SUBJECTS[1], t),
                  subjectScale(SUBJECTS[0], t)];
  const draws = [drawGalaxy, drawEarth, drawCity, drawHouse, drawTeacup];
  for (let i = 0; i < draws.length; i++) {
    const r = PEAK * scales[i] * cam.z;
    if (r < 1.5) continue;
    draws[i](r, sx, sy);
  }

  // ---- HUD: title (wiped in) + live scale readout -----------------------
  const titleSize = fitSize(TITLE, W - 2 * M, MW * 0.07, 800);
  const titleW = measure(TITLE, 800, titleSize).width;
  const tx = portrait ? (W - titleW) / 2 : M;
  const ty = M + titleSize * 0.95;
  wipeText(TITLE, tx, ty, titleSize, 800, eio(seg(t, 0, 1.4)), C.cream);

  const readout = `${dom.label} · ${dom.name}`;
  const roSize = Math.max(20, titleSize * 0.45);
  setFont(700, roSize);
  const roW = measure(readout, 700, roSize).width;
  const rx = portrait ? (W - roW) / 2 : M;
  const ry = ty + titleSize * 1.35;
  F(C.mist);
  ctx.fillText(readout, rx, ry);
}

window.render = t => draw(clamp(t, 0, window.DUR));

// text the viewer must read: title + the live scale readout, with screen boxes
window.TEXTS = t => {
  t = clamp(t, 0, window.DUR);
  const out = [];
  const titleSize = fitSize(TITLE, W - 2 * M, MW * 0.07, 800);
  const titleW = measure(TITLE, 800, titleSize).width;
  const tx = portrait ? (W - titleW) / 2 : M;
  const ty = M + titleSize * 0.95;
  if (eio(seg(t, 0, 1.4)) > 0) {
    out.push({ id: 'title', text: TITLE,
      x0: tx - 2, y0: ty - titleSize * 1.04, x1: tx + titleW + 2, y1: ty + titleSize * 0.35 });
  }
  const dom = dominant(t);
  const readout = `${dom.label} · ${dom.name}`;
  const roSize = Math.max(20, titleSize * 0.45);
  setFont(700, roSize);
  const roW = measure(readout, 700, roSize).width;
  const rx = portrait ? (W - roW) / 2 : M;
  const ry = ty + titleSize * 1.35;
  out.push({ id: 'readout', text: readout,
    x0: rx, y0: ry - roSize * 1.04, x1: rx + roW, y1: ry + roSize * 0.35 });
  return out;
};

try {
  await Promise.all([
    document.fonts.load('800 96px "Jost"', TITLE),
    document.fonts.load('700 40px "Jost"', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\u2248·,.'),
  ]);
} catch (e) { console.error(e); }
await document.fonts.ready;

draw(0);
window.READY = true;
