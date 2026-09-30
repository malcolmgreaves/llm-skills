---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if one function validates the whole batch (magic, version, every
length, and UTF-8) and returns a value whose records are then read without
a `Result`.

FAIL if an accessor parses or validates again, or returns a `Result`.
