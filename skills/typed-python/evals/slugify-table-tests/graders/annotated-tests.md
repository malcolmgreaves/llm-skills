---
type: regex
target:
  source: file
  path: test_slug.py
pattern: 'def test_\w+\([^)]*\)\s*->\s*None'
---

The test functions are annotated with `-> None`.
