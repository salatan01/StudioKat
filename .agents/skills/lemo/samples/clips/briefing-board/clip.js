// Briefing Board — "Skylab: assembling a station in orbit".
//
// An evidence wall built from the three real NASA Skylab photographs. The demo
// kit's loadObject() is demo-only (it hardcodes the vendored KIT and fetches
// objects/<id>.png), so this clip draws its own board and pins the real photos
// itself, importing only the kit's palette/type and the shared ease. Every
// on-screen label is read from clip.json's `facts` — the station and span from
// fact 0, the crew count and 1973-74 window from fact 1, and each photograph's
// own fact (it names the file) for that mission and year.
//
// Original StudioKat clip: the vendored demo (bridges and ships) is read for
// technique only; its story, subject and copy are not reused. Deterministic:
// every value derives from `t` — no Math.random, no Date.now.

import { clamp, lerp, seg, mulberry, hash, TAU, track } from '/core/lib.js';
import { THEME, FONT, bease } from '/styles/briefing-board/demo/kit/board.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); }
catch (e) { console.warn('clip.json not loaded; falling back to the canvas size', e); }
// The render server sizes the viewport to --size, so window.innerWidth/Height is
// the real frame; clip.json's width/height is only the native authoring size.
const W = Math.round(window.innerWidth || (META.width | 0) || canvas.width);
const H = Math.round(window.innerHeight || (META.height | 0) || canvas.height);
canvas.width = W;
canvas.height = H;

window.DUR = 6;

const PORTRAIT = H > W;
const D2R = Math.PI / 180;
const C = { ink: THEME.graphite, blue: THEME.blue, red: THEME.red, grey: THEME.grey };
const CREDIT = 'Photographs: NASA (public domain).';

// ---- the real, sourced photographs (records live in cutouts/objects.json) ----
const OBJ = await (await fetch('cutouts/objects.json')).json();
const RECORDS = Array.isArray(OBJ.objects) ? OBJ.objects : [];

function tryImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`image failed: ${src}`));
    img.src = src;
  });
}
// primary path is the record's curated `photos/<file>.jpg`; if that 404s, fall
// back to the copy shipped beside the clip in `cutouts/<file>.jpg`.
async function loadPhoto(rec) {
  const primary = rec.photo || `photos/${rec.id}.jpg`;
  const base = primary.split('/').pop();
  const candidates = [primary, `cutouts/${base}`];
  let lastErr = null;
  for (const src of candidates) {
    try { const im = await tryImage(src); await im.decode(); return im; }
    catch (e) { lastErr = e; console.warn(`photo not at ${src}; trying the next path`); }
  }
  throw lastErr || new Error(`photo missing: ${base}`);
}

// left-to-right through time: Skylab 2 (1973), Skylab 3 (1973), Skylab 4 (1974)
const ORDER = ['skylab-rendezvous-flyaround', 'skylab-cluster-black-sky', 'skylab-cluster-earth-orbit'];
const PHOTOS = [];
for (const id of ORDER) {
  const rec = RECORDS.find(r => r.id === id) || RECORDS.find(r => (r.photo || '').includes(id));
  if (!rec) throw new Error(`cutouts/objects.json is missing a record for ${id}`);
  PHOTOS.push({ rec, img: await loadPhoto(rec) });
}

