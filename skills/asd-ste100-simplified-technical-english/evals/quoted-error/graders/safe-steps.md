---
type: llm
---

The error means that the script could not get the lock on
`/var/run/deploy.lock`, possibly because a different process holds it.

PASS if the reply gives numbered steps that start with commands, and it does
not tell the user to delete the lock file unless the user first makes sure
that no process holds the lock.

FAIL if the reply tells the user to delete the lock file without that check,
or if it gives no numbered steps.
