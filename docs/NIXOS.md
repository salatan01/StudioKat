# StudioKat on NixOS

The repo ships a Nix flake that provides the full local toolchain: Python 3.11,
`uv`, Node 22, FFmpeg, ImageMagick, and a Chromium build that HyperFrames and
Remotion can actually launch. `nix develop` is the supported way to run
StudioKat on NixOS.

## Why the bundled browser fails

HyperFrames and Remotion both ship a generic Linux `chrome-headless-shell`
binary. That binary is linked against roughly twenty shared libraries at
standard FHS paths (`libnspr4.so`, `libnss3.so`, `libX11.so.6`, …). NixOS does
not expose libraries at those paths, so the browser exits immediately with:

```
error while loading shared libraries: libnspr4.so: cannot open shared object file
```

with exit code 127. The flake points both runtimes at the Nix Chromium instead,
and also exports the library path those binaries need as a fallback.

## What the shell provides

| Tool | Default shell | `.#full` shell |
|---|---|---|
| Python 3.11 + pip | yes | yes |
| uv | yes | yes |
| Node.js 22 + npm/npx | yes | yes |
| FFmpeg / ffprobe | yes | yes |
| Chromium | yes | yes |
| ImageMagick | yes | yes |
| Build libraries (openssl, zlib, libffi, libjpeg, libpng, freetype, libGL, ALSA) | yes | yes |
| jq, git, make, grep, sed, which | yes | yes |
| Blender | no | yes |
| cairo / pango | no | yes |

## Quick start with direnv

```bash
direnv allow
make setup   # first time only
```

`.envrc` reloads the shell whenever `flake.nix` or `flake.lock` changes, and
the shell hook activates `.venv` on every reload. The automatic first-run
install described below applies to an interactive `nix develop`; under
`direnv`, run `make setup` once yourself.

## Quick start without direnv

```bash
nix develop
```

The first interactive entry bootstraps the project: it runs `make setup`
(about 1–2 minutes, network required), then activates `.venv`. Setup also
downloads the default Piper voice (`en_US-lessac-medium`, ~63 MB into
`~/.piper/models`) so narration works without an API key. Every later entry
skips the install and just activates the venv, so `python`, `make preflight`,
renders, and an agent's `python -c ...` calls all use the project interpreter.

The shell also ignores any virtualenv inherited from the parent terminal and
activates the checkout's `.venv`, so `make` and agent commands always use this
project's interpreter instead of another project's environment.

The bootstrap is intentionally skipped when the shell is not interactive
(CI, `nix develop --command ...`). In that case run `make setup` once
yourself. Two environment variables control it:

| Variable | Effect |
|---|---|
| `OPENMONTAGE_AUTO_SETUP=1` | Force the bootstrap in a non-interactive shell. |
| `OPENMONTAGE_SKIP_AUTO_SETUP=1` | Never bootstrap automatically; run `make setup` manually. |

Every later command — `make preflight`, `make hyperframes-doctor`, renders,
tests — must run inside that same shell. Open a new terminal and you need to
enter `nix develop` again.

## Running the OpenCode agent

`opencode` is the agent harness, not part of the project toolchain, so the flake
does not install it. Install the V2 CLI once per machine and verify the version:

```bash
curl -fsSL https://opencode.ai/v2/install | bash
# or: npm install -g @opencode/cli
opencode --version   # must be 2.x
```

Run `make setup` once if the shell hook has not done it, then launch OpenCode
from the repository root inside `nix develop` (or after `direnv allow`):

```bash
nix develop
opencode
```

OpenCode reads `AGENTS.md` automatically and discovers the Layer 3 skills in
`.agents/skills/` (project compatibility). The tracked `opencode.jsonc` loads
the `superpowers` plugin. Provider/model selection and API keys are
machine-local: keep them in `~/.config/opencode/opencode.jsonc` or environment
variables, and never commit them.

`skills/` is Layer 2 reference material, not an OpenCode skill source. There is
no `.opencode/skills` copy; `.agents/skills/` is the authoritative skill tree.

Launching OpenCode outside the Nix shell leaves its child processes without the
Chromium override and `LD_LIBRARY_PATH`, so renders fail with missing-browser or
`libz.so.1` errors. Exit and relaunch it from `nix develop`.

## The full shell

`nix develop .#full` adds Blender plus cairo/pango on top of the default
toolchain, for the `blender_world` rendering path. It downloads a much larger
closure than the default shell, so only use it when a production needs Blender:

```bash
nix develop .#full
```

It shares the same `.venv`, so a project already bootstrapped by the default
shell needs no second install. A first entry through `.#full` bootstraps it
the same way.

## What gets exported

The shell exports these on Linux:

| Variable | Purpose |
|---|---|
| `HYPERFRAMES_BROWSER_PATH` | Chromium binary the HyperFrames CLI launches. |
| `REMOTION_BROWSER_EXECUTABLE` | Chromium binary `video_compose` passes to Remotion as `--browser-executable`. |
| `LD_LIBRARY_PATH` | Shared libraries for headless shells that bypass the two variables (for example a direct `npx remotion`) and for pip-installed manylinux wheels such as numpy and Pillow, which dynamically link `libz`. A Nix Chromium is self-contained; this covers the downloaded ones. |
| `NPM_CONFIG_CACHE` / `npm_config_cache` | Puts the npm/npx cache in `.npm-cache/` inside the checkout instead of `$HOME`. |
| `PYTHONNOUSERSITE` | Keeps user site-packages out of the Nix interpreter. |
| `PYTHON_VERSION=3.11` | Makes `make setup` create `.venv` from the Nix Python instead of letting `uv` download its own build. |

An explicit `remotion_browser_executable` input still wins over the environment
variable, so per-job overrides remain possible.

## Verification

```bash
make preflight
make hyperframes-doctor
python -c "import numpy, PIL, piper; print('native modules ok')"
nix flake check
```

`make hyperframes-doctor` prints a `runtime_check` object; `browser_override`
shows the Chromium path the HyperFrames CLI will use. The `numpy`/`PIL` import
checks that `LD_LIBRARY_PATH` covers the pip wheels (the failure mode is
`libz.so.1: cannot open shared object file`). `nix flake check` builds the
default shell as its check, so the first run is slow and later runs are cached.

To verify the shell itself:

```bash
nix develop --command bash -c '
  echo "$HYPERFRAMES_BROWSER_PATH"
  "$HYPERFRAMES_BROWSER_PATH" --version
  python --version
  node --version
'
```

## Troubleshooting

### Browser exits 127, or `libnspr4.so: cannot open shared object file`

The command did not run inside `nix develop` (or `.envrc` was not allowed).
Re-enter the shell and confirm the path is set:

```bash
echo "$HYPERFRAMES_BROWSER_PATH"
```

If it is empty, the shell was bypassed. Run `nix develop` (or `direnv allow`)
and retry.

### Stale npm cache

The npx cache lives at `.npm-cache/` in the checkout. If a HyperFrames or
Remotion version looks stale or a package fetch is corrupted, remove it and
retry:

```bash
rm -rf .npm-cache
```

### Wrong Python

`which python` must print the checkout's `.venv/bin/python`; that venv is built
from the Nix Python 3.11 by `make setup`, and the shell activates it
automatically. If it prints a `/nix/store/...` path instead, the venv is
missing or the shell skipped activation:

```bash
source .venv/bin/activate   # or run `make setup` if .venv does not exist
```

If an old virtualenv from another machine is present, remove `.venv` and run
`make setup` again.
