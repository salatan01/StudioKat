// Teardown sample — "Field Lamp FL-1".
//
// The lamp hangs in a clean void. Its six illustrated layers — shell, diffuser,
// driver board, cell ×2, bracket ×2, M3 bolt ×4 — lift along ONE axis in the
// order the parts spec lists, each on its own short eased move, and settle as a
// labelled stack that holds for the last beat. The accent marks the active
// layer and nothing else. Every label carries the word "illustrative" and no
// dimension, tolerance or unit is drawn: the spec is illustrative.
//
// This style ships no vendored scene (its folder is empty) and no face. The
// clip is authored from the shared helpers only, and the labels are set in the
// system's technical monospace — no webfont is fetched.
//
// Deterministic: every value derives from `t` or a fixed seed (mulberry). The
// geometry is built once; the frame redraws it at the current progress. No
// Math.random, no Date.now.

import { clamp, lerp, seg, ss, eio, mulberry, TAU } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

// The render server sizes the viewport to --size, so window.innerWidth/Height
// give the real frame; clip.json's width/height is the native authoring
// fallback only. The whole layout keys off W and H, never off clip.json's size.
let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = Math.round(window.innerWidth || (META.width | 0) || canvas.width);
const H = Math.round(window.innerHeight || (META.height | 0) || canvas.height);
canvas.width = W;
canvas.height = H;

window.DUR = 6;

const portrait = H > W;
const cx = W / 2, cy = H / 2;

// The explode axis runs left→right in 16:9 and top→bottom in 9:16.
const axisLen = portrait ? H : W;        // length along the explode axis
const acrossLen = portrait ? W : H;      // length perpendicular to it
const acrossCenter = portrait ? 0.38 * W : 0.5 * H;   // 9:16 leaves the right for labels
const gapStep = (portrait ? 0.135 : 0.115) * axisLen;

// ---- palette: one graphite line, one light metal, one shadow metal, one accent
const VOID = '#f4f5f7';
const LINE = '#2b2b2e';       // graphite line colour
const LIT = '#d9dce1';        // light metal (lit face)
const SHADOW = '#a7adb6';     // shadow metal (shadow face / cut edge)
const ACCENT = '#e2621b';     // the one accent — the active layer only
const ACCENT_D = '#a8440f';   // the active layer's shadow face (same hue)

// ---- the parts spec: read it, never invent a part ----------------------------
// The labels (name + count) come straight from parts_spec.json; the fallback
// mirrors that file exactly so the page still reads if the fetch is blocked.
let SPEC = null;
try { SPEC = await (await fetch('parts_spec.json')).json(); } catch {}
const RAW = (SPEC && Array.isArray(SPEC.parts) && SPEC.parts.length) ? SPEC.parts : [
  { id: 'shell', name: 'shell', layer: 0, count: 1 },
  { id: 'diffuser', name: 'diffuser', layer: 1, count: 1 },
  { id: 'board', name: 'driver board', layer: 2, count: 1 },
  { id: 'cell', name: 'cell', layer: 3, count: 2 },
  { id: 'bracket', name: 'bracket', layer: 4, count: 2 },
  { id: 'bolt', name: 'M3 bolt', layer: 5, count: 4 },
];
const PRODUCT = (SPEC && SPEC.product) || 'Field Lamp FL-1';

// Geometry per part kind: th = full thickness along the axis (fraction of the
// axis length), half = half-extent across it (fraction of the across length).
const GEOM = {
  shell:    { th: 0.052, half: { land: 0.270, port: 0.215 }, kind: 'shell' },
  diffuser: { th: 0.022, half: { land: 0.240, port: 0.190 }, kind: 'diffuser' },
  board:    { th: 0.016, half: { land: 0.205, port: 0.170 }, kind: 'board' },
  cell:     { th: 0.038, half: { land: 0.175, port: 0.150 }, kind: 'cell' },
  bracket:  { th: 0.014, half: { land: 0.245, port: 0.205 }, kind: 'bracket' },
  bolt:     { th: 0.013, half: { land: 0.105, port: 0.090 }, kind: 'bolt' },
};
const DEFAULT_G = { th: 0.016, half: { land: 0.180, port: 0.150 }, kind: 'shell' };

const SORTED = [...RAW].sort((a, b) => a.layer - b.layer);
const N = SORTED.length;
const KEY = Math.max(0, SORTED.findIndex(p => p.id === 'board'));  // the key layer

