# Testing the type design

Read this when you add tests for a type-level guarantee, and before you
finish a change that adds a seal, a typestate rule, an encoding, or an enum
variant. In the doctests, `my_crate` stands for the name of your crate.

## Contents

- [`compile_fail` doctests](#compile_fail-doctests)
- [trybuild for macros](#trybuild-for-macros)
- [Static assertions](#static-assertions)
- [Golden bytes and identity matrices](#golden-bytes-and-identity-matrices)
- [Table tests](#table-tests)
- [Property and differential tests](#property-and-differential-tests)
- [State-machine tests](#state-machine-tests)
- [Tests that can fail](#tests-that-can-fail)

## `compile_fail` doctests

A seal or a typestate rule says that some code doesn't compile. A unit test
inside the crate can't check that: inside the defining module, the private
field is visible and the forbidden call compiles. A doctest compiles as a
separate crate that sees only the public API, which is the view you want to
test.

- Put one forbidden thing in each `compile_fail` block. With two, the block
  passes when either one fails, so the other can regress unnoticed.
- Put a block that does the legal thing next to them, and make it compile
  and run. A `compile_fail` block passes on any compile error, including a
  typo or a wrong path, and stable rustdoc doesn't check an error code
  written on the block (`compile_fail,E0603`). The legal block shows that
  the paths and names in the failing blocks are right, so each failure is
  the intended one.
- Test each route into the type: the tuple constructor, `From`/`Into`, each
  `pub(crate)` constructor, and each method that only some stages have.
- Doctests run only for library targets. If the types live in a binary
  crate, move them into `src/lib.rs`.
- cargo-nextest doesn't run doctests. In a project that uses nextest, also
  run `cargo test --doc`.
- A language change can make a failing block compile. The test then fails,
  and you check whether the seal still holds.

```rust
use std::fmt;

/// A user ID. Code outside the crate gets one only by parsing.
///
/// ```compile_fail
/// let id = my_crate::UserId(42);
/// ```
///
/// ```compile_fail
/// let id: my_crate::UserId = 42u64.into();
/// ```
///
/// ```compile_fail
/// let id = my_crate::UserId::from_db(42);
/// ```
///
/// ```
/// let id = my_crate::UserId::parse("u-42").unwrap();
/// assert_eq!(id.to_string(), "u-42");
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct UserId(u64);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BadUserId(pub String);

impl UserId {
    pub fn parse(raw: &str) -> Result<Self, BadUserId> {
        raw.strip_prefix("u-")
            .and_then(|digits| digits.parse().ok())
            .map(UserId)
            .ok_or_else(|| BadUserId(raw.to_string()))
    }

    /// For the database layer only: the column holds IDs this crate wrote.
    pub(crate) fn from_db(raw: u64) -> Self {
        UserId(raw)
    }
}

impl fmt::Display for UserId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "u-{}", self.0)
    }
}

/// The database layer turns stored rows back into IDs.
pub fn load_ids(rows: &[u64]) -> Vec<UserId> {
    rows.iter().copied().map(UserId::from_db).collect()
}
```

## trybuild for macros

For a derive or procedural macro, the test must also check the error
message that the user sees. Use the `trybuild` crate: each file in
`tests/compile_fail/` is a program that must fail, and a committed `.stderr`
file next to it holds the exact expected output.

```rust
// In tests/compile_tests.rs:
#[test]
fn compile_tests() {
    let cases = trybuild::TestCases::new();
    // A pass case makes trybuild run `cargo build`, not `cargo check`.
    cases.pass("tests/pass/*.rs");
    cases.compile_fail("tests/compile_fail/*.rs");
}
```

- Register at least one `pass` case. Without one, trybuild runs
  `cargo check`, which doesn't evaluate `const` assertions made during
  monomorphization, so a compile-time rule written as such a `const` can't
  fail. The pass case also checks that the macro's output compiles.
- Write one fixture for each entry point that reaches each guard.
- Generate or update the `.stderr` files with
  `TRYBUILD=overwrite cargo test --test compile_tests`, read each diff, and
  commit them. Compiler messages change between releases, so pin the
  toolchain in CI, or regenerate the files when you upgrade.

## Static assertions

Check facts that the compiler knows with `const` assertions. They fail the
build, not a test run.

- Trait facts: `const _: () = assert!(<Option<u64> as Field>::NULLABLE);`
- Layout of on-disk or FFI structs: `size_of`, `align_of`, and `offset_of!`.
- Relations between constants, such as a header length and the sum of its
  field widths.

```rust
use std::mem::{offset_of, size_of};

/// The on-disk header. Its layout is part of the file format.
#[repr(C)]
pub struct Header {
    pub magic: [u8; 4],
    pub version: u32,
    pub count: u64,
}

pub const HEADER_LEN: usize = 16;

const _: () = assert!(size_of::<Header>() == HEADER_LEN);
const _: () = assert!(offset_of!(Header, version) == 4);
const _: () = assert!(offset_of!(Header, count) == 8);

impl Header {
    pub fn to_bytes(&self) -> [u8; HEADER_LEN] {
        let mut out = [0; HEADER_LEN];
        out[..4].copy_from_slice(&self.magic);
        out[4..8].copy_from_slice(&self.version.to_le_bytes());
        out[8..].copy_from_slice(&self.count.to_le_bytes());
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Golden bytes: a change to the encoding must change this test.
    #[test]
    fn header_bytes_are_stable() {
        let header = Header {
            magic: *b"RSK1",
            version: 2,
            count: 3,
        };
        assert_eq!(
            header.to_bytes(),
            *b"RSK1\x02\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00"
        );
    }
}
```

## Golden bytes and identity matrices

- **Golden bytes.** For each encoding that is stored or sent, and for each
  identity hash, pin the exact bytes of a few known values in a test. A
  refactor that changes the bytes then fails a test, instead of silently
  making old data unreadable.
- **Identity matrices.** When an identity is derived from several inputs,
  build a base case and one case per input with only that input changed,
  and assert that all the identities are different. The test fails when an
  input doesn't reach the identity, which is the bug that lets two different
  objects share an identity.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct CommitId(u64);

impl CommitId {
    /// Every input reaches the identity. A tag byte keeps `None` apart from
    /// every `Some` value.
    pub fn new(tree: u64, parent: Option<u64>, message: &str, time: i64) -> Self {
        let mut input = tree.to_le_bytes().to_vec();
        match parent {
            None => input.push(0),
            Some(parent) => {
                input.push(1);
                input.extend_from_slice(&parent.to_le_bytes());
            }
        }
        input.extend_from_slice(&time.to_le_bytes());
        input.extend_from_slice(message.as_bytes());
        CommitId(input.iter().fold(0xcbf2_9ce4_8422_2325, |h, b| {
            (h ^ u64::from(*b)).wrapping_mul(0x0100_0000_01b3)
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn each_input_changes_the_identity() {
        let ids = [
            CommitId::new(1, Some(9), "fix", 100),
            CommitId::new(2, Some(9), "fix", 100),
            CommitId::new(1, None, "fix", 100),
            CommitId::new(1, Some(u64::MAX), "fix", 100),
            CommitId::new(1, Some(8), "fix", 100),
            CommitId::new(1, Some(9), "fix!", 100),
            CommitId::new(1, Some(9), "fix", 101),
        ];
        let distinct: HashSet<_> = ids.iter().collect();
        assert_eq!(distinct.len(), ids.len());
    }
}
```

## Table tests

Rust has no built-in parametrized test. Write one test function that loops
over an array of cases, and put a name or the input in each assertion
message, so a failure says which case broke. If the project uses `rstest`,
use `#[case]`, which reports each case as its own test.

- Cover each variant of each enum that the code under test produces or
  consumes, including error variants.
- Cover the boundaries: empty input, one element, the maximum, one past the
  maximum, and unknown tags.
- Put error cases in the same table when the function returns `Result`, and
  compare the whole `Result`, so that a case fails when the error variant or
  its fields are wrong.

## Property and differential tests

- **Round trips.** For each codec, check that decoding an encoded value gives
  the value back, and that decoding refuses each truncation of a valid
  encoding.
- **Differential tests.** When you replace a simple algorithm with a faster
  or more incremental one, keep the simple one as a reference in the tests,
  and compare the two on many inputs.
- **Orders and equivalences.** When a type's `Ord` or `Eq` must agree with
  another representation (a sort key's bytes, a rendered string), check the
  agreement on many generated pairs.

Use `proptest` or `quickcheck` if the project has one. Otherwise, a small
seeded generator gives deterministic inputs without a dependency:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VarintError {
    Truncated,
    Overflow,
}

/// LEB128: seven bits per byte, low bits first.
pub fn encode(mut value: u64) -> Vec<u8> {
    let mut out = Vec::new();
    loop {
        let byte = (value & 0x7f) as u8;
        value >>= 7;
        if value == 0 {
            out.push(byte);
            return out;
        }
        out.push(byte | 0x80);
    }
}

/// Returns the value and the number of bytes read.
pub fn decode(bytes: &[u8]) -> Result<(u64, usize), VarintError> {
    let mut value = 0u64;
    for (index, byte) in bytes.iter().enumerate() {
        let shift = 7 * index as u32;
        let part = u64::from(byte & 0x7f);
        if shift >= 64 || (shift == 63 && part > 1) {
            return Err(VarintError::Overflow);
        }
        value |= part << shift;
        if byte & 0x80 == 0 {
            return Ok((value, index + 1));
        }
    }
    Err(VarintError::Truncated)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A deterministic generator: the same seed gives the same inputs.
    fn xorshift(mut state: u64) -> impl Iterator<Item = u64> {
        std::iter::from_fn(move || {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            Some(state)
        })
    }

    #[test]
    fn round_trips() {
        let edges = [0, 1, 127, 128, 16_383, 16_384, u64::MAX];
        let random = xorshift(0x9e37_79b9_7f4a_7c15).take(10_000);
        for value in edges.into_iter().chain(random) {
            let bytes = encode(value);
            assert_eq!(decode(&bytes), Ok((value, bytes.len())), "{value}");
            for cut in 0..bytes.len() {
                assert_eq!(
                    decode(&bytes[..cut]),
                    Err(VarintError::Truncated),
                    "{value}"
                );
            }
        }
    }
}
```

## State-machine tests

- Assert that each illegal transition returns its typed error, not only that
  the legal path works.
- For each transaction, test that dropping it before its terminal method
  leaves no trace.
- Simulate a crash between two persisted steps: run the first step, drop
  every in-memory value, reopen from storage, and run the recovery path.
  Check that repeating a completed step succeeds and changes nothing.
- After an operation is refused, commit and read back, so that the test
  shows the refusal changed nothing. Without the commit, an abort explains
  the same result.

## Tests that can fail

A test that can't fail proves nothing.

- In the test's name or comment, name the regression it guards against.
- Build the fixture so that the regression would trip it: a `None` in the
  middle of a column, a sibling field next to the one under test, an index
  above 0, two items that differ only in the input under test.
- Once, change the code under test on purpose (flip a comparison, drop an
  input from a hash) and confirm that the test fails.
- Assert values, not incidental facts such as which lifetime a borrow has.
- To check a complexity bound, wrap a dependency in a test double that
  counts calls, and assert the count.
