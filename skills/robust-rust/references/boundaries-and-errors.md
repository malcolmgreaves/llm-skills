# Boundaries and errors

Read this when you write a parser, a `serde` impl, a conversion from a raw
representation, or an error type. In the doctests, `my_crate` stands for the
name of your crate.

## Contents

- [Parse, don't validate](#parse-dont-validate)
- [Decode each byte format in one place](#decode-each-byte-format-in-one-place)
- [Keep escape hatches narrow](#keep-escape-hatches-narrow)
- [Evidence types](#evidence-types)
- [Error enums](#error-enums)
- [Panics](#panics)

## Parse, don't validate

A function that validates returns `bool` or `Result<(), E>`, and the caller
then carries the original, unrefined value. Nothing stops the next caller
from skipping the check, so code deeper in the program checks again. A
function that parses returns a new type that can only hold valid values. The
check happens once, and every function that takes the new type relies on it.

- Put the parse at the boundary where the data enters: a CLI argument, a
  config file, a request body, a database row, bytes read from disk.
- Implement `TryFrom<&str>` (and `FromStr`, if users type the value), or a
  `parse` function, that returns the refined type or a typed error.
- Route deserialization through the same function with
  `#[serde(try_from = "String")]`. A derived `Deserialize` writes the private
  field directly and skips the check.
- Order a refined type by its domain, not by its rendering. Paths compare
  component by component: `a/b` comes before `a-b`, although `/` sorts after
  `-` as a byte.

```rust
use serde::{Deserialize, Serialize};
use std::fmt;

/// One path component: not empty, no `/`, and not `.` or `..`.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct Name(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NameError {
    Empty,
    Separator { at: usize },
    Dots,
}

impl fmt::Display for NameError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Empty => write!(f, "a name can't be empty"),
            Self::Separator { at } => write!(f, "a name can't hold '/' (byte {at})"),
            Self::Dots => write!(f, "a name can't be '.' or '..'"),
        }
    }
}

impl std::error::Error for NameError {}

impl TryFrom<&str> for Name {
    type Error = NameError;

    fn try_from(raw: &str) -> Result<Self, NameError> {
        if raw.is_empty() {
            Err(NameError::Empty)
        } else if let Some(at) = raw.find('/') {
            Err(NameError::Separator { at })
        } else if raw == "." || raw == ".." {
            Err(NameError::Dots)
        } else {
            Ok(Name(raw.to_string()))
        }
    }
}

impl TryFrom<String> for Name {
    type Error = NameError;

    fn try_from(raw: String) -> Result<Self, NameError> {
        Name::try_from(raw.as_str())
    }
}

impl From<Name> for String {
    fn from(name: Name) -> String {
        name.0
    }
}

impl Name {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// A relative path. `Ord` compares component by component.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct RelPath(Vec<Name>);

impl TryFrom<&str> for RelPath {
    type Error = NameError;

    fn try_from(raw: &str) -> Result<Self, NameError> {
        raw.split('/')
            .map(Name::try_from)
            .collect::<Result<Vec<_>, _>>()
            .map(RelPath)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deserialize_runs_the_same_checks() {
        let name: Result<Name, _> = serde_json::from_str("\"notes\"");
        assert_eq!(name.map(String::from).ok().as_deref(), Some("notes"));
        assert!(serde_json::from_str::<Name>("\"a/b\"").is_err());
        assert!(serde_json::from_str::<Name>("\"..\"").is_err());
    }

    #[test]
    fn paths_sort_by_component() {
        let slash = RelPath::try_from("a/b").unwrap();
        let dash = RelPath::try_from("a-b").unwrap();
        assert!(slash < dash);
        assert!("a/b" > "a-b");
    }
}
```

## Decode each byte format in one place

Give each byte format exactly one decoder and one encoder. The decoder checks
everything once and returns a view whose accessors can't fail:

- Lengths and offsets, with checked arithmetic (`checked_add`,
  `split_at_checked`, `usize::try_from`). A declared length can be any
  number, so an unchecked `offset + len` can overflow or slice past the end.
  Read fixed-width fields as arrays (`split_first_chunk::<N>()`), so that
  converting them to integers can't fail and needs no `expect`.
- Magic bytes and the format version. Accept only the versions that the code
  can read, and refuse others with a typed error.
- Tag bytes, through a function that returns `Option` or `Result`.
- UTF-8, when a field is text.
- Trailing bytes after the last field. Refuse them: they mean the declared
  counts are wrong.

Return a typed error for each failure, with the byte offset where it
happened. Never panic on input: an index or slice past the end is a panic, so
use `get` and the `_checked` methods.

```rust
use std::fmt;

const MAGIC: &[u8; 2] = b"RS";
const VERSION: u8 = 1;

/// A validated buffer of length-prefixed UTF-8 records.
/// Its accessors can't fail, and they return slices of the input.
#[derive(Debug)]
pub struct Records<'a> {
    items: Vec<&'a str>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FormatError {
    Truncated { at: usize, needed: usize },
    BadMagic,
    UnsupportedVersion(u8),
    NotUtf8 { record: u32 },
    TrailingBytes { at: usize },
}

impl fmt::Display for FormatError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Truncated { at, needed } => {
                write!(f, "needed {needed} more bytes at offset {at}")
            }
            Self::BadMagic => write!(f, "the buffer doesn't start with {MAGIC:?}"),
            Self::UnsupportedVersion(v) => write!(f, "version {v} isn't supported"),
            Self::NotUtf8 { record } => write!(f, "record {record} isn't UTF-8"),
            Self::TrailingBytes { at } => write!(f, "unexpected bytes from offset {at}"),
        }
    }
}

impl std::error::Error for FormatError {}

/// Takes `n` bytes from the front of `rest`, or reports where input ran out.
fn take<'a>(rest: &mut &'a [u8], n: usize, at: usize) -> Result<&'a [u8], FormatError> {
    let (head, tail) = rest
        .split_at_checked(n)
        .ok_or(FormatError::Truncated { at, needed: n })?;
    *rest = tail;
    Ok(head)
}

/// Takes exactly `N` bytes as an array, so no later length check can fail.
fn take_array<const N: usize>(rest: &mut &[u8], at: usize) -> Result<[u8; N], FormatError> {
    let (head, tail) = rest
        .split_first_chunk::<N>()
        .ok_or(FormatError::Truncated { at, needed: N })?;
    *rest = tail;
    Ok(*head)
}

impl<'a> Records<'a> {
    pub fn parse(bytes: &'a [u8]) -> Result<Self, FormatError> {
        let mut rest = bytes;
        let offset = |rest: &[u8]| bytes.len() - rest.len();
        if take_array(&mut rest, 0)? != *MAGIC {
            return Err(FormatError::BadMagic);
        }
        let [version] = take_array(&mut rest, 2)?;
        if version != VERSION {
            return Err(FormatError::UnsupportedVersion(version));
        }
        let count = u32::from_le_bytes(take_array(&mut rest, 3)?);
        let items = (0..count)
            .map(|record| {
                let at = offset(rest);
                let len = u16::from_le_bytes(take_array(&mut rest, at)?);
                let at = offset(rest);
                let body = take(&mut rest, usize::from(len), at)?;
                std::str::from_utf8(body).map_err(|_| FormatError::NotUtf8 { record })
            })
            .collect::<Result<Vec<_>, _>>()?;
        if !rest.is_empty() {
            return Err(FormatError::TrailingBytes { at: offset(rest) });
        }
        Ok(Records { items })
    }

    pub fn len(&self) -> usize {
        self.items.len()
    }

    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    /// The records borrow from the input buffer, not from `self`.
    pub fn iter(&self) -> impl Iterator<Item = &'a str> {
        self.items.iter().copied()
    }

    pub fn longest(&self) -> Option<&'a str> {
        self.iter().max_by_key(|record| record.len())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn encode(records: &[&str]) -> Vec<u8> {
        let mut out = MAGIC.to_vec();
        out.push(VERSION);
        out.extend_from_slice(&(records.len() as u32).to_le_bytes());
        for record in records {
            out.extend_from_slice(&(record.len() as u16).to_le_bytes());
            out.extend_from_slice(record.as_bytes());
        }
        out
    }

    #[test]
    fn parses_valid_input() {
        let bytes = encode(&["a", "ccc", "bb"]);
        let records = Records::parse(&bytes).unwrap();
        assert_eq!(records.len(), 3);
        assert_eq!(records.longest(), Some("ccc"));
    }

    #[test]
    fn refuses_bad_input() {
        let good = encode(&["ab"]);
        let cases: [(&str, Vec<u8>, FormatError); 5] = [
            ("empty", vec![], FormatError::Truncated { at: 0, needed: 2 }),
            ("magic", b"XX\x01".to_vec(), FormatError::BadMagic),
            (
                "version",
                b"RS\x02".to_vec(),
                FormatError::UnsupportedVersion(2),
            ),
            (
                "short body",
                good[..good.len() - 1].to_vec(),
                FormatError::Truncated { at: 9, needed: 2 },
            ),
            (
                "trailing",
                [good.as_slice(), b"!"].concat(),
                FormatError::TrailingBytes { at: 11 },
            ),
        ];
        for (name, bytes, expected) in cases {
            assert_eq!(Records::parse(&bytes).unwrap_err(), expected, "{name}");
        }
    }
}
```

## Keep escape hatches narrow

Some code must turn a raw value into a typed one without the usual check: a
storage layer reads back a key that it wrote from a valid value. Each such
conversion is a hole in the type's guarantee, so keep each one as small as
the design allows. In order of preference:

1. **No raw-to-typed conversion.** Constructors take the typed inputs that
   the value is derived from.
2. **A typed codec.** The storage layer's key encoder and decoder take and
   return the typed value, so no other code holds the raw key.
3. **A private or `pub(crate)` converter**, called from the few places that
   read storage. Give it a fixed-size input (`[u8; 16]` instead of `&[u8]`)
   when it decodes bytes, so that the caller must check the length first.
4. **Test-only constructors** behind `#[cfg(test)]`.

Anything wider is an exception, and needs the user's explicit approval for
the one site, after you explain the rule, its reason, and the consequences.
Cross-crate boundaries are the usual reason:

- **A `pub` converter that another crate must call.** Name it for its trust
  assumption (`from_key_trusted`, `new_unchecked`), and say in its doc
  comment what the caller must guarantee and who may call it.
- **A `test-support` feature** that exposes constructors to another crate's
  tests. Cargo unifies features across a workspace, so check that a
  production build doesn't turn the feature on.

Mark each approved exception at its site with an `EXCEPTION` comment that
names the rule, the reason, the approval, and the consequence.

Never add these to a type with an invariant, except through the same
approval:

- A public field.
- `impl From<raw>` or a public `from_raw`. `From` is also called silently by
  `?` and `.into()`.
- `#[derive(Deserialize)]` without `#[serde(try_from = ..)]`. An evidence
  type gets no derived `Deserialize` at all, because no input can prove how
  a value was made.
- `impl DerefMut`. It lets any caller change the inner value and break the
  invariant.
- `impl Deref<Target = raw>` on an identity type. It makes every method of
  the raw type callable on the ID, and lets `*id` flow into any function
  that takes the raw type. Expose the raw form through a named, read-only
  method (`get()`, `as_bytes()`), so that each use is visible. On other
  constrained types, such as a validated name, `Deref` to the raw type
  isn't forbidden, but prefer a named accessor (`as_str()`) for the same
  reason.

## Evidence types

Some values are trustworthy only because of how they were made: a length
that was counted while the bytes were hashed, a receipt that a step
completed. A plain `u64` can't tell a counted length from one a peer
claimed. Make the provenance a type:

- Wrap the value in a type with private fields and no derived
  `Deserialize`. Only the code that produces the evidence can construct it,
  usually a method that takes `self`, such as `finish(self)`. A public field
  or a derived `Copy` plus a public constructor turns the proof back into a
  plain value.
- Make each consumer that must trust the value take the evidence type as a
  required argument, not an `Option` and not a runtime flag.
- When both trusted and untrusted values flow through the same code, use an
  enum (`Length::Verified(CountedLen)` or `Length::Claimed(u64)`), and give it
  methods named for each use.
- Pin the seal with a `compile_fail` doctest.
- State in the doc comment what the seal prevents: it stops mistakes, not a
  caller who uses `unsafe` or a test-only constructor on purpose.

```rust
/// A byte length counted while hashing. Only [`Hasher::finish`] makes one.
///
/// ```compile_fail
/// let forged = my_crate::CountedLen(7);
/// ```
///
/// ```
/// let mut hasher = my_crate::Hasher::default();
/// hasher.update(b"abc");
/// let (_digest, len) = hasher.finish();
/// assert_eq!(len.get(), 3);
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CountedLen(u64);

impl CountedLen {
    pub fn get(self) -> u64 {
        self.0
    }
}

#[derive(Default)]
pub struct Hasher {
    state: u64,
    count: u64,
}

impl Hasher {
    pub fn update(&mut self, bytes: &[u8]) {
        self.state = bytes.iter().fold(self.state, |h, b| {
            (h ^ u64::from(*b)).wrapping_mul(0x0100_0000_01b3)
        });
        self.count += bytes.len() as u64;
    }

    pub fn finish(self) -> (u64, CountedLen) {
        (self.state, CountedLen(self.count))
    }
}

/// Where a length came from.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Length {
    Verified(CountedLen),
    Claimed(u64),
}

/// The index stores only lengths that it can trust.
#[derive(Default)]
pub struct Index {
    entries: Vec<(u64, u64)>,
}

impl Index {
    /// Takes `CountedLen`, so a claimed length can't reach the index.
    pub fn record(&mut self, digest: u64, len: CountedLen) {
        self.entries.push((digest, len.get()));
    }

    pub fn total(&self) -> u64 {
        self.entries.iter().map(|(_, len)| len).sum()
    }
}
```

## Error enums

- **One enum per boundary.** Each subsystem (a parser, a store, a network
  client) gets its own error enum. One crate-wide enum makes every function
  appear to fail in every way.
- **One variant per distinct response.** Add a variant when a caller or an
  operator would do something different, not for each place that fails.
- **Typed, named fields.** `Mismatch { expected: Hash, actual: Hash }`, not
  `Mismatch(String)`. Include the identifier and the offset that let an
  operator find the problem. When an identifier is unknown, use
  `Option<Id>`; never make up a zero ID.
- **Keep the cause.** Implement `std::error::Error::source()`, or use
  `#[source]` with `thiserror`. When a foreign library's error type can't
  appear in yours, box it (`Box<dyn std::error::Error + Send + Sync>`)
  instead of converting it to a `String`, so that the cause stays available.
- **Separate failure from corruption.** "The backend failed to answer" and
  "the backend answered, and the answer proves the data is broken" need
  different responses (retry or repair). Keep them in different variants,
  and don't report one as the other.
- **Keep a generic backend's error type.** A function generic over a backend
  returns `MyError<B::Error>`, or requires `MyError: From<B::Error>`. Don't
  erase the backend error to a string.
- **Discharge impossible errors with `Infallible`.** An in-memory backend
  that can't fail uses `type Error = Infallible`, and code removes that arm
  with `match never {}`, so no `unreachable!()` is needed.
- **Add context with a curried constructor.** A method that returns
  `impl FnOnce(E) -> MyError` keeps `map_err` short and makes each call site
  supply the context.
- **Add `#[non_exhaustive]`** only to error enums published for other
  people's crates.
- **Write `Debug` by hand** for a generic error whose fields are
  associated-type projections. `#[derive(Debug)]` bounds the type
  parameters, not the projections.

```rust
use std::collections::HashMap;
use std::convert::Infallible;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Table {
    Chunks,
    Manifests,
}

/// Errors of the index. The backend's own error type is kept.
#[derive(Debug, thiserror::Error)]
pub enum IndexError<E: std::error::Error + 'static> {
    #[error("the {table:?} table failed")]
    Backend {
        table: Table,
        #[source]
        source: E,
    },
    #[error("key {key:#x} in the {table:?} table holds {len} bytes, not 16")]
    Corrupt { table: Table, key: u64, len: usize },
}

impl Table {
    /// Makes each `map_err` name the table that failed.
    pub fn failed<E: std::error::Error + 'static>(self) -> impl FnOnce(E) -> IndexError<E> {
        move |source| IndexError::Backend {
            table: self,
            source,
        }
    }
}

/// The signature that a key-value backend implements.
pub trait Kv {
    type Error: std::error::Error + 'static;
    fn get(&self, table: Table, key: u64) -> Result<Option<Vec<u8>>, Self::Error>;
}

/// Reads one 16-byte record. `Ok(None)` means absent; a wrong size is corrupt.
pub fn record<K: Kv>(kv: &K, key: u64) -> Result<Option<[u8; 16]>, IndexError<K::Error>> {
    let Some(bytes) = kv.get(Table::Chunks, key).map_err(Table::Chunks.failed())? else {
        return Ok(None);
    };
    let len = bytes.len();
    <[u8; 16]>::try_from(bytes)
        .map(Some)
        .map_err(|_| IndexError::Corrupt {
            table: Table::Chunks,
            key,
            len,
        })
}

/// An in-memory backend can't fail.
#[derive(Default)]
pub struct MemKv(HashMap<(Table, u64), Vec<u8>>);

impl Kv for MemKv {
    type Error = Infallible;

    fn get(&self, table: Table, key: u64) -> Result<Option<Vec<u8>>, Infallible> {
        Ok(self.0.get(&(table, key)).cloned())
    }
}

/// With an infallible backend, only corruption is left to handle.
pub fn corrupt_key(error: IndexError<Infallible>) -> u64 {
    match error {
        IndexError::Backend { source, .. } => match source {},
        IndexError::Corrupt { key, .. } => key,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn absent_and_corrupt_are_different() {
        let mut kv = MemKv::default();
        kv.0.insert((Table::Chunks, 7), vec![0; 3]);
        assert!(matches!(record(&kv, 1), Ok(None)));
        let error = record(&kv, 7).unwrap_err();
        assert_eq!(
            error.to_string(),
            "key 0x7 in the Chunks table holds 3 bytes, not 16"
        );
        assert_eq!(corrupt_key(error), 7);
    }
}
```

## Panics

A panic is a bug report, not error handling.

- **Never call `unwrap()` outside test code.** Unit tests, integration tests,
  and doctests may call it, because there a panic is a test failure.
- **Avoid `expect()`.** First make the failure impossible: read a
  fixed-width field as an array, keep a non-empty collection in a type that
  can't be empty, or restructure so the value can't be absent. Otherwise,
  return a typed error with `ok_or`, `ok_or_else`, or `let ... else`.
- **When `expect` is the only option,** give it a static message that states
  the invariant that broke: `expect("the index holds each key it listed")`.
  Not `expect("failed")`, not `expect("")`, and not a formatted string.
  Call it right after the check that established the invariant.
- **Don't panic on input data.** Indexing and slicing past the end panic, so
  use `get` and the `_checked` methods at boundaries. Use
  `std::convert::Infallible` and `match never {}` instead of
  `unreachable!()` for cases that types can rule out.
- **Use `debug_assert!`** only for checks that are too slow for release
  builds, and only where another mechanism (a type, a test) also covers the
  rule.
- **Recommend the lints** that enforce this, and apply them only if the user
  agrees. In `Cargo.toml`, `[lints.clippy]` with `unwrap_used = "deny"` and
  `expect_used = "deny"`; in `clippy.toml`, `allow-unwrap-in-tests = true`
  and `allow-expect-in-tests = true`. These settings exempt `#[test]`
  functions and `#[cfg(test)]` modules, but not helper functions in
  `tests/`: put `#![allow(clippy::unwrap_used, clippy::expect_used)]` at the
  top of each integration test file that has helpers.
