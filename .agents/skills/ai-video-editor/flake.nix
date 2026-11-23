{
  description = "ai-video-editor development environment";

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
      in
      {
        devShells.default = pkgs.mkShell {
          name = "ai-video-editor";
          buildInputs = [
            pkgs.python3
            pkgs.python3Packages.pip
            pkgs.python3Packages.pillow
            pkgs.python3Packages.playwright
            pkgs.python3Packages.fonttools
            pkgs.ffmpeg
            pkgs.fontconfig
            pkgs.chromium
            pkgs.jq
            pkgs.git
          ];
          shellHook = pkgs.lib.optionalString pkgs.stdenv.isLinux ''
            export LD_LIBRARY_PATH="${
              pkgs.lib.makeLibraryPath (
                with pkgs;
                [
                  zlib
                  nspr
                  nss
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
                ]
              )
            }''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
          '';
        };
      }
    );
}
