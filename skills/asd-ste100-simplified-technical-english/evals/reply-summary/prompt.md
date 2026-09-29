---
name: reply-summary
description: A summary of a change for the team gives the result first, keeps the facts, and uses no modal verbs, contractions, or semicolons that STE rules out.
expected_outcome: >-
  The summary starts with the result (the cache entries expire after 10
  minutes, and the 4 new tests pass). It tells the team that the integration
  tests did not run and why. It has no should, might, would, may, or shall, no
  contractions, and no semicolons.
plugins: ["../.."]
tags: [behavior, reply]
allowed_tools: [Skill, Read]
---

Write in Simplified Technical English for this session.

I changed `src/cache.py` so that cache entries expire after 10 minutes instead
of never. I added `tests/test_cache.py` with 4 tests, and they all pass. I did
not run the integration tests, because they need a Redis server that I don't
have locally.

Write the message that I'll post to the team channel about this change.
