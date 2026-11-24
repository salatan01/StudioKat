// Lemo smoke fixture: a 1 s 320x180 page that proves the vendored engine can
// render. No fonts, no external assets — it only needs a working canvas, so a
// failure here is the environment, not the clip. The page contract is the real
// one: window.DUR, window.render(t), window.READY after the fonts are ready.
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const W = canvas.width;
const H = canvas.height;
const TAU = Math.PI * 2;

window.DUR = 1;

function draw(t) {
  const p = Math.min(1, Math.max(0, t / window.DUR));

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';

  ctx.fillStyle = '#15161a';
  ctx.fillRect(0, 0, W, H);

  // one bar sweeps left to right as t advances — pure function of t
  const bw = Math.round(W * 0.14);
  const bh = Math.round(H * 0.2);
  const x = Math.round(p * (W - bw));
  const y = Math.round((H - bh) / 2);
  ctx.fillStyle = '#e4572e';
  ctx.fillRect(x, y, bw, bh);

  // a marker that pulses once over the clip, to prove t is live
  ctx.fillStyle = 'rgba(236,234,228,' + (0.5 + 0.5 * Math.sin(TAU * p)).toFixed(3) + ')';
  ctx.beginPath();
  ctx.arc(W * 0.08, H * 0.08, W * 0.02, 0, TAU);
  ctx.fill();
}

window.render = draw;

await document.fonts.ready;

draw(0);
window.READY = true;