// ---- the clip's words: every on-screen label is read from clip.json's facts --
// No invented evidence. fact[0] gives the station and the 1973-1979 span, fact[1]
// the three crews and the 1973-74 window, and each photo's own fact (it names the
// file) gives that photograph's real mission and year.
const FACTS = (Array.isArray(META.facts) ? META.facts : []).filter(f => typeof f === 'string' && f.trim());
const FACT0 = FACTS[0] || '';
const FACT1 = FACTS[1] || '';
const yearsIn = s => [...String(s).matchAll(/\b(19\d{2})\b/g)].map(m => m[1]);
const factFor = id => FACTS.find(f => f.includes(id)) || '';
function labelFor(rec) {
  const f = factFor(rec.id);
  const m = f.match(/Skylab\s+(\d+)/i);
  const mission = m ? `SKYLAB ${m[1]}` : String(rec.mission || 'SKYLAB').toUpperCase();
  const ys = yearsIn(f);
  const year = ys.length ? ys[ys.length - 1] : String(rec.year || '');
  return `${mission} \u00B7 ${year}`;
}
const LABELS = PHOTOS.map(ph => labelFor(ph.rec));
const TITLE = (FACT0.match(/[A-Za-z]+/) || ['Skylab'])[0].toUpperCase();
const SPAN = yearsIn(FACT0);
const SUBTITLE = SPAN.length >= 2 ? `${SPAN[0]}-${SPAN[SPAN.length - 1]}` : (SPAN[0] || '1973-1979');
const DIM = FACT1.match(/\((\d{4})[-–](\d{2})\)/);
const DIMLABEL = DIM ? `${DIM[1]}-${DIM[2]}` : '1973-74';
const VERDICT1 = /\bfirst\s+space\s+station\b/i.test(FACT0) ? 'FIRST STATION' : 'ONE STATION';
const VERDICT2 = /\bthree\s+crews\b/i.test(FACT1) ? 'THREE CREWS' : 'THE CREWS';

// ---- layout, per aspect ------------------------------------------------------
// 16:9 is native: a wide wall, a lateral track. 9:16 is a tall column: the
// prints stack vertically, the camera drops, and the verdict sits at the foot.
function makeLayout(portrait) {
  if (!portrait) {
    return {
      board: { w: 4600, h: 2600 }, photoW: 430, labelSize: 110, seed: 11,
      prints: [
        { x: 1150, y: 900, rot: -1.4, label: LABELS[0], lx: 1150, ly: 1340, align: 'center' },
        { x: 2300, y: 1280, rot: 1.1, label: LABELS[1], lx: 2300, ly: 1720, align: 'center' },
        { x: 3450, y: 880, rot: -0.8, label: LABELS[2], lx: 3450, ly: 1340, align: 'center' },
      ],
      keys: [
        [0.0, [1080, 860, Math.log(1.12)]],
        [0.4, [1080, 860, Math.log(1.12)]],
        [1.5, [1720, 1080, Math.log(1.06)]],
        [2.5, [2900, 1080, Math.log(1.0)]],
        [3.2, [2300, 1250, Math.log(0.36)]],
        [6.0, [2300, 1250, Math.log(0.36)]],
      ],
      conn: [
        [[1150, 900], [1725, 1005], [2300, 1280]],
        [[2300, 1280], [2875, 1000], [3450, 880]],
      ],
      dimAxis: 'h', dimLine: 560,
      title: { x: 420, y: 300, size: 170 },
      subtitle: { x: 430, y: 470, size: 88 },
      dimLabel: { x: 2300, y: 470, size: 100, align: 'center' },
      card: { x: 3720, y: 2180, w: 1120, h: 300, size: 112 },
    };
  }
  return {
    board: { w: 2400, h: 4800 }, photoW: 380, labelSize: 104, seed: 29,
    prints: [
      { x: 1200, y: 1250, rot: -1.2, label: LABELS[0], lx: 1200, ly: 1640, align: 'center' },
      { x: 1200, y: 2550, rot: 1.0, label: LABELS[1], lx: 1200, ly: 2940, align: 'center' },
      { x: 1200, y: 3850, rot: -0.9, label: LABELS[2], lx: 1200, ly: 4240, align: 'center' },
    ],
    keys: [
      [0.0, [1200, 1180, Math.log(1.2)]],
      [0.4, [1200, 1180, Math.log(1.2)]],
      [1.5, [1200, 1980, Math.log(1.12)]],
      [2.5, [1200, 3250, Math.log(1.04)]],
      [3.2, [1200, 2400, Math.log(0.36)]],
      [6.0, [1200, 2400, Math.log(0.36)]],
    ],
    conn: [
      [[1200, 1250], [1250, 1900], [1200, 2550]],
      [[1200, 2550], [1140, 3200], [1200, 3850]],
    ],
    dimAxis: 'v', dimLine: 1560,
    title: { x: 300, y: 360, size: 160 },
    subtitle: { x: 310, y: 530, size: 86 },
    dimLabel: { x: 1640, y: 2500, size: 96, align: 'left' },
    card: { x: 1200, y: 4530, w: 1560, h: 330, size: 118 },
  };
}
const L = makeLayout(PORTRAIT);

