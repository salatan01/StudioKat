// Mid-century Toon pilot — "How a thermos keeps tea hot".
//
// An original limited-animation spot written in the vendored style's grammar:
// the two-cel register (flat fills printed off the ink line, re-jittered on
// twos), the pressure-ribbon ink that never quite closes, abstract colour
// planes instead of a room, a held body with only the hands acting, and a
// paper finish over the lot. The presenter and the flask are our own drawings;
// the demo's cast (June, Pip) and its robot-vacuum story are not reused. The
// vendored modules are read as a codex of technique only.
//
// Deterministic: every value derives from `t` — no Math.random, no Date.now.

import { PAL, shape, plane, ink, ellipse, spline, rrect, rect, move, star, sparkle,
         atom, text, measure, twos, ss, eo, back, seg, reg, setClock, REG, hash,
         paperFinish, TAU, clamp, lerp } from '/styles/midcentury-toon/demo/engine/toon.js';
import { armJoints, drawHand } from '/styles/midcentury-toon/demo/engine/chars.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
canvas.width = W;
canvas.height = H;

window.DUR = 6;

// ---- the clip's own words ---------------------------------------------------
const KICKER = 'One small marvel';
const TITLE = ['HOW A THERMOS', 'KEEPS TEA HOT'];
const CAPTION = 'The sealed lid traps the rising heat.';
const DETAIL = 'HEAT STAYS IN';

// ---- timings: 120 bpm, a beat every half second ----------------------------
const T_KICK = 0.35, S_KICK = 0.7;
const T_TITLE = 0.7, S_TITLE = 0.55;
const T_CAP = 1.45, S_CAP = 0.5;
const T_RING = 2.35, S_RING = 0.45;
const T_LEAD = 2.55, S_LEAD = 0.35;
const T_PRESS0 = 3.0, T_PRESS1 = 3.30;   // anticipation: the hand settles down
const T_STROKE0 = 3.30, T_STROKE1 = 3.90; // the quick lift, easing out
const T_OVER0 = 3.90, T_OVER1 = 4.15;    // follow-through: the hand overshoots
const T_SETTLE0 = 4.15, T_SETTLE1 = 4.45; // and lands squarely on the beat
const T_TAG = 4.0, S_TAG = 0.35;
const T_STEAM = 3.55;
const BEAT = 0.5;

// ---- the presenter's rig ----------------------------------------------------
// local units: feet at (0,0), hair top about -560, facing +x. The engine's own
// shoulder points and arm lengths are reused so the rig matches the style.
const SH_F = [40, -384], SH_B = [-36, -386];
const UA = 100, FA = 92;
const TB = [96, -276];          // the flask hand (back arm) — holds the body low
const LID_DOWN = [156, -431];   // the lid hand (front arm), resting on the lid
const LID_UP = [154, -524];     // and lifted clear of the neck
const LID_OFF = [-21, -6];      // lid centre, relative to the lid hand
const NECK = [136, -426];       // the flask's open neck: where the steam leaves

// two-bone arm solve: reach a target with the style's arm, elbow bending by `bend`.
function ik(sh, target, bend) {
  const dx = target[0] - sh[0], dy = target[1] - sh[1];
  const d = Math.max(Math.abs(UA - FA) + 2, Math.min((UA + FA) * 0.995, Math.hypot(dx, dy)));
  const phi = Math.atan2(dy, dx);
  const tx = sh[0] + Math.cos(phi) * d, ty = sh[1] + Math.sin(phi) * d;
  const ca = clamp((UA * UA + d * d - FA * FA) / (2 * UA * d), -1, 1);
  const a1 = phi + bend * Math.acos(ca);
  const el = [sh[0] + Math.cos(a1) * UA, sh[1] + Math.sin(a1) * UA];
  const a2 = Math.atan2(ty - el[1], tx - el[0]);
  return { a1, a2 };
}

// the lift: hold, anticipate down, a quick stroke, a follow-through overshoot,
// then land. Everything is stepped on twos, so this reads as drawn-on-twos.
function liftQ(t) {
  if (t <= T_PRESS0) return 0;
  if (t < T_PRESS1) return -0.13 * ss(seg(t, T_PRESS0, T_PRESS1));
  if (t < T_STROKE1) return lerp(-0.13, 1, eo(seg(t, T_STROKE0, T_STROKE1)));
  if (t < T_OVER1) return lerp(1, 1.07, ss(seg(t, T_OVER0, T_OVER1)));
  return lerp(1.07, 1, ss(seg(t, T_SETTLE0, T_SETTLE1)));
}
const lidHand = q => [lerp(LID_DOWN[0], LID_UP[0], q), lerp(LID_DOWN[1], LID_UP[1], q)];

