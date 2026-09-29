---
type: llm
---

Restarting the deployment drops all open database connections, and requests
in flight fail.

PASS if a CAUTION or WARNING comes immediately before the restart step (or at
the start of that step, before its command), and it tells the reader that the
restart drops the connections or makes requests fail.

FAIL if there is no such safety instruction, if it comes after the restart
command, or if it does not state the consequence.