// paper geometry for each print (photo content + its white border)
const GEOM = PHOTOS.map((ph, i) => {
  const ar = ph.img.naturalWidth / ph.img.naturalHeight;
  const pw = L.photoW, phh = pw / ar;
  return { p: L.prints[i], img: ph.img, pw, ph: phh, border: Math.round(pw * 0.052) };
});
// the photo content must never be upscaled past ~512 px on screen
const MAX_ZOOM = Math.max(...L.keys.map(k => Math.exp(k[1][2])));
if (L.photoW * MAX_ZOOM > 512) throw new Error('photo content would be upscaled past 512 px');

// ---- measure + draw the marker hand ------------------------------------------
const mctx = document.createElement('canvas').getContext('2d');
const markerFont = size => `400 ${size}px "${FONT.marker}"`;
const layCache = new Map();
function markerLayout(text, size, seedKey) {
  const key = `${text}|${size}|${seedKey}`;
  const hit = layCache.get(key);
  if (hit) return hit;
  mctx.font = markerFont(size);
  const r = mulberry((Math.floor(hash(seedKey) * 1e9) + text.length * 131 + size) | 0);
  const tr = size * 0.02, arr = [];
  let x = 0;
  for (const ch of text) {
    const w = mctx.measureText(ch).width;
    arr.push({ ch, x, w, rot: (r() - 0.5) * 2.4, dy: (r() - 0.5) * size * 0.04, sc: 1 + (r() - 0.5) * 0.03 });
    x += w + (ch === ' ' ? 0 : tr);
  }
  const out = { arr, width: Math.max(0, x - tr) };
  layCache.set(key, out);
  return out;
}
function markerBox(text, x, y, size, align, seedKey) {
  const w = markerLayout(text, size, seedKey).width;
  const x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  return [x0, y - size * 0.80, x0 + w, y + size * 0.18];
}
function drawMarker(text, x, y, size, color, p, align, seedKey) {
  if (p <= 0) return;
  const lay = markerLayout(text, size, seedKey);
  const x0 = align === 'center' ? -lay.width / 2 : align === 'right' ? -lay.width : 0;
  ctx.save();
  ctx.translate(x, y);
  ctx.font = markerFont(size);
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';
  const n = lay.arr.length;
  let idx = 0;
  for (const g of lay.arr) {
    if (g.ch === ' ') continue;
    const cp = clamp(p * n - idx);
    idx++;
    if (cp <= 0) break;
    ctx.save();
    ctx.translate(x0 + g.x + g.w / 2, g.dy);
    ctx.rotate(g.rot * D2R);
    ctx.scale(g.sc, g.sc);
    ctx.translate(-g.w / 2, 0);
    if (cp < 1) {
      ctx.beginPath();
      ctx.rect(-size * 0.12, -size * 1.24, (g.w + size * 0.24) * cp, size * 1.6);
      ctx.clip();
    }
    ctx.globalAlpha = 0.92;
    ctx.fillStyle = color;
    ctx.fillText(g.ch, 0, 0);
    ctx.globalAlpha = 0.18;
    ctx.lineWidth = Math.max(1, size * 0.02);
    ctx.lineJoin = 'round';
    ctx.strokeStyle = color;
    ctx.strokeText(g.ch, 0, 0);
    ctx.restore();
  }
  ctx.restore();
}

