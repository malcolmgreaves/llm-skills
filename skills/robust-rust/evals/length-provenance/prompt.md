---
name: length-provenance
description: Only lengths computed by the hashing pass can enter the index; the type system enforces it.
expected_outcome: >-
  The skill wraps a computed length in an evidence type with a private field that only the hashing code can construct, makes the index take that type, and pins the seal with a compile_fail doctest.
plugins: ["../.."]
tags: [behavior, evidence]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 50
timeout_seconds: 1200
---

In src/lib.rs, write an index that records each stored file's hash and byte
length. Usually we compute the length ourselves while we hash the bytes, but
sometimes a remote peer reports a length that we haven't checked. Only
lengths that we computed may go into the index. Put the tests in
tests/index.rs.
