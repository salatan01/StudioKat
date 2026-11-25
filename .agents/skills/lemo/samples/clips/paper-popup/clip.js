// Paper Pop-up sample — "A lighthouse opens".
//
// A closed book sits on a warm desk. Its board cover swings open and back to
// stand as the backdrop; out of the spread a paper lighthouse and a layered
// paper sea spring up, each cut-out carrying a cream border, a cardboard edge
// and a real cast shadow. A macro lens pushes in across the six seconds.
//
// Original StudioKat clip. The vendored demo is a Three.js/WebGL paper-book
// adventure; it is not vendored as a drawing engine, so this clip is a bespoke
// Canvas-2D 2.5D pop-up — the book, the cover hinge, the folded sets, the
// paper grain and the drop shadows are all drawn here.
//
// Deterministic: every value derives from `t` or a fixed seed (mulberry /
// vnoise from /core/lib.js). No Math.random, no Date.now.

import { mulberry, clamp, lerp, seg, ss, eio, spring, vnoise } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

// The render server sizes the viewport to --size, so window.innerWidth/Height
// give 1920x1080 or 1080x1920; clip.json is only a fallback.
let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = window.innerWidth || (META.width | 0) || 1920;
const H = window.innerHeight || (META.height | 0) || 1080;
canvas.width = W;
canvas.height = H;

window.DUR = 6;

const portrait = H > W;
const cx = W / 2;

// ---- palette: warm paper, kraft card, one red-and-cream lighthouse ---------
const C = {
  bgHi: '#3c2a1c', bgLo: '#150e0a',
  paperA: '#f8f0de', paperB: '#eee1c5', paperC: '#e5d4b3',
  pageEdge: '#cdb38c', gutter: '#b19a76',
  coverOut: '#8c5836', coverOutD: '#6c4226', coverOutHi: '#a06a44',
  coverIn: '#f1e5ca', board: '#5a361f',
  cream: '#fdf8ec', card: '#cdb691', ink: '#392a22',
  sea: ['#9cc6d6', '#6fa5bf', '#4d87a7'],
  foam: '#f6f1e3', rock: '#cdbb9e',
  stripeA: '#d4584a', stripeB: '#f3e7cf', stripeD: '#b04237',
  lamp: '#ffcf6f', beam: '#ffe3a2',
};

function mixc(a, b, t) {
  const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
  const r = Math.round(lerp((pa >> 16) & 255, (pb >> 16) & 255, t));
  const g = Math.round(lerp((pa >> 8) & 255, (pb >> 8) & 255, t));
  const bl = Math.round(lerp(pa & 255, pb & 255, t));
  return `rgb(${r},${g},${bl})`;
}

// ---- the book's layout, per aspect ----------------------------------------
const L = portrait ? {
  spineY: 0.46 * H, nearY: 0.93 * H,
  backHalf: 0.33 * W, foreHalf: 0.42 * W,
  coverH: 0.34 * H,
  baseY: 0.61 * H, seaY: 0.72 * H,
  lightBase: { x: 0.55 * W, y: 0.62 * H }, towerTop: 0.22 * H,
  title: { x: 0.32 * W, y: 0.665 * H, size: 0.026 * H },
} : {
  spineY: 0.58 * H, nearY: 0.95 * H,
  backHalf: 0.33 * W, foreHalf: 0.42 * W,
  coverH: 0.40 * H,
  baseY: 0.70 * H, seaY: 0.795 * H,
  lightBase: { x: 0.585 * W, y: 0.72 * H }, towerTop: 0.17 * H,
  title: { x: 0.30 * W, y: 0.685 * H, size: 0.050 * H },
};