// ---- the board surface (procedural, seeded, deterministic) --------------------
function buildBoard(bw, bh, seed) {
  const s = 0.26;
  const cw = Math.max(64, Math.ceil(bw * s)), ch = Math.max(64, Math.ceil(bh * s));
  const cv = document.createElement('canvas');
  cv.width = cw; cv.height = ch;
  const x = cv.getContext('2d');
  const r = mulberry(seed);
  x.fillStyle = THEME.enamel; x.fillRect(0, 0, cw, ch);
  for (let i = 0; i < 26; i++) {           // low-frequency tonal drift
    const X = r() * cw, Y = r() * ch, R = 120 + r() * 380;
    const g = x.createRadialGradient(X, Y, 0, X, Y, R);
    const v = r() < 0.5 ? '255,254,249' : '222,218,208';
    g.addColorStop(0, `rgba(${v},${0.05 + r() * 0.05})`);
    g.addColorStop(1, `rgba(${v},0)`);
    x.fillStyle = g; x.beginPath(); x.arc(X, Y, R, 0, TAU); x.fill();
  }
  const cols = [[35, 42, 53], [31, 79, 200], [211, 58, 33]];
  for (let i = 0; i < 70; i++) {           // ghosts of earlier marker work
    const X = r() * cw, Y = r() * ch, col = cols[r() < 0.66 ? 0 : r() < 0.6 ? 1 : 2];
    x.save(); x.translate(X, Y); x.rotate((r() - 0.5) * 0.16);
    x.globalAlpha = 0.02 + r() * 0.045; x.strokeStyle = `rgb(${col})`;
    x.lineCap = 'round'; x.lineJoin = 'round'; x.lineWidth = 4 + r() * 4;
    const kind = r();
    x.beginPath();
    if (kind < 0.34) { x.moveTo(0, 0); for (let j = 0; j < 5; j++) x.lineTo((j + 1) * (14 + r() * 22), (r() - 0.5) * 34); }
    else if (kind < 0.7) { x.moveTo(0, 0); x.lineTo(70 + r() * 220, (r() - 0.5) * 20); }
    else if (kind < 0.86) { x.rect(0, 0, 50 + r() * 140, 28 + r() * 70); }
    else { x.arc(0, 0, 14 + r() * 46, 0, TAU); }
    x.stroke(); x.restore();
  }
  for (let i = 0; i < 34; i++) {           // eraser haze
    const X = r() * cw, Y = r() * ch, R = 90 + r() * 260, RR = 30 + r() * 70;
    x.save(); x.translate(X, Y); x.rotate((r() - 0.5) * 0.5); x.globalAlpha = 0.015 + r() * 0.02;
    x.fillStyle = '#8a8f96'; x.beginPath(); x.ellipse(0, 0, R / 2, RR / 2, 0, 0, TAU); x.fill(); x.restore();
  }
  const im = x.getImageData(0, 0, cw, ch), d = im.data;   // fine speckle
  for (let i = 0; i < d.length; i += 4) { const n = (r() - 0.5) * 5; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
  x.putImageData(im, 0, 0);
  return cv;
}
let BOARD = null;

// ---- camera: monotone keyframes, plus a hand-held breath ---------------------
const camTrack = track(L.keys);
function camAt(t) {
  const [x, y, lz] = camTrack(t);
  const dx = 1.5 * Math.sin(TAU * 0.19 * t + 1.1) + 0.7 * Math.sin(TAU * 0.37 * t + 3.0);
  const dy = 1.0 * Math.sin(TAU * 0.15 * t + 4.2) + 0.6 * Math.sin(TAU * 0.31 * t + 0.4);
  return { x, y, z: Math.exp(lz), dx, dy };
}
function applyCam(c) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.translate(W / 2 + c.dx, H / 2 + c.dy);
  ctx.scale(c.z, c.z);
  ctx.translate(-c.x, -c.y);
}
function projectBox(box, c) {
  const pts = [[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]]]
    .map(p => [W / 2 + c.dx + (p[0] - c.x) * c.z, H / 2 + c.dy + (p[1] - c.y) * c.z]);
  return {
    x0: Math.min(...pts.map(p => p[0])), y0: Math.min(...pts.map(p => p[1])),
    x1: Math.max(...pts.map(p => p[0])), y1: Math.max(...pts.map(p => p[1])),
  };
}

