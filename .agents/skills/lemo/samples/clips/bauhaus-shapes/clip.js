// Bauhaus Shapes — "How compound growth stacks".
//
// A point becomes a line, the line a plane, and the plane's area doubles each
// beat: 1 -> 2 -> 4. Flat primary geometry on paper, hard edges — discs,
// squares and straight rules only. Original StudioKat clip; the vendored demo
// is technique only, its story and numbers are not reused. Deterministic:
// every value derives from `t`.

import { clamp, ss, TAU } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
canvas.width = W;
canvas.height = H;

window.DUR = (META.duration_seconds | 0) || 6;

// ---- layout (scales to the rendered aspect) ---------------------------------
const portrait = H > W;
const cx = W * 0.5;
const cy = portrait ? H * 0.30 : H * 0.50;   // 16:9 centred ; 9:16 upper two-thirds
const u = Math.round(Math.min(W, H) * 0.13);  // unit module
const M = Math.round(Math.min(W, H) * 0.04);  // margin
const numSize = Math.round(u * 0.45);         // running-total label size
const ax = cx - u / 2;                        // figure bottom-left (unit square)
const ay = cy - u / 2;
const lw = Math.max(2, Math.round(u * 0.05)); // rule thickness

// ---- timeline (beats of 0.9 s; the final figure holds to 6 s) ---------------
const D = 0.9;
const T_POINT = 0.0;
const T_LINE = D;
const T_PLANE = 2 * D;
const T_DOUBLE_2 = 3 * D;
const T_DOUBLE_4 = 4 * D;

function progress(t, t0) { return ss(clamp((t - t0) / D, 0, 1)); }

// ---- palette: paper, ink, one flat (red) and a tint for newly added area ----
const PAPER = '#f7f5f0';
const INK = '#212121';
const FLAT = '#c62828';
const TINT = '#ef9a9a';

// ---- type -------------------------------------------------------------------
const HEADLINE = 'area doubles each beat';

function setText(size, weight) {
  ctx.font = `${weight} ${Math.round(size)}px "Jost"`;
  ctx.letterSpacing = '0px';
  ctx.textBaseline = 'alphabetic';
}
function measure(text, size, weight) {
  setText(size, weight);
  return ctx.measureText(text).width;
}
function drawTextC(text, x, y, size, weight, col) {   // centred on (x, y)
  setText(size, weight);
  ctx.fillStyle = col;
  const w = ctx.measureText(text).width;
  ctx.fillText(text, Math.round(x - w / 2), Math.round(y + size * 0.35));
}

// ---- figure state at time t -------------------------------------------------
function figureState(t) {
  t = clamp(t, 0, window.DUR);
  const pc = progress(t, T_PLANE);
  const active2 = t >= T_DOUBLE_2 && t < T_DOUBLE_2 + D;
  const p2 = active2 ? progress(t, T_DOUBLE_2) : 0;
  const active4 = t >= T_DOUBLE_4 && t < T_DOUBLE_4 + D;
  const p4 = active4 ? progress(t, T_DOUBLE_4) : 0;
  let fw = 0, fh = 0, phase = 0;
  let tintX = 0, tintY = 0, tintW = 0, tintH = 0;
  if (pc > 0) { fw = u * pc; fh = u; phase = 2; }
  if (active2) { fw = u + u * p2; fh = u; tintX = ax + u; tintY = ay; tintW = u * p2; tintH = u; phase = 3; }
  if (!active2 && t >= T_DOUBLE_2) { fw = 2 * u; fh = u; phase = 3; }
  if (active4) { fw = 2 * u; fh = u + u * p4; tintX = ax; tintY = ay + u; tintW = 2 * u; tintH = u * p4; phase = 4; }
  if (!active4 && t >= T_DOUBLE_4) { fw = 2 * u; fh = 2 * u; phase = 4; }
  return { fw, fh, phase, tintX, tintY, tintW, tintH };
}

