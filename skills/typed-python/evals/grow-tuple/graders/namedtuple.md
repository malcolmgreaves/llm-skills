---
type: regex
target:
  source: file
  path: stats.py
pattern: 'NamedTuple|namedtuple'
---

stats.py returns a NamedTuple, which still unpacks and indexes like the
original tuple.
