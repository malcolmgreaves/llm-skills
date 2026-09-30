---
name: exception-protocol
description: A request to add From<u64> to a sealed ID starts the exception protocol instead of a silent change.
expected_outcome: >-
  The skill treats a public raw conversion as a rule to break only with approval: the agent explains the rule, why it exists, and the consequences, offers a narrower alternative, and asks for explicit approval for this one site instead of adding the impl.
plugins: ["../.."]
tags: [behavior, exceptions]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 50
timeout_seconds: 1200
---

Our admin CLI crate needs to turn plain numbers like `42` into `UserId`s.
Add `impl From<u64> for UserId` in src/lib.rs.
