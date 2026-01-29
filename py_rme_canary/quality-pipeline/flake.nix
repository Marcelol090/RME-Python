{
  description = "Quality Pipeline - Reproducible Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, rust-overlay, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };

        # Rust toolchain (stable)
        rustToolchain = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-src" "rust-analyzer" ];
        };

        # Python with quality tools
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Core dependencies
          pyyaml
          requests
          tenacity

          # AI integrations
          openai
          anthropic

          # Static analysis
          # Note: ruff, mypy installed via cargo/pip for latest versions
          radon

          # Testing
          pytest
          pytest-cov
          pytest-xdist
          pytest-benchmark

          # Development
          black
          isort
        ]);

        # Native dependencies
        nativeDeps = with pkgs; [
          # Build tools
          gcc
          gnumake
          pkg-config

          # Quality tools
          shellcheck  # Shell linting

          # TUI/CLI
          gum  # Dashboard
          jq   # JSON processing
          yq-go  # YAML processing

          # Redis (optional, for distributed cache)
          redis

          # Git
          git
        ];

        # Cargo-installed tools (Rust ecosystem)
        cargoTools = with pkgs; [
          # ast-grep (Rust-based AST matching)
          # Note: Build from source for latest

          # ruff (Rust-based Python linter)
          # Note: Installed via rustToolchain build
        ];

      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            rustToolchain
          ] ++ nativeDeps;

          shellHook = ''
            echo "🚀 Quality Pipeline Development Environment"
            echo "   Python: $(python --version)"
            echo "   Rust: $(rustc --version)"
            echo "   System: ${system}"
            echo ""

            # Install Rust-based tools if not present
            if ! command -v ast-grep &> /dev/null; then
              echo "📦 Installing ast-grep..."
              cargo install ast-grep --locked
            fi

            if ! command -v ruff &> /dev/null; then
              echo "📦 Installing ruff..."
              cargo install ruff --locked
            fi

            # Export environment variables
            export QUALITY_ENV="nix"
            export QUALITY_VERSION="2.2.0"
            export PYTHONPATH="$PWD:$PYTHONPATH"

            # Redis (if enabled)
            export REDIS_HOST="localhost"
            export REDIS_PORT="6379"

            echo "✅ Environment ready"
            echo "   Run: ./quality.sh run"
            echo "   Docs: cat README.md"
          '';
        };

        # CI shell (minimal, no interactive tools)
        devShells.ci = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.jq
          ];

          shellHook = ''
            export CI=true
            export QUALITY_ENV="nix-ci"
          '';
        };

        # Build Rust worker (v3.0)
        packages.quality-worker-rust = pkgs.rustPlatform.buildRustPackage rec {
          pname = "quality-worker";
          version = "3.0.0-alpha";

          src = ./workers-rust;

          cargoLock = {
            lockFile = ./workers-rust/Cargo.lock;
          };

          nativeBuildInputs = [ rustToolchain ];

          meta = with pkgs.lib; {
            description = "Quality Pipeline Rust Worker (v3.0)";
            license = licenses.mit;
          };
        };

        # Docker image (for CI/CD)
        packages.docker = pkgs.dockerTools.buildImage {
          name = "quality-pipeline";
          tag = "latest";

          contents = [
            pythonEnv
            pkgs.bash
            pkgs.coreutils
            pkgs.git
          ];

          config = {
            Cmd = [ "/bin/bash" ];
            WorkingDir = "/workspace";
            Env = [
              "QUALITY_ENV=docker"
              "PATH=/bin"
            ];
          };
        };

        # Default package (orchestrator)
        packages.default = pkgs.writeShellScriptBin "quality" ''
          #!/usr/bin/env bash
          exec ${pkgs.bash}/bin/bash ${./quality.sh} "$@"
        '';

        # Formatter
        formatter = pkgs.nixpkgs-fmt;
      }
    );
}
