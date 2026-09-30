---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if a checksum mismatch is a typed error value that carries both the
expected and the actual checksum.

FAIL if the mismatch is a string, a `bool`, a panic, or an error without
both checksums.