// ---- layout, scaled from W/H so one clip renders at any aspect --------------
const portrait = H > W;
const LAY = (() => {
  const s = portrait ? H * 0.50 / 620 : H * 0.56 / 620;
  const fx = portrait ? W * 0.42 : W * 0.34;
  const feetY = portrait ? H * 0.885 : H * 0.90;
  const mx = (portrait ? 0.06 : 0.05) * W;
  const kick = portrait ? H * 0.028 : H * 0.045;
  const titlePx = portrait ? H * 0.072 : H * 0.095;
  const maxTitle = portrait ? W * 0.82 : W * 0.52;
  const kickBaseline = portrait ? H * 0.07 : H * 0.075;
  return { s, fx, feetY, mx, kick, titlePx, maxTitle, kickBaseline };
})();
// local figure point -> screen point (used for the call-out, which tracks the hand)
const T = (lx, ly) => [LAY.fx + lx * LAY.s, LAY.feetY + ly * LAY.s];

// The title is fitted to the loaded slab face, so it is measured after
// document.fonts.ready (before then the fallback face under-measures).
let TSZ = 0, TITLE_BASE0 = 0;
function fitStr(str, maxW, start) {
  for (let p = start; p > start * 0.45; p -= 2) {
    if (measure(ctx, str, `${Math.round(p)}px Slab`) <= maxW) return Math.round(p);
  }
  return Math.round(start * 0.45);
}
function fitTitle() {
  TSZ = Math.min(fitStr(TITLE[0], LAY.maxTitle, LAY.titlePx), fitStr(TITLE[1], LAY.maxTitle, LAY.titlePx));
  TITLE_BASE0 = (portrait ? H * 0.085 : H * 0.105) + TSZ;
}

// ---- background: abstract planes, never a room ------------------------------
function drawBackground() {
  plane(ctx, rect(-W * 0.2, -H * 0.2, W * 1.4, H * 1.4), PAL.kraftL, { grain: 0.3 });
  // a light halo disc behind the keeper
  const [cx, cy] = T(0, -470);
  shape(ctx, ellipse(cx, cy, H * 0.40, H * 0.42, 40), { fill: PAL.paper, line: 0, grain: 0.25, seed: 5 });
  // the wall's only decoration: atomic-age motifs, kept clear of the type
  atom(ctx, W * 0.83, H * 0.28, Math.min(W, H) * 0.05, { color: PAL.kraftD, w: 3 });
  sparkle(ctx, W * 0.11, H * 0.36, Math.min(W, H) * 0.03, { fill: PAL.paperD });
  sparkle(ctx, W * 0.90, H * 0.60, Math.min(W, H) * 0.022, { fill: PAL.paperD });
  // the floor band, then a broken horizon
  plane(ctx, rect(-W * 0.2, LAY.feetY, W * 1.4, H * 0.5), PAL.kraft, { grain: 0.32 });
  ink(ctx, [[-W * 0.1, LAY.feetY], [W * 1.1, LAY.feetY]], 4,
      { color: PAL.kraftD, breaks: 0.42, seed: 9, taper: false });
}

// ---- the arm: a broad ink band under a narrower colour band ----------------
function drawArm(g, J, col, cuffCol, seed, handKind) {
  const P = spline([J.sh, [(J.sh[0] + J.el[0]) / 2, (J.sh[1] + J.el[1]) / 2], J.el,
    [(J.el[0] + J.ha[0]) / 2, (J.el[1] + J.ha[1]) / 2], J.ha], false, 6);
  ink(g, P, 25, { seed, taper: false, wob: 0.08 });
  const o = reg(seed, 1);
  ink(g, move(P, o[0] * 0.6, o[1] * 0.6), 17, { seed: seed + 1, taper: false, wob: 0.05, color: col });
  const a = J.a2, cx = J.ha[0] - Math.cos(a) * 8, cy = J.ha[1] - Math.sin(a) * 8;
  ink(g, [[cx + Math.cos(a + 1.57) * 11, cy + Math.sin(a + 1.57) * 11],
          [cx - Math.cos(a + 1.57) * 11, cy - Math.sin(a + 1.57) * 11]], 3,
      { seed: seed + 2, taper: false, color: cuffCol });
  drawHand(g, J.ha[0], J.ha[1], a, handKind, 1);
}