// ---- macro camera: one slow push-in across the whole clip ------------------
const focus = portrait ? { x: 0.52 * W, y: 0.46 * H } : { x: 0.55 * W, y: 0.44 * H };
const camZ = t => 1 + 0.20 * ss(seg(t, 0, 6));
// Each layer has a depth (0 far .. 1 focal); it scales less when it is deeper,
// which is the slight parallax that makes the paper read as stacked cut-outs.
function camPt(t, x, y, depth) {
  const zd = 1 + (camZ(t) - 1) * depth;
  return { x: focus.x + (x - focus.x) * zd, y: focus.y + (y - focus.y) * zd };
}
function withCam(t, depth, fn) {
  const zd = 1 + (camZ(t) - 1) * depth;
  ctx.save();
  ctx.translate(focus.x, focus.y);
  ctx.scale(zd, zd);
  ctx.translate(-focus.x, -focus.y);
  fn();
  ctx.restore();
}
const BOOK_DEPTH = 0.7, SEA_DEPTH = 0.92, TOWER_DEPTH = 1.05;

// ---- paper grain: one seeded tile, overlaid at the end ---------------------
const grain = (() => {
  const g = document.createElement('canvas'); g.width = g.height = 128;
  const gc = g.getContext('2d'), img = gc.createImageData(128, 128), d = img.data;
  const R = mulberry(1129);
  for (let i = 0; i < 128 * 128; i++) {
    const c = R() < 0.5 ? 0 : 255;
    d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = c;
    d[i * 4 + 3] = Math.floor(6 + R() * 16);
  }
  gc.putImageData(img, 0, 0);
  return g;
})();
let grainPat = null;

// ---- small drawing helpers -------------------------------------------------
function quad(pts, fill) {
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
}
function tri(a, b, c, fill) { quad([a, b, c], fill); }

