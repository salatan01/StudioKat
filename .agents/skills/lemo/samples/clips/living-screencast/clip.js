// Living Screencast — "Cascade: filing a task".
// The original mascot Pebble presses "Add to board" inside the invented
// Cascade UI, and a new task row lands on the board. Drawn only from
// ui_spec.json. Pebble is an original StudioKat character; no real product
// or brand is named. Deterministic: every value derives from `t`. No
// Math.random / Date.now.

import { clamp, lerp, ss, spring } from '/core/lib.js';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let META = {};
try { META = await (await fetch('clip.json')).json(); } catch {}
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
canvas.width = W;
canvas.height = H;

const res = await fetch('ui_spec.json');
if (!res.ok) throw new Error(`ui_spec.json failed: ${res.status}`);
const SPEC = await res.json();

window.DUR = 6;

const PORTRAIT = H > W;

// palette: neutral ground + ink + exactly one accent (scarf, active state)
const C = {
  ground: '#f5f3ee',
  pane: '#ffffff',
  border: '#d9d7ce',
  ink: '#1c1a18',
  accent: '#e8643c',
  mute: '#7a766f',
  body: '#e7e5e0',
};

const SAMPLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,.—';

function layout() {
  const win = { x: 0, y: 0, w: 0, h: 0 };
  const sidebar = { x: 0, y: 0, w: 0, h: 0 };
  const board = { x: 0, y: 0, w: 0, h: 0 };
  const composer = { x: 0, y: 0, w: 0, h: 0 };
  const mascot = { x: 0, y: 0, w: 0, h: 0 };
  if (PORTRAIT) {
    // 9:16: window fills the width; panes stack vertically; mascot clear of controls
    win.x = 40; win.y = 50; win.w = W - 80; win.h = H - 100;
    const cx = win.x + 36; const cw = win.w - 72;
    sidebar.x = cx; sidebar.y = win.y + 105; sidebar.w = cw; sidebar.h = 300;
    board.x = cx; board.y = sidebar.y + sidebar.h + 26; board.w = cw; board.h = 540;
    composer.x = cx; composer.y = board.y + board.h + 26; composer.w = cw; composer.h = 400;
    mascot.x = cx + cw * 0.5 - 110; mascot.y = win.y + win.h + 30; mascot.w = 220; mascot.h = 140;
  } else {
    // 16:9: wide window with the mascot beside the active pane
    win.x = 250; win.y = 80; win.w = 1180; win.h = 910;
    const cx = win.x + 40;
    const inner = win.w - 80;
    const gap = 20;
    const sw = 200;
    const bw = 450;
    sidebar.x = cx; sidebar.y = win.y + 100; sidebar.w = sw; sidebar.h = 710;
    board.x = cx + sw + gap; board.y = win.y + 100; board.w = bw; board.h = 710;
    composer.x = cx + sw + gap + bw + gap; composer.y = win.y + 100;
    composer.w = inner - sw - bw - 2 * gap; composer.h = 710;
    mascot.x = win.x + win.w + 28; mascot.y = win.y + 260; mascot.w = 250; mascot.h = 150;
  }
  return { win, sidebar, board, composer, mascot };
}

const L = layout();

const app = (SPEC && SPEC.app) ? SPEC.app : 'Cascade';
const winTitle = (SPEC && SPEC.window && SPEC.window.title) ? SPEC.window.title : app + ' — Launch Board';

const panes = (SPEC && SPEC.panes) || [];
const sidebarPane = panes.find(p => p.id === 'sidebar') || { title: 'Boards', items: [] };
const boardPane = panes.find(p => p.id === 'board') || { title: 'Launch Board', items: [] };
const composerPane = panes.find(p => p.id === 'composer') || { title: 'New task', items: [] };

const newLabel = ((composerPane.items.find(it => it.id === 'title') || {}).value) || 'Pin the source cards';

// button geometry (composer's "Add to board" control)
const buttonW = Math.min(200, L.composer.w - 60);
const buttonH = 38;
const buttonX = L.composer.x + 24;
const buttonY = L.composer.y + 252;
const buttonCenter = { x: buttonX + buttonW / 2, y: buttonY + buttonH / 2 };

