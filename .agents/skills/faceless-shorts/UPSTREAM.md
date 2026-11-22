# Upstream provenance

- Source: `/home/superkat01/Projects/faceless-shorts`
- Vendored: 2026-11-19
- Permission: the user confirmed permission to vendor this skill into OpenMontage on 2026-11-19.
- This is a maintained fork. The tree that must stay byte-identical is `styles/**` plus
  `scripts/**` except `scripts/py` and the six `styles/*/example/tools/capture.mjs` files
  (see below).
- Compatibility edits are limited to `SKILL.md`, `README.md`, `references/**`, `scripts/py`,
  the six `styles/*/example/tools/capture.mjs`, and this file. `UPSTREAM.patch` is the
  vendoring-time diff (`SKILL.md`, `README.md`, `scripts/py`); the later `capture.mjs`
  hardening is pinned by `UPSTREAM.sha256` instead.
- Checksums: `UPSTREAM.sha256` lists every file under `scripts/` and `styles/`, including
  `scripts/py`, so an accidental edit anywhere in the engine still fails the contract test.

## The one engine edit: `scripts/py` shebang

`#!/bin/bash` → `#!/usr/bin/env bash`.

This is not cosmetic. `selftest.sh`, `SKILL.md`, and the `faceless_render` adapter all invoke
`scripts/py` **directly** (not via `bash scripts/py`), so the kernel reads the shebang. On
NixOS `/bin/bash` does not exist — not even inside `nix develop` — so every engine command
died with `bad interpreter: No such file or directory`, and `selftest.sh` failed on all six
styles in under a second.

`/usr/bin/env bash` is correct on NixOS, macOS, and Linux, and is the portable form. Under
Git Bash on Windows `env` resolves `bash` off `PATH`, so that path is unaffected.

No engine logic, `STYLE.md`, `style-sheet.png`, or `example/` file was modified. `diff -r`
against the source shows this as the only difference in the tree.

## The sanctioned `capture.mjs` hardening (Chromium death must not hang)

The six `styles/*/example/tools/capture.mjs` are the only files under `styles/**` this port
edits, and they ship byte-identical to one another. Before the edit, an unhandled WebSocket
close wedged `capture.mjs` forever: `send()` parks every request in a pending map that only
settles on a reply, so when headless Chromium died mid-render the socket closed and every
in-flight `await` hung with no timeout. The edit adds `ws.onclose`/`ws.onerror` handlers that
reject every pending request, plus process-level cleanup and a detached watchdog so a hard
kill of Node cannot orphan Chromium. No capture logic changed.

## Regenerate the checksums and patch from the skill root

```bash
find scripts styles -type f -print0 | sort -z | xargs -0 sha256sum > UPSTREAM.sha256

UP=/home/superkat01/Projects/faceless-shorts
{ diff -u "$UP/SKILL.md" SKILL.md --label a/SKILL.md --label b/SKILL.md
  diff -u "$UP/README.md" README.md --label a/README.md --label b/README.md
  diff -u "$UP/scripts/py" scripts/py --label a/scripts/py --label b/scripts/py
} > UPSTREAM.patch
```
