#!/usr/bin/env bash
# Seeds this case's workspace with an edition 2024 library crate.
set -euo pipefail

# shared: robust-rust/eval-project
# This block is the same in every case's fixture.sh, and
# scripts/validate.py fails if the copies differ.

# evals/run.sh puts a Rust toolchain on PATH where the agent's sandbox can
# read it, and records it in .eval-tools/ in the skill's directory. The
# harness doesn't pass run.sh's other variables to this script, but it runs
# the script from its place in the repository, so the path is relative to it.
tools="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/.eval-tools"
if [[ ! -f "$tools/sysroot" ]]; then
  echo "fixture.sh: no toolchain setup. Run the suite with evals/run.sh." >&2
  exit 1
fi
mkdir -p src tests .cargo
# The cases need no dependencies, and the sandbox has no network: fail fast.
printf '[net]\noffline = true\n' > .cargo/config.toml
cat > Cargo.toml <<'EOF'
[package]
name = "domain"
version = "0.1.0"
edition = "2024"

[dependencies]
EOF
printf '.PHONY: check\ncheck:\n\tcargo clippy --all-targets -- -D warnings\n\tcargo test\n' \
  > Makefile
# /shared

: > src/lib.rs
