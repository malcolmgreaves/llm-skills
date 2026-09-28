---
type: regex
target:
  source: file
  path: priorities.py
pattern: 'bound\s*=|def\s+highest\s*\[\s*\w+\s*:'
---

priorities.py declares a bound type variable for `highest`: either
`TypeVar(..., bound=...)` or the Python 3.12 form
`def highest[T: Bound](...)`.
