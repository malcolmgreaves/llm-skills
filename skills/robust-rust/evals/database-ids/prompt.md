---
name: database-ids
description: ID types for rows keyed by u64 are sealed newtypes with no public raw conversion.
expected_outcome: >-
  The skill makes each ID a newtype with a private field, no From<u64>, Deref, or alias, parses typed IDs through FromStr, and keeps the database conversion narrow.
plugins: ["../.."]
tags: [behavior, newtypes]
allowed_tools: [Skill, Read, Glob, Grep, Write, Edit, Bash]
max_turns: 50
timeout_seconds: 1200
---

Our service stores users, orders, and products in Postgres, each keyed by a
BIGINT that we read as `u64`. In src/lib.rs, add ID types for the three, and
a function `place_order` that takes a user, a product, and a quantity, and
returns an order record with a new order ID. Our CLI reads IDs as text like
`u-42`, `p-7`, and `o-9`. Put the tests in tests/ids.rs.
