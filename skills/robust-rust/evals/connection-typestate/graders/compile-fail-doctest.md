---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: '```[^\n`]*compile_fail'
---

src/lib.rs has at least one `compile_fail` doctest, which checks that
submitting a job before log-in doesn't compile.