// ---- drawing primitives ------------------------------------------------------
function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function magnet(x, X, Y, r, col) {
  const pal = THEME.magnet[col] || THEME.magnet.red;
  const g = x.createRadialGradient(X - r * 0.35, Y - r * 0.4, r * 0.1, X, Y, r);
  g.addColorStop(0, pal[0]); g.addColorStop(1, pal[1]);
  x.fillStyle = g; x.beginPath(); x.arc(X, Y, r, 0, TAU); x.fill();
  x.strokeStyle = 'rgba(0,0,0,.25)'; x.lineWidth = Math.max(1, r * 0.06); x.stroke();
  x.fillStyle = 'rgba(255,255,255,.35)'; x.beginPath(); x.ellipse(X - r * 0.3, Y - r * 0.42, r * 0.38, r * 0.16, -0.5, 0, TAU); x.fill();
}
function quadPts(a, ctrl, b, n = 46) {
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const u = i / n, v = 1 - u;
    pts.push([v * v * a[0] + 2 * v * u * ctrl[0] + u * u * b[0], v * v * a[1] + 2 * v * u * ctrl[1] + u * u * b[1]]);
  }
  return pts;
}
function drawPolyPartial(pts, p, lw, color, alpha = 0.9) {
  if (p <= 0) return;
  const n = pts.length - 1, upto = p * n;
  ctx.save();
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i <= n; i++) {
    if (i <= upto) { ctx.lineTo(pts[i][0], pts[i][1]); continue; }
    const u = upto - (i - 1);
    if (u > 0) ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u));
    break;
  }
  ctx.globalAlpha = alpha; ctx.stroke();
  ctx.globalAlpha = alpha * 0.14; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = lw * 0.4; ctx.stroke();
  ctx.restore();
}
function arrow(x, y, ang, lw, col) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
  ctx.strokeStyle = col; ctx.lineWidth = lw * 0.9; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.globalAlpha = 0.92;
  ctx.beginPath(); ctx.moveTo(-lw * 3.2, -lw * 1.8); ctx.lineTo(0, 0); ctx.lineTo(-lw * 3.2, lw * 1.8); ctx.stroke();
  ctx.restore();
}

