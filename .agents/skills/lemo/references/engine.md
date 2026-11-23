# Lemo engine: the page contract, server and render commands

This documents only what the vendored engine at `.agents/skills/lemo/library/core/` actually does.
Read `core/render/page.mjs`, `still.mjs`, `video.mjs`, `events.mjs`, `readcheck.mjs`, `serve.mjs` and
`core/lib.js` before you rely on anything here.

## The render server

`core/render/serve.mjs` is a minimal static server, on purpose: ES modules cannot load over
`file://`.

- **Root.** `core/render/page.mjs` sets `ROOT` to the `library/` directory (two levels up from
  `core/render/`). So `/core/lib.js`, `/styles/<id>/demo/...` and `/assets/fonts/<path>` all resolve
  from `library/`.
- **`/@film/`.** A demo folder *outside* the root — your clip at
  `projects/<id>/lemo/clips/<clip_id>/` — is mounted at `/@film/`. The page URL becomes
  `http://127.0.0.1:<port>/@film/index.html`, while `/core/...`, `/styles/...`, `/node_modules/...`
  and `/assets/...` still come from the library root. This is how your clip imports the engine.
- **Absolute imports only.** Because the clip is served from `/@film/`, a relative import (`./lib.js`,
  `../lib.js`, `styles/swiss-motion/demo/film.js`) is resolved against that mount and points at the
  clip folder, not the library — the server answers 404. Every engine import a clip makes must be an
  **absolute server URL**: `/core/lib.js`, `/styles/<style-id>/demo/...`, `/node_modules/...`,
  `/assets/...`. Only the clip's own files (`clip.js`, `clip.json`, files you place in the clip
  folder) load relatively.
- **Safety and types.** It binds `127.0.0.1` only, rejects a bad Host header (DNS rebinding), refuses
  paths that escape the root (403), and sends every text type as UTF-8 (`.html`, `.js`, `.mjs`,
  `.json`, `.css`, `.txt`). A page can still omit `<meta charset>` without mojibaking Chinese, but
  always declare it.
- Query strings pass through: `?name=value` reaches the page as `location.search`, which the demos
  use for variants (e.g. `?cut=a:b`, `?nosub=1`). The tools pass these with `--q`.

## The page contract

A page is `index.html` that loads a module script. It must set three globals:

| Global | Meaning |
|---|---|
| `window.DUR` | the clip length in **seconds** (a positive number). `video.mjs` requires `window.DUR > 0`. |
| `window.render(t)` | draw the frame at second `t`. Called once per output frame; must be deterministic and self-contained (reset transforms/state each call). |
| `window.READY = true` | set **only after** fonts and any other assets are loaded. Never set it on the first line: the tool waits for it and refuses to capture until it is `true`. |

Optional globals:

| Global | Meaning |
|---|---|
| `window.EV` | sound-effect / narration events. `events.mjs` reads `{ dur: window.DUR, ev: window.EV || [] }`. |
| `window.TEXTS(t)` | `[{id, text, x0, y0, x1, y1}]` — every readable text box at second `t`, in viewport pixels. Required by `readcheck.mjs`; see `authoring.md`. |
| `window.SUBS` / `window.SRT` | subtitle data some demos expose. Not part of the core contract; subtitles are checked from the srt, not from `TEXTS`. |

### How the tool reacts to the page

`openDemo()` (in `page.mjs`) is shared by every command:

- It waits for `window.READY === true`. A hint prints at **20 s**, the hard limit is **180 s**.
- A JavaScript error (`pageerror`) exits immediately, non-zero — a broken page never yields a film.
- A missing resource of type `script` or `document` (a 404 on the page or a script/module import)
  exits immediately. A missing **font** file prints a one-line warning naming the file; a missing
  fetch/xhr/image warns once and lets the page fall back.
- A lost WebGL context before the first frame fails the render (a blank film is worse than a failed
  one).

## Render commands and flags

All are run from the repository root as `node .agents/skills/lemo/library/core/render/<tool>.mjs
<demo> ...`. `lemo_render` wraps them; use them directly only to debug.

### Stills — `still.mjs`

```
node .../core/render/still.mjs <demo> <t> [<t> ...] [--range a:b:step] \
  [--q 'k=v&..'] [--prefix t_] [--out dir] [--size 1920x1080]
```

`<demo>` is the folder holding `index.html`. One page renders every time point. Writes
`<out>/<prefix><t>.jpg` (JPEG, quality 92); default `<out>` is `<demo>/stills`. It calls
`window.render(t)` for each `t`. `--range a:b:step` expands to points `a, a+step, …` up to `b`.

### Video — `video.mjs`

```
node .../core/render/video.mjs <demo> [--fps 24] [--workers 3] [--q 'k=v'] \
  [--out <demo>/out/video.mp4] [--size 1920x1080]
```

- Opens the page once to read `window.DUR`, then computes `TOTAL = Math.round(DUR * fps)` and splits
  the frames across workers. Each worker drives its own browser and pipes JPEG screenshots into
  ffmpeg (`libx264`, `-crf 14`, `-pix_fmt yuv420p`); the segments are joined losslessly at the end.
- `window.DUR` must be a positive number, and `--fps` must be `> 0`; `--workers` an integer `≥ 1`.
  Default 3 workers; a single render alone can use up to 6.
- Each `--out` has a `<out>.lock` holding the owner pid, so two renders cannot write the same file.
  A lock is stale (and taken over) when the pid is gone or the file is older than 12 hours. Use a
  different `--out` for each render.
- Set `RENDER_SLOTS` (an integer) to cap how many full renders run at once; `RENDER_SLOTS` unset means
  no limit.

### Events — `events.mjs`

```
node .../core/render/events.mjs <demo> [--q '...'] [--out file] [--size 1920x1080]
```

Reads the page with drawing off and writes `{ dur, ev }` from `window.DUR` and `window.EV`. Default
output is `<demo>/events.json`; pass `--q` and `--out` to export a variant without overwriting it.

### Reading-time check — `readcheck.mjs`

```
node .../core/render/readcheck.mjs <demo> [--q 'k=v'] [--step 0.04] \
  [--latin-cps 15] [--cjk-cps 4.5] [--pad 1.5] [--min 1.5] [--size 1920x1080]
```

Steps through the clip calling `window.render(t)` and `window.TEXTS(t)`, and checks that every block
of readable text stays fully in frame long enough to be read (`hanzi/kana/hangul ÷ cjk-cps + other
non-space chars ÷ latin-cps + pad`, never less than `min`). Exit `0` all pass, `1` a failure, `2` it
could not run (no `window.TEXTS`, or no text at all — not a pass). See `authoring.md` for the `TEXTS`
details.

### Shared flags

- `--size WxH`: width and height must be **even** (an H.264 yuv420p requirement) and between 16 and
  8192, e.g. `1920x1080`, `1080x1920`. Default `1920x1080`.
- `--q 'k=v&k2=v2'`: page query string, forwarded verbatim.
- `--fps`, `--workers`: as above.

## `core/lib.js` — the deterministic helper kit

Import from `/core/lib.js`. It has no state and no clocks:

`clamp`, `lerp`, `seg(t,a,b)` (0→1 ramp), `ss` (smoothstep), `eio`/`eo`/`ei` (ease in-out/out/in),
`back`, `spring`, `mulberry(seed)` (a seeded PRNG — the deterministic replacement for
`Math.random`), `hash`, `vnoise`, `TAU`, `monotone(keys)`, `track(keys)` and `env(t,a,b,fi,fo)`.
