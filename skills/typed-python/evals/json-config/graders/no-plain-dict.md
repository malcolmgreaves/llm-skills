---
type: regex
target:
  source: file
  path: config.py
pattern: '->\s*(dict|Dict)\b'
match: not_contains
---

No function in config.py returns a plain `dict` type.