// ---- the keeper: our own presenter, drawn in the style's own engine ---------
function drawFigure(t) {
  const q = liftQ(t);
  const pose = { view: 'q' };
  pose.armB = ik(SH_B, TB, 1);
  pose.armF = ik(SH_F, lidHand(q), 1);
  const JB = armJoints(pose, 'B');
  const JF = armJoints(pose, 'F');
  const lh = lidHand(q);

  ctx.save();
  ctx.translate(LAY.fx, LAY.feetY);
  ctx.scale(LAY.s, LAY.s);

  // ground contact
  ctx.save(); ctx.globalAlpha = 0.16; ctx.fillStyle = PAL.ink;
  ctx.beginPath(); ctx.ellipse(8, 2, 92, 11, 0, 0, TAU); ctx.fill(); ctx.restore();

  drawArm(ctx, JB, PAL.blue, PAL.blueD, 70, 'grip');   // back arm, behind the body
  drawThermos(ctx, TB[0], TB[1]);
  drawSteam(ctx, t);

  // legs (cigarette trousers) and ink flats
  const legs = [[[-38, -286], [6, -286], [-2, -26], [-26, -26]],
                [[-2, -286], [42, -286], [30, -26], [8, -26]]];
  legs.forEach((Lg, i) => {
    const ax = (Lg[2][0] + Lg[3][0]) / 2;
    shape(ctx, rect(ax - 7, -30, 14, 18), { fill: PAL.skin, line: 0, grain: 0, seed: 40 + i });
    shape(ctx, Lg, { fill: PAL.plum, line: 3.8, grain: 0.3, breaks: 0.15, seed: 42 + i,
      shade: i === 1 ? [{ pts: [[14, -290], [50, -290], [50, 0], [12, 0]], color: PAL.brown, alpha: 0.25 }] : null });
    const fx2 = ax;
    shape(ctx, spline([[fx2 - 16, -12], [fx2 + 6, -15], [fx2 + 28, -6], [fx2 + 24, 0], [fx2 - 16, 0]], true, 4),
      { fill: PAL.ink, line: 0, off: [0, 0], grain: 0 });
  });

  // the smock (blue) with the accent apron (coral); one shade plane each
  shape(ctx, spline([[-50, -392], [-40, -410], [40, -410], [50, -392], [46, -286], [-46, -286]], true, 6),
    { fill: PAL.blue, line: 4.2, grain: 0.35, breaks: 0.2, seed: 50,
      shade: [{ pts: [[20, -412], [64, -412], [64, -284], [24, -284]], color: PAL.blueD, alpha: 0.5 }] });
  shape(ctx, spline([[-32, -386], [-36, -300], [36, -300], [32, -386]], true, 6),
    { fill: PAL.coral, line: 3.4, grain: 0.3, breaks: 0.25, seed: 51,
      shade: [{ pts: [[12, -390], [46, -390], [46, -294], [16, -294]], color: PAL.coralD, alpha: 0.45 }] });
  shape(ctx, rrect(-18, -344, 36, 28, 6), { fill: PAL.paper, line: 3, grain: 0.2, seed: 52 });   // apron pocket
  shape(ctx, rrect(-22, -414, 44, 13, 6), { fill: PAL.paper, line: 3, grain: 0.2, seed: 53 });   // collar

  drawHead(ctx);

  drawArm(ctx, JF, PAL.blue, PAL.blueD, 60, 'grip');   // front arm, over everything
  drawLid(ctx, lh[0], lh[1]);

  ctx.restore();
}

