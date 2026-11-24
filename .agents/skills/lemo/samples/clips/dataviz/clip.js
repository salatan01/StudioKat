// Data Visualization pilot — "A warming record".
//
// An original six-second cutaway written in the vendored style's grammar: cream
// paper under a faint dot grid, a two-lead pencil drawing a real series on as
// the axis grows, marks landing in order and coloured by their value, and one
// handwritten annotation ringing the record's warmest year. The numbers are
// NASA GISTEMP v4 (public domain); the demo's own dataset, story and copy are
// not reused. The vendored modules are read as a codex of technique only.
//
// The vendored engine.js fixes its page at 1920x1080 (applyCam/drawPaper/
// drawPencil close over its own W/H), so this clip lays the chart out in screen
// coordinates from its own canvas size and draws its own paper; it draws with
// the engine's coordinate-explicit primitives (pencilStroke, dataDot, inkLine,
// handText, setType, leader, ringPath, valueColor) and blits the engine's
// screen-space pencil through a 1920x1080 stencil so it survives any aspect.
//
// Deterministic: every value derives from `t` — no Math.random, no Date.now.

import { P, valueColor, pencilStroke, dataDot, inkLine, handText, measureHand,
         setType, leader, ringPath, drawPencil } from '/styles/dataviz/demo/engine.js';
import { mulberry, clamp, lerp } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
canvas.width = W;
canvas.height = H;

window.DUR = 6;

// ---- the real series (NASA GISTEMP v4, annual mean; see data_manifest.json) --
const CSV = await (await fetch('data/data.csv')).text();
const YEAR_COL = 0, VALUE_COL = 1;               // columns chosen by header name
const rows = CSV.trim().split(/\r?\n/);
const header = rows[0].split(',');
if (header[YEAR_COL] !== 'Year' || header[VALUE_COL] !== 'J-D') {
  throw new Error('data.csv: expected a "Year" first column and a "J-D" second');
}
const DATA = rows.slice(1).map(line => {
  const cells = line.split(',');
  return { year: +cells[YEAR_COL], v: parseFloat(cells[VALUE_COL]) };
}).filter(d => Number.isFinite(d.year) && Number.isFinite(d.v));

const Y0 = DATA[0].year, Y1 = DATA[DATA.length - 1].year;
let peakIdx = 0;
DATA.forEach((d, i) => { if (d.v > DATA[peakIdx].v) peakIdx = i; });
const PEAK = DATA[peakIdx];

// ---- the clip's own words ---------------------------------------------------
const KICKER = 'GLOBAL TEMPERATURE ANOMALY · °C VS 1951–1980';
const TITLE = 'A warming record';
const CAPTION = 'Annual mean surface temperature, 1996–2025, above the 1951–1980 mean.';
const CAP_KICKER = 'NASA GISTEMP v4';
const NOTE = `warmest year: +${PEAK.v.toFixed(2)} °C`;

// ---- timings (6 s, locked camera: the drawing is the movement) --------------
const T_KICK = 0.42, S_KICK = 0.7;
const T_TITLE = 0.6, S_TITLE = 0.7;
const T_AXIS0 = 0.3, T_AXIS1 = 1.0;
const T_S0 = 1.0, T_S1 = 3.4;                    // the series inks on left→right
const T_RING = 3.5, S_RING = 0.4;
const T_LEAD = 3.9, S_LEAD = 0.32;
const T_NOTE = 4.2, S_NOTE = 0.55;
const T_LEAVE = 4.78, S_LEAVE = 0.6;
const T_CAP = 4.3;

// ---- layout, scaled from W/H so one clip renders at any aspect --------------
const portrait = H > W;
const BOX = portrait
  ? { x0: W * 0.15, x1: W * 0.95, yT: H * 0.285, yB: H * 0.72 }
  : { x0: W * 0.135, x1: W * 0.95, yT: H * 0.315, yB: H * 0.80 };
const V0 = 0, V1 = 1.5;                          // value axis 0.0 .. 1.5 °C
const X = year => BOX.x0 + (year - Y0) / (Y1 - Y0) * (BOX.x1 - BOX.x0);
const Y = v => BOX.yB - (v - V0) / (V1 - V0) * (BOX.yB - BOX.yT);
const PT = DATA.map(d => ({ x: X(d.year), y: Y(d.v), v: d.v }));
const peakPt = PT[peakIdx];

