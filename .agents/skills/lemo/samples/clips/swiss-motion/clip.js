// Swiss Motion pilot — "A tide timetable".
//
// A day of sea-level readings laid on a strict grid: six plain blocks on a
// water-level axis, and one red signal line that traces the tide across their
// tops and, on the last beat, leaves the page. Original StudioKat clip — the
// vendored demo (a 1961 concert poster) is used for technique only; its story,
// programme and score are not. Deterministic: every value derives from `t`.

import { clamp } from '/core/lib.js';
import { lerp, snap, lin, E8, E16, BEAT } from '/styles/swiss-motion/demo/ease.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
canvas.width = W;
canvas.height = H;

window.DUR = 6;

// ---- the clip's own content: a day of readings ------------------------------
const READINGS = [
  { at: '00:00', m: 2.1 },
  { at: '04:00', m: 3.6 },
  { at: '08:00', m: 4.2 },
  { at: '12:00', m: 1.4 },
  { at: '16:00', m: 0.6 },
  { at: '20:00', m: 2.8 },
];
const HEAD = ['TIDE', 'TIMETABLE'];
const CAPTION = 'Sea level in metres';
const COUNTER = 'SIX READINGS';
const HMAX = 4.6;

// ---- palette: paper, ink, greys and one signal red --------------------------
const C = {
  page: '#eae9e5', sheet: '#ffffff', ink: '#111111', red: '#e30613',
  grid: '#d7d6d1', level: '#e7e6e1', soft: '#cfcec9', mute: '#78776f',
};

// ---- layout, scaled from W/H so one clip renders at any aspect --------------
const M = Math.round(Math.min(W, H) * 0.055);
const contentW = W - 2 * M;
const gap = contentW * 0.02;
const moduleW = (contentW - 5 * gap) / 6;
const portrait = H > W;
const sheetTop = Math.round(H * (portrait ? 0.24 : 0.36));
const baseline = H - Math.round(M * 1.8);
const maxBarH = (baseline - sheetTop) * 0.66;
const levelY = h => baseline - (h / HMAX) * maxBarH;

// ---- type -------------------------------------------------------------------
function fitSize(text, maxW, start, weight) {
  let s = start;
  for (let i = 0; i < 60 && s > 8; i++) {
    ctx.letterSpacing = '0px';
    ctx.font = `${weight} ${Math.round(s)}px "Clip Sans"`;
    if (ctx.measureText(text).width <= maxW) break;
    s *= 0.94;
  }
  return s;
}
function setFont(weight, size) {
  ctx.font = `${weight} ${Math.round(size)}px "Clip Sans"`;
  ctx.letterSpacing = size >= 90 ? `${(-size * 0.022).toFixed(1)}px` : '0px';
}
// a run of text wiped in from below the baseline (p: 0→1), never a fade
function reveal(text, x, y, size, weight, p, color = C.ink) {
  if (p <= 0) return;
  setFont(weight, size);
  ctx.fillStyle = color;
  const w = ctx.measureText(text).width + size * 0.12;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x - 2, y - size * 1.04, w + 4, size * 1.34);
  ctx.clip();
  ctx.fillText(text, x, y + (1 - p) * size * 1.06);
  ctx.restore();
}
function headLayout() {
  const captionBase = M * 1.5;
  const sizeW = fitSize(HEAD[1], contentW, H * 0.3, 800);
  const sizeV = (sheetTop - captionBase - M * 0.5) / 2;   // clears the caption and the sheet
  const size = Math.min(H * (portrait ? 0.10 : 0.135), sizeW, sizeV);
  const baseTop = captionBase + size * 0.95;
  const lines = HEAD.map((text, i) => ({ text, baseline: baseTop + i * size * 1.02 }));
  return { size, lines, top: baseTop - size * 0.8, bottom: sheetTop - M * 0.15 };
}

// ---- timeline: 120 bpm, a beat every 0.5 s ----------------------------------
const T_GRID = 0.5, T_HEAD = 0.75, T_CAP = 1.5;
const T_MOD0 = 2.0, MOD_D = 0.45;
const T_EXIT = 5.0, T_OUT = 0.55;   // the break lands on the tenth beat
const arrival = i => T_MOD0 + i * MOD_D;

// the one exception element: the tide line moves linearly, off the beat, and
// pauses on each slack reading.
function waterLevel(t) {
  let h = 0;
  for (let i = 0; i < READINGS.length; i++) {
    const a = arrival(i);
    h = lerp(h, READINGS[i].m, lin(t, a - E8 * 1.6, a));
  }
  return h;
}

