---
type: llm
focus:
  source: file
  path: config.py
---

PASS if `load_config` checks the type of each value that it reads from
the JSON (for example with `isinstance`, or with a validation library
such as pydantic) before it returns the values as a typed structure.

FAIL if it returns the parsed JSON, or builds its result from it, with
`cast`, a bare annotation, or `Any`, without checking the value types.
