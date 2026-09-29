---
name: quoted-error
description: The agent explains an error message in STE and copies the message without a change.
expected_outcome: >-
  The reply copies the error text exactly (it is quoted text), explains it in
  STE, and gives the steps as numbered commands with the condition first. It
  tells the user to make sure that no other deploy runs before the user
  removes the lock file.
plugins: ["../.."]
tags: [behavior, quoted-text]
allowed_tools: [Skill, Read]
---

Please use Simplified Technical English (ASD-STE100) in all replies.

My deploy script printed this and stopped:

```text
Error: failed to acquire lock on /var/run/deploy.lock: resource temporarily unavailable (is another deploy already running?)
```

What does it mean and what should I do?
