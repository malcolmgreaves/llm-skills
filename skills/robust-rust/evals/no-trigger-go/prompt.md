---
name: no-trigger-go
description: A state-machine request in Go must not load the skill.
expected_outcome: >-
  The skill does not fire. Over-trigger control: the request names a state machine and types, but in Go.
plugins: ["../.."]
tags: [trigger]
allowed_tools: [Skill]
---

Write a Go package with a type-safe state machine for a TCP connection:
closed, listening, established, and closing, with methods for each
transition.
