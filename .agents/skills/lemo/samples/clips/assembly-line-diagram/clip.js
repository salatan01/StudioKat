// Assembly-Line Diagram · "From cocoa pod to chocolate bar" (8 s, 24 fps)
// A cut-away factory: the camera rides one cocoa pod on a belt through two
// stations — roast (120 °C) then mold (85 g bar) — and pulls out on the bar.
// Original StudioKat clip; the vendored demo (a 54.9 s body-route factory) is
// technique only — its story, stations and cargo are not reused. Deterministic:
// every value derives from `t`; no Math.random, no clock.

import { clamp, lerp, seg, eio, ss } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
canvas.width = W;
canvas.height = H;

const portrait = H > W;

window.DUR = 8;

// ---------- palette (scheme A: warm paper, indigo ink) ----------
const C = {
  paper: '#F2ECE0', ink: '#1D2030', paperD: '#E3D9C7',
  blush: '#EE9F87', blushD: '#C8735C',
  sun: '#F3B23A', sunD: '#C98A1E',
  teal: '#2E8D87', tealD: '#1D625E',
  red: '#E04A2F', ground: '#24345A',
  wall: '#FBF7EE', wallD: '#EFE7D7', cream: '#FFFBF3', shade: '#DCCFB8',
  brown: '#A67C52', brownD: '#8F6744',
};
// per-colour misregistration (offset px); ink lines stay put
const REG = { red: [1.6, 0.8], sun: [-1.2, 1.3], teal: [1.0, -1.2], blush: [-0.8, -0.6] };
function regOf(col) { for (const k in REG) if (C[k] === col) return REG[k]; return [0, 0]; }

// ---------- deterministic grain texture ----------
const grainCanvas = (() => {
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const g = c.getContext('2d'), im = g.createImageData(256, 256), d = im.data;
  let s = 11; const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  for (let i = 0; i < d.length; i += 4) { const v = 230 + rnd() * 20; d[i] = v; d[i + 1] = v - 2; d[i + 2] = v - 4; d[i + 3] = 255; }
  g.putImageData(im, 0, 0);
  return c;
})();

// ---------- timeline ----------
const P_START = 300, P_S1 = 650, P_S2 = 1750, P_END = 2050;
const BELT = 560;              // belt coordinate (travel axis value at the belt)
const STATIONS = [
  { id: 'roast', name: 'ROAST', value: '120 °C', zh: '烘豆', pos: P_S1 },
  { id: 'mold',  name: 'BAR',   value: '85 g',  zh: '成型', pos: P_S2 },
];

function cargoP(t) {
  if (t < 2.6) return P_START + (P_S1 - P_START) * eio(seg(t, 0, 2.6));   // ride into roaster
  if (t < 4.6) return P_S1 + 16 * Math.sin((t - 2.6) * 7);                 // at roaster (bob)
  if (t < 5.6) return P_S1 + (P_S2 - P_S1) * seg(t, 4.6, 5.6);              // belt travel to molder
  return P_S2 + 12 * Math.sin((t - 5.6) * 5);                               // at molder (bob)
}
function camZ(t) {
  if (t < 2.6) return 1 + 0.18 * ss(seg(t, 0, 2.6));   // push into roaster
  if (t < 4.6) return 1.18;                            // at roaster
  if (t < 5.6) return 1.18 - 0.18 * seg(t, 4.6, 5.6);  // pull back while traveling
  return 1 + 0.12 * ss(seg(t, 5.6, 8.0));              // gentle push at molder
}
function camAt(t) {
  const p = cargoP(t), z = camZ(t);
  // camera rides the cargo: cargo sits at screen centre; belt slightly off-centre
  // so the floor / labels show on the far side.
  if (portrait) return { x: BELT + W * 0.05, y: p, z };
  return { x: p, y: BELT - H * 0.05, z };
}

// ---------- screen transform (world -> screen pixels) ----------
function sx(cam, x) { return (x - cam.x) * cam.z + W / 2; }
function sy(cam, y) { return (y - cam.y) * cam.z + H / 2; }
function sw(cam, w) { return w * cam.z; }
function lw(cam, w) { return Math.max(0.5, w * cam.z); }

