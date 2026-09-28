---
type: regex
target: trace
pattern: 'Success: no issues found'
---

A mypy run in the session reported no errors. The graders can't run mypy
themselves, so this checks the output of the agent's own run.
