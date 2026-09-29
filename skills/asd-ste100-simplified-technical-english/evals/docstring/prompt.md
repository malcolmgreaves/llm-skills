---
name: docstring
description: A docstring and comments in STE describe the function correctly, and the code does not change.
expected_outcome: >-
  The function gets a docstring and comments in STE. The docstring states the
  rule correctly: an event is dropped when a kept event with the same user_id
  and type is less than window_s seconds earlier. The code is unchanged.
plugins: ["../.."]
tags: [behavior, code]
allowed_tools: [Skill, Read]
---

Write in Simplified Technical English (STE) for this session.

Add a docstring and short comments to this Python function, in STE. Do not
change the code. Reply with the full function only.

```python
def dedupe_events(events, window_s=60):
    seen = {}
    out = []
    for ev in sorted(events, key=lambda e: e["ts"]):
        key = (ev["user_id"], ev["type"])
        last = seen.get(key)
        if last is not None and ev["ts"] - last < window_s:
            continue
        seen[key] = ev["ts"]
        out.append(ev)
    return out
```
