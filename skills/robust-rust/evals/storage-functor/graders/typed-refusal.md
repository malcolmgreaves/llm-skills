---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if the size-limited layer refuses a value that is too large with a
typed error value (an enum variant or a struct) that carries the value's
size and the limit.

FAIL if the refusal is a string, a `bool`, a panic, or an error without
both numbers.
