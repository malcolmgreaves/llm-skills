# Generic associated types and lifetimes

Read this before you write a generic associated type (GAT), and whenever a
lifetime error appears in code that uses one.

## Contents

- [When a GAT is warranted](#when-a-gat-is-warranted)
- [Lend handles from `&self`](#lend-handles-from-self)
- [Separate the borrow lifetime from the data lifetime](#separate-the-borrow-lifetime-from-the-data-lifetime)
- [Repeat the trait's where-clauses in each impl](#repeat-the-traits-where-clauses-in-each-impl)
- [Give a GAT only the parameters it uses](#give-a-gat-only-the-parameters-it-uses)
- [Type-constructor GATs: modes](#type-constructor-gats-modes)
- [Pitfalls](#pitfalls)
- [Diagnostics](#diagnostics)

## When a GAT is warranted

Use a GAT when:

1. A trait lends a handle that borrows from `&self`: a read session, a
   transaction, a cursor, or a view. The GAT's lifetime parameter lets each
   implementation return a type that borrows from itself, and the borrow
   checker keeps each handle inside the lifetime of its source.
2. The lifetime of an output's data changes from call to call, as in
   zero-copy decoding, where the output borrows from the input buffer.
3. A signature needs a type constructor, for example an output type that is
   `T` in one mode and `()` in another.

Don't use a GAT when:

- The outputs are owned. A plain associated type is enough.
- The trait must work as `dyn Trait`. A trait with a GAT isn't
  dyn-compatible (E0038). Use generics, or an enum of the implementations.
- You want `Functor` or `Monad` traits. GATs aren't higher-kinded types, and
  such towers hit compiler limits quickly. Write a GAT for a concrete need of
  the domain.

## Lend handles from `&self`

Declare the handle as a GAT with a lifetime and the bound `where Self: 's`.
The compiler requires this bound ("missing required bound"), because the
handle borrows from `Self`.

Give the view trait its own data lifetime, and make its accessors return data
tied to that lifetime, not to the view value. A caller can then drop the view
and keep the data, for as long as the session lives.

Build an owned value from a view through the owned type's constructor, so
that the owned value's invariants and derived fields (such as an identity
hash) are computed, not copied. Don't name that method `to_owned`:
`std::borrow::ToOwned` is in the prelude, and any view that derives `Clone`
then has two `to_owned` methods.

```rust
use std::convert::Infallible;

/// A session that lends views of its nodes.
pub trait ReadSession {
    type Error: std::error::Error;
    type Node<'s>: NodeView<'s>
    where
        Self: 's;

    fn node(&self, id: usize) -> Result<Option<Self::Node<'_>>, Self::Error>;
}

/// A borrowed node. Accessors return data tied to `'a`, not to `&self`.
pub trait NodeView<'a> {
    fn name(&self) -> &'a str;
    fn size(&self) -> u64;

    /// Builds the owned node through its constructor.
    fn to_node(&self) -> Node {
        Node::new(self.name(), self.size())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Node {
    name: String,
    size: u64,
    label: String,
}

impl Node {
    pub fn new(name: &str, size: u64) -> Self {
        Node {
            name: name.to_string(),
            size,
            label: format!("{name} ({size} bytes)"),
        }
    }

    pub fn label(&self) -> &str {
        &self.label
    }
}

pub struct MemSession {
    nodes: Vec<(String, u64)>,
}

pub struct MemNode<'a> {
    name: &'a str,
    size: u64,
}

impl<'a> NodeView<'a> for MemNode<'a> {
    fn name(&self) -> &'a str {
        self.name
    }

    fn size(&self) -> u64 {
        self.size
    }
}

impl ReadSession for MemSession {
    type Error = Infallible;
    type Node<'s> = MemNode<'s>;

    fn node(&self, id: usize) -> Result<Option<MemNode<'_>>, Infallible> {
        Ok(self.nodes.get(id).map(|(name, size)| MemNode {
            name: name.as_str(),
            size: *size,
        }))
    }
}

/// The returned name outlives each view, and lives as long as the session.
pub fn largest<'s, S: ReadSession>(
    session: &'s S,
    ids: &[usize],
) -> Result<Option<&'s str>, S::Error> {
    let views = ids
        .iter()
        .map(|id| session.node(*id))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(views
        .into_iter()
        .flatten()
        .max_by_key(|view| view.size())
        .map(|view| view.name()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn views_lend_names_and_build_owned_nodes() {
        let session = MemSession {
            nodes: vec![("a".into(), 3), ("b".into(), 9)],
        };
        assert_eq!(largest(&session, &[0, 1, 7]), Ok(Some("b")));
        let Ok(Some(view)) = session.node(0) else {
            panic!("node 0 exists");
        };
        assert_eq!(view.to_node().label(), "a (3 bytes)");
    }
}
```

## Separate the borrow lifetime from the data lifetime

When a trait method borrows a value whose type has a lifetime parameter, it
involves two lifetimes: `'data`, how long the underlying data lives, and
`'borrow`, how long this call borrows the value. If one lifetime names both,
as in `&'a Self::Storage<'a>`, the output lives only as long as the borrow.
A caller that borrows a local storage value then can't return the output
(E0515). In generic code, where `A::Storage<'a>` stays a projection, the
projection is invariant in `'a`, so the compiler can't shorten the data
lifetime to fit the borrow; the borrow must last as long as the data, and a
local storage value doesn't live long enough (E0597):

```rust
// Does not compile: one lifetime for the borrow and the data (E0515).
pub trait Accessor {
    type Storage<'data>;
    type Output<'data>;

    fn get<'a>(storage: &'a Self::Storage<'a>, index: usize) -> Self::Output<'a>;
}

pub struct Text;

impl Accessor for Text {
    type Storage<'data> = Vec<&'data str>;
    type Output<'data> = &'data str;

    fn get<'a>(storage: &'a Self::Storage<'a>, index: usize) -> Self::Output<'a> {
        storage[index]
    }
}

/// The output borrows from the local `storage`, not from `data`.
pub fn first(data: &[String]) -> &str {
    let storage: Vec<&str> = data.iter().map(String::as_str).collect();
    Text::get(&storage, 0)
}
```

Give the borrow its own lifetime, bounded by the data lifetime, and keep it
out of the return type:

```rust
pub trait Accessor {
    type Storage<'data>;
    type Output<'data>;

    fn get<'borrow, 'data>(
        storage: &'borrow Self::Storage<'data>,
        index: usize,
    ) -> Self::Output<'data>
    where
        'data: 'borrow;
}

pub struct Text;

impl Accessor for Text {
    type Storage<'data> = Vec<&'data str>;
    type Output<'data> = &'data str;

    fn get<'borrow, 'data>(
        storage: &'borrow Self::Storage<'data>,
        index: usize,
    ) -> Self::Output<'data>
    where
        'data: 'borrow,
    {
        storage[index]
    }
}

/// The output borrows from `data`, so it outlives the local `storage`.
pub fn first(data: &[String]) -> &str {
    let storage: Vec<&str> = data.iter().map(String::as_str).collect();
    Text::get(&storage, 0)
}
```

Apply the split to every method of the trait family, not only to the one
where the error appeared. A fix in one method moves the error to the next
caller.

When the storage can be a `Copy` view (a slice, a pair of references), a
simpler design removes `'borrow` entirely: declare `type Storage<'data>:
Copy;` and pass the storage by value. A function that takes the view by value
can't tie its output to a borrow of the view.

## Repeat the trait's where-clauses in each impl

An impl method must declare the same lifetime bounds as the trait method. If
the impl leaves out `where 'data: 'borrow`, the compiler reports E0195
("lifetime parameters do not match the trait definition"), because the bound
makes `'borrow` early-bound in the trait and late-bound in the impl.
Copy the trait method's signature, including its where-clause, into the impl.
Writing the signature with the trait's projections (`Self::Storage<'data>`)
instead of the concrete types keeps the impl readable when the concrete types
are long.

```rust
// Does not compile: the impl omits the trait's where-clause (E0195).
pub trait Accessor {
    type Storage<'data>;

    fn get<'borrow, 'data>(storage: &'borrow Self::Storage<'data>) -> usize
    where
        'data: 'borrow;
}

pub struct Text;

impl Accessor for Text {
    type Storage<'data> = Vec<&'data str>;

    fn get<'borrow, 'data>(storage: &'borrow Self::Storage<'data>) -> usize {
        storage.len()
    }
}
```

## Give a GAT only the parameters it uses

Declare on each GAT only the lifetimes that its values can depend on. If
storage must never hold a borrow of the table that owns it, declare
`type Storage<'data>`, not `type Storage<'borrow, 'data>`. With the second
form, an impl can capture a short borrow, and only a comment can forbid it.
With the first, the wrong impl doesn't compile.

Keep the type that describes the domain (a schema, a record type) owned and
`'static`, and put lifetimes only on the view types derived from it.

## Type-constructor GATs: modes

A GAT with a type parameter lets one function run in several modes. In the
example, `Check` validates input and builds nothing, and `Emit` builds the
value. Each mode is a unit struct that implements the signature, and the
function is written once.

```rust
/// A signature for how much work a parser does.
pub trait Mode {
    type Output<T>;

    fn produce<T>(make: impl FnOnce() -> T) -> Self::Output<T>;

    fn combine<A, B, C>(
        a: Self::Output<A>,
        b: Self::Output<B>,
        join: impl FnOnce(A, B) -> C,
    ) -> Self::Output<C>;
}

/// Validates only: allocates nothing.
pub struct Check;

/// Builds the parsed value.
pub struct Emit;

impl Mode for Check {
    type Output<T> = ();

    fn produce<T>(_make: impl FnOnce() -> T) -> Self::Output<T> {}

    fn combine<A, B, C>(
        _a: Self::Output<A>,
        _b: Self::Output<B>,
        _join: impl FnOnce(A, B) -> C,
    ) -> Self::Output<C> {
    }
}

impl Mode for Emit {
    type Output<T> = T;

    fn produce<T>(make: impl FnOnce() -> T) -> T {
        make()
    }

    fn combine<A, B, C>(a: A, b: B, join: impl FnOnce(A, B) -> C) -> C {
        join(a, b)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PairError {
    MissingEquals,
    EmptyKey,
}

/// Parses `key=value`. The checks are the same in every mode.
pub fn parse_pair<M: Mode>(input: &str) -> Result<M::Output<(String, String)>, PairError> {
    let (key, value) = input.split_once('=').ok_or(PairError::MissingEquals)?;
    if key.is_empty() {
        return Err(PairError::EmptyKey);
    }
    let key = M::produce(|| key.to_string());
    let value = M::produce(|| value.to_string());
    Ok(M::combine(key, value, |k, v| (k, v)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn modes_share_the_checks() {
        assert_eq!(parse_pair::<Check>("a=b"), Ok(()));
        assert_eq!(
            parse_pair::<Emit>("a=b"),
            Ok(("a".to_string(), "b".to_string()))
        );
        assert_eq!(parse_pair::<Check>("=b"), Err(PairError::EmptyKey));
        assert_eq!(parse_pair::<Emit>("ab"), Err(PairError::MissingEquals));
    }
}
```

## Pitfalls

- **A higher-ranked bound on a GAT implies `'static`.** A bound such as
  `for<'a> I::Item<'a>: Debug` currently requires `I: 'static`, so a caller
  that passes a borrowing implementation fails with E0521 ("borrowed data
  escapes outside of function"). Avoid higher-ranked bounds over GAT
  projections: bound the concrete use instead, or restructure so that the
  generic function doesn't need the bound for every lifetime.
- **`derive` adds bounds on type parameters, not on fields.**
  `#[derive(Clone, Copy)]` on `struct View<'d, A: Accessor>` requires
  `A: Clone + Copy`, even when `A` is a marker and only
  `A::Storage<'d>` is stored. Write the impls by hand, with the bound on the
  projection: `impl<'d, A: Accessor> Clone for View<'d, A> where
  A::Storage<'d>: Copy`. The same applies to `Debug` on an error type whose
  fields are associated-type projections such as `S::Error`.
- **A method named `to_owned` on a view** conflicts with
  `std::borrow::ToOwned::to_owned` when the view is `Clone`. Use a
  domain name, such as `to_node`.
- **A trait with a GAT isn't dyn-compatible.** Decide early whether the
  trait needs `dyn`. If it does, move the lending method to a separate trait
  or return owned values.
- **The workaround for higher-ranked bounds is costly.** Moving the
  associated type into a helper trait with a lifetime parameter
  (`trait Lend<'a> { type Item; }` with `for<'a> T: Lend<'a>`) avoids the
  `'static` requirement, but it adds boilerplate and is still not
  dyn-compatible. Use it only when the design needs the bound.
- **Some constraints can't be stated in types.** For example, a database may
  allow only one read transaction per thread. Enforce such a rule where the
  handle is created (for example, a debug-build check with a thread-local
  flag), and state it in the handle's doc comment.

## Diagnostics

| Error | Likely cause | Fix |
| --- | --- | --- |
| E0597 or E0515 in a caller of a GAT method | One lifetime for the borrow and the data | Split `'borrow` from `'data` in every method of the trait family |
| E0195 | The impl method omits the trait method's where-clause | Copy the trait signature, including its where-clause |
| "missing required bound on `X`" | A lending GAT without `where Self: 'a` | Add the bound that the compiler names |
| E0521 with a `for<'a>` bound on a GAT | The higher-ranked bound implies `'static` | Remove or narrow the bound |
| E0038 | A trait with a GAT used as `dyn Trait` | Use generics or an enum, or split the trait |
