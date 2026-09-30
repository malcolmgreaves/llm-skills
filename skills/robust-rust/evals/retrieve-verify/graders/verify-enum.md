---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if the caller chooses whether to verify checksums by passing an enum
that has a named variant for each choice.

FAIL otherwise, for example if the choice is a `bool` or an `Option<bool>`.
