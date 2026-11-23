// Lemo clip page. `lemo_render new` copies this template into
// projects/<id>/lemo/clips/<clip_id>/ and replaces the __TOKEN__ placeholders.
//
// Page contract: set window.DUR, draw second t in window.render(t), and set
// window.READY = true only after the fonts (and any other assets) have loaded.
// Deterministic: every value derives from t — no Math.random, no clock.
//
// This placeholder draws a grid and a title block so `validate` passes before
// you author the clip. Replace the drawing with the real clip, using the demo
// modules named in references/style-map.md as grammar only — never their story.
import { clamp, lerp, seg, ss, hash, mulberry } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const W = __WIDTH__, H = __HEIGHT__;
const TAU = Math.PI * 2;

// clip.json is the source of truth for the clip's text.
let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const SUBJECT = META.subject || 'Lemo clip';
const ONE_IDEA = META.one_idea || '';

window.DUR = __DURATION__;

const INK = '#15161a';
const PAPER = '#eceae4';
const ACCENT = '#e4572e';

function fitText(text, x, y, maxW, size, weight) {
  let s = size;
  for (let i = 0; i < 48; i++) {
    ctx.font = `${weight} ${Math.round(s)}px "Clip Sans"`;
    if (ctx.measureText(text).width <= maxW || s <= 12) break;
    s *= 0.94;
  }
  ctx.fillText(text, x, y);
}

function draw(t) {
  const p = ss(seg(t, 0, window.DUR)); // 0 -> 1 across the clip

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';

  ctx.fillStyle = PAPER;
  ctx.fillRect(0, 0, W, H);

  // grid
  const cols = 12, rows = Math.round(cols * H / W);
  ctx.strokeStyle = 'rgba(21,22,26,0.14)';
  ctx.lineWidth = Math.max(1, W / 1920);
  ctx.beginPath();
  for (let i = 1; i < cols; i++) { const x = Math.round(W * i / cols) + 0.5; ctx.moveTo(x, 0); ctx.lineTo(x, H); }
  for (let j = 1; j < rows; j++) { const y = Math.round(H * j / rows) + 0.5; ctx.moveTo(0, y); ctx.lineTo(W, y); }
  ctx.stroke();

  // fixed deterministic dots that breathe on t
  const rnd = mulberry(7);
  for (let i = 0; i < 36; i++) {
    const x = rnd() * W, y = rnd() * H;
    const pulse = 0.5 + 0.5 * Math.sin(TAU * (t / window.DUR) + hash(i) * TAU);
    ctx.fillStyle = 'rgba(21,22,26,' + (0.08 + 0.10 * pulse).toFixed(3) + ')';
    ctx.beginPath();
    ctx.arc(x, y, lerp(W * 0.003, W * 0.008, hash(i + 100)), 0, TAU);
    ctx.fill();
  }

  // one accent cell slides along the grid as t advances
  const bw = W / cols, bh = H / rows;
  const ci = Math.min(cols - 1, Math.floor(p * cols));
  ctx.fillStyle = ACCENT;
  ctx.fillRect(ci * bw, (rows - 2) * bh, bw, bh);

  // title block: the subject, then the one idea
  const margin = Math.round(W * 0.06);
  const title = Math.round(W * 0.072);
  const sub = Math.round(W * 0.026);
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = INK;
  fitText(SUBJECT, margin, H * 0.5, W - 2 * margin, title, 700);
  if (ONE_IDEA) {
    ctx.fillStyle = 'rgba(21,22,26,0.72)';
    fitText(ONE_IDEA, margin, H * 0.5 + title * 0.9, W - 2 * margin, sub, 500);
  }
}

window.render = t => draw(clamp(t, 0, window.DUR));

try {
  await Promise.all([
    document.fonts.load(`700 ${Math.round(W * 0.072)}px "Clip Sans"`, SUBJECT),
    document.fonts.load(`500 ${Math.round(W * 0.026)}px "Clip Sans"`, ONE_IDEA || 'A'),
  ]);
} catch (e) {}
await document.fonts.ready;

draw(0);
window.READY = true;
