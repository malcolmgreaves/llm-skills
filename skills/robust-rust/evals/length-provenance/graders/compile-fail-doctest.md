---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: '```[^\n`]*compile_fail'
---

src/lib.rs has at least one `compile_fail` doctest, which checks that
recording an unverified length doesn't compile.
