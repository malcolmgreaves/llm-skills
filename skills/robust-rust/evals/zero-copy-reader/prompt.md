---
name: zero-copy-reader
description: A reader for a length-prefixed binary format validates once and never panics on input.
expected_outcome: >-
  The skill parses the whole buffer in one function with checked lengths and a typed error per failure, refuses trailing bytes, returns borrowed &str records, and has no unwrap or expect in library code.
plugins: ["../.."]
tags: [behavior, boundaries, panics]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 50
timeout_seconds: 1200
---

Our log shipper sends batches in a binary format: the 4-byte magic `LOGB`,
a 1-byte version (1), a little-endian `u16` record count, and then each
record as a little-endian `u32` length followed by that many bytes of UTF-8.
In src/lib.rs, write a reader that gives back each record as a `&str`
without copying, and a function that returns the longest record in a batch.
Put the tests in tests/reader.rs.
