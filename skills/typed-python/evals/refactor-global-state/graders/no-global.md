---
type: regex
target:
  source: file
  path: report.py
pattern: '^\s*global\s'
flags: m
match: not_contains
---

report.py has no `global` statement.
