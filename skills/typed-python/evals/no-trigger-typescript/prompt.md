---
name: no-trigger-typescript
description: A typed-code request in another language must not load the skill.
expected_outcome: >-
  The skill does not fire. Over-trigger control: the request is about types, but in TypeScript.
plugins: ["../.."]
tags: [trigger]
allowed_tools: [Skill]
---

Write a TypeScript function that groups an array of orders by customer ID
and returns a Map from each customer ID to the total amount of their
orders.