// ---- drawing ----------------------------------------------------------------
function draw(t) {
  t = clamp(t, 0, window.DUR);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic';

  ctx.fillStyle = PAPER;
  ctx.fillRect(0, 0, W, H);

  const st = figureState(t);
  const { fw, fh, phase, tintX, tintY, tintW, tintH } = st;

  // point: lands at the figure's bottom-left corner (visible at t=0, grows during the beat)
  const pp = progress(t, T_POINT);
  if (t < T_LINE) {
    const r = u * (0.05 + 0.04 * pp);   // small visible base radius at t=0, grows to 0.09 u
    ctx.fillStyle = FLAT;
    ctx.beginPath();
    ctx.arc(Math.round(ax), Math.round(ay), Math.round(r), 0, TAU);
    ctx.fill();
  }

  // line: a rule rising from the point (becomes the figure's left edge)
  const pl = progress(t, T_LINE);
  if ((pl > 0 || phase >= 2) && t < T_DOUBLE_2) {
    const lh = (phase >= 2) ? fh : (u * pl);
    ctx.fillStyle = INK;
    ctx.fillRect(Math.round(ax), Math.round(ay), lw, Math.round(lh));
  }

  // figure body: flat area; the newly added block shows in tint during its beat
  if (fw > 0) {
    ctx.fillStyle = FLAT;
    ctx.fillRect(Math.round(ax), Math.round(ay), Math.round(fw), Math.round(fh));
    if (tintW > 0 && tintH > 0) {
      ctx.fillStyle = TINT;
      ctx.fillRect(Math.round(tintX), Math.round(tintY), Math.round(tintW), Math.round(tintH));
    }
    // the original line, re-struck as the figure's left edge
    if (phase >= 2) {
      ctx.fillStyle = INK;
      ctx.fillRect(Math.round(ax), Math.round(ay), lw, Math.round(fh));
    }
  }

  // running total label: 1 -> 2 -> 4
  let num = null, nx = cx, ny = cy;
  if (phase >= 2) { num = '1'; nx = ax + u / 2; ny = ay + u / 2; }
  if (phase >= 3) { num = '2'; nx = ax + u; ny = ay + u / 2; }
  if (phase >= 4) { num = '4'; nx = ax + u; ny = ay + u; }
  if (num) {
    drawTextC(num, nx, ny, numSize, 800, INK);
  }

  // headline: wipes in from the left (clip box matches the measured text,
  // capped so it never escapes the frame)
  const hp = progress(t, 0.4);
  if (hp > 0) {
    setText(H * 0.04, 600);
    const hw = ctx.measureText(HEADLINE).width;
    const revealW = Math.round(Math.min(hw + M, W - M) * hp);
    ctx.save();
    ctx.beginPath();
    ctx.rect(Math.round(M), Math.round(H * 0.07), revealW, Math.round(H * 0.06));
    ctx.clip();
    ctx.fillStyle = INK;
    ctx.fillText(HEADLINE, Math.round(M), Math.round(H * 0.07 + H * 0.042));
    ctx.restore();
  }
}

window.render = t => draw(clamp(t, 0, window.DUR));

// ---- text boxes for the reading-time check ----------------------------------
window.TEXTS = t => {
  t = clamp(t, 0, window.DUR);
  const out = [];
  const hp = progress(t, 0.4);
  if (hp > 0) {
    const hw = measure(HEADLINE, H * 0.04, 600);
    out.push({
      id: 'head',
      text: HEADLINE,
      x0: M, y0: H * 0.07,
      x1: M + hw, y1: H * 0.07 + H * 0.06,
    });
  }
  const st = figureState(t);
  let num = null, nx = cx, ny = cy;
  if (st.phase >= 2) { num = '1'; nx = ax + u / 2; ny = ay + u / 2; }
  if (st.phase >= 3) { num = '2'; nx = ax + u; ny = ay + u / 2; }
  if (st.phase >= 4) { num = '4'; nx = ax + u; ny = ay + u; }
  if (num) {
    const nw = measure(num, numSize, 800);
    const nh = numSize * 1.2;
    out.push({
      id: 'num',
      text: num,
      x0: Math.round(nx - nw / 2), y0: Math.round(ny - numSize * 0.4),
      x1: Math.round(nx + nw / 2), y1: Math.round(ny + numSize * 0.8),
    });
  }
  return out;
};

try {
  await Promise.all([
    document.fonts.load(`700 ${Math.round(H * 0.04)}px "Jost"`, HEADLINE + ' 1234'),
    document.fonts.load(`800 ${numSize}px "Jost"`, '1234'),
  ]);
} catch (e) {}
await document.fonts.ready;

draw(0);
window.READY = true;
