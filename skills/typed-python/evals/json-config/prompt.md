---
name: json-config
description: Loading a JSON file with fixed keys produces a validated TypedDict or dataclass, with table tests.
expected_outcome: >-
  The config has fixed keys with a type per key. The skill says to model
  it with a TypedDict or dataclass, to validate the `Any` from
  `json.loads` at the boundary instead of casting it, and to test with a
  parametrized table.
plugins: ["../.."]
tags: [behavior, types, tests]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 40
timeout_seconds: 900
---

Write `load_config(path)` in config.py. It reads a JSON file with `host`
(a string), `port` (an integer), and an optional `debug` (a boolean that
defaults to false). Put its tests in test_config.py.
