---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if the reader reports each kind of malformed input (wrong magic,
unsupported version, truncation, invalid UTF-8) as its own variant of an
error enum or its own typed error value.

FAIL if errors are strings or `&str`, or if different kinds of malformed
input share one error value.