// ---- the book: spread pages, gutter, fore-edge, hinge shadow ---------------
function pagePoly(side) {
  return [
    { x: cx, y: L.spineY },
    { x: cx + side * L.backHalf, y: L.spineY },
    { x: cx + side * L.foreHalf, y: L.nearY },
    { x: cx, y: L.nearY },
  ];
}
function drawPage(side) {
  const [innerB, outerB, outerN, innerN] = pagePoly(side);
  const grad = ctx.createLinearGradient(cx, L.spineY, outerB.x, L.nearY);
  grad.addColorStop(0, C.paperB);
  grad.addColorStop(0.35, C.paperA);
  grad.addColorStop(1, C.paperC);
  quad([innerB, outerB, outerN, innerN], grad);
  // fore-edge: the stacked page block, a few thin kraft lines near the edge
  ctx.strokeStyle = C.pageEdge;
  ctx.lineWidth = 1.6;
  for (let i = 1; i <= 3; i++) {
    ctx.globalAlpha = 0.5 - i * 0.11;
    ctx.beginPath();
    ctx.moveTo(outerN.x + side * i * 3, outerN.y + i * 3);
    ctx.lineTo(innerN.x, innerN.y + i * 3);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}
function drawBook(t) {
  // soft grounding shadow beneath the whole spread
  ctx.save();
  ctx.globalAlpha = 0.5;
  ctx.fillStyle = C.bgLo;
  ctx.beginPath();
  ctx.ellipse(cx, L.nearY - 6, L.foreHalf * 1.02, 40, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  drawPage(-1);
  drawPage(1);
  drawCover(t);

  // spine: a darker kraft gutter band at the hinge
  const g = ctx.createLinearGradient(0, L.spineY - 14, 0, L.spineY + 26);
  g.addColorStop(0, 'rgba(90,54,31,0)');
  g.addColorStop(0.5, 'rgba(90,54,31,0.55)');
  g.addColorStop(1, 'rgba(90,54,31,0)');
  ctx.fillStyle = g;
  ctx.fillRect(cx - L.backHalf - 4, L.spineY - 14, (L.backHalf + 4) * 2, 40);
}

// ---- the board cover: closed over the spread, then up as the backdrop ------
function drawCover(t) {
  const open = eio(seg(t, 0.15, 1.40));      // 0 closed -> 1 standing
  const hingeY = L.spineY;
  const freeY = lerp(L.nearY, L.spineY - L.coverH, open);
  const hw = lerp(L.foreHalf, L.backHalf * 0.97, open);

  const hingeLo = { x: cx - L.backHalf * 0.98, y: hingeY };
  const hingeHi = { x: cx + L.backHalf * 0.98, y: hingeY };
  const freeLo = { x: cx - hw, y: freeY };
  const freeHi = { x: cx + hw, y: freeY };
  const board = [hingeLo, hingeHi, freeHi, freeLo];

  // cover's own cast shadow onto the spread while it is lifting
  if (open < 0.98) {
    ctx.save();
    ctx.globalAlpha = 0.22 * (1 - ss(open));
    ctx.fillStyle = C.bgLo;
    quad([hingeLo, hingeHi, { x: freeHi.x, y: freeHi.y + 26 }, { x: freeLo.x, y: freeLo.y + 26 }], C.bgLo);
    ctx.restore();
  }

  // the outside is warm leather; once it stands past 90 deg we see its cream inside
  const inside = ss(seg(open, 0.32, 0.78));
  const face = mixc(C.coverOut, C.coverIn, inside);
  const grad = ctx.createLinearGradient(0, hingeY, 0, freeY);
  grad.addColorStop(0, mixc(C.coverOutD, C.coverIn, inside));
  grad.addColorStop(0.5, face);
  grad.addColorStop(1, mixc(C.coverOutHi, C.coverIn, inside));
  quad(board, grad);

  // a leather sheen while we still look at the outside
  if (inside < 0.9) {
    ctx.save();
    ctx.globalAlpha = 0.28 * (1 - inside);
    const sheen = ctx.createLinearGradient(hingeLo.x, hingeY, hingeHi.x, freeY);
    sheen.addColorStop(0, 'rgba(255,235,200,0)');
    sheen.addColorStop(0.45, 'rgba(255,235,200,0.5)');
    sheen.addColorStop(1, 'rgba(255,235,200,0)');
    quad(board, sheen);
    ctx.restore();
  }

  // board thickness along the free edge + a faint cut line around the cover
  ctx.lineJoin = 'round';
  ctx.strokeStyle = C.board;
  ctx.lineWidth = 7;
  ctx.beginPath(); ctx.moveTo(freeLo.x, freeLo.y); ctx.lineTo(freeHi.x, freeHi.y); ctx.stroke();
  ctx.strokeStyle = 'rgba(60,36,20,0.5)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(board[0].x, board[0].y);
  for (let i = 1; i < board.length; i++) ctx.lineTo(board[i].x, board[i].y);
  ctx.closePath();
  ctx.stroke();

  // a printed rule on the inside of the cover, part of the title page
  if (inside > 0.5) {
    ctx.save();
    ctx.globalAlpha = (inside - 0.5) * 1.6;
    ctx.strokeStyle = 'rgba(90,54,31,0.45)';
    ctx.lineWidth = 2;
    const ry = hingeY - L.coverH * 0.16;
    ctx.beginPath(); ctx.moveTo(cx - hw * 0.55, ry); ctx.lineTo(cx + hw * 0.55, ry); ctx.stroke();
    ctx.restore();
  }
}

// ---- the sea: layered paper waves that roll up out of the spread -----------
function wavePath(x0, x1, ybase, amp, phase, t, H2) {
  ctx.beginPath();
  ctx.moveTo(x0, ybase);
  const n = 60;
  for (let i = 0; i <= n; i++) {
    const f = i / n, x = lerp(x0, x1, f);
    const ripple = 0.55 + 0.45 * Math.sin(f * 17 + phase * 3.1);
    const y = ybase - amp * Math.sin(f * Math.PI * 2.4 + phase + t * 0.5) * ripple;
    ctx.lineTo(x, y);
  }
  ctx.lineTo(x1, ybase + H2);
  ctx.lineTo(x0, ybase + H2);
  ctx.closePath();
}
function drawSea(t) {
  const p = clamp(spring(seg(t, 1.12, 2.75), 7, 0.42), 0, 1.06);
  if (p <= 0.001) return;
  const span = L.foreHalf * 0.96;
  for (let layer = 0; layer < 3; layer++) {
    const rise = (1 - p) * 0.20 * H;       // starts low, rolls up
    const y = L.seaY + layer * 0.045 * H + rise;
    const x0 = cx - span + layer * 18, x1 = cx + span - layer * 18;
    const amp = (14 + layer * 6) * (0.5 + 0.5 * p);
    const phase = vnoise(layer * 4.7 + 1.3) * 6.28 + layer;
    // cast shadow on the page under the crest
    ctx.save();
    ctx.globalAlpha = 0.14 * p;
    ctx.fillStyle = C.bgLo;
    wavePath(x0 + 6, x1 + 6, y + 16, amp, phase, t, 0.3 * H);
    ctx.fill();
    ctx.restore();
    // the folded strip, shaded lit-side to shadow-side
    const g = ctx.createLinearGradient(0, y - amp, 0, y + 0.12 * H);
    g.addColorStop(0, mixc(C.sea[layer], C.foam, 0.35));
    g.addColorStop(1, C.sea[Math.min(2, layer + 1)]);
    wavePath(x0, x1, y, amp, phase, t, 0.3 * H);
    ctx.fillStyle = g;
    ctx.fill();
    // cream cut edge along the crest
    ctx.save();
    ctx.lineWidth = 6;
    ctx.strokeStyle = C.foam;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    const n = 60;
    for (let i = 0; i <= n; i++) {
      const f = i / n, x = lerp(x0, x1, f);
      const ripple = 0.55 + 0.45 * Math.sin(f * 17 + phase * 3.1);
      const yy = y - amp * Math.sin(f * Math.PI * 2.4 + phase + t * 0.5) * ripple;
      i ? ctx.lineTo(x, yy) : ctx.moveTo(x, yy);
    }
    ctx.stroke();
    ctx.restore();
  }
}

// ---- the lighthouse: striped tower, lamp room, sweeping beam ---------------
function towerP(t) {
  // one spring rise per piece: overshoot past 1, then settle — paper weight
  return clamp(spring(seg(t, 1.55, 3.05), 8, 0.34), 0, 1.08);
}
function drawLighthouse(t) {
  const p = towerP(t);
  if (p <= 0.001) return;
  const bx = L.lightBase.x, by = L.lightBase.y;
  const h = (by - L.towerTop) * p;
  const top = by - h;
  const wb = (portrait ? 0.075 : 0.052) * Math.min(W, H);
  const wt = wb * 0.62;

  const bL = { x: bx - wb, y: by }, bR = { x: bx + wb, y: by };
  const tL = { x: bx - wt, y: top }, tR = { x: bx + wt, y: top };

  // rock / paper base plate
  ctx.save();
  ctx.globalAlpha = 0.5 * p;
  ctx.fillStyle = C.bgLo;
  ctx.beginPath(); ctx.ellipse(bx + 8, by + 10, wb * 1.7, 12, 0, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
  ctx.beginPath();
  ctx.moveTo(bL.x - wb * 0.5, by + 6);
  ctx.lineTo(bx - wb * 1.25, by - 4);
  ctx.lineTo(bx - wb * 0.4, by - 14);
  ctx.lineTo(bx + wb * 0.55, by - 12);
  ctx.lineTo(bx + wb * 1.3, by + 2);
  ctx.lineTo(bR.x + wb * 0.4, by + 8);
  ctx.closePath();
  ctx.fillStyle = C.rock; ctx.fill();
  ctx.strokeStyle = C.cream; ctx.lineWidth = 5; ctx.lineJoin = 'round'; ctx.stroke();

  // tower: cast shadow, cardboard edge, cream cut border, then stripes
  const tower = () => {
    ctx.beginPath();
    ctx.moveTo(bL.x, bL.y); ctx.lineTo(tL.x, tL.y); ctx.lineTo(tR.x, tR.y);
    ctx.lineTo(bR.x, bR.y); ctx.closePath();
  };
  ctx.save();
  ctx.globalAlpha = 0.22 * p;
  ctx.translate(10, 8);
  tower(); ctx.fillStyle = C.bgLo; ctx.fill();
  ctx.restore();

  ctx.lineJoin = 'round';
  tower(); ctx.strokeStyle = C.card; ctx.lineWidth = 16; ctx.stroke();
  tower(); ctx.strokeStyle = C.cream; ctx.lineWidth = 10; ctx.stroke();

  ctx.save();
  tower(); ctx.clip();
  const bands = 7, bh = h / bands;
  for (let i = 0; i < bands; i++) {
    const yy = top + i * bh;
    ctx.fillStyle = i % 2 ? C.stripeB : C.stripeA;
    ctx.fillRect(bx - wb * 1.6, yy - 1, wb * 3.2, bh + 2);
  }
  // lit side / shadow side, one plane each (flat paper shading, no gradient)
  ctx.globalAlpha = 0.16;
  ctx.fillStyle = C.cream; ctx.fillRect(bx - wb * 1.6, top, wb * 0.9, h);
  ctx.fillStyle = C.ink; ctx.fillRect(bx + wb * 0.4, top, wb * 1.2, h);
  ctx.restore();

  tower();
  ctx.strokeStyle = 'rgba(57,42,34,0.7)'; ctx.lineWidth = 2; ctx.stroke();

  // gallery slab
  const galW = wt * 1.7, galH = 12;
  ctx.fillStyle = C.cream;
  ctx.fillRect(bx - galW, top - galH, galW * 2, galH + 4);
  ctx.strokeStyle = C.ink; ctx.lineWidth = 2;
  ctx.strokeRect(bx - galW, top - galH, galW * 2, galH + 4);

  // lamp room: cream block with two dark windows and a glowing lamp
  const lrH = (portrait ? 0.030 : 0.022) * Math.min(W, H);
  const lrW = wt * 1.15;
  const lrTop = top - galH - lrH;
  ctx.fillStyle = C.cream;
  ctx.fillRect(bx - lrW, lrTop, lrW * 2, lrH);
  ctx.strokeStyle = C.ink; ctx.lineWidth = 2;
  ctx.strokeRect(bx - lrW, lrTop, lrW * 2, lrH);
  const win = ctx.createLinearGradient(0, lrTop, 0, lrTop + lrH);
  win.addColorStop(0, C.lamp); win.addColorStop(1, '#e2952f');
  ctx.fillStyle = win;
  ctx.fillRect(bx - lrW * 0.8, lrTop + 4, lrW * 1.6, lrH - 8);

  // roof: a small red dome
  ctx.beginPath();
  ctx.moveTo(bx - lrW - 4, lrTop);
  ctx.quadraticCurveTo(bx, lrTop - lrH * 1.15, bx + lrW + 4, lrTop);
  ctx.closePath();
  ctx.fillStyle = C.stripeD; ctx.fill();
  ctx.strokeStyle = C.cream; ctx.lineWidth = 4; ctx.stroke();

  // beam: a soft fan that sweeps as the lamp turns (only once lit)
  const lit = ss(seg(t, 2.35, 3.0));
  if (lit > 0.001) {
    const lampC = { x: bx, y: lrTop + lrH / 2 };
    const sweep = 0.22 * Math.sin(t * 0.9 - 0.4);
    const arm = (dir) => {
      const a0 = dir < 0 ? Math.PI + sweep : sweep;
      const a1 = dir < 0 ? Math.PI - sweep : -sweep;
      const len = Math.min(W, H) * 0.55;
      ctx.beginPath();
      ctx.moveTo(lampC.x, lampC.y);
      ctx.lineTo(lampC.x + Math.cos(a0) * len, lampC.y + Math.sin(a0) * len * 0.55);
      ctx.lineTo(lampC.x + Math.cos(a1) * len, lampC.y + Math.sin(a1) * len * 0.55);
      ctx.closePath();
      const bg = ctx.createRadialGradient(lampC.x, lampC.y, 4, lampC.x, lampC.y, len);
      bg.addColorStop(0, `rgba(255,227,162,${0.55 * lit})`);
      bg.addColorStop(1, 'rgba(255,227,162,0)');
      ctx.fillStyle = bg; ctx.fill();
    };
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    arm(1); arm(-1);
    ctx.restore();
    // the lamp itself
    ctx.beginPath(); ctx.arc(lampC.x, lampC.y, 9, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,235,180,${lit})`; ctx.fill();
  }
}

// ---- the readable line: a title printed on the left page -------------------
const TITLE = 'THE LIGHTHOUSE';
const TITLE_T0 = 1.35;
function titleFont() { return `400 ${Math.round(L.title.size)}px "IM Fell English"`; }
function titleBox(t) {
  ctx.save();
  ctx.font = titleFont();
  const w = ctx.measureText(TITLE).width;
  ctx.restore();
  const lx = L.title.x, ly = L.title.y, s = L.title.size;
  const p0 = camPt(t, lx - w / 2 - 6, ly - s * 0.92, BOOK_DEPTH);
  const p1 = camPt(t, lx + w / 2 + 6, ly + s * 0.26, BOOK_DEPTH);
  return { x0: Math.min(p0.x, p1.x), y0: Math.min(p0.y, p1.y), x1: Math.max(p0.x, p1.x), y1: Math.max(p0.y, p1.y) };
}
function drawTitle(t) {
  const vis = ss(seg(t, TITLE_T0, TITLE_T0 + 0.5));
  if (vis <= 0.001) return;
  const lx = L.title.x, ly = L.title.y, s = L.title.size;
  ctx.save();
  ctx.globalAlpha = vis;
  ctx.font = titleFont();
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = C.ink;
  ctx.fillText(TITLE, lx, ly);
  ctx.strokeStyle = 'rgba(90,54,31,0.5)';
  ctx.lineWidth = Math.max(1.5, s * 0.035);
  const w = ctx.measureText(TITLE).width;
  ctx.beginPath();
  ctx.moveTo(lx - w / 2 + 4, ly + s * 0.24);
  ctx.lineTo(lx + w / 2 - 4, ly + s * 0.24);
  ctx.stroke();
  ctx.restore();
}

// ---- frame ----------------------------------------------------------------
function drawBg() {
  const g = ctx.createRadialGradient(cx, H * 0.42, Math.min(W, H) * 0.14, cx, H * 0.5, Math.max(W, H) * 0.72);
  g.addColorStop(0, C.bgHi);
  g.addColorStop(1, C.bgLo);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}
function drawVignette() {
  const g = ctx.createRadialGradient(cx, H * 0.48, Math.min(W, H) * 0.28, cx, H * 0.5, Math.max(W, H) * 0.68);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(10,6,3,0.6)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

function draw(t) {
  t = clamp(t, 0, window.DUR);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.filter = 'none';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';
  ctx.lineJoin = 'miter';

  drawBg();

  withCam(t, BOOK_DEPTH, () => { drawBook(t); drawTitle(t); });
  withCam(t, SEA_DEPTH, () => drawSea(t));
  withCam(t, TOWER_DEPTH, () => drawLighthouse(t));

  drawVignette();

  // one paper-grain pass over the whole frame keeps it reading as stock
  if (!grainPat) grainPat = ctx.createPattern(grain, 'repeat');
  ctx.save();
  ctx.globalAlpha = 0.06;
  ctx.globalCompositeOperation = 'overlay';
  ctx.fillStyle = grainPat;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

window.render = t => draw(t);

// text the viewer must read: the title on the page, with its screen box
window.TEXTS = t => {
  t = clamp(t, 0, window.DUR);
  if (t < TITLE_T0) return [];
  const b = titleBox(t);
  return [{ id: 'page-title', text: TITLE, x0: b.x0, y0: b.y0, x1: b.x1, y1: b.y1 }];
};

// load the face we draw with, then declare ready — no swallowed rejection
await Promise.all([
  document.fonts.load(titleFont(), TITLE),
]);
await document.fonts.ready;

draw(0);
window.READY = true;
