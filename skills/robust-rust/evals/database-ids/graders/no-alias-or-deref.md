---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: 'type\s+\w*Id\s*=\s*u64\b|Deref\s+for\s+(?:\w*Id\b|\$\w+)'
match: not_contains
---

No ID in src/lib.rs is a type alias for `u64`, and no ID type implements
`Deref`, including through a `macro_rules!` impl.
