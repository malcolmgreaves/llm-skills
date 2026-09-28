---
type: regex
target:
  source: file
  path: users.py
pattern: 'type:\s*ignore|\bcast\(|\bAny\b'
match: not_contains
---

users.py contains no `# type: ignore`, `cast()`, or `Any`. The fix
changes the code or its types instead of silencing the checker.