// cumulative arc-length fraction of each mark (lands the dot when the pencil passes)
const FRAC = (() => {
  const out = [0]; let tot = 0;
  for (let i = 1; i < PT.length; i++) { tot += Math.hypot(PT[i].x - PT[i - 1].x, PT[i].y - PT[i - 1].y); out.push(tot); }
  return out.map(d => d / (tot || 1));
})();
function tipAt(p) {
  for (let i = 1; i < FRAC.length; i++) {
    if (p <= FRAC[i]) { const k = (p - FRAC[i - 1]) / Math.max(1e-6, FRAC[i] - FRAC[i - 1]);
      return [lerp(PT[i - 1].x, PT[i].x, k), lerp(PT[i - 1].y, PT[i].y, k)]; }
  }
  return [PT[PT.length - 1].x, PT[PT.length - 1].y];
}

// ---- the pencil: the engine draws it in a fixed 1920x1080 stencil, so blit --
const PEN_W = 1920, PEN_H = 1080, PEN_ANCHOR = [190, 140];
const PEN_S = portrait ? 0.44 : 0.62;            // the stencil is native px, so shrink for portrait
const penCanvas = document.createElement('canvas');
penCanvas.width = PEN_W; penCanvas.height = PEN_H;
const penCtx = penCanvas.getContext('2d');
function drawPencilAt(tip, o = {}) {
  penCtx.setTransform(1, 0, 0, 1, 0, 0); penCtx.clearRect(0, 0, PEN_W, PEN_H);
  drawPencil(penCtx, { tip: PEN_ANCHOR, s: o.s ?? PEN_S, lift: o.lift ?? 0, flip: o.flip ?? 0,
    blur: o.blur ?? 0, alpha: o.alpha ?? 1, ang: o.ang ?? 0.62 });
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(penCanvas, tip[0] - PEN_ANCHOR[0], tip[1] - PEN_ANCHOR[1]);
  ctx.restore();
}

// ---- the paper: cream stock, fibre speckle, faint dot grid -------------------
function paper() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = P.paper; ctx.fillRect(0, 0, W, H);
  const R = mulberry(7);
  ctx.fillStyle = 'rgba(120,100,70,.05)';
  const fibres = Math.round(W * H / 9000);
  for (let i = 0; i < fibres; i++) {
    const x = R() * W, y = R() * H, l = 2 + R() * 11, a = R() * Math.PI;
    ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.fillRect(0, 0, l, 0.7); ctx.restore();
  }
  ctx.fillStyle = P.dotgrid;
  const step = Math.max(22, Math.round(Math.min(W, H) / 40)), r = step * 0.045;
  for (let x = step * 0.5; x < W; x += step)
    for (let y = step * 0.5; y < H; y += step) ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
}

// ---- axes: a frame that grows, pale gridlines, mono ticks -------------------
function mono(str, x, y, o = {}) { return setType(ctx, str, x, y, { font: 'IBM Plex Mono', ...o }); }
function line(a, b) { inkLine(ctx, [a, b], { width: 1, color: P.rule }); }

function drawAxes(p) {
  const yBase = Y(0), xEnd = lerp(BOX.x0, BOX.x1, p);
  const yTop = lerp(yBase, Y(V1), p);
  inkLine(ctx, [[BOX.x0, yBase], [xEnd, yBase]], { width: 1.4, color: P.ink, alpha: 0.9 });
  inkLine(ctx, [[BOX.x0, yBase], [BOX.x0, yTop]], { width: 1.4, color: P.ink, alpha: 0.9 });
  [0.5, 1.0].forEach(v => { const g = clamp(p * (V1 / v) - 0.15);
    if (g > 0) line([BOX.x0, Y(v)], [lerp(BOX.x0, BOX.x1, g), Y(v)]); });
  const tk = Math.max(14, Math.round(portrait ? H * 0.017 : H * 0.024));
  [[V0, '0.0'], [0.5, '0.5'], [1.0, '1.0'], [V1, '1.5']].forEach(([v, s]) => {
    if (v !== V0 && Y(v) < yTop - 2) return;         // a tick the growing rule hasn't reached
    mono(s, BOX.x0 - tk, Y(v) + tk * 0.34, { size: tk, color: P.inkSoft, align: 'right', alpha: p });
  });
  [2000, 2010, 2020].forEach(yr => { const frac = (yr - Y0) / (Y1 - Y0), a = clamp((p - frac) * 3);
    if (a > 0) mono(String(yr), X(yr), yBase + tk * 1.5, { size: tk, color: P.inkSoft, align: 'center', alpha: a }); });
}

