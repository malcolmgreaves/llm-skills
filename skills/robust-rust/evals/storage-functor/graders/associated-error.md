---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: '\btrait\s+\w+[^{;]*\{[^}]*?\btype\s+Err(?:or)?\b'
---

A trait in src/lib.rs declares an associated error type (`type Error`), so
each backend chooses its own error. A `type Error` in an impl, such as
`impl TryFrom`, doesn't count.
