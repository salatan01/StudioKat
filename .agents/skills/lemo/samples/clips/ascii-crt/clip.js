// ASCII CRT · "A boot log that types itself"
//
// An original six-second boot log for a fictional machine ("VOIDBYTE") that
// types itself one line at a time on a character grid, then the camera pushes
// into the grid until a single glyph fills the frame. The screen is an amber
// phosphor CRT: power-on raster, barrel curvature, scanlines, phosphor glow.
//
// The vendored demo (styles/ascii-crt/demo) is the technique reference only — its
// own story, lines and composition are not used here. Deterministic: every value
// derives from `t`.

import { initTerm, glyph, text, cursor } from '/styles/ascii-crt/demo/term.js';
import { makeCRT } from '/styles/ascii-crt/demo/crt.js';
import { clamp, seg, eio } from '/core/lib.js';

const canvas = document.getElementById('c');
const iW = Math.max(2, Math.round(window.innerWidth) & ~1);   // even
const iH = Math.max(2, Math.round(window.innerHeight) & ~1); // even
canvas.width = iW;
canvas.height = iH;
window.DUR = 6;

const scene = document.createElement('canvas'); // offscreen: the character grid
scene.width = iW;
scene.height = iH;
const g = scene.getContext('2d');
const crt = makeCRT(canvas); // the CRT post-process draws into the visible canvas

await document.fonts.load('160px VT323');
await initTerm();

// ---- the clip's own boot log (original text; the demo's lines are not reused) --
const RATE = 24; // terminal types one glyph per frame at 24 fps
const LINES = [
  { id: 'boot-0', text: 'VOIDBYTE BIOS v4.2', t0: 1.00 },
  { id: 'boot-1', text: 'MEMORY 64K',         t0: 1.85 },
  { id: 'boot-2', text: 'READY',              t0: 2.35 },
];
const ZOOM0 = 4.60, ZOOM1 = 5.70; // character-grid zoom window

// ---- layout from the live viewport: ~80 columns (16:9) / ~40 narrow columns (9:16)
const portrait = iH > iW;
const COLS = portrait ? 40 : 80;
const MX = Math.max(8, Math.round(iW * 0.05));
const MY = Math.max(8, Math.round(iH * 0.06));
const grid = { ox: MX, oy: MY, cw: (iW - 2 * MX) / COLS, cols: COLS };

const rowTop = i => grid.oy + i * grid.cw * 2;

function typed(t, L) {
  return t < L.t0 ? 0 : Math.min(L.text.length, Math.floor((t - L.t0) * RATE));
}

function draw(t) {
  g.globalCompositeOperation = 'source-over';
  g.globalAlpha = 1;
  g.fillStyle = '#000';
  g.fillRect(0, 0, iW, iH);
  g.globalCompositeOperation = 'lighter';

  const z = eio(seg(t, ZOOM0, ZOOM1));
  const s = grid.cw + z * (Math.min(iW, iH) / 2 - grid.cw); // cell size at this zoom; final = half the frame

  if (z <= 0.0001) {
    for (let i = 0; i < LINES.length; i++) {
      const L = LINES[i];
      if (t < L.t0) continue;
      const n = typed(t, L);
      if (n <= 0) continue;
      text(g, L.text.slice(0, n), 0, i, { ox: grid.ox, oy: grid.oy, cw: grid.cw }, 1 - i * 0.18);
    }

    // block cursor at the end of the newest line that has started typing
    let lastIdx = -1;
    for (let i = LINES.length - 1; i >= 0; i--) if (t >= LINES[i].t0) { lastIdx = i; break; }
    if (lastIdx >= 0) {
      const L = LINES[lastIdx];
      const n = typed(t, L);
      if (n < L.text.length) cursor(g, n, lastIdx, { ox: grid.ox, oy: grid.oy, cw: grid.cw }, (t % 0.5) < 0.25 ? 1 : 0);
    }
  }

  if (z > 0.0001) {
    // the character-grid zoom: camera pushes into the grid until the glyph fills the frame
    const last = LINES[LINES.length - 1];
    const col = last.text.length - 1;
    glyph(g, last.text[col], (iW - s) / 2, (iH - 2 * s) / 2, s, 1, 0);
  }
}

window.render = t => {
  draw(clamp(t, 0, window.DUR));
  crt.render(scene, Math.round(t * 24), { power: seg(t, 0.30, 0.95), off: seg(t, 5.80, 6.00) });
};

window.TEXTS = t => t < ZOOM0 ? LINES.filter(L => t >= L.t0).map(L => {
  const i = LINES.indexOf(L);
  return {
    id: L.id,
    text: L.text,
    x0: Math.round(grid.ox),
    y0: Math.round(rowTop(i)),
    x1: Math.round(grid.ox + L.text.length * grid.cw),
    y1: Math.round(rowTop(i) + grid.cw * 2),
  };
}) : [];

await document.fonts.load('160px VT323');
await initTerm();
draw(0);
window.READY = true;