function drawHead(g) {
  shape(g, rrect(-13, -430, 26, 44, 8), { fill: PAL.skinD, line: 0, grain: 0.1, seed: 60 });     // neck
  shape(g, ellipse(0, -470, 50, 60, 30), { fill: PAL.skin, line: 4, grain: 0.15, breaks: 0.2, seed: 66 });
  // a middle-parted cap and a low bun — a different head from the demo's
  shape(g, spline([[-46, -486], [-30, -528], [10, -540], [46, -512], [40, -492], [16, -500], [-6, -498], [-28, -506]], true, 6),
    { fill: PAL.hair, line: 0, seed: 68, grain: 0.3 });
  shape(g, ellipse(-38, -540, 20, 18, 18), { fill: PAL.hair, line: 0, seed: 69, grain: 0.3 });
  shape(g, ellipse(22, -474, 7, 9, 14), { fill: PAL.ink, line: 0, grain: 0, off: [0, 0] });
  shape(g, ellipse(24.5, -478, 2.2, 2.6, 8), { fill: PAL.white, line: 0, grain: 0, off: [0, 0] });
  ink(g, [[11, -496], [33, -494]], 3.4, { seed: 90 });
  ink(g, spline([[9, -446], [20, -440], [30, -448]], false, 5), 3.2, { seed: 100 });
  shape(g, ellipse(31, -456, 9, 6, 14), { fill: PAL.pink, line: 0, grain: 0, seed: 101, alpha: 0.85 });
}

// ---- the flask: an original vacuum flask, drawn flat and off-register -------
function drawThermos(g, x, y) {
  g.save(); g.translate(x, y);
  shape(g, rrect(-4, -120, 86, 168, 20), { fill: PAL.teal, line: 4, grain: 0.3, breaks: 0.18, seed: 200,
    shade: [{ pts: [[40, -120], [82, -120], [82, 48], [44, 48]], color: PAL.tealD, alpha: 0.45 }] });
  shape(g, rrect(0, -76, 78, 30, 6), { fill: PAL.white, line: 3, grain: 0.2, seed: 201 });      // cream band
  shape(g, rrect(8, -70, 62, 18, 4), { fill: PAL.mustard, line: 2.6, grain: 0.2, seed: 202 });  // label plate
  shape(g, rrect(16, -136, 46, 20, 6), { fill: PAL.chrome, line: 3, grain: 0.15, seed: 203 });  // chrome collar
  shape(g, rrect(20, -150, 38, 26, 6), { fill: PAL.white, line: 3.4, grain: 0.15, seed: 204 }); // neck
  g.restore();
}

function drawLid(g, hx, hy) {
  const cx = hx + LID_OFF[0], cy = hy + LID_OFF[1];
  g.save(); g.translate(cx, cy);
  shape(g, rrect(-29, -19, 58, 38, 13), { fill: PAL.white, line: 3.8, grain: 0.2, breaks: 0.15, seed: 210,
    shade: [{ pts: [[6, -19], [29, -19], [29, 19], [8, 19]], color: PAL.paperD, alpha: 0.7 }] });
  shape(g, ellipse(0, -23, 9, 7, 14), { fill: PAL.chrome, line: 2.6, grain: 0.1, seed: 211 });
  g.restore();
}

// ---- held steam: the heat the lid was keeping in ----------------------------
// A wispy curl, printed as a soft-edged white ribbon so it reads on the cream
// halo (plain white would vanish there). Two strands, held once risen.
function drawSteam(g, t) {
  const on = ss(seg(t, T_STEAM, T_STEAM + 0.55));
  if (on <= 0) return;
  const [ox, oy] = NECK;
  for (let i = 0; i < 3; i++) {
    const ph = i * 2.3, rise = (118 + i * 30) * on;
    const amp = 20 + i * 9, lean = 12 + i * 7;   // a sideways drift, not a straight rail
    const pts = [];
    for (let k = 0; k <= 26; k++) {
      const u = k / 26;
      const y = oy - u * rise;
      const bulge = Math.sin(u * Math.PI);        // fattest mid-rise, thin foot and tip
      const x = ox + lean * u + Math.sin(u * 5.4 - t * 2.2 + ph) * amp * (0.35 + bulge);
      pts.push([x, y]);
    }
    // a soft warm edge, then the white core: a held curl of steam, tapered so it dissolves
    ink(g, pts, 30, { color: PAL.paperD, alpha: 0.85, wob: 0.5, seed: 220 + i * 2, taper: true });
    ink(g, pts, 17, { color: PAL.white, alpha: 1, wob: 0.5, seed: 221 + i * 2, taper: true });
  }
}

