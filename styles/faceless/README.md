# Faceless styles — selection manifests

These six JSON files are **selection metadata plus pointers**, not style definitions.

- They are **not** YAML playbooks and **not** `.visual-style.md` files.
- They point at `.agents/skills/faceless-shorts/styles/<id>/`. The `STYLE.md` and
  `style-sheet.png` in that folder are the look contract; the `example/` there is a
  complete project that renders as-is.
- **Never pass these IDs to `style_playbook`.** `init_project`/`write_checkpoint`
  validate that field against `styles/*.yaml`, so a faceless ID belongs in
  `brief.visual_style` and in the `style_lock` artifact instead.
- Faceless styles run on the `faceless-short` pipeline through the `faceless_render`
  tool. They are not routed through `video_compose`.

## Commands

```bash
.venv/bin/python -m styles.faceless.loader list
.venv/bin/python -m styles.faceless.loader show inside-out
.venv/bin/python -m styles.faceless.loader resolve "Inside Out"
```

`resolve` prints `{"style": {...}, "matched_on": "canonical"|"alias", "query": ...}`.
A generic query (`3D`, `cartoon`, `what happens if`) prints
`{"error": "ambiguous", "candidates": [...]}` and exits 2 — ask the user which one they
want rather than picking for them.

## Paths

Every `style_md`, `style_sheet`, and `example` value is repo-relative. The loader and
the `faceless-short` checkpoint gate both verify those paths exist and that their
`styles/<id>/` segment matches the manifest's own `id`.
