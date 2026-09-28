---
type: regex
target: trace
pattern: '(\\n|=+ )[1-9]\d* passed in'
---

A pytest run in the session passed with no failures. The pattern matches a
summary line that starts with the pass count, which pytest prints only when
no test failed or errored.