// ---- the call-out: a ring that opens onto the hand, with a leader ----------
function ringGeom() {
  const [cx, cy] = T(134, -484);
  return { cx, cy, rx: 88 * LAY.s, ry: 108 * LAY.s };
}
function tagRect() {
  const r = ringGeom();
  if (portrait) return { x: r.cx - W * 0.26, y: r.cy + r.ry + 22, w: W * 0.52, h: H * 0.062 };
  return { x: r.cx + r.rx + 26, y: r.cy - H * 0.042, w: W * 0.19, h: H * 0.085 };
}
function drawCallout(t) {
  const p = ss(seg(t, T_RING, T_RING + S_RING));
  if (p <= 0) return;
  const r = ringGeom();
  const a0 = -Math.PI / 2;
  ink(ctx, ellipse(r.cx, r.cy, r.rx, r.ry, 64, a0, a0 + TAU * p), 6,
      { closed: false, color: PAL.ink, breaks: 0.12, seed: 300, taper: false });
}

function drawTag(t) {
  const p = ss(seg(t, T_TAG, T_TAG + S_TAG));
  const l = seg(t, T_LEAD, T_LEAD + S_LEAD);
  const r = ringGeom(), b = tagRect();
  const anchor = portrait ? [b.x + b.w / 2, b.y] : [b.x, b.y + b.h / 2];
  if (l > 0) {
    const ang = Math.atan2(anchor[1] - r.cy, anchor[0] - r.cx);
    const edge = [r.cx + Math.cos(ang) * r.rx, r.cy + Math.sin(ang) * r.ry];
    const end = [lerp(edge[0], anchor[0], ss(l)), lerp(edge[1], anchor[1], ss(l))];
    ink(ctx, [edge, end], 5, { seed: 305, taper: false });
  }
  if (p <= 0) return;
  const k = back(p);
  const ccx = b.x + b.w / 2, ccy = b.y + b.h / 2;
  ctx.save();
  ctx.translate(ccx, ccy); ctx.scale(k, k); ctx.translate(-ccx, -ccy);
  shape(ctx, rrect(b.x, b.y, b.w, b.h, b.h * 0.2), { fill: PAL.paper, line: 3.2, grain: 0.22, breaks: 0.14, seed: 310 });
  star(ctx, b.x + b.h * 0.5, ccy, b.h * 0.26, { n: 8, fill: PAL.coral, seed: 311 });
  text(ctx, DETAIL, b.x + b.h * 0.86, ccy + 1,
    { font: `${Math.round(b.h * 0.42)}px Jost`, fill: PAL.ink, base: 'middle', track: b.h * 0.03 });
  ctx.restore();
}

// ---- two-plate lettering ----------------------------------------------------
function wipeText(str, x, baseline, fontPx, font, color, p, seed) {
  if (p <= 0) return;
  ctx.save();
  ctx.font = font; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  const w = ctx.measureText(str).width;
  ctx.beginPath(); ctx.rect(x - 6, baseline - fontPx * 1.05, (w + 12) * p, fontPx * 1.35); ctx.clip();
  ctx.fillStyle = color; ctx.fillText(str, x, baseline);
  ctx.restore();
}
function drawKicker(t) {
  const p = ss(seg(t, T_KICK, T_KICK + S_KICK));
  wipeText(KICKER, LAY.mx, LAY.kickBaseline, LAY.kick, `700 ${Math.round(LAY.kick)}px Oleo`, PAL.coralD, p, 340);
}
function drawTitle(t) {
  const font = `${Math.round(TSZ)}px Slab`;
  TITLE.forEach((line, i) => {
    const p = ss(seg(t, T_TITLE + i * 0.12, T_TITLE + i * 0.12 + S_TITLE));
    if (p <= 0) return;
    const y = TITLE_BASE0 + i * TSZ * 1.04;
    const w = measure(ctx, line, font);
    ctx.save();
    ctx.translate((1 - p) * -0.05 * W, 0);
    shape(ctx, rrect(LAY.mx - TSZ * 0.18, y - TSZ * 0.84, w + TSZ * 0.36, TSZ * 1.06, TSZ * 0.12),
      { fill: PAL.mustard, line: 0, grain: 0.28, seed: 330 + i });
    text(ctx, line, LAY.mx, y, { font, fill: PAL.ink, seed: 331 + i });
    ctx.restore();
  });
}

