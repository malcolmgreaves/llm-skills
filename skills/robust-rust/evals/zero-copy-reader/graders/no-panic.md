---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if no code path can panic on a malformed batch: every slice or index
that uses a length or offset read from the input is checked first, and
arithmetic on those values can't overflow.

FAIL if some malformed batch can make the reader panic.
