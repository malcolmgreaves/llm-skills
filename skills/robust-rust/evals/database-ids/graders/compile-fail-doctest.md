---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: '```[^\n`]*compile_fail'
---

src/lib.rs has at least one `compile_fail` doctest, which checks that
building an ID from a raw number or mixing ID types doesn't compile.