// ---- the caption card, bottom-centre ---------------------------------------
function captionRect() {
  if (portrait) return { x: W * 0.08, y: H * 0.90, w: W * 0.84, h: H * 0.062 };
  return { x: W * 0.37, y: H * 0.905, w: W * 0.46, h: H * 0.068 };
}
function drawCaption(t) {
  const p = ss(seg(t, T_CAP, T_CAP + S_CAP));
  if (p <= 0) return;
  const c = captionRect(), cx = c.x + c.w / 2, cy = c.y + c.h / 2;
  const k = back(p);
  ctx.save();
  ctx.globalAlpha = p;
  ctx.translate(cx, cy); ctx.scale(k, k); ctx.translate(-cx, -cy);
  shape(ctx, rrect(c.x, c.y, c.w, c.h, c.h * 0.42), { fill: PAL.paper, line: 3.2, grain: 0.22, breaks: 0.14, seed: 320 });
  star(ctx, c.x + c.h * 0.52, cy, c.h * 0.26, { n: 8, fill: PAL.coral, seed: 321 });
  star(ctx, c.x + c.w - c.h * 0.52, cy, c.h * 0.26, { n: 8, fill: PAL.mustard, seed: 322 });
  const px = Math.round(c.h * 0.40);
  const font = `${px}px Jost`;
  const maxW = c.w - c.h * 1.5;
  let useFont = font;
  for (let p2 = px; p2 > px * 0.6; p2 -= 2) {
    if (measure(ctx, CAPTION, `${p2}px Jost`) <= maxW) { useFont = `${p2}px Jost`; break; }
  }
  text(ctx, CAPTION, cx, cy + 1, { font: useFont, fill: PAL.ink, align: 'center', base: 'middle' });
  ctx.restore();
}

// ---- frame ------------------------------------------------------------------
function camK(t) { return 1 + 0.022 * ss(seg(t, 0.15, window.DUR)); }

function draw(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left'; ctx.letterSpacing = '0px';
  setClock(t);
  // the cel misregistration re-rolls on the beat
  const beat = Math.floor(t / BEAT + 1e-6);
  REG.dx = 6 + (hash(beat, 11, 1) - 0.5) * 2.4;
  REG.dy = 4 + (hash(beat, 11, 2) - 0.5) * 2.4;

  const tq = twos(t);                       // bodies, hands and the paper step at 12 fps

  ctx.fillStyle = PAL.paper;
  ctx.fillRect(0, 0, W, H);

  ctx.save();                               // the tripod: a slow push, never handheld
  const k = camK(t);
  ctx.translate(W / 2, H / 2); ctx.scale(k, k); ctx.translate(-W / 2, -H / 2);
  drawBackground();
  drawFigure(tq);
  ctx.restore();

  drawCallout(t);
  drawTag(t);
  drawTitle(t);
  drawKicker(t);
  drawCaption(t);

  paperFinish(ctx, W, H);
}

window.render = t => draw(clamp(t, 0, window.DUR));

// text the viewer must read, with its screen-space box
window.TEXTS = () => {
  const font = `${Math.round(TSZ)}px Slab`;
  const w1 = measure(ctx, TITLE[0], font), w2 = measure(ctx, TITLE[1], font);
  const c = captionRect(), b = tagRect();
  return [
    { id: 'kicker', text: KICKER, x0: LAY.mx, y0: LAY.kickBaseline - LAY.kick, x1: LAY.mx + LAY.maxTitle * 0.5, y1: LAY.kickBaseline + LAY.kick * 0.3 },
    { id: 'title1', text: TITLE[0], x0: LAY.mx, y0: TITLE_BASE0 - TSZ, x1: LAY.mx + w1, y1: TITLE_BASE0 + TSZ * 0.2 },
    { id: 'title2', text: TITLE[1], x0: LAY.mx, y0: TITLE_BASE0 + TSZ * 1.04 - TSZ, x1: LAY.mx + w2, y1: TITLE_BASE0 + TSZ * 1.24 },
    { id: 'caption', text: CAPTION, x0: c.x, y0: c.y, x1: c.x + c.w, y1: c.y + c.h },
    { id: 'tag', text: DETAIL, x0: b.x, y0: b.y, x1: b.x + b.w, y1: b.y + b.h },
  ];
};

try {
  await Promise.all([
    '400 100px Oleo', '700 100px Oleo', '100px Slab',
    '400 100px Jost', '500 100px Jost', '700 100px Jost',
  ].map(f => document.fonts.load(f, 'HOW A THERMOS KEEPS TEA HOT 0123456789.')));
} catch (e) {}
await document.fonts.ready;

fitTitle();   // measure the title against the now-loaded slab face
draw(0);
window.READY = true;
