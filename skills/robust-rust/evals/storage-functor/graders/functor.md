---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if the size-limited layer is one generic type (for example
`Limited<B: Store>`) that works over any backend that implements the
storage trait.

FAIL if there is a separate size-limited type, or copied size-limit logic,
for each backend.
