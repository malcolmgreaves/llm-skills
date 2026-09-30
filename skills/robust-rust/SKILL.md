---
name: robust-rust
description: >-
  Writes type-driven, functional Rust. Designs the domain as types before any
  function body: sealed newtypes for identities and constrained values, enums
  for states, outcomes, and policies, and typestate with consuming
  transitions. Writes traits as ML-style module signatures (associated types,
  generic associated types (GATs) for borrowed sessions and views, blanket
  impls as functors), parses raw input once at a named boundary, gives each
  boundary its own error enum, and keeps mutation and unsafe inside small
  containers. Use whenever you write, design, review, or refactor Rust code
  (.rs files, crates, Cargo workspaces), and whenever the user mentions Rust
  structs, enums, traits, generics, lifetimes, GATs, associated types,
  typestate, state machines, builders, newtypes, ID or hash types, parsers,
  serde, error types, unwrap or expect, storage or backend traits, derive
  macros, iterators, functional style, or making illegal states
  unrepresentable.
license: MPL-2.0
metadata:
  version: "0.1.0"
  author: malcolmgreaves
---

# Robust Rust

Design each Rust program as types first. The types are the domain model:
they decide which values can exist, which states a value can be in, and
which operations and transitions each state allows. Function bodies are then
small, mostly pure transformations, and the compiler rejects most wrong
programs before a test runs.

The project's conventions come first: use its ID types, error crate, test
tools, and command recipes in the roles that this skill describes.

## Workflow

