---
name: generic-bound
description: A function used with several classes gets a bound TypeVar, so callers keep their type.
expected_outcome: >-
  priorities.py has three unrelated dataclasses with a `priority` field and
  an unimplemented, unannotated `highest(items)`. report.py already calls
  `highest(tasks).assignee` and `highest(alerts).source`, so a signature
  that returns a shared base or Protocol type fails `mypy --strict`. The
  skill's answer is a TypeVar bound to a Protocol (or base class) with
  `priority`, and a clean mypy run.
plugins: ["../.."]
tags: [behavior, types]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 40
timeout_seconds: 900
---

Implement `highest` in priorities.py.
