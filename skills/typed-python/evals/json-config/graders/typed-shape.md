---
type: regex
target:
  source: file
  path: config.py
pattern: 'TypedDict|@dataclass|NamedTuple|BaseModel'
---

config.py describes the config's shape with a TypedDict, a dataclass, a
NamedTuple, or a pydantic model.