const parts = SORTED.map((raw, i) => {
  const g = GEOM[raw.id] || DEFAULT_G;
  const thPx = g.th * axisLen;
  const halfPx = (portrait ? g.half.port : g.half.land) * acrossLen;
  const exA = axisLen * 0.5 + (i - (N - 1) / 2) * gapStep;   // exploded along-centre
  const cnt = raw.count > 1 ? ` \u00d7${raw.count}` : '';
  return {
    id: raw.id, count: raw.count, layer: i, kind: g.kind,
    thPx, halfPx, exA, bC: acrossCenter,
    txt: `${String(raw.name).toUpperCase()}${cnt} \u00b7 ILLUSTRATIVE`,
  };
});

// Assembled state: the plates are butted edge to edge into one solid.
{
  let sum = 0;
  for (const p of parts) sum += p.thPx;
  let cur = axisLen * 0.5 - sum / 2;
  for (const p of parts) { p.asA = cur + p.thPx / 2; cur += p.thPx; }
}

// ---- the explode: one short eased move per layer, in order -------------------
const START = 0.55, STAGGER = 0.34, MOVE = 0.62;
const prog = (i, t) => eio(seg(t, START + i * STAGGER, START + i * STAGGER + MOVE));
for (let i = 0; i < N; i++) parts[i].reveal = START + i * STAGGER + MOVE - 0.12;

// The active layer: the one still in motion, or — once the stack has settled —
// the key layer (the driver board). It is the only plate that takes the accent.
function activeIdx(t) {
  if (t < 0.45) return -1;                 // nothing active yet
  let cur = -1;
  for (let i = 0; i < N; i++) { const p = prog(i, t); if (p > 0.03 && p < 0.985) cur = i; }
  if (cur < 0 && t >= START) cur = KEY;
  return cur;
}

// ---- camera: a slow push-in that settles as the stack opens ------------------
const camScale = t => 1 + 0.05 * ss(seg(t, 0.2, 4.8));
const camPt = (x, y, s) => [cx + (x - cx) * s, cy + (y - cy) * s];
function applyCam(t) {
  const s = camScale(t);
  ctx.translate(cx, cy); ctx.scale(s, s); ctx.translate(-cx, -cy);
}

// ---- small drawing helpers ---------------------------------------------------
// Along/across → screen. 16:9: along→x, across→y. 9:16: along→y, across→x.
const P = (a, b) => (portrait ? [b, a] : [a, b]);

function roundRect(x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
// A plate centred at (a,b): t = half-thickness along the axis, h = half-extent across.
function plate(a, b, t, h, fill, stroke, lw) {
  const c = P(a, b);
  const wp = portrait ? 2 * h : 2 * t;
  const hp = portrait ? 2 * t : 2 * h;
  roundRect(c[0] - wp / 2, c[1] - hp / 2, wp, hp, Math.min(wp, hp) * 0.2);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke !== false) { ctx.strokeStyle = stroke || LINE; ctx.lineWidth = lw || 2; ctx.stroke(); }
}
function ln(a1, b1, a2, b2, col, lw, dash) {
  const p1 = P(a1, b1), p2 = P(a2, b2);
  ctx.beginPath(); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]);
  ctx.strokeStyle = col; ctx.lineWidth = lw || 1.5;
  ctx.setLineDash(dash || []); ctx.stroke(); ctx.setLineDash([]);
}
function dot(a, b, r, col) {
  const p = P(a, b);
  ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, TAU); ctx.fillStyle = col; ctx.fill();
}
function hex(a, b, r, fill) {
  const p = P(a, b);
  ctx.beginPath();
  for (let k = 0; k < 6; k++) {
    const ang = k / 6 * TAU + Math.PI / 6;
    const x = p[0] + Math.cos(ang) * r, y = p[1] + Math.sin(ang) * r;
    k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  }
  ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
}

