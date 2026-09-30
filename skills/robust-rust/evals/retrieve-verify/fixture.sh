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

cat > src/lib.rs <<'EOF'
//! A small content store: a file is a list of chunks, stored by checksum.
use std::collections::HashMap;

pub fn checksum(bytes: &[u8]) -> u64 {
    bytes.iter().fold(0xcbf2_9ce4_8422_2325, |hash, byte| {
        (hash ^ u64::from(*byte)).wrapping_mul(0x0100_0000_01b3)
    })
}

#[derive(Default)]
pub struct Store {
    chunks: HashMap<u64, Vec<u8>>,
    files: HashMap<String, Vec<u64>>,
}

impl Store {
    /// Stores `bytes` as the file `name`, in chunks of `chunk_size` bytes.
    pub fn put(&mut self, name: &str, bytes: &[u8], chunk_size: usize) {
        let ids = bytes
            .chunks(chunk_size.max(1))
            .map(|chunk| {
                let id = checksum(chunk);
                self.chunks.insert(id, chunk.to_vec());
                id
            })
            .collect();
        self.files.insert(name.to_string(), ids);
    }

    /// Replaces the bytes of a stored chunk. Tests use it to simulate damage.
    pub fn damage_chunk(&mut self, id: u64, bytes: Vec<u8>) {
        self.chunks.insert(id, bytes);
    }

    pub fn chunk_ids(&self, name: &str) -> Option<&[u64]> {
        self.files.get(name).map(Vec::as_slice)
    }
}
EOF
