{
  description = "StudioKat NixOS development environment";

  inputs = {
    nixpkgs.url = "github:Nixos/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (pkgs) lib;

        corePackages =
          with pkgs;
          [
            python311
            python311Packages.pip
            uv
            nodejs_22
            ffmpeg
            imagemagick
            jq
            git
            gnumake
            gnused
            gnugrep
            which
            pkg-config
            openssl
            zlib
            libffi
            libjpeg
            libpng
            freetype
            libGL
            # Manim / pycairo / manimpango build deps
            pango
            cairo
            glib
            fribidi
            harfbuzz
            fontconfig
            libthai
            # Piper TTS
            espeak-ng
            # Whisper.cpp (for hyperframes doctor / local STT)
            whisper-cpp
          ]
          ++ lib.optionals stdenv.isLinux [
            chromium
            alsa-lib
          ];

        # Shared libraries the *downloaded* headless shells and pip wheels look
        # up at runtime. The Nix Chromium is self-contained; this covers paths
        # that bypass the two browser variables (for example an agent running
        # `npx remotion`) and manylinux wheels such as numpy and Pillow, which
        # dynamically link libz. NixOS has no /lib, so without this they fail
        # with "libz.so.1: cannot open shared object file".
        runtimeLibs = with pkgs; [
          zlib
          nspr
          nss
          glib
          alsa-lib
          udev
          libX11
          libxcb
          libXcomposite
          libXdamage
          libXext
          libXfixes
          libXrandr
          libgbm
          libxkbcommon
          pango
          cairo
          at-spi2-atk
          at-spi2-core
          atk
          cups
          dbus
          expat
          libdrm
          libxshmfence
        ];

        linuxEnv = lib.optionalString pkgs.stdenv.isLinux ''
          export HYPERFRAMES_BROWSER_PATH="${pkgs.chromium}/bin/chromium"
          export REMOTION_BROWSER_EXECUTABLE="${pkgs.chromium}/bin/chromium"
          export CHROME="${pkgs.chromium}/bin/chromium"
          export LD_LIBRARY_PATH="${lib.makeLibraryPath runtimeLibs}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        '';

        linuxBanner = lib.optionalString pkgs.stdenv.isLinux ''
          echo "    Chromium: $(${pkgs.chromium}/bin/chromium --version 2>/dev/null)"
        '';

        mkShell =
          extraPackages: envName:
          pkgs.mkShell {
            name = envName;
            buildInputs = corePackages ++ extraPackages;
            shellHook = ''
              export PYTHONNOUSERSITE=1
              # Keep npx/HyperFrames/Remotion writes inside the checkout.
              export NPM_CONFIG_CACHE="$PWD/.npm-cache"
              export npm_config_cache="$PWD/.npm-cache"
              # `make setup` builds .venv from this interpreter. Without this,
              # uv would fetch its own Python 3.10 build instead.
              export PYTHON_VERSION=3.11
              ${linuxEnv}
              echo "🎬 StudioKat Nix environment: ${envName}"
              echo "    Node:     $(node --version 2>&1)"
              echo "    FFmpeg:   $(ffmpeg -version 2>/dev/null | head -n 1)"
              ${linuxBanner}

              _om_deps_ready() {
                [ -x .venv/bin/python ] &&
                  .venv/bin/python -c 'import requests, yaml, numpy, PIL, faster_whisper, playwright' >/dev/null 2>&1 &&
                  [ -x remotion-composer/node_modules/.bin/remotion ]
              }

              # The editor pipeline's engine skill runs through editor_render.
              # When the system Chromium exists (CHROME, exported below), the
              # skill's own setup uses it and does not re-download a browser.
              _om_editor_setup() {
                if [ -x .venv/bin/python ] &&
                   .venv/bin/python -c 'import faster_whisper, playwright' >/dev/null 2>&1; then
                  if [ -n "''${CHROME:-}" ] && [ -x "''${CHROME}" ]; then
                    echo "    Editor skill: ready (Chromium: ''${CHROME##*/})"
                  else
                    echo "    Editor skill: deps ready — set CHROME to a Chromium binary"
                  fi
                else
                  echo "    Editor skill: deps missing — run 'make setup' (installs playwright; the browser is in this shell)"
                fi
              }

              # Only link whisper-cpp after .venv/bin exists so uv venv never
              # sees a pre-created .venv directory on a fresh clone.
              _om_link_whisper() {
                if [ -d .venv/bin ] && [ -x "${pkgs.whisper-cpp}/bin/whisper-cli" ] && [ ! -L .venv/bin/whisper-cpp ]; then
                  ln -sf "${pkgs.whisper-cpp}/bin/whisper-cli" .venv/bin/whisper-cpp
                fi
              }

              # Fresh clone: an interactive `nix develop` bootstraps once, then
              # activates the venv so `python` in this shell is the project
              # interpreter (the agent guide and all make targets assume it).
              # Non-interactive shells and CI never auto-install; set
              # OPENMONTAGE_AUTO_SETUP=1 to force it, or
              # OPENMONTAGE_SKIP_AUTO_SETUP=1 to opt out.
              #
              # Entering this repo's shell is a statement that the project
              # environment is wanted: never let a virtualenv activated in the
              # parent terminal leak in. `make setup` would otherwise install
              # into it and leave this checkout without a usable .venv.
              if [ -f Makefile ] && [ -f flake.nix ]; then
                if [ -f .venv/bin/activate ]; then
                  . .venv/bin/activate
                  _om_link_whisper
                else
                  unset VIRTUAL_ENV CONDA_PREFIX
                fi
              fi

              if _om_deps_ready; then
                _om_link_whisper
                _om_editor_setup
                echo "    deps:     ready (venv active)"
              elif [ -n "''${OPENMONTAGE_SKIP_AUTO_SETUP:-}" ]; then
                echo "    deps:     missing — run 'make setup'"
                _om_editor_setup
              elif [ -f Makefile ] && { { [ -t 0 ] && [ -t 1 ]; } || [ -n "''${OPENMONTAGE_AUTO_SETUP:-}" ]; }; then
                echo "    deps:     first run — installing (about 1–2 minutes)…"
                if make setup && [ -f .venv/bin/activate ]; then
                  . .venv/bin/activate
                  _om_link_whisper
                  _om_editor_setup
                  echo "    deps:     ready (venv active)"
                else
                  echo "    deps:     setup failed — fix the error above, then run 'make setup'"
                fi
              else
                echo "    deps:     missing — run 'make setup'"
              fi
              echo "    Python:   $(python --version 2>&1) ($(command -v python))"
            '';
          };

        defaultShell = mkShell [ ] "default";
        fullShell = mkShell [
          pkgs.blender
          pkgs.cairo
          pkgs.pango
        ] "full";
      in
      {
        devShells.default = defaultShell;
        devShells.full = fullShell;
        checks.default = defaultShell;
        formatter = pkgs.nixfmt;
      }
    );
}