// one plate's own detail: traces, frosted lines, cells, brackets, bolts
function detail(p, a, b, t, h, ink) {
  switch (p.kind) {
    case 'shell':
      plate(a, b, t * 0.62, h * 0.80, null, ink, 1.6);
      ln(a - t * 0.5, b - h * 0.42, a - t * 0.5, b + h * 0.42, ink, 1.3);
      break;
    case 'diffuser': {
      const n = portrait ? 5 : 4;
      for (let k = 1; k < n; k++) { const aa = a - t + 2 * t * k / n; ln(aa, b - h * 0.86, aa, b + h * 0.86, ink, 1.2); }
      break;
    }
    case 'board':
      plate(a, b, t * 0.50, h * 0.28, ink, false);            // chip
      ln(a, b - h * 0.62, a, b + h * 0.62, ink, 1.2);         // bus trace
      for (let k = 0; k < 3; k++) plate(a, b + (k - 1) * h * 0.42, t * 0.40, h * 0.10, ink, false);
      break;
    case 'cell':
      for (let k = 0; k < 2; k++) {
        const bb = b + (k - 0.5) * h * 0.62;
        plate(a, bb, t * 0.82, h * 0.26, null, ink, 1.6);
        ln(a - t * 0.30, bb, a + t * 0.30, bb, ink, 1.3);
      }
      break;
    case 'bracket':
      for (let k = 0; k < 2; k++) {
        const bb = b + (k ? h * 0.62 : -h * 0.62);
        ln(a - t * 0.7, bb, a + t * 0.5, bb, ink, 2);
        ln(a + t * 0.5, bb, a + t * 0.5, bb + (k ? -1 : 1) * h * 0.14, ink, 2);
      }
      break;
    case 'bolt': {
      const r = Math.min(t * 0.7, h * 0.26);
      for (let k = 0; k < 4; k++) hex(a, b + (k - 1.5) * h * 0.5, r, ink);
      break;
    }
  }
}

function drawPart(p, i, t) {
  const acc = i === activeIdx(t);
  const a = lerp(p.asA, p.exA, prog(i, t));
  const tHalf = p.thPx / 2, h = p.halfPx;
  // shadow slab offset down-right gives the plate its cut edge and thickness
  plate(a + tHalf * 0.5, p.bC + h * 0.12, tHalf, h, acc ? ACCENT_D : SHADOW, LINE, 1.6);
  // lit face
  plate(a, p.bC, tHalf, h, acc ? ACCENT : LIT, LINE, 2);
  // detail ink reads on either fill
  detail(p, a, p.bC, tHalf, h, acc ? '#3a1c07' : LINE);
}

// ---- labels: short noun + count, on a leader line, always "illustrative" -----
const fs = portrait ? Math.round(0.0204 * Math.min(W, H)) : Math.round(0.0241 * Math.min(W, H));
const fsTitle = portrait ? Math.round(0.026 * Math.min(W, H)) : Math.round(0.028 * Math.min(W, H));
const FONT = px => `${px}px ui-monospace, "SFMono-Regular", Menlo, Consolas, "DejaVu Sans Mono", monospace`;
const TITLE = `${PRODUCT.toUpperCase()} \u00b7 ILLUSTRATIVE`;
const titleAnchor = portrait ? { x: 0.06 * W, y: 0.055 * H } : { x: 0.055 * W, y: 0.085 * H };
const TITLE_T0 = 0.35;

function measure(txt, px) { ctx.save(); ctx.font = FONT(px); const w = ctx.measureText(txt).width; ctx.restore(); return w; }

// every label's screen box, in the layout's own unscaled coordinates
function labelBox(p, i) {
  const w = measure(p.txt, fs);
  if (portrait) return [0.63 * W, p.exA - fs * 0.78, 0.63 * W + w, p.exA + fs * 0.78];
  const above = (i % 2 === 0), y = (above ? 0.135 : 0.895) * H;
  return [p.exA - w / 2, y - fs * 0.78, p.exA + w / 2, y + fs * 0.78];
}

function drawLabel(p, i, t) {
  const rev = p.reveal, alpha = clamp(seg(t, rev - 0.18, rev));
  if (alpha <= 0) return;
  const acc = i === activeIdx(t);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.font = FONT(fs);
  ctx.textBaseline = 'middle';
  ctx.fillStyle = acc ? ACCENT : LINE;
  ctx.strokeStyle = acc ? ACCENT : LINE;
  ctx.lineWidth = 1.6;
  if (portrait) {
    const lx = 0.63 * W;
    ln(p.bC + p.halfPx + 6, p.exA, lx - 8, p.exA, LINE, 1.4);   // leader to the plate
    dot(p.bC + p.halfPx + 6, p.exA, 2.4, LINE);
    ctx.textAlign = 'left';
    ctx.fillText(p.txt, lx, p.exA);
  } else {
    const above = (i % 2 === 0);
    const y = (above ? 0.135 : 0.895) * H;
    const yTo = above ? p.bC - p.halfPx - 8 : p.bC + p.halfPx + 8;
    ln(p.exA, y, p.exA, yTo, LINE, 1.4);                        // leader to the plate
    dot(p.exA, yTo, 2.4, LINE);
    ctx.textAlign = 'center';
    ctx.fillText(p.txt, p.exA, y);
  }
  ctx.restore();
}

