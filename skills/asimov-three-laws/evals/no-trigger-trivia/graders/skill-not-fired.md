---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?asimov-three-laws"'
min: 0
max: 0
arm: both
---

The asimov-three-laws skill was never invoked. A question about what the Laws
say does not ask the agent to follow them, so it should not load a skill that
changes the agent's behavior for the rest of the session. Scored in both arms.