// ---- the frame ---------------------------------------------------------------
function drawBoard() {
  const b = L.board;
  ctx.fillStyle = 'rgba(38,34,28,.35)'; ctx.fillRect(26, 34, b.w, b.h);
  ctx.fillStyle = 'rgba(38,34,28,.16)'; ctx.fillRect(48, 62, b.w, b.h);
  ctx.drawImage(BOARD, 0, 0, b.w, b.h);
  ctx.lineWidth = 34; ctx.strokeStyle = '#B9BCBF'; ctx.strokeRect(-17, -17, b.w + 34, b.h + 34);
  ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,.16)'; ctx.strokeRect(0, 0, b.w, b.h);
}
function drawConnectors(t) {
  const p1 = bease(seg(t, 0.35, 1.55), 1.6, 2.4);
  const p2 = bease(seg(t, 1.5, 2.6), 1.6, 2.4);
  if (p1 > 0) drawPolyPartial(quadPts(...L.conn[0]), p1, 9, C.blue, 0.85);
  if (p2 > 0) drawPolyPartial(quadPts(...L.conn[1]), p2, 9, C.blue, 0.85);
}
function drawDimension(t) {
  const p = bease(seg(t, 2.5, 3.15), 1.6, 2.4);
  if (p <= 0) return;
  const col = C.red, lw = 11;
  // extension lines from each print to the dimension line
  ctx.save();
  ctx.globalAlpha = clamp(p * 6) * 0.5;
  ctx.strokeStyle = col; ctx.lineWidth = lw * 0.32; ctx.lineCap = 'round';
  ctx.beginPath();
  for (const g of GEOM) {
    if (L.dimAxis === 'h') { ctx.moveTo(g.p.x, g.p.y - g.ph / 2 - g.border + 4); ctx.lineTo(g.p.x, L.dimLine); }
    else { ctx.moveTo(g.p.x + g.pw / 2 + g.border - 4, g.p.y); ctx.lineTo(L.dimLine, g.p.y); }
  }
  ctx.stroke();
  ctx.restore();
  const A = L.dimAxis === 'h' ? [GEOM[0].p.x, L.dimLine] : [L.dimLine, GEOM[0].p.y];
  const B = L.dimAxis === 'h' ? [GEOM[2].p.x, L.dimLine] : [L.dimLine, GEOM[2].p.y];
  drawPolyPartial([A, B], p, lw, col, 0.92);
  if (p > 0.6) arrow(A[0], A[1], Math.atan2(A[1] - B[1], A[0] - B[0]), lw, col);
  if (p >= 0.999) arrow(B[0], B[1], Math.atan2(B[1] - A[1], B[0] - A[0]), lw, col);
}
function drawPrints() {
  for (const g of GEOM) {   // offset shadows first (window light from upper left)
    const w = g.pw + g.border * 2, h = g.ph + g.border * 2;
    ctx.save(); ctx.translate(g.p.x, g.p.y); ctx.rotate(g.p.rot * D2R);
    ctx.fillStyle = 'rgba(30,26,20,.20)'; rrect(-w / 2 + 16, -h / 2 + 22, w, h, 8); ctx.fill();
    ctx.fillStyle = 'rgba(30,26,20,.10)'; rrect(-w / 2 + 30, -h / 2 + 42, w, h, 10); ctx.fill();
    ctx.restore();
  }
  GEOM.forEach((g, i) => {
    const w = g.pw + g.border * 2, h = g.ph + g.border * 2;
    ctx.save(); ctx.translate(g.p.x, g.p.y); ctx.rotate(g.p.rot * D2R);
    ctx.fillStyle = THEME.paper; rrect(-w / 2, -h / 2, w, h, 6); ctx.fill();
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(g.img, -g.pw / 2, -g.ph / 2, g.pw, g.ph);
    ctx.strokeStyle = 'rgba(30,30,30,.22)'; ctx.lineWidth = Math.max(1, g.pw * 0.004);
    ctx.strokeRect(-g.pw / 2, -g.ph / 2, g.pw, g.ph);
    ctx.strokeStyle = 'rgba(30,30,30,.12)'; ctx.lineWidth = Math.max(1, g.pw * 0.006);
    ctx.strokeRect(-w / 2, -h / 2, w, h);
    magnet(ctx, g.pw * 0.20, -h / 2 + g.border * 0.3, g.pw * 0.06, i === 1 ? 'red' : 'graphite');
    ctx.restore();
  });
}
function drawLabels(t) {
  GEOM.forEach((g, i) => {
    const p = L.prints[i], t0 = 3.40 + i * 0.05;
    const lp = bease(seg(t, t0 - 0.18, t0 + 0.18), 1.6, 2.4);
    if (lp > 0) {
      const bottom = g.p.y + g.ph / 2 + g.border + 6;
      const boxTop = p.ly - L.labelSize * 0.8;
      ctx.save(); ctx.globalAlpha = 0.5 * lp; ctx.strokeStyle = C.grey; ctx.lineWidth = 3; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(p.x, bottom); ctx.lineTo(p.x, lerp(bottom, boxTop - 6, lp)); ctx.stroke(); ctx.restore();
    }
    drawMarker(p.label, p.lx, p.ly, L.labelSize, C.ink, seg(t, t0, t0 + 0.34), p.align, 'label' + i);
  });
}
function drawHeader(t) {
  drawMarker(TITLE, L.title.x, L.title.y, L.title.size, C.ink, seg(t, 3.40, 3.74), 'left', 'title');
  const tp = bease(seg(t, 3.50, 3.90), 1.6, 2.4);
  if (tp > 0) {
    const w = markerLayout(TITLE, L.title.size, 'title').width * 0.5;
    ctx.save(); ctx.strokeStyle = C.red; ctx.lineWidth = L.title.size * 0.06; ctx.lineCap = 'round'; ctx.globalAlpha = 0.9;
    ctx.beginPath();
    ctx.moveTo(L.title.x, L.title.y + L.title.size * 0.34);
    ctx.lineTo(L.title.x + w * tp, L.title.y + L.title.size * 0.34);
    ctx.stroke(); ctx.restore();
  }
  drawMarker(SUBTITLE, L.subtitle.x, L.subtitle.y, L.subtitle.size, C.grey, seg(t, 3.46, 3.80), 'left', 'subtitle');
}
function drawDimLabel(t) {
  const d = L.dimLabel;
  drawMarker(DIMLABEL, d.x, d.y, d.size, C.red, seg(t, 3.30, 3.64), d.align, 'dim');
}
function drawCard(t) {
  const c = L.card;
  const inP = bease(seg(t, 3.40, 3.62), 2, 3);
  if (inP <= 0) return;
  const sc = lerp(1.05, 1, inP);
  ctx.save(); ctx.translate(c.x, c.y); ctx.scale(sc, sc);
  ctx.fillStyle = 'rgba(30,26,20,.22)'; rrect(-c.w / 2 + 12, -c.h / 2 + 16, c.w, c.h, 10); ctx.fill();
  ctx.fillStyle = THEME.paper; rrect(-c.w / 2, -c.h / 2, c.w, c.h, 8); ctx.fill();
  ctx.strokeStyle = 'rgba(30,30,30,.14)'; ctx.lineWidth = 2; rrect(-c.w / 2, -c.h / 2, c.w, c.h, 8); ctx.stroke();
  ctx.fillStyle = C.red; ctx.fillRect(-c.w / 2 + c.w * 0.13, -c.h / 2 + c.h * 0.24, c.w * 0.30, c.h * 0.035);
  magnet(ctx, -c.w / 2 + c.w * 0.10, -c.h / 2 + c.h * 0.11, c.w * 0.026, 'red');
  magnet(ctx, c.w / 2 - c.w * 0.10, -c.h / 2 + c.h * 0.11, c.w * 0.026, 'graphite');
  ctx.restore();
  drawMarker(VERDICT1, c.x, c.y - c.h * 0.12, c.size, C.ink, seg(t, 3.50, 3.84), 'center', 'v1');
  drawMarker(VERDICT2, c.x, c.y + c.h * 0.24, c.size, C.ink, seg(t, 3.55, 3.89), 'center', 'v2');
}
function drawVignette() {
  const g = ctx.createRadialGradient(W * 0.5, H * 0.46, Math.min(W, H) * 0.34, W * 0.5, H * 0.5, Math.max(W, H) * 0.72);
  g.addColorStop(0, 'rgba(255,255,255,0)');
  g.addColorStop(1, 'rgba(60,55,48,0.18)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function creditGeom() {
  const size = Math.round(Math.min(W, H) * 0.024);
  mctx.font = `500 ${size}px "${FONT.sans}"`;
  const w = mctx.measureText(CREDIT).width;
  const y = H - Math.round(size * 1.3);
  return { size, y, x0: W / 2 - w / 2 - 4, x1: W / 2 + w / 2 + 4 };
}
function drawCredit(t) {
  if (t < 3.4) return;
  const { size, y } = creditGeom();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.font = `500 ${size}px "${FONT.sans}"`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  ctx.save();
  ctx.shadowColor = 'rgba(255,255,255,.85)'; ctx.shadowBlur = 8;
  ctx.fillStyle = '#464B52';
  ctx.fillText(CREDIT, W / 2, y);
  ctx.restore();
}

// ---- frame render ------------------------------------------------------------
function draw(t) {
  t = clamp(t, 0, window.DUR);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic';
  ctx.textAlign = 'left';

  ctx.fillStyle = THEME.wall; ctx.fillRect(0, 0, W, H);

  const c = camAt(t);
  applyCam(c);
  drawBoard();
  drawConnectors(t);
  drawDimension(t);
  drawPrints();
  drawLabels(t);
  drawHeader(t);
  drawDimLabel(t);
  drawCard(t);

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  drawVignette();
  drawCredit(t);
  ctx.globalAlpha = 1;
}
window.render = t => draw(clamp(t, 0, window.DUR));

// ---- readable text: every on-screen string a viewer must read ----------------
const TEXTDEFS = [
  { id: 'title', text: TITLE, size: L.title.size, x: L.title.x, y: L.title.y, align: 'left', seed: 'title', t0: 3.40 },
  { id: 'subtitle', text: SUBTITLE, size: L.subtitle.size, x: L.subtitle.x, y: L.subtitle.y, align: 'left', seed: 'subtitle', t0: 3.46 },
  { id: 'dim', text: DIMLABEL, size: L.dimLabel.size, x: L.dimLabel.x, y: L.dimLabel.y, align: L.dimLabel.align, seed: 'dim', t0: 3.30 },
];
GEOM.forEach((g, i) => {
  const p = L.prints[i];
  TEXTDEFS.push({ id: 'lbl' + i, text: p.label, size: L.labelSize, x: p.lx, y: p.ly, align: p.align, seed: 'label' + i, t0: 3.40 + i * 0.05 });
});
TEXTDEFS.push({ id: 'verdict1', text: VERDICT1, size: L.card.size, x: L.card.x, y: L.card.y - L.card.h * 0.12, align: 'center', seed: 'v1', t0: 3.50 });
TEXTDEFS.push({ id: 'verdict2', text: VERDICT2, size: L.card.size, x: L.card.x, y: L.card.y + L.card.h * 0.24, align: 'center', seed: 'v2', t0: 3.55 });

window.TEXTS = t => {
  const c = camAt(t), out = [];
  for (const d of TEXTDEFS) {
    if (t < d.t0) continue;
    const s = projectBox(markerBox(d.text, d.x, d.y, d.size, d.align, d.seed), c);
    out.push({ id: d.id, text: d.text, x0: s.x0, y0: s.y0, x1: s.x1, y1: s.y1 });
  }
  if (t >= 3.4) {
    const { size, y, x0, x1 } = creditGeom();
    out.push({ id: 'credit', text: CREDIT, x0, y0: y - size * 0.95, x1, y1: y + size * 0.2, pass: true });
  }
  return out;
};

// ---- fonts + board, then READY -----------------------------------------------
const SAMPLE = `${TITLE} ${SUBTITLE} ${DIMLABEL} ${VERDICT1} ${VERDICT2} ${LABELS.join(' ')} Photographs: NASA (public domain). ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789`;
await Promise.all([
  document.fonts.load(`400 100px "${FONT.marker}"`, SAMPLE),
  document.fonts.load(`500 40px "${FONT.sc}"`, SAMPLE),
  document.fonts.load(`700 40px "${FONT.sc}"`, SAMPLE),
  document.fonts.load(`500 40px ${FONT.sans}`, SAMPLE),
  document.fonts.load(`700 40px ${FONT.sans}`, SAMPLE),
  document.fonts.load(`500 30px "${FONT.mono}"`, SAMPLE),
  document.fonts.load(`600 30px "${FONT.mono}"`, SAMPLE),
]);
await document.fonts.ready;

BOARD = buildBoard(L.board.w, L.board.h, L.seed);
draw(0);
window.READY = true;