// ---- the series: a pencil line, marks landing in order ----------------------
function drawSeries(t) {
  const p = clamp((t - T_S0) / (T_S1 - T_S0));
  if (p <= 0) return null;
  const path = PT.map(d => [d.x, d.y]);
  const tip = pencilStroke(ctx, path, { progress: p, color: P.ink, width: 2.2, wobble: 0.5, passes: 2, alpha: 0.9, grain: 0.5 });
  const r = Math.max(4, Math.min(W, H) * 0.0085);
  PT.forEach((d, i) => {
    const fresh = t - (T_S0 + FRAC[i] * (T_S1 - T_S0));
    if (fresh < 0) return;
    dataDot(ctx, d.x, d.y, r, valueColor(d.v, { center: 0, half: 1.4 }),
      { fresh, ripple: i % 3 === 0 ? 1 : 0, ring: P.ink, ringW: 1.1 });
  });
  return { p, tip };
}

// ---- the annotation: a ring, a leader, a handwritten note -------------------
// The note sits in the empty upper band on each aspect: one handwritten line,
// left of the peak, so the pencil finishes writing into open paper.
const noteX = () => portrait ? W * 0.22 : W * 0.40;
const noteY = () => portrait ? Y(1.34) : Y(1.33);
const noteSize = () => portrait ? H * 0.03 : H * 0.045;
function drawAnnotation(t) {
  let pen = null;
  const r = Math.max(18, Math.min(W, H) * 0.028);
  if (t >= T_RING) {
    const rp = clamp((t - T_RING) / S_RING);
    const tip = pencilStroke(ctx, ringPath(peakPt.x, peakPt.y, r, 3), { progress: rp, color: P.red, width: 1.7, wobble: 0.5, passes: 1 });
    if (rp < 1) pen = { tip, flip: 1, lift: 0.02 };
  }
  const nx = noteX(), ny = noteY(), nsize = noteSize();
  const anchor = [nx + measureHand(ctx, NOTE, nsize) + nsize * 0.4, ny - nsize * 0.28];
  if (t >= T_LEAD) {
    const lp = clamp((t - T_LEAD) / S_LEAD);
    const tip = leader(ctx, anchor, [peakPt.x, peakPt.y], { progress: lp, color: P.red, width: 1.5, wobble: 0.4, bend: -0.12 });
    if (lp < 1 && !pen) pen = { tip, flip: 1, lift: 0.02 };
  }
  if (t >= T_NOTE) {
    const np = clamp((t - T_NOTE) / S_NOTE);
    const rr = handText(ctx, NOTE, nx, ny, { progress: np, color: P.red, size: nsize });
    if (t >= T_LEAVE) pen = { tip: rr.tip, flip: 1, lift: 0.05 + 0.6 * clamp((t - T_LEAVE) / S_LEAVE), alpha: clamp(1 - (t - T_LEAVE) / S_LEAVE) };
    else pen = { tip: rr.tip, flip: 1, lift: np < 1 ? 0.02 : 0.04 };
  }
  return pen;
}

// ---- the headline and its kicker -------------------------------------------
function drawTitle(t) {
  const size = portrait ? H * 0.05 : H * 0.072;
  const tx = BOX.x0, ty = portrait ? H * 0.11 : H * 0.135;
  const ks = Math.max(13, Math.round(portrait ? H * 0.015 : H * 0.019));
  const kp = clamp((t - T_KICK) / S_KICK);
  if (kp > 0) mono(KICKER, tx, ty - size * 1.32, { size: ks, color: P.inkSoft, track: ks * 0.06, progress: kp });
  const tp = clamp((t - T_TITLE) / S_TITLE);
  if (tp > 0) setType(ctx, TITLE, tx, ty, { font: 'Newsreader', weight: 500, size, color: P.ink, progress: tp });
}

