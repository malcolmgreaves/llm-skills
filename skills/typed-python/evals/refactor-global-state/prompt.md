---
name: refactor-global-state
description: A monolithic, untyped module with global state becomes typed, composed pure functions with table tests.
expected_outcome: >-
  report.py reads a CSV, filters, sums, and prints in one function, and
  keeps its counters in module-level variables that it mutates. The skill
  asks for separate parse, filter, aggregate, and format functions, I/O
  only at the edges, no mutable module-level state, annotations, table
  tests, and a clean type-checker run.
plugins: ["../.."]
tags: [behavior, composition, tests]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 40
timeout_seconds: 900
---

report.py is part of our package, and other modules import it. Refactor
it so its logic can be tested, and add tests in test_report.py. Keep its
output the same.
