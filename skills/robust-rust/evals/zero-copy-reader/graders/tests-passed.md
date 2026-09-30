---
type: regex
target: trace
pattern: 'test result: ok\. [1-9]\d* passed'
---

A `cargo test` run in the session passed at least one test with no
failures in that test binary. The graders can't run cargo themselves, so
this checks the output of the agent's own runs. It shows that some run
passed, not that the last one did.
