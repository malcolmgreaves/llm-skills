# Traits as ML-style modules

Read this when you design a trait, a backend abstraction, a blanket impl, a
sealed trait, or a macro that generates impls.

## Contents

- [The correspondence](#the-correspondence)
- [Associated type or type parameter](#associated-type-or-type-parameter)
- [Signatures, functors, and platforms](#signatures-functors-and-platforms)
- [Several structures for one signature](#several-structures-for-one-signature)
- [Linked traits and sharing constraints](#linked-traits-and-sharing-constraints)
- [Static facts and functors over type constructors](#static-facts-and-functors-over-type-constructors)
- [Sealed traits](#sealed-traits)
- [Abstract return types](#abstract-return-types)
- [Static or dynamic dispatch](#static-or-dynamic-dispatch)
- [When not to write a trait](#when-not-to-write-a-trait)
- [Macros that generate impls](#macros-that-generate-impls)

## The correspondence

In ML, a signature lists abstract types and the operations over them; a
structure implements a signature; a functor builds a structure from other
structures. Client code depends on the signature only, so the compiler checks
each structure against it and each client can use any structure.

| ML | Rust |
| --- | --- |
| Signature | Trait |
| Abstract type | Associated type, including a generic associated type |
| Value in a signature | Associated function or associated const |
| Structure | A type with an impl of the trait. A unit struct when the structure has no data. |
| Functor | A generic struct `F<M: Sig>`, or a blanket impl `impl<T: A> B for T` |
| Sharing constraint (`with type t = u`) | Associated type equality (`M: Sig<Error = E>`) |
| Signature inclusion | Supertrait (`trait Store: Reader + Writer`) |

Design a subsystem as signatures first: name the abstract types, then the
operations. Write each implementation as a structure, and write the code that
combines implementations as functors.

## Associated type or type parameter

- Use an **associated type** when the implementation decides the type: its
  error, session, transaction, view, key, digest, or companion builder. The
  caller never writes it, and generic code reaches it as `S::Error`.
- Use a **type parameter** when one type has several impls of the trait, one
  per parameter: `From<T>`, `Add<Rhs>`, `Encode<Format>`.
- Default to an associated `type Error`. A trait with an `Error` parameter
  lets one type implement it once per error type, which is almost never what
  the design means.

## Signatures, functors, and platforms

- Split a subsystem into a read signature and a write signature, each with
  its own `Error`. Name the combination with a trait that has a blanket impl
  and equates the two errors. Generic code asks for the smallest signature it
  uses, so a read-only function accepts a read-only implementation.
- Put what a backend must do in a small signature, and build the full
  behavior as a functor over it. Each new backend then implements only the
  small signature and gets the full behavior.
- When a layer needs a coherent choice of several implementations, group the
  choices in one trait that has only associated types (a platform). The
  layer then takes one parameter, and a test uses one unit struct to pick
  every double.

```rust
use std::collections::HashMap;
use std::fmt;

/// The read signature.
pub trait Reader {
    type Error: std::error::Error;
    fn get(&self, key: u64) -> Result<Option<Vec<u8>>, Self::Error>;
}

/// The write signature.
pub trait Writer {
    type Error: std::error::Error;
    fn put(&mut self, key: u64, value: Vec<u8>) -> Result<(), Self::Error>;
}

/// Both halves, with one error type.
pub trait Store: Reader + Writer<Error = <Self as Reader>::Error> {}

impl<T: Reader + Writer<Error = <T as Reader>::Error>> Store for T {}

/// The small signature that a raw backend implements.
pub trait Blob {
    fn read(&self, key: u64) -> Option<&[u8]>;
    fn write(&mut self, key: u64, value: Vec<u8>);
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TooLarge {
    pub size: usize,
    pub cap: usize,
}

impl fmt::Display for TooLarge {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} bytes exceeds the cap of {}", self.size, self.cap)
    }
}

impl std::error::Error for TooLarge {}

/// A functor: from any `Blob`, a `Store` that refuses values over a cap.
pub struct Capped<B> {
    backend: B,
    cap: usize,
}

impl<B: Blob> Capped<B> {
    pub fn new(backend: B, cap: usize) -> Self {
        Capped { backend, cap }
    }
}

impl<B: Blob> Reader for Capped<B> {
    type Error = TooLarge;

    fn get(&self, key: u64) -> Result<Option<Vec<u8>>, TooLarge> {
        Ok(self.backend.read(key).map(<[u8]>::to_vec))
    }
}

impl<B: Blob> Writer for Capped<B> {
    type Error = TooLarge;

    fn put(&mut self, key: u64, value: Vec<u8>) -> Result<(), TooLarge> {
        if value.len() > self.cap {
            return Err(TooLarge {
                size: value.len(),
                cap: self.cap,
            });
        }
        self.backend.write(key, value);
        Ok(())
    }
}

/// One structure of the small signature.
#[derive(Default)]
pub struct MemBlob(HashMap<u64, Vec<u8>>);

impl Blob for MemBlob {
    fn read(&self, key: u64) -> Option<&[u8]> {
        self.0.get(&key).map(Vec::as_slice)
    }

    fn write(&mut self, key: u64, value: Vec<u8>) {
        self.0.insert(key, value);
    }
}

/// Splits bytes into chunks.
pub trait Chunker {
    fn chunks<'a>(&self, bytes: &'a [u8]) -> Vec<&'a [u8]>;
}

pub struct FixedChunker(pub usize);

impl Chunker for FixedChunker {
    fn chunks<'a>(&self, bytes: &'a [u8]) -> Vec<&'a [u8]> {
        bytes.chunks(self.0).collect()
    }
}

/// A platform: one parameter that fixes every module choice of a layer.
pub trait Platform {
    type Store: Store;
    type Chunker: Chunker;
}

pub struct Repo<P: Platform> {
    store: P::Store,
    chunker: P::Chunker,
    next_key: u64,
}

impl<P: Platform> Repo<P> {
    pub fn new(store: P::Store, chunker: P::Chunker) -> Self {
        Repo {
            store,
            chunker,
            next_key: 0,
        }
    }

    /// Stores each chunk of `bytes`, and returns their keys.
    pub fn add(&mut self, bytes: &[u8]) -> Result<Vec<u64>, <P::Store as Reader>::Error> {
        let mut keys = Vec::new();
        for chunk in self.chunker.chunks(bytes) {
            self.store.put(self.next_key, chunk.to_vec())?;
            keys.push(self.next_key);
            self.next_key += 1;
        }
        Ok(keys)
    }

    pub fn store(&self) -> &P::Store {
        &self.store
    }
}

/// Generic code asks for only the signature it uses.
pub fn total_len<R: Reader>(store: &R, keys: &[u64]) -> Result<usize, R::Error> {
    keys.iter().try_fold(0, |total, key| {
        Ok(total + store.get(*key)?.map_or(0, |value| value.len()))
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestPlatform;

    impl Platform for TestPlatform {
        type Store = Capped<MemBlob>;
        type Chunker = FixedChunker;
    }

    #[test]
    fn stores_chunks_through_the_platform() {
        let store = Capped::new(MemBlob::default(), 4);
        let mut repo: Repo<TestPlatform> = Repo::new(store, FixedChunker(4));
        let keys = repo.add(b"abcdefghij").unwrap();
        assert_eq!(keys, [0, 1, 2]);
        assert_eq!(total_len(repo.store(), &keys), Ok(10));
    }
}
```

## Several structures for one signature

ML allows many structures for one signature, such as two orderings of the
same element type. Rust allows one impl of a trait per type (coherence), so
`String` can't implement one `Order` trait twice. Make each structure a unit
struct instead, give the trait associated functions without `self`, and pass
the structure as a type parameter. The functor below works like OCaml's
`Set.Make`.

```rust
use std::cmp::Ordering;
use std::marker::PhantomData;

/// A signature: an element type and a total order on it.
pub trait Order {
    type Item;
    fn compare(a: &Self::Item, b: &Self::Item) -> Ordering;
}

/// Two structures for the same element type.
pub struct Lexical;
pub struct ByLength;

impl Order for Lexical {
    type Item = String;

    fn compare(a: &String, b: &String) -> Ordering {
        a.cmp(b)
    }
}

impl Order for ByLength {
    type Item = String;

    fn compare(a: &String, b: &String) -> Ordering {
        a.len().cmp(&b.len()).then_with(|| a.cmp(b))
    }
}

/// A functor: a sorted collection for any `Order`.
pub struct Sorted<O: Order> {
    items: Vec<O::Item>,
    order: PhantomData<O>,
}

impl<O: Order> Default for Sorted<O> {
    fn default() -> Self {
        Sorted {
            items: Vec::new(),
            order: PhantomData,
        }
    }
}

impl<O: Order> Sorted<O> {
    pub fn insert(&mut self, item: O::Item) {
        let (Ok(at) | Err(at)) = self.items.binary_search_by(|x| O::compare(x, &item));
        self.items.insert(at, item);
    }

    pub fn iter(&self) -> impl Iterator<Item = &O::Item> {
        self.items.iter()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn each_structure_orders_differently() {
        let words = ["ccc", "b", "aa"].map(String::from);
        let mut lexical = Sorted::<Lexical>::default();
        let mut by_length = Sorted::<ByLength>::default();
        for word in words {
            lexical.insert(word.clone());
            by_length.insert(word);
        }
        assert!(lexical.iter().eq(["aa", "b", "ccc"].iter()));
        assert!(by_length.iter().eq(["b", "aa", "ccc"].iter()));
    }
}
```

## Linked traits and sharing constraints

When several traits describe parts of one concept (a schema, its table view,
its row view), make each trait name the others through associated types, and
state the equations between them in the trait declarations. Generic code can
then move from any part to the others and rely on them agreeing. An impl that
breaks an equation fails to compile.

State each equation that generic code needs, even when every current impl
already satisfies it. Generic code can use only the equations that the traits
state, not the ones that happen to hold.

```rust
/// A record type whose rows are stored as a table.
pub trait Schema: Sized + 'static {
    type Table<'d>: Table<'d, Schema = Self>;

    fn table(rows: &[u64]) -> Self::Table<'_>;
}

/// A table view over borrowed rows.
pub trait Table<'d>: Sized {
    type Schema: Schema<Table<'d> = Self>;

    fn len(&self) -> usize;

    fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

pub struct Person;

pub struct PersonTable<'d>(&'d [u64]);

impl Schema for Person {
    type Table<'d> = PersonTable<'d>;

    fn table(rows: &[u64]) -> PersonTable<'_> {
        PersonTable(rows)
    }
}

impl<'d> Table<'d> for PersonTable<'d> {
    type Schema = Person;

    fn len(&self) -> usize {
        self.0.len()
    }
}

/// Moves from the schema to its table with no extra bounds.
pub fn row_count<S: Schema>(rows: &[u64]) -> usize {
    S::table(rows).len()
}
```

## Static facts and functors over type constructors

A fact that depends only on a type (its wire type, its width, whether it can
be null) belongs to the type, as an associated const or an associated
function without `self`. Compute the facts of a container type from the
facts of its element type with a blanket impl. These impls are functors over
type constructors: `Option<T>` and `Vec<T>` each get their facts from `T`.

A `const` inside a generic impl can enforce a domain rule at compile time.
Rust evaluates such a `const` only when it compiles the generic code for a
concrete type, and `cargo check` doesn't do that step. The rule then fails
only in `cargo build` and `cargo test`.

```rust
use std::marker::PhantomData;

/// The static facts of a field type.
pub trait Field {
    const NULLABLE: bool = false;

    fn type_name() -> String;
}

impl Field for u64 {
    fn type_name() -> String {
        "UInt64".to_string()
    }
}

impl Field for String {
    fn type_name() -> String {
        "Utf8".to_string()
    }
}

impl<T: Field> Field for Option<T> {
    const NULLABLE: bool = true;

    fn type_name() -> String {
        T::type_name()
    }
}

impl<T: Field> Field for Vec<T> {
    fn type_name() -> String {
        let null = if T::NULLABLE { "?" } else { "" };
        format!("List<{}{null}>", T::type_name())
    }
}

/// A map from keys to values. A key can't be null.
pub struct Map<K, V>(PhantomData<(K, V)>);

struct NonNullKey<K>(PhantomData<K>);

impl<K: Field> NonNullKey<K> {
    const CHECK: () = assert!(!K::NULLABLE, "a map key can't be nullable");
}

impl<K: Field, V: Field> Field for Map<K, V> {
    fn type_name() -> String {
        let () = NonNullKey::<K>::CHECK;
        format!("Map<{}, {}>", K::type_name(), V::type_name())
    }
}

const _: () = assert!(<Option<u64> as Field>::NULLABLE);
const _: () = assert!(!<Vec<Option<u64>> as Field>::NULLABLE);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn container_facts_come_from_elements() {
        assert_eq!(<Vec<Option<u64>>>::type_name(), "List<UInt64?>");
        assert_eq!(
            <Map<String, Vec<u64>>>::type_name(),
            "Map<Utf8, List<UInt64>>"
        );
    }
}
```

## Sealed traits

Seal a trait when its set of implementors is part of the design: the stages
of a typestate, a closed set of units, the kinds of a node. Make it a public
trait with a supertrait that lives in a private module. Other crates can name
and use the trait, but they can't implement the supertrait, so they can't
add an implementor. You can then add methods to the trait without a breaking
change, because no outside impl exists.

Leave a trait open when other crates must implement it, such as a storage
backend. Don't add a blanket impl of the private supertrait
(`impl<T> Sealed for T`), because it opens the seal again.

```rust
use std::marker::PhantomData;

mod sealed {
    pub trait Sealed {}
}

/// A unit of time. The set of units is closed.
///
/// ```compile_fail
/// struct Minutes;
/// impl my_crate::Unit for Minutes {
///     const SUFFIX: &'static str = "min";
/// }
/// ```
///
/// ```
/// use my_crate::{Seconds, Span};
/// assert_eq!(Span::<Seconds>::new(2).render(), "2s");
/// ```
pub trait Unit: sealed::Sealed {
    const SUFFIX: &'static str;
}

// `derive` on `Span<U>` requires the same traits of `U`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Seconds;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Millis;

impl sealed::Sealed for Seconds {}
impl sealed::Sealed for Millis {}

impl Unit for Seconds {
    const SUFFIX: &'static str = "s";
}

impl Unit for Millis {
    const SUFFIX: &'static str = "ms";
}

/// The unit is part of the type, so seconds can't be added to milliseconds.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Span<U: Unit> {
    count: u64,
    unit: PhantomData<U>,
}

impl<U: Unit> Span<U> {
    pub fn new(count: u64) -> Self {
        Span {
            count,
            unit: PhantomData,
        }
    }

    pub fn checked_add(self, other: Self) -> Option<Self> {
        self.count.checked_add(other.count).map(Self::new)
    }

    pub fn render(self) -> String {
        format!("{}{}", self.count, U::SUFFIX)
    }
}

impl Span<Seconds> {
    pub fn to_millis(self) -> Option<Span<Millis>> {
        self.count.checked_mul(1000).map(Span::new)
    }
}
```

## Abstract return types

Return-position `impl Trait` is an abstract type: the caller can use only the
trait's operations, and you can change the concrete type later without
breaking the caller. Return `impl Iterator<Item = T>` instead of a named
iterator struct or a `Vec` when the caller only iterates. Every return path
must produce the same concrete type; when paths differ, return an enum that
implements the trait, or `Box<dyn Trait>`.

## Static or dynamic dispatch

- Use generics (static dispatch) in the core. The compiler checks each use
  against the concrete type and can inline across the call.
- Use `dyn Trait` at cold boundaries where the set of implementations is open
  or a collection holds different types, such as a plugin registry. A trait
  with a generic method or a GAT isn't dyn-compatible.
- Each distinct type argument compiles the generic code again, which costs
  compile time and binary size. When a generic function only converts its
  argument (`impl AsRef<Path>`), convert it and call a private non-generic
  inner function that holds the body.

## When not to write a trait

- One algorithm with one implementation is a function. Write algorithms as
  free generic functions over existing traits.
- A second implementation is a reason for a trait. A test double counts as
  one, for example a wrapper that counts reads so a test can assert a
  complexity bound.
- A family of types that share a representation but must not share
  constructors (identities built from different inputs) doesn't need a
  shared trait. A trait would force one constructor surface on every member.
  Generate each capability with a small macro, as the next section shows.

When two traits in scope, or a trait and an inherent method, have a method
with the same name, call it with a fully qualified path
(`<T as Field>::type_name()`). Method-call syntax picks one by its own rules,
and a wrong pick can compile, for example as infinite recursion.

## Macros that generate impls

- Use a blanket impl, not a macro, when the impl follows from a trait bound.
- For a family of mechanical impls, write one small `macro_rules!` per
  capability, and invoke on each type only the capabilities that its meaning
  allows. A list of one-line invocations then reads as a table of which type
  has which capability, and a change to one capability changes one macro.

```rust
macro_rules! hash_from_bytes {
    () => {
        pub fn new(bytes: &[u8]) -> Self {
            Self(
                bytes
                    .iter()
                    .fold(0u64, |h, b| h.rotate_left(5) ^ u64::from(*b)),
            )
        }
    };
}

macro_rules! little_endian_bytes {
    () => {
        pub fn to_le_bytes(self) -> [u8; 8] {
            self.0.to_le_bytes()
        }
    };
}

macro_rules! from_storage_key {
    () => {
        /// For the storage layer only: the key was written from a valid value.
        pub(crate) fn from_storage_key(key: u64) -> Self {
            Self(key)
        }
    };
}

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct ChunkId(u64);

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct SignatureId(u64);

impl ChunkId {
    hash_from_bytes!();
    little_endian_bytes!();
    from_storage_key!();
}

// A signature is never a storage key, so it has no `from_storage_key`.
impl SignatureId {
    hash_from_bytes!();
    little_endian_bytes!();
}

/// The storage layer keeps raw keys, and only it turns them back into IDs.
#[derive(Default)]
pub struct ChunkIndex {
    keys: Vec<u64>,
}

impl ChunkIndex {
    pub fn insert(&mut self, id: ChunkId) {
        self.keys.push(u64::from_le_bytes(id.to_le_bytes()));
    }

    pub fn ids(&self) -> impl Iterator<Item = ChunkId> {
        self.keys.iter().copied().map(ChunkId::from_storage_key)
    }
}
```

For derive and procedural macros:

- Don't decide a property of a type from its written syntax, such as "the
  last path segment is `Option`". A type alias or a re-export defeats the
  check. Emit code that asks the trait (`<#ty as Field>::NULLABLE`) and let
  the compiler resolve it.
- Refuse unsupported input (a tuple struct, a generic parameter) at the start,
  with a `syn::Error` on the offending span whose message shows the supported
  form.
- In generated code, use absolute paths (`::core::option::Option`,
  `::my_crate::Field`) and fully qualified trait calls, so that names in the
  user's scope can't change what the code means.
- Give generated types the visibility of the input type. A public item that
  mentions a less visible type gets a `private_interfaces` warning (error
  E0446 in an associated type of a trait impl), and other crates can't use
  it.