// ---------- drawing helpers ----------
function rect(cam, x, y, w, h, fill, stroke, sw_) {
  const X = sx(cam, x), Y = sy(cam, y), WW = sw(cam, w), HH = sw(cam, h);
  if (fill) { ctx.fillStyle = fill; ctx.fillRect(X, Y, WW, HH); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw(cam, sw_ || 3); ctx.strokeRect(X, Y, WW, HH); }
}
function line(cam, pts, w, col = C.ink) {
  ctx.strokeStyle = col; ctx.lineWidth = lw(cam, w); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath();
  for (let i = 0; i < pts.length; i++) { const [px, py] = pts[i]; (i === 0 ? ctx.moveTo : ctx.lineTo).call(ctx, sx(cam, px), sy(cam, py)); }
  ctx.stroke();
}
function circle(cam, x, y, r, fill, stroke) {
  ctx.beginPath(); ctx.arc(sx(cam, x), sy(cam, y), sw(cam, r), 0, Math.PI * 2);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw(cam, 1.4); ctx.stroke(); }
}
function ellipse(cam, x, y, rx, ry, fill, stroke) {
  ctx.beginPath(); ctx.ellipse(sx(cam, x), sy(cam, y), sw(cam, rx), sw(cam, ry), 0, 0, Math.PI * 2);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw(cam, 2.2); ctx.stroke(); }
}
// a colour plate with its own misregistration + crisp ink outline
function plate(cam, x, y, w, h, col, sw_ = 2.6) {
  const off = regOf(col);
  ctx.fillStyle = col;
  ctx.fillRect(sx(cam, x + off[0]), sy(cam, y + off[1]), sw(cam, w), sw(cam, h));
  ctx.strokeStyle = C.ink; ctx.lineWidth = lw(cam, sw_);
  ctx.strokeRect(sx(cam, x), sy(cam, y), sw(cam, w), sw(cam, h));
}
function text(cam, x, y, s, size, weight, fam, fill = C.ink, anchor = 'start') {
  const off = regOf(fill);
  ctx.font = `${weight} ${Math.round(size * cam.z)}px ${fam}`;
  ctx.fillStyle = fill;
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = anchor;
  ctx.fillText(s, sx(cam, x + off[0]), sy(cam, y + off[1]));
}
function measure(s, sizeScreen, weight, fam) {
  ctx.font = `${weight} ${Math.round(sizeScreen)}px ${fam}`;
  return ctx.measureText(s);
}

// ---------- grain overlay ----------
function drawGrain(cam) {
  ctx.globalAlpha = 0.22;
  ctx.drawImage(grainCanvas, 0, 0, W, H);
  ctx.globalAlpha = 1;
}

// ---------- world ----------
function drawFloor(cam) {
  ctx.fillStyle = C.ground;
  if (portrait) rect(cam, BELT + 26, -9000, 260, 18000, C.ground);
  else rect(cam, -9000, BELT + 26, 18000, 260, C.ground);
}
function drawBelt(cam, t) {
  // belt line
  line(cam, portrait ? [[BELT, -9000], [BELT, 9000]] : [[-9000, BELT], [9000, BELT]], 24, C.ink);
  line(cam, portrait ? [[BELT, -9000], [BELT, 9000]] : [[-9000, BELT], [9000, BELT]], 18, '#4A4D5C');
  // rollers (moving with t to sell travel)
  const ph = (t * 110) % 64;
  const step = portrait ? 220 : 260;
  const len = portrait ? 18000 : 18000;
  const a = portrait ? -9000 : -9000;
  const b = portrait ? 9000 : 9000;
  const fixed = portrait ? BELT : BELT;
  const cross = portrait ? (u) => [BELT, a + u] : (u) => [a + u, BELT];
  for (let u = a + ph; u < b; u += step) {
    const [rx, ry] = cross(u);
    circle(cam, rx, ry, 5, C.wallD, C.ink);
  }
}
function drawStation(cam, s, t) {
  const pos = s.pos;
  const rw = portrait ? 150 : 360, rh = portrait ? 360 : 160;
  const wx = portrait ? BELT : pos, wy = portrait ? pos : BELT;
  // room shadow + wall + frame
  rect(cam, wx - rw / 2 + 14, wy - rh / 2 + 10, rw, rh, C.shade);
  rect(cam, wx - rw / 2, wy - rh / 2, rw, rh, C.wall);
  rect(cam, wx - rw / 2, wy - rh / 2, rw, rh, null, C.ink, 3);
  // floor strip
  if (portrait) rect(cam, wx - rw / 2, wy + rh / 2 - 24, rw, 24, C.wallD);
  else rect(cam, wx - rw / 2, wy + rh / 2 - 24, rw, 24, C.wallD);
  // number badge
  circle(cam, wx - rw / 2 + 30, wy - rh / 2 + 30, 16, C.sun, C.ink);
  text(cam, wx - rw / 2 + 30, wy - rh / 2 + 30 + 6, String(iOf(s)), 18, 800, 'Archivo', C.ink, 'center');
  // station name above
  text(cam, wx, wy - rh / 2 - 44, s.name, 30, 800, 'Archivo', C.ink, 'center');
  // door into the station (facing travel)
  const doorW = portrait ? 26 : 62, doorH = portrait ? 62 : 26;
  const dx = portrait ? wx - doorW / 2 : pos - doorW / 2;
  const dy = portrait ? pos - doorH / 2 : wy - doorH / 2;
  rect(cam, dx, dy, doorW, doorH, C.groundD);
  rect(cam, dx, dy, doorW, doorH, null, C.ink, 2.2);
  // pendant lamp
  const lx = portrait ? wx : pos - (portrait ? 0 : 90);
  const ly = portrait ? pos - 120 : wy - 90;
  line(cam, [[lx, ly - 70], [lx, ly - 10]], 2);
  ellipse(cam, lx, ly, 18, 10, C.sun, C.ink);
}
// index of a station in STATIONS
function iOf(s) { return STATIONS.indexOf(s) + 1; }

