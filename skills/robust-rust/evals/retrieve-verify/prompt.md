---
name: retrieve-verify
description: Reading a stored file returns an outcome that tells missing from empty, with a verification policy enum.
expected_outcome: >-
  The skill returns an outcome enum or Option so a missing file is not Ok(0), takes the verification choice as a two-variant enum rather than a bool, and reports a mismatch as a typed error with expected and actual checksums.
plugins: ["../.."]
tags: [behavior, enums]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 50
timeout_seconds: 1200
---

src/lib.rs has a small content store. Add a method that writes a stored
file's bytes to any `std::io::Write` and returns how many bytes it wrote.
Callers need to be able to ask it to verify each chunk's checksum while it
reads. Put the tests in tests/read.rs.
