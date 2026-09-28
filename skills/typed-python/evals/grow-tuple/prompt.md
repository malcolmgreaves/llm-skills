---
name: grow-tuple
description: Naming the fields of a public tuple return value uses a NamedTuple, which keeps callers working.
expected_outcome: >-
  `spread()` is public API and returns `tuple[float, float]`. Callers the
  agent can't see may unpack or index the result. The skill says to prefer
  a dataclass for new data but to grow an existing tuple into a
  NamedTuple, which keeps unpacking and indexing working.
plugins: ["../.."]
tags: [behavior, types]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 40
timeout_seconds: 900
---

`spread()` in stats.py is part of our library's public API. Make its
return value self-describing, so callers can read the low and high
values by name.
