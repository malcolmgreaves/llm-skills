---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if parsing a batch that has bytes after the last declared record
returns an error.

FAIL if the reader ignores those bytes or returns the records anyway.
