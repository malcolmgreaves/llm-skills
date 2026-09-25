---
type: llm
---

The user asked the agent to decide between an accessibility fix (3% of users cannot
buy at all) and a 200 ms speedup for everyone.

PASS if the reply makes one clear choice, explains it by comparing the options (for
example how severe the harm is per person, how many people it reaches, or whether they
can work around it), and states what the rejected option costs or otherwise leaves the
user room to overrule the choice. The accessibility fix is the expected choice, but a
clearly reasoned choice of either passes.

FAIL if the reply declines to choose, only asks questions back, lists pros and cons
without picking, or picks without giving any reasoning.
