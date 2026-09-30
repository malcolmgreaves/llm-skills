---
type: regex
target:
  source: file
  path: src/lib.rs
pattern: '^(?:(?!#\[cfg\(test\)\])[\s\S])*?(?:^|\n)(?![ \t]*/[/*])[^\n]*(?:\.|::)(?:unwrap|expect)\('
match: not_contains
---

No line of src/lib.rs before its first `#[cfg(test)]` calls `unwrap()` or
`expect()`, including a chained call on its own line (`.expect("..")`).
Lines that start with `//` or `/*` (comments and doctests) are exempt, and
so is a test module at the end of the file.