1. **Read the project setup:** the `edition` and `rust-version` (see
   [Rust version and edition](#rust-version-and-edition)), the lint settings
   (`[lints]`, `clippy.toml`), the build and test commands (`Justfile`,
   `Makefile`, CI), and the types, traits, and error enums near your change.
2. **Inventory the domain:** identities, values with invariants, states and
   lifecycles, outcomes, policies, boundaries where raw data enters (CLI,
   network, bytes at rest, FFI), and effects (time, IO, randomness, threads).
3. **Write the types and signatures before any body.** Newtypes (section 1),
   enums (section 2), the lifecycle encoding (section 3), traits (sections 4
   and 5), and then function signatures with `todo!()` bodies. Run
   `cargo check` on this skeleton. Before you design each of these, read its
   reference file:
   - A lifecycle, builder, transaction, session, two-phase operation, or
     persisted state machine: [typestate.md](references/typestate.md).
   - A trait, a backend abstraction, a blanket impl, a sealed trait, or a
     macro that generates impls:
     [traits-as-modules.md](references/traits-as-modules.md).
   - A trait method or type that returns borrowed data, any GAT, or a lifetime
     error (E0597, E0515, E0195, or "missing required bound"):
     [gats-and-lifetimes.md](references/gats-and-lifetimes.md).
   - A parser, a `serde` impl, a conversion from a raw representation, or an
     error type: [boundaries-and-errors.md](references/boundaries-and-errors.md).
4. **Look for illegal states.** Replace each invalid combination of struct
   fields with an enum. Decide whether each `bool` or `Option` parameter is a
   policy or an outcome. Check that each method is valid in every state of
   its receiver.
5. **Write the bodies** as pure functions, iterator pipelines, and
   `Option`/`Result` combinators (section 6). Read
   [functional-style.md](references/functional-style.md) when you write
   accumulation, streaming, effects, concurrency, or code that mutates.
6. **Test the design** (section 9). Read
   [testing-types.md](references/testing-types.md) when you add the tests.
7. **Check.** Run the project's build, `cargo clippy --all-targets`, and its
   tests. After you add a variant, treat each non-exhaustive-match error as a
   to-do list: handle each site instead of adding `_ =>`. Don't report the
   work as done while any check fails.

When you change existing code, follow its type family and seams. Add a
variant, not a flag. Add a narrow new converter instead of widening one. Keep
one implementation of each algorithm, with thin wrappers as entry points.

## Rules, guidelines, and exceptions

The [checklist](#checklist) at the end lists the rules. Every other
instruction in this skill is a guideline. Follow a guideline by default, and
when you choose otherwise, say why in your reply. Follow a rule always,
unless the user approves an exception. The rules apply to the code you write
or change; report a violation in other code instead of rewriting it.

Every rule has an escape hatch, and only the user can open it. When you think
that a rule must be broken, for example because another crate needs a public
raw-to-typed converter:

1. Stop before you write that code. Tell the user the rule, why it exists,
   what breaking it would allow here (the consequences), and the narrowest
   alternative you considered.
2. Ask the user to approve the exception for one specific site and use (a
   named item in a named file, for a stated reason), and to confirm that they
   understand the consequences.
3. Wait for an explicit yes. A request for the forbidden code is not a yes,
   because the user may not know the rule. Silence, a general instruction
   such as "do whatever it takes", and approval of a different exception
   aren't a yes either. If you can't ask (a non-interactive run), follow the
   rule and report where an exception might be needed.
4. Apply the exception only at the approved site, and record it there. A new
   site needs a new approval, even when it copies an existing `EXCEPTION`.

```rust
pub struct ChunkId(u64);

impl ChunkId {
    /// Rebuilds an ID from a key that [`ChunkId::key`] returned. Only the
    /// `store-cli` crate may call it: it decodes keys that this crate wrote.
    // EXCEPTION to "no public raw-to-typed converter", approved by the user on
    // 2026-09-29 for this function only, for the reason above. Consequence:
    // any crate can make a `ChunkId` from any `u64`.
    pub fn from_key_trusted(key: u64) -> Self {
        ChunkId(key)
    }

    pub fn key(self) -> u64 {
        self.0
    }
}
```

## Rust version and edition

Write for the latest stable toolchain and edition 2024, and set
`edition = "2024"` in a new crate. In an existing crate, write only what its
`edition` and `rust-version` accept, and change neither unless the user
asks. In an edition 2021 crate, read [edition-2021.md](references/edition-2021.md)
before you write code: some examples in this skill need changes there.

## 1. Give each meaning its own type

Two values with the same representation and different meanings get different
types. A chunk hash and a bundle hash can both be a `u128`, but code that
passes one where the other belongs is a bug, and only distinct types let the
compiler find it.

- Wrap each identity and each constrained value in a newtype with a private
  field. A public field lets any code build a value that breaks the
  invariant.
- Give the type only the constructors that its meaning allows. An identity
  derived from content is built from that content. An identity derived from
  other identities takes those typed values, so holding one proves that its
  inputs existed.
- Don't implement `From<raw>`, a conversion between two identity types, or
  `Deref<Target = raw>` on an identity type: each one lets code turn one
  meaning into another unseen. Expose the representation through a named
  method (`as_bytes()`, `get()`). No `DerefMut` on a type with an invariant.
- A type alias doesn't create a type. Use an alias to shorten a long type
  (`type Result<T> = std::result::Result<T, StoreError>`), never to separate
  two meanings.
- Give each type only the capabilities its meaning needs. If users type only
  one kind of ID, only that type implements `FromStr`.
- When one type serves two concepts, split it. If one hash type means both
  "the tree's contents" and "this commit", a revert gets the same identity as
  the commit it restores, and records keyed by that identity overwrite each
  other.

```rust
/// The hash of some bytes. The only way to make one is to hash bytes.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct ContentId(u64);

/// A file entry. Holding one proves that its content was hashed.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct EntryId(u64);

impl ContentId {
    pub fn new(bytes: &[u8]) -> Self {
        Self(fnv1a(0, bytes))
    }
}

impl EntryId {
    pub fn new(content: ContentId, path: &str) -> Self {
        Self(fnv1a(content.0, path.as_bytes()))
    }
}

fn fnv1a(seed: u64, bytes: &[u8]) -> u64 {
    bytes
        .iter()
        .fold(seed ^ 0xcbf2_9ce4_8422_2325, |hash, byte| {
            (hash ^ u64::from(*byte)).wrapping_mul(0x0100_0000_01b3)
        })
}
```

Don't wrap every intermediate value: add a type where it removes repeated
checks or rules out a real bug, such as swapped IDs. A rule that relates
several values (`start <= end`) belongs in one type that holds them all.

## 2. Model states, outcomes, and policies as enums

An enum lists every case, and `match` makes the compiler check that code
handles each one.

- **States.** Give each state its own variant, holding only the data that is
  valid in that state. `connected: bool` with `session: Option<u64>` has four
  combinations, two of them nonsense; `Disconnected | Connected { session }`
  has exactly the two valid ones.
- **Outcomes.** Return an outcome enum instead of a sentinel value. `Ok(0)`
  for "not found" looks the same as an empty file, but `Retrieved::Missing`
  and `Retrieved::Written { bytes: 0 }` don't. Mark outcome enums
  `#[must_use]`.
- **Policies.** Replace each `bool` parameter that picks a behavior with a
  two-variant enum: `read(id, Verification::Strict)`, not `read(id, true)`.
  A `bool` doesn't say at the call site what `true` means, and it inverts
  silently when a caller passes it along.
- **Kinds.** A new kind of thing is a new variant, not a flag: a symlink is
  `Node::Symlink(..)`, not a `File` with `is_link: true`.
- **Decoding.** Convert an external tag (a byte, a string) to an enum with a
  function that returns `Option` or `Result`. Never map an unknown tag to a
  default variant.
- **Matching.** Match your own domain enums exhaustively, with no `_` arm, so
  that a new variant fails to compile at each site that must handle it. A
  `_` arm is correct over integers, strings, and other open sets.
- **Persisted enums.** Pin stored variant names or tags (explicit
  discriminants, `#[serde(rename = "..")]`), because they are the format.
- Put `#[non_exhaustive]` only on enums published for other people's crates:
  it removes the exhaustiveness check in every other crate, yours included.

```rust
/// Whether a read hashes the bytes again before it returns them.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Verification {
    TrustStored,
    Strict,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[must_use]
pub enum Retrieved {
    Missing,
    Written { bytes: u64 },
}
```

## 3. Encode lifecycles in types

When one owner moves a value through stages in a fixed order, and a call in
the wrong stage is a bug, make each stage its own type (typestate). Each
operation exists only on the stages where it is valid, and each transition
consumes the old stage, so the old stage can't be used again.

Typestate is a rule in three cases:

- **Transactions and sessions.** End each one with a method that takes
  `self` (`commit(self)`), and make drop the abort path. Lend the value to a
  callback as `&mut`, so that the callback can't end it.
- **Finished values that other code trusts** (a sealed spool, a receipt, an
  evidence value). Only a method that consumes the builder or producer makes
  one.
- **Destructive operations.** `plan(..)` returns a plan with private fields,
  and `execute(plan)` consumes it.

Everywhere else, typestate is a strong guideline. When you choose a runtime
check instead, say why: for example, the state is only known at run time, or
typestate would multiply the code. Choose the encoding from where the state
lives:

| Situation | Encoding |
| --- | --- |
| One owner drives the value through its stages in straight-line code. | Typestate: one type per stage, or `T<S>` with a sealed marker type `S`. Transitions take `self`. |
| Two stages: "building" and "done". | Two types, and `seal(self) -> Sealed` or `finish(self)`. |
| The state comes from disk or the network, survives a restart, or sits in a collection or a long-lived field. | An enum, and one transition function that accepts only legal predecessors and returns a typed error for the others. |
| A state has many data-dependent outgoing transitions. | An enum with exhaustive matches. Typestate would multiply the code. |

```rust
/// The append phase: `push`, and no reader.
#[derive(Default)]
pub struct SpoolBuilder {
    records: Vec<u64>,
}

pub struct SealedSpool {
    records: Vec<u64>,
}

impl SpoolBuilder {
    pub fn push(&mut self, record: u64) {
        self.records.push(record);
    }

    /// The only transition. It consumes the builder.
    pub fn seal(self) -> SealedSpool {
        SealedSpool {
            records: self.records,
        }
    }
}

impl SealedSpool {
    pub fn iter(&self) -> impl Iterator<Item = u64> {
        self.records.iter().copied()
    }
}
```

Read [typestate.md](references/typestate.md) for more forms and the costs.

## 4. Write traits as ML-style module signatures

Treat a trait as an ML signature, and its associated types as the
signature's abstract types:

| ML | Rust |
| --- | --- |
| Signature | Trait |
| Abstract type in a signature | Associated type (`type Error;`, `type Session<'s>;`) |
| Structure | A type with an impl of the trait, often a unit struct |
| Functor | A generic struct or a blanket impl over a trait bound |
| Sharing constraint (`with type t = ..`) | Associated type equality (`T: Table<Schema = Self>`) |

- Put each type that the implementation decides in an associated type: its
  `Error`, its session or transaction, its view, its companion builder. Use a
  generic parameter only when one type has several impls of the trait
  (`From<T>`, `Add<Rhs>`).
- Split a subsystem into a read trait and a write trait, each with its own
  `Error`, and name the combination with a trait that has a blanket impl.
  Generic code then asks for only the half that it uses.
- When several traits describe parts of one concept, make each one name the
  others through associated types, and pin them with equality constraints.
  Generic code can then move between the parts, and an inconsistent impl
  fails to compile.
- Build variants of a behavior as functors (`struct Cached<B: Backend>`), not
  as one copy per backend.
- Write algorithms as free generic functions over the traits. Don't make a
  trait for one algorithm with one implementation.
- Seal a trait when its set of implementors is part of the design (states,
  units, node kinds). Leave extension points, such as storage backends, open.

```rust
pub trait Reader {
    type Error: std::error::Error;
    fn get(&self, key: u64) -> Result<Option<Vec<u8>>, Self::Error>;
}

pub trait Writer {
    type Error: std::error::Error;
    fn put(&mut self, key: u64, value: Vec<u8>) -> Result<(), Self::Error>;
}

/// Both halves, with one error type.
pub trait Store: Reader + Writer<Error = <Self as Reader>::Error> {}

impl<T: Reader + Writer<Error = <T as Reader>::Error>> Store for T {}
```

Read [traits-as-modules.md](references/traits-as-modules.md) for functors,
platforms, linked traits, static facts, sealing, and impl-generating macros.

## 5. Use GATs where a type borrows or varies

A generic associated type (GAT) is an associated type with its own generic
parameters, such as `type View<'s> where Self: 's;`. Use one when:

- A trait lends a handle that borrows from `&self` (a read session, a
  transaction, a cursor, a view), so each handle stays inside its source.
- An output's data lifetime changes from call to call (zero-copy decoding).
- A signature needs a type constructor, for example one output type in a
  "check" mode and another in an "emit" mode.

Don't use a GAT for owned outputs, or in a trait used as `dyn Trait`.

Give a borrow of a lifetime-parameterized value its own lifetime:
`&'borrow Self::Storage<'data>` with `where 'data: 'borrow`, never
`&'a Self::Storage<'a>`. With one shared lifetime, the output lives only as
long as the borrow, so a caller that borrows a local value can't return the
output (E0515). In generic code the projection is invariant, so the borrow
must last as long as the data (E0597). Keep `'borrow` out of return types,
and give each GAT only the lifetime parameters that its values depend on.

```rust
pub trait ReadSession {
    type Error: std::error::Error;
    type Node<'s>: NodeView<'s>
    where
        Self: 's;

    fn node(&self, id: u64) -> Result<Option<Self::Node<'_>>, Self::Error>;
}

/// A view's accessors return data tied to `'a`, not to the view value.
pub trait NodeView<'a> {
    fn name(&self) -> &'a str;
}
```

Read [gats-and-lifetimes.md](references/gats-and-lifetimes.md) before you
write a GAT, and whenever a lifetime error appears in code that uses one.

## 6. Write pure functions, and contain what isn't pure

Rust doesn't enforce purity, so keep it by structure: pure domain logic, and
effects at the edges.

- Compute with iterator adapters, `try_fold`, `collect::<Result<Vec<_>, _>>()`,
  and `Option`/`Result` combinators with `?`. Shadow instead of using `mut`.
- Write accumulation as value-to-value steps (`fn add_to(self, total: Total)
  -> Total`, marked `#[must_use]`), not out-parameters.
- Use checked arithmetic on values derived from input.
- Return lazy iterators. A batch lookup yields one item per input, with
  `None` for a missing key, not a shorter stream.
- Use a `for` loop when the body has several typed early exits, and an
  explicit stack instead of deep recursion (no guaranteed tail calls).
- Pass time, randomness, and the environment in, as a value or a small trait.
- Contain mutation in a builder that ends with `finish(self)` or a local
  value that a function returns. Use interior mutability only in rebuildable
  caches. Keep each `unsafe` block in a small function with a `// SAFETY:`
  comment.

## 7. Parse raw data once, at a named boundary

Convert raw data to refined types where it enters the program. The rest of
the code then takes the refined types and doesn't check them again.

- Accept raw input only through `TryFrom`, `FromStr`, or a `parse` function
  that returns the refined type or a typed error.
- Send deserialization through the same validation, with
  `#[serde(try_from = "String")]` or a hand-written `Deserialize`. A plain
  derived `Deserialize` writes the fields directly and skips the check.
- Decode each byte format in exactly one function. Check lengths (with
  checked arithmetic), magic numbers, versions, tags, UTF-8, and trailing
  bytes there, and return a view whose accessors can't fail.
- Keep each conversion that skips validation as narrow as possible: none at
  all, a typed codec (a storage key encoder and decoder that take and return
  the typed value), or a private or `pub(crate)` function. Put test-only
  constructors behind `#[cfg(test)]`. A `pub` converter that another crate
  needs is an exception: name it for its trust assumption
  (`from_key_trusted`), say in its doc comment who may call it, and get the
  user's approval.
- When a value is trustworthy only because of how it was made (a length
  counted while hashing, a receipt from a completed step), wrap it in an
  evidence type with private fields that only its producer can construct,
  and make each consumer require that type.

## 8. Give each boundary its own error enum

- Define one error enum per subsystem or boundary, not one for the whole
  crate. Give each variant typed, named fields (`expected`, `actual`, the ID,
  a byte offset). Add a variant only for a cause that a caller handles
  differently.
- Implement `Display` and `std::error::Error` (with `source()`), by hand or
  with the project's error crate, so that errors work with `?` and
  `Box<dyn Error>`.
- Keep "the backend failed" separate from "the backend answered, and the
  answer shows corrupt data". Don't report one as the other.
- Use `std::convert::Infallible` as the error of an operation that can't
  fail, and remove the impossible arm with `match never {}`.
- Never call `unwrap()` outside test code. Tests and doctests may.
- Avoid `expect()`. First make the failure impossible with a type, or return
  a typed error (`ok_or`, `let ... else`). Use `expect` only when neither
  works, with a static message that states the broken invariant:
  `expect("a header is 16 bytes")`, not `expect("failed")` or a formatted
  string. Recommend clippy's `unwrap_used` and `expect_used` lints (with
  `allow-unwrap-in-tests` and `allow-expect-in-tests` in `clippy.toml`), but
  change lint settings only if the user agrees.

Read [boundaries-and-errors.md](references/boundaries-and-errors.md) for
parsers, validated views, serde, evidence types, and error enums.

## 9. Test the type design

A type-level rule claims that some code doesn't compile. Test that claim.

- For each sealed constructor and typestate rule, write a `compile_fail`
  doctest (a separate crate that sees only your public API) with one
  forbidden thing per block, next to a block that does the legal thing. A
  `compile_fail` block passes on any error, even a typo, and stable rustdoc
  ignores error codes on it; the legal block proves the paths.
- For derive and procedural macros, use `trybuild` with committed `.stderr`
  files and at least one `pass` case: without one, trybuild runs only
  `cargo check`, which skips `const` assertions made in monomorphization.
- Assert static facts with `const _: () = assert!(..);`.
- Write table tests with one case for each variant of each enum you add, and
  property or differential tests (against a simple reference implementation)
  for folds, orderings, and encodings.

## Checklist

Before you report Rust work as done, confirm each item.

**Rules.** Each one holds unless the user approved an exception for that site
(see [Rules, guidelines, and exceptions](#rules-guidelines-and-exceptions)).

- Identities and constrained values are newtypes with private fields, not
  type aliases. No public `From<raw>`, conversion between identity types,
  public raw-to-typed converter, or `Deref<Target = raw>` on an identity
  type. No `DerefMut` on a type with an invariant.
- Types with invariants and evidence types have no public fields. Evidence
  types have no derived `Deserialize`, and other invariant types deserialize
  only through their validation (`#[serde(try_from = ..)]` or by hand).
- No `bool` mode parameters, no sentinel values for absence, no default
  variant for an unknown tag, and no `_` arm in a match on your own domain
  enum.
- Transactions and sessions end in a method that takes `self`. Trusted
  finished values come only from consuming their builder. Destructive
  operations are plan, then execute.
- No GAT method takes `&'a Self::X<'a>`.
- Each byte format has one decoder, which doesn't panic on any input.
  Arithmetic on untrusted values (lengths, counts, offsets, request fields)
  uses checked operations.
- Each boundary has its own error enum with typed fields (not a formatted
  `String` message), `Display`, and `Error`.
- No `unwrap()` outside test code. Each `expect` is unavoidable and has a
  static message that states the invariant.
- Each `unsafe` block is in a small function with a `// SAFETY:` comment.
- Each seal and each required typestate rule has a `compile_fail` doctest
  next to a legal one.
- The build, clippy, and the tests pass.

**Guidelines.** Say why in your reply when you depart from one.

- Typestate for the other in-process lifecycles.
- Implementation-chosen types in associated types, the smallest trait bound
  in generic code, and a functor instead of a copy per backend.
- GATs with only the lifetime parameters that their values use.
- Pure functions, value-to-value steps, and lazy streams. Mutation and
  interior mutability in small containers, and effects passed in.
- A test case for each new enum variant.