function drawCargo(cam, t) {
  const p = cargoP(t);
  const wx = portrait ? BELT : p, wy = portrait ? p : BELT;
  const k = portrait ? 0.85 : 1.0;
  if (t < 5.6) {
    // cocoa pod: whole until the roast, then cracked beans while traveling
    const roasted = t >= 2.6;
    const body = roasted ? C.blushD : C.blush;
    ellipse(cam, wx, wy, 34 * k, 24 * k, body, C.ink);
    // ridges
    for (const xx of [-14, 0, 14]) line(cam, [[wx + xx * k, wy - 22 * k], [wx + xx * k, wy + 22 * k]], 1.6, C.ink);
    // stem
    line(cam, [[wx, wy - 24 * k], [wx, wy - 38 * k]], 2.2, C.tealD);
    ellipse(cam, wx, wy - 40 * k, 7, 5, C.teal, C.ink);
    if (roasted) {
      // heat glow around pod at roaster
      const g = 0.35 + 0.25 * Math.sin((t - 2.6) * 14);
      ctx.globalAlpha = g;
      ellipse(cam, wx, wy, 56 * k, 46 * k, C.sun);
      ctx.globalAlpha = 1;
    }
  } else {
    // chocolate bar at the molder
    rect(cam, wx - 34 * k, wy - 16 * k, 68 * k, 32 * k, C.brown, C.ink, 2.2);
    for (const xx of [-18, -6, 6, 18]) line(cam, [[wx + xx * k, wy - 16 * k], [wx + xx * k, wy + 16 * k]], 1.4, C.brownD);
    text(cam, wx, wy + 30 * k, '85 g', 22, 800, 'Archivo', C.ink, 'center');
  }
}

// ---------- screen-space title ----------
function drawTitle(t) {
  const p = clamp(seg(t, 0, 0.9));
  if (p <= 0) return;
  const M = Math.round(W * 0.05);
  const size = 56;
  const w = measure(TITLE_TEXT, size * 1, 900, 'Big Shoulders Display').width;
  const x = M, y = Math.round(H * 0.13);
  ctx.save();
  ctx.globalAlpha = p;
  ctx.fillStyle = C.ink;
  ctx.font = `900 ${size}px "Big Shoulders Display"`;
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'start';
  ctx.fillRect(M - 14, y - size * 1.05, w + 28, size * 1.35);
  ctx.fillStyle = C.cream;
  ctx.fillText(TITLE_TEXT, x, y);
  ctx.restore();
}

const TITLE_TEXT = 'FROM POD TO BAR';
const PLATE1_TEXT = 'ROAST 120 °C';
const PLATE2_TEXT = 'BAR 85 g';

