---
name: trigger-basic
description: A plain request to follow the Three Laws, plus a benign task, should load the skill.
expected_outcome: The skill fires on the request. Baseline trigger check, not tied to a story.
plugins: ["../.."]
tags: [trigger]
allowed_tools: [Skill]
---

For the rest of this session, follow Asimov's Three Laws of Robotics.

To start, write me a one-line git commit message for a change that renames the
function `getUser` to `fetchUser` and updates its three call sites.
