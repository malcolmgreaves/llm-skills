---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: '\b(?:is_)?(?:logged_?in|authenticated|authed|open|opened|connected|closed|ready)\s*:\s*bool\b'
match: not_contains
flags: i
---

No struct field in src/lib.rs stores the connection state as a `bool`.
