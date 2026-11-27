# Task 2 Report — Font manifest and setup/check

Status: DONE
Commit: `dc13ba2` feat(lemo): pin and verify OFL fonts

## What I implemented

- **`tests/contracts/test_lemo_fonts.py`** — copied verbatim from the brief (3 tests:
  content-pinned manifest, gitignored binaries, `verify_fonts` missing/bad-hash reporting).
- **`.agents/skills/lemo/library/assets/fonts/manifest.json`** —
  `{version: 1, google_fonts_commit: "06bfe0d62a98375cb09c942fa18e68bd32cff057", files: [...]}`.
  35 entries across the 29 slugs from the brief's table. Each entry is
  `{path, slug, family, url, sha256, licence_path}` with:
  - `path` relative to `assets/fonts/` (e.g. `newsreader/Newsreader[opsz,wght].ttf`),
  - a percent-encoded raw URL under `.../<commit>/ofl/<slug>/` (`[`→`%5B`, `]`→`%5D`, `,`→`%2C`),
  - SHA-256 computed from the actual downloaded bytes.
- **`.agents/skills/lemo/library/assets/fonts/licenses/<slug>.txt`** — 29 OFL texts
  fetched from `ofl/<slug>/OFL.txt` at the pinned commit (committed).
- **`.agents/skills/lemo/library/assets/fonts/.gitignore`** — `*.ttf`, `*.otf`, `*.woff2`
  and `*.part` (binaries ignored).
- **`tools/video/lemo/__init__.py`** and **`tools/video/lemo/setup.py`** —
  `verify_fonts(root, files) -> list[str]`, `download_fonts(root, files) -> None`,
  `load_manifest`, `fonts_root`, and `main()`. `download_fonts` verifies the SHA-256 of
  the downloaded bytes before writing, writes to a sibling `.part` file, then
  `Path.replace()`s atomically (never leaves a partial file) and skips files that already
  match. `main` supports `--check`, `--fonts`, `--offline`; `--check` prints `FONTS OK`
  or the problem list and exits 1.
- **`.agents/skills/lemo/scripts/setup.py`** — thin shim that inserts the repo root
  (`parents[4]`) on `sys.path` and calls `tools.video.lemo.setup.main()`.

No CSS is generated. No vendored library source was modified. Font binaries and
`node_modules` are not committed.

## RED evidence

Command: `.venv/bin/python -m pytest tests/contracts/test_lemo_fonts.py -v`

```
tests/contracts/test_lemo_fonts.py::test_manifest_is_content_pinned FAILED [ 33%]
tests/contracts/test_lemo_fonts.py::test_font_binaries_are_gitignored FAILED [ 66%]
tests/contracts/test_lemo_fonts.py::test_verify_fonts_reports_missing_and_bad_hashes FAILED [100%]

E  FileNotFoundError: .../.agents/skills/lemo/library/assets/fonts/manifest.json   (test 1)
E  FileNotFoundError: .../.agents/skills/lemo/library/assets/fonts/.gitignore      (test 2)
E  ModuleNotFoundError: No module named 'tools.video.lemo'                          (test 3)

3 failed in 0.25s
```

Why expected: none of the deliverables existed yet — no manifest, no `.gitignore`,
no `tools.video.lemo` package. The three failures are exactly the three artifacts this
task creates.

## GREEN evidence

Command: `.venv/bin/python -m pytest tests/contracts/test_lemo_fonts.py -v`

```
tests/contracts/test_lemo_fonts.py::test_manifest_is_content_pinned PASSED [ 33%]
tests/contracts/test_lemo_fonts.py::test_font_binaries_are_gitignored PASSED [ 66%]
tests/contracts/test_lemo_fonts.py::test_verify_fonts_reports_missing_and_bad_hashes PASSED [100%]

3 passed in 0.04s
```

Round-trip (`download_fonts` + `verify_fonts`) via a throwaway script:

```
manifest commit=06bfe0d62a98375cb09c942fa18e68bd32cff057 files=35
before download: 35 problems
after download: 0 problems -> []
total on disk: 66204792 bytes (63.1 MiB)
ROUND-TRIP OK
```

All 29 `OFL.txt` files and all 35 font files downloaded successfully from the pinned
commit — **no 404s**.

## `--check` output

```
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py --check
FONTS OK
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py --check --offline
FONTS OK
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py --fonts   # idempotent, 0.3s
FONTS OK (35 files)
```

Negative path (a binary moved aside, offline):

```
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py --check --offline
FONT PROBLEMS:
  missing: italiana/Italiana-Regular.ttf
exit=1
```

The shim also works from another cwd (`cd /tmp && .../scripts/setup.py --check --offline`
→ `FONTS OK`), confirming the `sys.path` insertion.

## Ignore proof

```
$ git add <paths> && git diff --cached --name-only | grep -E '\.(ttf|otf|woff2)$'
(none)
$ git check-ignore -v .agents/skills/lemo/library/assets/fonts/italiana/Italiana-Regular.ttf
.agents/skills/lemo/library/assets/fonts/.gitignore:4:*.ttf	...
$ git status --short
(clean after commit)
```

Only the manifest, `.gitignore`, 29 `licenses/*.txt`, the two Python modules, and the
test are committed — 34 files.

## Files changed

- `tests/contracts/test_lemo_fonts.py` (new)
- `.agents/skills/lemo/library/assets/fonts/manifest.json` (new)
- `.agents/skills/lemo/library/assets/fonts/.gitignore` (new)
- `.agents/skills/lemo/library/assets/fonts/licenses/*.txt` (new, 29 files)
- `tools/video/lemo/__init__.py`, `tools/video/lemo/setup.py` (new)
- `.agents/skills/lemo/scripts/setup.py` (new)

