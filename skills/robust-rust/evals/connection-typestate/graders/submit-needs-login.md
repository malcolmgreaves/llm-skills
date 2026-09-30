---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if the method that submits a job exists only on a type (or typestate
parameter) that the code can reach only through a successful log-in, so
that calling it on a connection that hasn't logged in is a compile error.

FAIL if submitting checks a runtime flag, an `Option`, or a state enum and
returns an error or panics when the connection hasn't logged in.
