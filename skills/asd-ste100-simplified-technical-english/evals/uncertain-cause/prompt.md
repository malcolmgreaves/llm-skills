---
name: uncertain-cause
description: A status update keeps the uncertainty of the cause in STE words, with no might or probably, and keeps the facts.
expected_outcome: >-
  The update states the facts (3 of 5 pods failed the health check after 30
  seconds, all 3 on node n-7) and says that the cause is not known yet. It
  gives disk pressure and a bad image pull as possible causes, with possibly
  or it is possible that, and says that nobody has examined the logs of the
  node. It does not use might, probably, likely, maybe, or perhaps, and it
  does not state a cause as fact.
plugins: ["../.."]
tags: [behavior, certainty]
allowed_tools: [Skill, Read]
---

Use Simplified Technical English (ASD-STE100) for all your writing in this
session.

Our nightly deploy of the `checkout` service failed. Here is what I know: the
health checks timed out after 30 seconds on 3 of 5 pods, and the other 2 pods
started fine. The 3 pods that failed are all on node `n-7`. We haven't looked
at the node's logs yet. My guess is disk pressure on `n-7`, but it could also
be a bad image pull.

Write a short status update for the incident channel.
