---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: '\b(?:verif\w*|check(?:sums?)?|validate)\s*:\s*bool\b'
match: not_contains
flags: i
---

No parameter or field in src/lib.rs takes the verification choice as a
`bool` (`verify: bool`, `check: bool`, and similar names).