## Files I could not fetch

None. Every `ofl/<slug>/<file>` and `ofl/<slug>/OFL.txt` in the brief's table returned
200 at commit `06bfe0d62a98375cb09c942fa18e68bd32cff057`.

## Self-review findings

- Test file is byte-for-byte the brief's code (including the `# tests/...` header and
  compact `json, re` import line).
- Manifest `url` values are percent-encoded and pass the test's `startswith` check; a
  spot check confirms `Archivo%5Bwdth%2Cwght%5D.ttf`. No `&text=` anywhere; full files only.
- `verify_fonts` returns `missing: <path>` / `sha256: <path> (...)`; test only asserts the
  prefixes, which hold.
- `download_fonts` is idempotent (skips matching files) and atomic (`.part` + rename);
  the hash is checked in memory before anything is written.
- `--offline` correctly suppresses network for `--check` and makes a bare download a no-op.
- `.gitattributes` normalizes CRLF→LF in a few OFL texts on commit; content is unaffected
  and the tests only assert file presence.
- Binaries total 63.1 MiB on disk, all ignored; working tree is clean after the commit.
- No vendored `library/` source file was touched (only new `assets/` content was added).

No concerns. No subagents were dispatched.

---

# Task 2 Fix Report — Round 1 (R17)

Status: DONE
Commit: `9de7ca3` fix(lemo): make font --check verify-only and harden download_fonts

## R17 (Important): a "check" must not mutate

**Defect:** `--check` without `--offline` called `download_fonts` before verifying, so
it wrote ~63 MiB and could never report `missing:` on a fresh checkout.

**Fix in `tools/video/lemo/setup.py`:**

- `--check` is now verify-only. It loads the manifest, calls `verify_fonts`, and prints
  `FONTS OK` or `FONT PROBLEMS:` + the list, exiting 1 on any problem. It never calls
  `download_fonts` and never touches the network.
- `--fonts` (and the no-flag default) downloads missing/corrupt files first, then
  verifies and reports (`FONTS OK (N files)`).
- `--offline` forbids the network. `--fonts --offline` skips the download, verifies, and
  exits 1 with the problem list if anything is missing/corrupt; it prints `FONTS OK`
  only when everything verifies.
- Module docstring updated to state the new semantics.

## Minor: whitespace-fragile download path matching

The old `bad = {line.split(": ", 1)[1].split(" ", 1)[0] ...}` parsed `verify_fonts`
strings, which mis-handles paths containing spaces. `download_fonts` now iterates entries
and downloads only when `not dest.is_file() or _sha256(dest) != entry["sha256"]`.
`verify_fonts`'s public contract is unchanged.

## Test added (hermetic, no network)

`tests/contracts/test_lemo_fonts.py::test_check_is_verify_only_and_never_downloads`
builds a tmp fonts root with a one-file manifest of a dummy `.ttf`, points
`DEFAULT_FONTS_ROOT` at it, and monkeypatches `urllib.request.urlopen` to raise
`AssertionError("network used by verify-only path")`. It asserts:

- `main(["--check"]) == 1`
- `main(["--check", "--offline"]) == 1`
- `main(["--fonts", "--offline"]) == 1`
- the tmp tree is byte-for-byte unchanged before/after (nothing written)
- output contains `missing: x/a.ttf` and not `FONTS OK`

No skips/xfails.

## RED evidence

`.venv/bin/python -m pytest tests/contracts/test_lemo_fonts.py::test_check_is_verify_only_and_never_downloads -v`

```
    assert s.main(["--check"]) == 1
tools/video/lemo/setup.py:136: in main
    download_fonts(root, files)
tools/video/lemo/setup.py:109: in download_fonts
    _download(entry["url"], dest, entry["sha256"])
tools/video/lemo/setup.py:75: in _download
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
E       AssertionError: network used by verify-only path
1 failed
```

Expected: the old `--check` reached the network; the new contract forbids it.

## GREEN evidence

`.venv/bin/python -m pytest tests/contracts/test_lemo_fonts.py -v`

```
tests/contracts/test_lemo_fonts.py::test_manifest_is_content_pinned PASSED [ 25%]
tests/contracts/test_lemo_fonts.py::test_font_binaries_are_gitignored PASSED [ 50%]
tests/contracts/test_lemo_fonts.py::test_verify_fonts_reports_missing_and_bad_hashes PASSED [ 75%]
tests/contracts/test_lemo_fonts.py::test_check_is_verify_only_and_never_downloads PASSED [100%]

4 passed in 0.06s
```

## Real CLI behaviour (fonts present)

```
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py --check
FONTS OK
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py --check --offline
FONTS OK
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py --fonts --offline
FONTS OK (35 files)
$ .venv/bin/python .agents/skills/lemo/scripts/setup.py
FONTS OK (35 files)
```

## No-mutation / offline proof (a binary moved aside)

```
$ mv .../italiana/Italiana-Regular.ttf .../Italiana-Regular.ttf.holdout
$ setup.py --check
FONT PROBLEMS:
  missing: italiana/Italiana-Regular.ttf
exit=1                         # and the file was still missing afterwards (no download)
$ setup.py --fonts --offline
FONT PROBLEMS:
  missing: italiana/Italiana-Regular.ttf
exit=1
$ setup.py --fonts
FONTS OK (35 files)            # re-downloaded the missing file
exit=0
```

## Files changed

- `tools/video/lemo/setup.py` (docstring, `download_fonts`, new `_finish`, `main`)
- `tests/contracts/test_lemo_fonts.py` (new CLI-semantics test)

Working tree is clean after the commit. No vendored source touched, no binaries or
`node_modules` committed. No subagents were dispatched.

