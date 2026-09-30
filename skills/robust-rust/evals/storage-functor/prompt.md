---
name: storage-functor
description: A capped layer over two storage backends is one generic type over a backend trait.
expected_outcome: >-
  The skill writes the backends against a trait with an associated Error, builds the cap as a functor over any backend, and gives the cap violation a typed error.
plugins: ["../.."]
tags: [behavior, traits]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 50
timeout_seconds: 1200
---

In src/lib.rs, write a key-value storage abstraction with two
implementations: one in memory, and one that stores each value in a file in
a directory. Then add a layer that refuses values larger than a byte limit
and works over either implementation. Put the tests in tests/storage.rs;
tests that need a directory can use one under `target/`.