// ---------- one frame ----------
function draw(t) {
  t = clamp(t, 0, window.DUR);
  const cam = camAt(t);

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = C.paper;
  ctx.fillRect(0, 0, W, H);
  drawGrain(cam);

  drawFloor(cam);
  drawBelt(cam, t);
  STATIONS.forEach(s => drawStation(cam, s, t));
  drawCargo(cam, t);

  drawTitle(t);

  // station plates: ROAST 120 °C (2.6–5.2), BAR 85 g (5.2–8.0)
  const plate1 = t >= 2.6 && t < 5.2;
  const plate2 = t >= 5.2 && t <= 8.0;
  if (plate1 || plate2) {
    const s = plate1 ? STATIONS[0] : STATIONS[1];
    const tx = plate1 ? PLATE1_TEXT : PLATE2_TEXT;
    const pos = s.pos;
    const wx = portrait ? BELT + 230 : pos + 270;
    const wy = portrait ? pos - 60 : BELT - 150;
    const size = 28;
    const pad = 14;
    const tw_ = measure(tx, size, 800, 'Archivo').width;
    const boxW = tw_ + pad * 2, boxH = size * 1.55;
    const bx = portrait ? BELT + 200 : pos + 240;
    const by = portrait ? pos - 100 : BELT - 190;
    plate(cam, bx, by, boxW, boxH, C.cream, 2.4);
    text(cam, bx + pad, by + boxH / 2 + size * 0.34, tx, size, 800, 'Archivo', C.ink, 'start');
  }
}

window.render = t => draw(clamp(t, 0, window.DUR));

// ---------- TEXTS (screen-space boxes for the reading-time check) ----------
function textVisibleBox(t, textStr, cam, x, y, size, weight, fam) {
  const tw_ = measure(textStr, size * cam.z, weight, fam).width;
  const h = size * cam.z * 1.35;
  const x0 = sx(cam, x), y0 = sy(cam, y) - size * cam.z * 1.05;
  return { x0, y0, x1: x0 + tw_, y1: y0 + h };
}
window.TEXTS = t => {
  t = clamp(t, 0, window.DUR);
  const cam = camAt(t);
  const out = [];
  if (t < 3.0) {
    const M = Math.round(W * 0.05);
    const size = 56;
    const tw_ = measure(TITLE_TEXT, size, 900, 'Big Shoulders Display').width;
    out.push({ id: 'title', text: TITLE_TEXT,
      x0: M - 14, y0: Math.round(H * 0.13) - size * 1.05, x1: M - 14 + tw_ + 28, y1: Math.round(H * 0.13) + size * 0.3 });
  }
  if (t >= 2.6 && t < 5.2) {
    const s = STATIONS[0];
    const pos = s.pos;
    const bx = portrait ? BELT + 200 : pos + 240;
    const by = portrait ? pos - 100 : BELT - 190;
    const size = 28, pad = 14;
    const tw_ = measure(PLATE1_TEXT, size * cam.z, 800, 'Archivo').width;
    const boxW = tw_ + pad * 2, boxH = size * cam.z * 1.55;
    out.push({ id: 'plate1', text: PLATE1_TEXT,
      x0: sx(cam, bx), y0: sy(cam, by), x1: sx(cam, bx) + boxW, y1: sy(cam, by) + boxH });
  }
  if (t >= 5.2 && t <= 8.0) {
    const s = STATIONS[1];
    const pos = s.pos;
    const bx = portrait ? BELT + 200 : pos + 240;
    const by = portrait ? pos - 100 : BELT - 190;
    const size = 28, pad = 14;
    const tw_ = measure(PLATE2_TEXT, size * cam.z, 800, 'Archivo').width;
    const boxW = tw_ + pad * 2, boxH = size * cam.z * 1.55;
    out.push({ id: 'plate2', text: PLATE2_TEXT,
      x0: sx(cam, bx), y0: sy(cam, by), x1: sx(cam, bx) + boxW, y1: sy(cam, by) + boxH });
  }
  return out;
};

// ---------- fonts: define every face, load, then READY ----------
try {
  await Promise.all([
    document.fonts.load(`900 56px "Big Shoulders Display"`, TITLE_TEXT),
    document.fonts.load(`800 28px "Archivo"`, `${PLATE1_TEXT} ${PLATE2_TEXT}`),
  ]);
} catch (e) { throw e; }
await document.fonts.ready;

draw(0);
window.READY = true;
