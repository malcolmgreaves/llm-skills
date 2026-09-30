---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: 'impl\s+(?:(?:::)?(?:core|std)::convert::)?From\s*<\s*u64\s*>\s+for\s+(?:\w*Id\b|\$\w+)'
match: not_contains
---

No ID type in src/lib.rs implements `From<u64>`, including through a
`macro_rules!` impl (`impl From<u64> for $name`).
