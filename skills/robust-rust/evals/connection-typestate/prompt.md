---
name: connection-typestate
description: A connection that must log in before it sends gets one type per stage, not a runtime flag.
expected_outcome: >-
  The skill makes each stage its own type with consuming transitions, so submitting before log-in fails to compile, and pins that with a compile_fail doctest.
plugins: ["../.."]
tags: [behavior, typestate]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 50
timeout_seconds: 1200
---

In src/lib.rs, write a client connection for our job queue. A connection is
opened to a host name, then it must log in with a token, and only after it
logs in can it submit jobs (a job is a string; keep submitted jobs in
memory, there's no real network). A connection can be closed at any time,
and closing it returns the number of jobs it submitted. Put the tests in
tests/connection.rs.
