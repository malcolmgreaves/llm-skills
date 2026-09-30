---
type: llm
focus:
  source: file
  path: src/lib.rs
---

PASS if the method that records a length in the index takes a type that
only the hashing code can construct (a private field, with no public
constructor that accepts an arbitrary number), so that passing a
peer-reported `u64` is a compile error.

FAIL if the index accepts a plain integer, or relies on a runtime flag, an
enum checked at run time, or a comment to keep unverified lengths out.
