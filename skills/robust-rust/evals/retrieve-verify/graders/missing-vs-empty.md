---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if the new method's return type tells a file that doesn't exist apart
from a file with zero bytes (an enum variant, an `Option`, or a dedicated
error variant).

FAIL if a missing file and an empty file give the same value, such as
`Ok(0)`.
