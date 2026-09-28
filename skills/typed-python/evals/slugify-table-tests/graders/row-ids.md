---
type: regex
target:
  source: file
  path: test_slug.py
pattern: 'pytest\.param\(|\bids\s*='
---

Each row of the table has an ID, through `pytest.param(..., id=...)` or
`ids=`.
