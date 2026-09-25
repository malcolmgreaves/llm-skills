---
name: no-trigger-trivia
description: A question about the Three Laws that does not ask the agent to follow them must not load the skill.
expected_outcome: >-
  The skill does not fire. Near-miss over-trigger control: the user asks what
  the Laws say, which the model can answer without adopting them. Loading the
  skill here would change the agent's behavior for the rest of the session.
plugins: ["../.."]
tags: [trigger]
allowed_tools: [Skill]
---

Settling a bet with a friend: what are Asimov's Three Laws of Robotics? Just
list them.
