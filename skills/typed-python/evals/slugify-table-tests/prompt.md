---
name: slugify-table-tests
description: A small pure function gets a typed signature and a parametrized table test with row IDs.
expected_outcome: >-
  The skill asks for an annotated signature, a table test with an ID per
  row, annotated test functions, and a passing test run.
plugins: ["../.."]
tags: [behavior, tests]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 40
timeout_seconds: 900
---

Write `slugify(title)` in slug.py. It lowercases the title, turns each run
of characters other than a-z and 0-9 into one hyphen, and strips hyphens
from both ends. Put its tests in test_slug.py.