function drawTitle(t) {
  const alpha = clamp(seg(t, 0, TITLE_T0));
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.font = FONT(fsTitle);
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = LINE;
  ctx.fillText(TITLE, titleAnchor.x, titleAnchor.y);
  ctx.restore();
}

// ---- background: flat void, a faint dot field, a soft vignette ---------------
const bgCv = document.createElement('canvas'); bgCv.width = W; bgCv.height = H;
(function buildVoid() {
  const g = bgCv.getContext('2d');
  g.fillStyle = VOID; g.fillRect(0, 0, W, H);
  const R = mulberry(71);
  const step = Math.round(Math.min(W, H) / 18);
  g.fillStyle = 'rgba(43,43,46,0.06)';
  for (let y = step / 2; y < H; y += step) {
    for (let x = step / 2; x < W; x += step) {
      const jx = (R() - 0.5) * step * 0.25, jy = (R() - 0.5) * step * 0.25;
      g.beginPath(); g.arc(x + jx, y + jy, 1.1, 0, TAU); g.fill();
    }
  }
})();
function drawBg() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  ctx.fillStyle = VOID; ctx.fillRect(0, 0, W, H);
  ctx.drawImage(bgCv, 0, 0);
  const vg = ctx.createRadialGradient(cx, cy, Math.min(W, H) * 0.12, cx, cy, Math.max(W, H) * 0.74);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, 'rgba(30,34,40,0.10)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
}

// the shared axis the layers lift along — a faint dashed line, not a decoration
function drawAxis() {
  const a0 = Math.min(...parts.map(p => p.exA)) - 10;
  const a1 = Math.max(...parts.map(p => p.exA)) + 10;
  ln(a0, acrossCenter, a1, acrossCenter, 'rgba(43,43,46,0.26)', 2, [10, 12]);
}

// ---- frame -------------------------------------------------------------------
function draw(t) {
  t = clamp(t, 0, window.DUR);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.filter = 'none'; ctx.lineJoin = 'round'; ctx.lineCap = 'round';

  drawBg();

  ctx.save();
  applyCam(t);
  drawAxis();
  for (let i = 0; i < N; i++) drawPart(parts[i], i, t);
  for (let i = 0; i < N; i++) drawLabel(parts[i], i, t);
  drawTitle(t);
  ctx.restore();
}

window.render = t => draw(t);

// text the viewer must read, with screen boxes (camera applied, so the box is
// where the text actually lands). The title plus every part label, revealed
// once its layer has settled and held to the end.
window.TEXTS = t => {
  t = clamp(t, 0, window.DUR);
  const s = camScale(t);
  const out = [];
  if (t >= TITLE_T0) {
    const w = measure(TITLE, fsTitle);
    const b = [titleAnchor.x, titleAnchor.y - fsTitle * 0.78, titleAnchor.x + w, titleAnchor.y + fsTitle * 0.78];
    const p0 = camPt(b[0], b[1], s), p1 = camPt(b[2], b[3], s);
    out.push({ id: 'title', text: TITLE, x0: p0[0], y0: p0[1], x1: p1[0], y1: p1[1] });
  }
  for (let i = 0; i < N; i++) {
    const p = parts[i];
    if (t < p.reveal) continue;
    const b = labelBox(p, i);
    const p0 = camPt(b[0], b[1], s), p1 = camPt(b[2], b[3], s);
    out.push({ id: `part-${p.id}`, text: p.txt, x0: p0[0], y0: p0[1], x1: p1[0], y1: p1[1] });
  }
  return out;
};

// no face is drawn, so nothing is fetched; still wait for the document's fonts
// before declaring ready, and never swallow a rejection.
await document.fonts.ready;

draw(0);
window.READY = true;
