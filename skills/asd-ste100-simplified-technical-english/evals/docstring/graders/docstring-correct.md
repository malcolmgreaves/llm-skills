---
type: llm
---

The function sorts the events by `ts`. It drops an event when the last kept
event with the same `user_id` and `type` is less than `window_s` seconds
earlier. Thus, the window starts again at each kept event, not at each event.

PASS if the docstring states that an event is dropped when it is less than
`window_s` seconds after the last kept event with the same `user_id` and
`type` (in any wording).

FAIL if the docstring states a different rule, for example that two events
are duplicates when their timestamps are less than `window_s` seconds apart,
or that each event is compared with the previous event, or if it leaves out
the condition that the user and the type are the same.