// ---- the caption band -------------------------------------------------------
let captionLines = null;
function drawCaption(t) {
  if (t < T_CAP || t > window.DUR + 0.4) return;
  const size = portrait ? H * 0.019 : H * 0.028;
  const x = BOX.x0, y = portrait ? H * 0.9 : H * 0.915;
  const fade = clamp((t - T_CAP) / 0.25) * (1 - clamp((t - window.DUR + 0.3) / 0.3));
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.font = `400 ${size}px Newsreader`; ctx.textBaseline = 'alphabetic';
  if (!captionLines) {
    const maxW = BOX.x1 - BOX.x0, sp = ctx.measureText(' ').width;
    const lines = [[]]; let lw = 0;
    for (const w of CAPTION.split(' ')) { const ww = ctx.measureText(w).width;
      if (lw + ww > maxW && lines[lines.length - 1].length) { lines.push([]); lw = 0; }
      lines[lines.length - 1].push(w); lw += ww + sp; }
    captionLines = lines;
  }
  const lines = captionLines, lh = size * 1.2, top = y - (lines.length - 1) * lh;
  const ruleY = top - size * 1.1;
  ctx.globalAlpha = fade; ctx.strokeStyle = P.ink; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(x, ruleY); ctx.lineTo(x + (BOX.x1 - BOX.x0) * clamp((t - T_CAP) * 1.4), ruleY); ctx.stroke();
  mono(CAP_KICKER, x, ruleY - size * 0.42, { size: Math.max(12, Math.round(size * 0.62)), color: P.inkSoft, track: 1, alpha: fade });
  ctx.globalAlpha = fade; ctx.fillStyle = P.ink; ctx.font = `400 ${size}px Newsreader`;
  lines.forEach((L, li) => ctx.fillText(L.join(' '), x, top + li * lh));
  ctx.restore();
}

// ---- frame ------------------------------------------------------------------
function draw(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left'; ctx.letterSpacing = '0px';
  paper();
  drawAxes(clamp((t - T_AXIS0) / (T_AXIS1 - T_AXIS0)));
  let pen = null;
  const s = drawSeries(t);
  if (s && t < T_RING) pen = t < T_S1
    ? { tip: s.tip, flip: 0, lift: 0 }
    : { tip: [PT[PT.length - 1].x, PT[PT.length - 1].y], flip: 0, lift: 0.12 * clamp((t - T_S1) / 0.2) };
  const a = drawAnnotation(t);
  if (a) pen = a;
  drawTitle(t);
  drawCaption(t);
  if (pen) drawPencilAt(pen.tip, { flip: pen.flip ?? 0, lift: pen.lift ?? 0, alpha: pen.alpha ?? 1 });
}

window.render = t => draw(clamp(t, 0, window.DUR));

// text the viewer must read, with its screen-space box
window.TEXTS = () => {
  const tsize = portrait ? H * 0.05 : H * 0.072;
  const ty = portrait ? H * 0.11 : H * 0.135;
  const nsize = noteSize();
  const nx = noteX(), ny = noteY();
  const csize = portrait ? H * 0.019 : H * 0.028;
  const cy = portrait ? H * 0.9 : H * 0.915;
  return [
    { id: 'title', text: TITLE, x0: BOX.x0, y0: ty - tsize, x1: BOX.x0 + W * 0.62, y1: ty + tsize * 0.3 },
    { id: 'kicker', text: KICKER, x0: BOX.x0, y0: ty - tsize * 1.6, x1: BOX.x0 + W * 0.82, y1: ty - tsize * 1.0 },
    { id: 'note', text: NOTE, x0: nx, y0: ny - nsize, x1: nx + measureHand(ctx, NOTE, nsize), y1: ny + nsize * 0.3 },
    { id: 'caption', text: CAPTION, x0: BOX.x0, y0: cy - csize * 2.0, x1: BOX.x1, y1: cy + csize * 0.3 },
  ];
};

try {
  await Promise.all([
    '400 100px Newsreader', '500 100px Newsreader',
    '400 100px Caveat', '500 100px Caveat', '700 100px Caveat',
    '400 100px "IBM Plex Mono"', '500 100px "IBM Plex Mono"',
  ].map(f => document.fonts.load(f, 'A warming record 0123456789. °C warmest in the')));
} catch (e) {}
await document.fonts.ready;

draw(0);
window.READY = true;
