---
type: regex
pattern: '^\s*(?:here is|here are|here''s|sure|certainly|of course)\b'
flags: i
match: not_contains
---

The reply does not start with a preamble such as "Here is the message". The
skill tells the agent to start with the information.