// ---------- drawing helpers ----------
function setFont(weight, size, family) {
  ctx.font = `${weight} ${size}px "${family}"`;
  ctx.textBaseline = 'alphabetic';
  ctx.textAlign = 'left';
}
function textWidth(text, size, weight, family) {
  setFont(weight, size, family);
  return ctx.measureText(text).width;
}
function drawText(text, x, y, size, weight, family, color) {
  setFont(weight, size, family);
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}
function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

// ---------- animation (all derived from t) ----------
function mascotOff(t) {
  if (t < 0.8) return (1 - ss(clamp(t / 0.8))) * 70;
  return Math.sin(t * 3.0) * 1.5;
}
function armReach(t) {
  if (t < 0.8) return 0;
  if (t < 1.35) return ss(clamp((t - 0.8) / 0.55));
  if (t < 1.6) return 1;
  if (t < 2.1) return 1 + 0.3 * clamp((t - 1.6) / 0.5);
  return 1 - clamp((t - 2.1) / 0.4);
}
function bodySquash(t) {
  if (t >= 1.35 && t < 1.6) return Math.sin((t - 1.4) / 0.2 * Math.PI) * 3;
  if (t >= 1.6 && t < 2.1) return 5 * (1 - clamp((t - 1.6) / 0.5));
  return 0;
}
function hop(t) {
  if (t >= 2.05 && t < 2.6) return spring(clamp((t - 2.05) / 0.55)) * 6;
  return 0;
}
function buttonPress(t) {
  if (t < 1.6) return 0;
  return Math.min(ss(clamp((t - 1.6) / 0.45)), 1);
}
function accented(t) { return t >= 2.05; }
function rowAlpha(t) {
  if (t < 2.5) return 0;
  if (t < 2.62) return ss(clamp((t - 2.5) / 0.12));
  return 1;
}
function cursorPos(t) {
  if (t < 1.6) return null;
  const p = ss(clamp((t - 1.6) / 0.55));
  const start = { x: L.mascot.x + L.mascot.w * 0.5 + 44, y: L.mascot.y + L.mascot.h * 0.5 + 6 };
  return { x: lerp(start.x, buttonCenter.x, p), y: lerp(start.y, buttonCenter.y, p) };
}

