---
name: trigger-basic
description: A plain request for a Rust function should load the skill.
expected_outcome: >-
  The skill fires. Baseline trigger check.
plugins: ["../.."]
tags: [trigger]
allowed_tools: [Skill]
---

Write a Rust function that takes log lines like
`2026-09-01T10:00:00 ERROR billing timeout` and returns how many ERROR
lines each service logged.