// ---- drawing ----------------------------------------------------------------
function drawSheet(t) {
  const p = snap(t, T_GRID + E16, E8);
  if (p <= 0) return;
  ctx.fillStyle = C.sheet;
  ctx.fillRect(0, lerp(sheetTop + H * 0.2, sheetTop, p), W, H);
}

function drawGrid(t) {
  ctx.lineWidth = 1;
  const hp = snap(t, T_GRID + E16 * 2, E8);         // metre levels, drawn first and palest
  ctx.strokeStyle = C.level;
  ctx.beginPath();
  for (let lv = 1; lv <= 4; lv++) {
    const y = Math.round(levelY(lv)) + 0.5;
    ctx.moveTo(M, y);
    ctx.lineTo(M + contentW * hp, y);
  }
  ctx.stroke();
  ctx.strokeStyle = C.grid;
  ctx.beginPath();
  for (let k = 0; k <= 6; k++) {                     // the six modules' columns
    const x = Math.round(M + k * (moduleW + gap)) + 0.5;
    const p = snap(t, T_GRID + k * E16 * 2 + E16, E16);
    if (p > 0) { ctx.moveTo(x, sheetTop); ctx.lineTo(x, lerp(sheetTop, baseline, p)); }
  }
  const p = snap(t, T_GRID + E16 * 3, E8);          // the water-level axis
  ctx.moveTo(M, baseline + 0.5);
  ctx.lineTo(M + contentW * p, baseline + 0.5);
  ctx.stroke();
}

function drawHeadline(t) {
  const { size, lines } = headLayout();
  lines.forEach((line, i) => {
    reveal(line.text, M, line.baseline, size, 800, snap(t, T_HEAD + i * E8 + E16, E16));
  });
  const p = snap(t, T_CAP, E8);
  setFont(500, M * 0.34);
  ctx.fillStyle = C.ink;
  ctx.fillRect(M, M * 0.9, contentW * p, 1);
  reveal(CAPTION, M, M * 1.5, M * 0.34, 500, p);
  const cw = ctx.measureText(COUNTER).width;
  reveal(COUNTER, W - M - cw, M * 1.5, M * 0.34, 500, snap(t, T_CAP + E8, E8), C.mute);
}

function drawModules(t) {
  for (let i = 0; i < READINGS.length; i++) {
    const pin = snap(t, arrival(i), E16);
    if (pin <= 0) continue;
    const x = M + i * (moduleW + gap);
    const y = levelY(READINGS[i].m);
    // the module: a plain grey block, wiped up from the axis
    ctx.fillStyle = C.soft;
    ctx.fillRect(x, y, moduleW, (baseline - y) * pin);
    // the reading above the block, the time below the axis
    reveal(`${READINGS[i].m.toFixed(1)} m`, x, y - moduleW * 0.12, moduleW * 0.19, 500, pin, C.mute);
    reveal(READINGS[i].at, x, baseline + M * 1.15, moduleW * 0.30, 700, pin);
  }
}

function drawTideLine(t) {
  const p0 = snap(t, T_GRID + E16, E8);             // enters along the axis
  if (p0 <= 0) return;
  const th = Math.max(3, Math.round(W / 480));
  const y = levelY(waterLevel(t));
  ctx.fillStyle = C.red;
  if (t < T_EXIT) {
    ctx.fillRect(M, y, (W - M) * p0 - M, th);
  } else {
    // the deliberate break: the signal line leaves the page
    const shift = lin(t, T_EXIT, T_EXIT + T_OUT) * (W * 1.25);
    ctx.fillRect(M + shift, y, contentW, th);
  }
}

function draw(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic';

  ctx.fillStyle = C.page;
  ctx.fillRect(0, 0, W, H);

  drawSheet(t);
  drawGrid(t);
  drawHeadline(t);
  drawModules(t);
  drawTideLine(t);
}

window.render = t => draw(clamp(t, 0, window.DUR));

// text the viewer must read: the headline holds; the timetable ticks are scanned
window.TEXTS = () => {
  const head = headLayout();
  const out = [{
    id: 'head', text: HEAD.join(' '),
    x0: M, y0: head.top, x1: M + contentW * 0.7, y1: head.bottom,
  }];
  for (let i = 0; i < READINGS.length; i++) {
    const x = M + i * (moduleW + gap);
    out.push({
      id: `r${i}`, text: `${READINGS[i].at} ${READINGS[i].m.toFixed(1)} m`,
      x0: x, y0: baseline, x1: x + moduleW, y1: H, pass: true,
    });
  }
  return out;
};

try {
  await Promise.all([300, 500, 700, 800].map(w =>
    document.fonts.load(`${w} 100px "Clip Sans"`, 'TIDE TIMETABLE 0123456789:.')));
} catch (e) {}
await document.fonts.ready;

draw(0);
window.READY = true;