// ---------- mascot (Pebble): rounded-triangle body, dot eyes, curved mouth,
// thin stick arms, stubby legs, scarf in the accent colour ----------
function drawMascot(t) {
  const mx = L.mascot.x + L.mascot.w * 0.5;
  const my = L.mascot.y + L.mascot.h * 0.5 + mascotOff(t) - hop(t);
  const oy = bodySquash(t);
  const reach = armReach(t);
  const bw = 44, bh = 58;

  // scarf (the single accent colour)
  ctx.fillStyle = C.accent;
  roundRect(mx - bw * 0.72, my - bh * 0.62, bw * 1.44, 12, 4);
  ctx.fill();

  // body (rounded triangle)
  ctx.fillStyle = C.body;
  ctx.strokeStyle = C.ink;
  ctx.lineWidth = 2.5;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(mx, my - bh * 0.5 + oy);
  ctx.lineTo(mx - bw, my + bh * 0.35 + oy);
  ctx.lineTo(mx + bw, my + bh * 0.35 + oy);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // legs (stubby)
  const lw = 16, lh = 24;
  [mx - bw + 10, mx + bw - 10 - lw].forEach((lx) => {
    roundRect(lx, my + bh * 0.35 + oy + 4, lw, lh, 6);
    ctx.fillStyle = C.body; ctx.fill();
    ctx.strokeStyle = C.ink; ctx.lineWidth = 2; ctx.stroke();
  });

  // left arm (idle, down)
  ctx.strokeStyle = C.ink;
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(mx - bw + 6, my + bh * 0.1 + oy);
  ctx.lineTo(mx - bw - 10, my + bh * 0.45 + oy);
  ctx.stroke();

  // right arm (points, then presses the button)
  const handX = mx + bw + reach * (buttonCenter.x - (mx + bw));
  const handY = my + bh * 0.1 + oy + reach * (buttonCenter.y - (my + bh * 0.1 + oy));
  ctx.beginPath();
  ctx.moveTo(mx + bw - 6, my + bh * 0.1 + oy);
  ctx.lineTo(handX, handY);
  ctx.stroke();
  if (reach > 0.9) {
    ctx.fillStyle = C.ink;
    ctx.beginPath();
    ctx.arc(handX, handY, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  // eyes (dots) and mouth (small curve)
  ctx.fillStyle = C.ink;
  ctx.beginPath();
  ctx.arc(mx - 12, my - bh * 0.22, 4.5, 0, Math.PI * 2);
  ctx.arc(mx + 12, my - bh * 0.22, 4.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = C.ink;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(mx - 6, my + 4);
  ctx.quadraticCurveTo(mx, my + 9, mx + 6, my + 4);
  ctx.stroke();
}

// ---------- cursor (pointer): travels to the control the mascot presses ----------
function drawCursor(t) {
  const cp = cursorPos(t);
  if (!cp) return;
  const ang = Math.atan2(buttonCenter.y - cp.y, buttonCenter.x - cp.x);
  ctx.save();
  ctx.translate(cp.x, cp.y);
  ctx.rotate(ang);
  ctx.fillStyle = C.ink;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-10, -6);
  ctx.lineTo(-10, 6);
  ctx.closePath();
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(-14, 0);
  ctx.lineTo(-28, 0);
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.ink;
  ctx.stroke();
  ctx.restore();
}

// ---------- panes ----------
function drawWindow() {
  const p = L.win;
  ctx.fillStyle = C.pane;
  roundRect(p.x, p.y, p.w, p.h, 10);
  ctx.fill();
  ctx.strokeStyle = C.border;
  ctx.lineWidth = 1.5;
  ctx.stroke();
  drawText(winTitle, p.x + 24, p.y + 34, 20, 700, 'Inter', C.ink);
  ctx.strokeStyle = C.border;
  ctx.beginPath();
  ctx.moveTo(p.x + 24, p.y + 56);
  ctx.lineTo(p.x + p.w - 24, p.y + 56);
  ctx.stroke();
}

function drawPaneTitle(pane, text) {
  drawText(text, pane.x + 24, pane.y + 42, 24, 700, 'Newsreader', C.ink);
  ctx.strokeStyle = C.border;
  ctx.beginPath();
  ctx.moveTo(pane.x + 24, pane.y + 66);
  ctx.lineTo(pane.x + pane.w - 24, pane.y + 66);
  ctx.stroke();
}

function drawRow(label, state, x, y) {
  const w = textWidth(label, 18, 500, 'Inter');
  ctx.fillStyle = C.ink;
  ctx.fillText(label, x, y);
  if (state === 'done') {
    ctx.beginPath();
    ctx.moveTo(x, y - 2);
    ctx.lineTo(x + w, y - 2);
    ctx.stroke();
  } else {
    ctx.strokeStyle = C.mute;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(x + w + 12, y, 5, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.strokeStyle = C.border;
  ctx.lineWidth = 1;
}

function drawSidebar() {
  const p = L.sidebar;
  drawPaneTitle(p, sidebarPane.title);
  sidebarPane.items.forEach((it, i) => {
    const y = p.y + 100 + i * 46;
    const sel = it.state === 'selected';
    if (sel) {
      ctx.fillStyle = '#f0ede4';
      roundRect(p.x + 16, y - 24, p.w - 32, 32, 8);
      ctx.fill();
    }
    drawText(it.label, p.x + 24, y, 18, 500, 'Inter', C.ink);
  });
}

function drawBoard(t) {
  const p = L.board;
  drawPaneTitle(p, boardPane.title);
  boardPane.items.forEach((it, i) => {
    drawRow(it.label, it.state, p.x + 24, p.y + 100 + i * 48);
  });
  const ny = p.y + 100 + boardPane.items.length * 48;
  const a = rowAlpha(t);
  if (a > 0) {
    ctx.globalAlpha = a;
    drawRow(newLabel, 'todo', p.x + 24, ny);
    ctx.globalAlpha = 1;
  }
}

function drawComposer(t) {
  const p = L.composer;
  drawPaneTitle(p, composerPane.title);
  composerPane.items.forEach((it, i) => {
    const y = p.y + 100 + i * 56;
    drawText(it.label, p.x + 24, y, 18, 500, 'Inter', C.ink);
    if (it.value !== undefined) {
      drawText(String(it.value), p.x + 24, y + 30, 18, 500, 'Inter', C.ink);
    }
    if (it.id === 'add') {
      const press = buttonPress(t);
      const act = accented(t);
      const by = buttonY + press * 4;
      ctx.fillStyle = act ? C.accent : C.pane;
      ctx.strokeStyle = act ? C.accent : C.ink;
      ctx.lineWidth = 1.5;
      roundRect(buttonX, by, buttonW, buttonH, 8);
      ctx.fill();
      ctx.stroke();
      setFont(700, 18, 'Inter');
      ctx.fillStyle = C.ink;
      const bw = textWidth(it.label, 18, 700, 'Inter');
      ctx.fillText(it.label, buttonX + (buttonW - bw) / 2, by + 24);
    }
  });
}

// ---------- frame ----------
function draw(t) {
  t = clamp(t, 0, window.DUR);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.textBaseline = 'alphabetic';

  ctx.fillStyle = C.ground;
  ctx.fillRect(0, 0, W, H);

  drawWindow();
  drawSidebar();
  drawBoard(t);
  drawComposer(t);
  drawMascot(t);
  drawCursor(t);
}

window.render = t => draw(clamp(t, 0, window.DUR));

// ---------- readable text (window.TEXTS) ----------
function textSpecs() {
  const s = [];
  s.push({ id: 'wintitle', text: winTitle, x: L.win.x + 24, y: L.win.y + 34, size: 20, weight: 700, family: 'Inter', show: () => true });
  s.push({ id: 'sidebar-title', text: sidebarPane.title, x: L.sidebar.x + 24, y: L.sidebar.y + 42, size: 24, weight: 700, family: 'Newsreader', show: () => true });
  sidebarPane.items.forEach((it, i) => {
    s.push({ id: `side-${it.id}`, text: it.label, x: L.sidebar.x + 24, y: L.sidebar.y + 100 + i * 46, size: 18, weight: 500, family: 'Inter', show: () => true });
  });
  s.push({ id: 'board-title', text: boardPane.title, x: L.board.x + 24, y: L.board.y + 42, size: 24, weight: 700, family: 'Newsreader', show: () => true });
  boardPane.items.forEach((it, i) => {
    s.push({ id: `board-${it.id}`, text: it.label, x: L.board.x + 24, y: L.board.y + 100 + i * 48, size: 18, weight: 500, family: 'Inter', show: () => true });
  });
  s.push({ id: 'board-new', text: newLabel, x: L.board.x + 24, y: L.board.y + 100 + boardPane.items.length * 48, size: 18, weight: 500, family: 'Inter', show: (t) => t >= 2.62 });
  s.push({ id: 'composer-title', text: composerPane.title, x: L.composer.x + 24, y: L.composer.y + 42, size: 24, weight: 700, family: 'Newsreader', show: () => true });
  composerPane.items.forEach((it, i) => {
    const y = L.composer.y + 100 + i * 56;
    if (it.id !== 'add') {
      s.push({ id: `comp-${it.id}-label`, text: it.label, x: L.composer.x + 24, y: y, size: 18, weight: 500, family: 'Inter', show: () => true });
    }
    if (it.value !== undefined) {
      s.push({ id: `comp-${it.id}-value`, text: String(it.value), x: L.composer.x + 24, y: y + 30, size: 18, weight: 500, family: 'Inter', show: () => true });
    }
    if (it.id === 'add') {
      s.push({ id: 'composer-add', text: it.label, x: buttonX, y: buttonY + 24, size: 18, weight: 700, family: 'Inter', show: () => true, centered: true, cw: buttonW });
    }
  });
  return s;
}

const TEXTSPEC = textSpecs();

window.TEXTS = (t) => {
  const out = [];
  for (const sp of TEXTSPEC) {
    if (!sp.show(t)) continue;
    const w = textWidth(sp.text, sp.size, sp.weight, sp.family);
    const x = sp.centered ? sp.x + (sp.cw - w) / 2 : sp.x;
    out.push({
      id: sp.id, text: sp.text,
      x0: x - 2, y0: sp.y - sp.size * 0.9,
      x1: x + w + 2, y1: sp.y + sp.size * 0.28,
    });
  }
  return out;
};

// ---------- fonts: define every face, load each, do NOT swallow rejections ----------
await document.fonts.load(`400 20px "Inter"`, SAMPLE);
await document.fonts.load(`700 24px "Newsreader"`, SAMPLE);
await document.fonts.load(`700 18px "Inter"`, SAMPLE);
await document.fonts.load(`500 18px "Inter"`, SAMPLE);
await document.fonts.ready;

window.READY = true;
draw(0);
