---
type: regex
pattern: '(?=.*if last is not None and ev\["ts"\] - last < window_s:)(?=.*seen\[key\] = ev\["ts"\])(?=.*for ev in sorted\(events, key=lambda e: e\["ts"\]\):)'
flags: s
match: contains
---

The code lines are unchanged.
