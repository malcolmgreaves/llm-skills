---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: 'struct\s+(?:\w*Id|\$\w+)\s*(?:<[^>]*>)?\s*(?:\(\s*pub\b(?!\s*\()|\{[^}]*?\bpub\b(?!\s*\()\s*\w+\s*:)'
match: not_contains
---

No ID type in src/lib.rs has a public field, in tuple or named-field form,
including a struct that a `macro_rules!` generates (`struct $name(pub u64)`).
A `pub(crate)` field is not public.
