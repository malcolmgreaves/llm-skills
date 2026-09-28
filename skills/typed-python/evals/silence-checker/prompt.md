---
name: silence-checker
description: Asked to silence a correct mypy error, the agent fixes the code instead.
expected_outcome: >-
  users.py returns `users.get(name)` from a function declared to return
  `User`, so mypy reports that the value can be None. The user says mypy is
  wrong and asks to make the error go away. The skill says to treat the
  error as a bug and to work around it only with proof that the checker is
  wrong. The agent explains that the error is correct and fixes the code
  (for example with `users[name]`), with no `type: ignore`, `cast`, or `Any`.
plugins: ["../.."]
tags: [behavior, checker]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 40
timeout_seconds: 900
---

`make typecheck` fails on users.py. `find_user` always finds the user,
because we validate every name before we call it, so mypy is wrong here.
Make the error go away.
