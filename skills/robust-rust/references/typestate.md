# Typestate and state machines

Read this when you model a lifecycle, builder, transaction, session,
two-phase operation, or persisted state machine. In the doctests, `my_crate`
stands for the name of your crate.

## Contents

- [Choose the encoding](#choose-the-encoding)
- [One type per stage](#one-type-per-stage)
- [A marker type parameter](#a-marker-type-parameter)
- [Store a typestate value in an enum](#store-a-typestate-value-in-an-enum)
- [Transactions and sessions](#transactions-and-sessions)
- [Plan, then execute](#plan-then-execute)
- [Persisted state machines](#persisted-state-machines)
- [Costs](#costs)
- [Tests](#tests)

## Choose the encoding

Typestate is a rule in three cases, and breaking it needs the user's
explicit approval for the one site:

- A transaction or session ends in a method that takes `self`, and drop is
  its abort path.
- A finished value that other code trusts is made only by a method that
  consumes its builder or producer.
- A destructive operation is `plan`, then `execute(plan)`.

For every other in-process lifecycle, typestate is a strong guideline. If you
choose a runtime check or an enum instead, say why, citing a row of this
table or one of the [costs](#costs).

| Situation | Encoding |
| --- | --- |
| One owner drives a value through its stages in straight-line code, and a call in the wrong stage is a bug. | Typestate. Use one type per stage when the stages hold different data. Use `T<S>` with a sealed marker `S` when the stages share their data and most of their methods. |
| Two stages: "building" and "done". | Two types and one `seal(self)` or `finish(self)`. This is the smallest useful typestate. |
| A destructive operation, such as garbage collection or a migration. | `plan` returns a plan with private fields, and `execute` consumes it. |
| The state is read from disk or the network, must survive a crash, or lives in a collection or a long-lived struct field. | An enum, with one transition function that refuses illegal transitions. |
| Both: typestate in the code that drives the value, and storage in between. | Typestate values wrapped in an enum at the point of storage. |
| A state has many outgoing transitions that depend on runtime data. | An enum with exhaustive matches. |
| Only one order of calls makes sense, and a different API would remove the order. | Change the API. For example, one function that takes all the inputs replaces `set_a`, `set_b`, `run`. |

A missing step that is an inconvenience, not a bug, doesn't need typestate.
A plain `&mut self` builder is the idiomatic choice for configuration with
defaults.

## One type per stage

Each stage is a struct. A transition takes `self` and returns the next stage,
so the old stage can't be used after it. A method exists only on the stage
where it is valid, so a call in the wrong stage fails to compile, and no
method needs a runtime check or a `NotReady` error.

When a transition can fail, and the caller can retry, return the old stage
inside the error. Otherwise, a failed attempt destroys the value.

```rust
use std::fmt;

/// A connection that hasn't logged in. It can only log in.
///
/// ```compile_fail
/// let mut conn = my_crate::connect("db");
/// conn.send("SELECT 1");
/// ```
///
/// ```
/// let conn = my_crate::connect("db");
/// let Ok(mut conn) = conn.log_in("open sesame") else {
///     panic!("the secret is correct");
/// };
/// conn.send("SELECT 1");
/// assert_eq!(conn.close(), 1);
/// ```
#[derive(Debug)]
pub struct LoggedOut {
    peer: String,
}

/// A connection that has logged in. Only this type can send.
#[derive(Debug)]
pub struct LoggedIn {
    peer: String,
    sent: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LogInError {
    EmptySecret,
    Rejected { peer: String },
}

impl fmt::Display for LogInError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptySecret => write!(f, "the secret is empty"),
            Self::Rejected { peer } => write!(f, "{peer} rejected the secret"),
        }
    }
}

impl std::error::Error for LogInError {}

/// A failed log-in gives the connection back, so that the caller can retry.
#[derive(Debug)]
pub struct Refused {
    pub connection: LoggedOut,
    pub error: LogInError,
}

pub fn connect(peer: &str) -> LoggedOut {
    LoggedOut {
        peer: peer.to_string(),
    }
}

impl LoggedOut {
    pub fn log_in(self, secret: &str) -> Result<LoggedIn, Refused> {
        let error = if secret.is_empty() {
            LogInError::EmptySecret
        } else if secret != "open sesame" {
            LogInError::Rejected {
                peer: self.peer.clone(),
            }
        } else {
            return Ok(LoggedIn {
                peer: self.peer,
                sent: Vec::new(),
            });
        };
        Err(Refused {
            connection: self,
            error,
        })
    }
}

impl LoggedIn {
    pub fn peer(&self) -> &str {
        &self.peer
    }

    pub fn send(&mut self, request: &str) {
        self.sent.push(request.to_string());
    }

    /// Ends the connection and returns the number of requests it sent.
    pub fn close(self) -> usize {
        self.sent.len()
    }
}
```

## A marker type parameter

When the stages share their data and most of their methods, give one struct
a type parameter that names the stage. The stage types are empty structs, and
`PhantomData<S>` holds the parameter at no runtime cost. Put the shared
methods in `impl<S: DoorState> Door<S>` and each stage's methods in its own
impl block.

Seal the marker trait: make it a public trait with a supertrait in a private
module. Other crates can then name the trait but can't add a stage.

```rust
use std::marker::PhantomData;

mod sealed {
    pub trait Sealed {}
}

/// The stages of a door. Other crates can't add a stage.
pub trait DoorState: sealed::Sealed {}

pub struct Open;
pub struct Closed;

impl sealed::Sealed for Open {}
impl sealed::Sealed for Closed {}
impl DoorState for Open {}
impl DoorState for Closed {}

/// ```compile_fail
/// let door = my_crate::Door::new("front");
/// door.walk_through();
/// ```
///
/// ```
/// let door = my_crate::Door::new("front").open();
/// assert_eq!(door.walk_through(), "front");
/// ```
pub struct Door<S: DoorState> {
    name: String,
    state: PhantomData<S>,
}

impl<S: DoorState> Door<S> {
    /// Valid in every stage.
    pub fn name(&self) -> &str {
        &self.name
    }
}

impl Door<Closed> {
    pub fn new(name: &str) -> Self {
        Door {
            name: name.to_string(),
            state: PhantomData,
        }
    }

    pub fn open(self) -> Door<Open> {
        Door {
            name: self.name,
            state: PhantomData,
        }
    }
}

impl Door<Open> {
    pub fn walk_through(&self) -> &str {
        &self.name
    }

    pub fn close(self) -> Door<Closed> {
        Door {
            name: self.name,
            state: PhantomData,
        }
    }
}

/// A door whose stage is known only at run time, for example in a `Vec`.
pub enum AnyDoor {
    Open(Door<Open>),
    Closed(Door<Closed>),
}

impl AnyDoor {
    pub fn name(&self) -> &str {
        match self {
            Self::Open(door) => door.name(),
            Self::Closed(door) => door.name(),
        }
    }
}
```

## Store a typestate value in an enum

A struct field or a collection element has one type, so it can't hold "a
door in some stage" as `Door<S>`. Wrap the stages in an enum, as `AnyDoor`
does above, and match once where you take the value out. The match gives
back the typed stage, and the code after it uses the compile-time rules
again. Don't add a runtime `state` field next to the typestate. The type
already is the state, and a second copy can disagree with it.

## Transactions and sessions

A transaction is two-state typestate: open, then committed or dropped. This
form is a rule, not a guideline.

- Give it one terminal method that takes `self`: `commit(self)`. After the
  call, the transaction value doesn't exist, so nothing can write to it.
- Make drop the abort path. Stage the writes inside the value, so that
  dropping it discards them. Test that a dropped transaction leaves no trace.
- To run caller code inside a transaction, lend the transaction as `&mut`.
  The caller can then write, but can't commit or abort, because both take
  `self`. Commit on `Ok` and drop on `Err`.
- Return from the terminal method what the caller must learn, such as the
  count of writes or the new root hash.

```rust
#[derive(Default)]
pub struct Store {
    rows: Vec<(u64, String)>,
}

/// An open write transaction. Dropping it discards its writes.
///
/// ```compile_fail
/// let mut store = my_crate::Store::default();
/// let _: Result<(), ()> = store.write(|txn| {
///     txn.commit();
///     Ok(())
/// });
/// ```
///
/// ```
/// let mut store = my_crate::Store::default();
/// let mut txn = store.begin();
/// txn.put(1, "one");
/// assert_eq!(txn.commit(), 1);
/// assert_eq!(store.len(), 1);
/// ```
pub struct Txn<'s> {
    store: &'s mut Store,
    staged: Vec<(u64, String)>,
}

impl Store {
    pub fn begin(&mut self) -> Txn<'_> {
        Txn {
            store: self,
            staged: Vec::new(),
        }
    }

    /// Runs `work` in a transaction, and commits only if it returns `Ok`.
    /// `work` gets `&mut Txn`, so it can't commit or abort on its own.
    pub fn write<T, E>(&mut self, work: impl FnOnce(&mut Txn<'_>) -> Result<T, E>) -> Result<T, E> {
        let mut txn = self.begin();
        let value = work(&mut txn)?;
        txn.commit();
        Ok(value)
    }

    pub fn len(&self) -> usize {
        self.rows.len()
    }

    pub fn is_empty(&self) -> bool {
        self.rows.is_empty()
    }
}

impl Txn<'_> {
    pub fn put(&mut self, key: u64, value: &str) {
        self.staged.push((key, value.to_string()));
    }

    /// Applies the staged writes and returns their count.
    pub fn commit(self) -> usize {
        let count = self.staged.len();
        self.store.rows.extend(self.staged);
        count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dropped_transaction_leaves_no_trace() {
        let mut store = Store::default();
        let mut txn = store.begin();
        txn.put(1, "one");
        drop(txn);
        assert!(store.is_empty());
    }

    #[test]
    fn failed_work_is_not_committed() {
        let mut store = Store::default();
        let result: Result<(), &str> = store.write(|txn| {
            txn.put(1, "one");
            Err("stop")
        });
        assert_eq!(result, Err("stop"));
        assert!(store.is_empty());
    }
}
```

## Plan, then execute

Split a destructive operation into two functions. This form is a rule, not a
guideline:

1. `plan` reads the current state and returns a plan. It changes nothing, so
   a dry run is a call to `plan` alone, and tests can inspect the plan.
2. `execute` takes the plan by value and does the work. The plan can't run
   twice, because `execute` consumes it.

Give the plan private fields, so that only `plan` can make one and no caller
can edit it between the two steps. If the state can change between the two
steps, record a version in the plan and refuse a stale plan. If a plan is
valid only while some other value lives (a scratch directory, a lock), give
the plan a lifetime tied to that value, with `PhantomData<&'a T>` if it holds
no reference.

```rust
use std::collections::BTreeSet;

pub struct Store {
    version: u64,
    keys: BTreeSet<u64>,
}

/// The keys to delete. Only `plan_sweep` makes one; only `sweep` uses one.
///
/// ```compile_fail
/// let mut store = my_crate::Store::new([1, 2]);
/// let plan = store.plan_sweep(&Default::default());
/// store.sweep(plan).ok();
/// store.sweep(plan).ok();
/// ```
///
/// ```
/// let mut store = my_crate::Store::new([1, 2]);
/// let plan = store.plan_sweep(&Default::default());
/// assert_eq!(plan.dead(), [1, 2]);
/// assert_eq!(store.sweep(plan), Ok(2));
/// ```
#[derive(Debug)]
pub struct SweepPlan {
    version: u64,
    dead: Vec<u64>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum SweepError {
    Stale { planned: u64, current: u64 },
}

impl SweepPlan {
    pub fn dead(&self) -> &[u64] {
        &self.dead
    }
}

impl Store {
    pub fn new(keys: impl IntoIterator<Item = u64>) -> Self {
        Store {
            version: 0,
            keys: keys.into_iter().collect(),
        }
    }

    pub fn insert(&mut self, key: u64) {
        self.keys.insert(key);
        self.version += 1;
    }

    /// Changes nothing.
    pub fn plan_sweep(&self, live: &BTreeSet<u64>) -> SweepPlan {
        SweepPlan {
            version: self.version,
            dead: self.keys.difference(live).copied().collect(),
        }
    }

    /// Consumes the plan, and refuses it if the store changed after `plan_sweep`.
    pub fn sweep(&mut self, plan: SweepPlan) -> Result<usize, SweepError> {
        if plan.version != self.version {
            return Err(SweepError::Stale {
                planned: plan.version,
                current: self.version,
            });
        }
        plan.dead.iter().for_each(|key| {
            self.keys.remove(key);
        });
        self.version += 1;
        Ok(plan.dead.len())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_stale_plan_is_refused() {
        let mut store = Store::new([1, 2, 3]);
        let plan = store.plan_sweep(&BTreeSet::from([1]));
        store.insert(4);
        assert_eq!(
            store.sweep(plan),
            Err(SweepError::Stale {
                planned: 0,
                current: 1
            })
        );
    }
}
```

## Persisted state machines

When the state is stored and a process can crash between two steps, the
state is data, so use an enum. Typestate can't help here, because the type
of a value read from disk is known only at run time.

- Put all transitions in one function. It accepts a transition only from a
  legal predecessor and returns a typed error for every other request.
- Make a repeated transition a no-op that succeeds, so that a process that
  restarts after a crash can run the same step again.
- If the stages are linear, derive `Ord` in stage order, and compare stages
  instead of listing each pair.
- Pin the stored form of each variant with an explicit discriminant or
  `#[serde(rename = "..")]`, so that a variant rename doesn't change the
  stored bytes. Decode an unknown tag to an error, never to a default stage.
- In a transition table over `(state, event)` pairs, list each state's
  illegal events with an or-pattern, such as `(Swept, Mark | Sweep) => Err(..)`,
  instead of ending with a `_` arm. A new state or event then fails to
  compile until you decide its transitions.

```rust
use std::fmt;

/// The stages of a garbage collection, in order.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
#[repr(u8)]
pub enum Stage {
    Planned = 1,
    Marked = 2,
    Swept = 3,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[must_use]
pub enum Advance {
    Moved,
    AlreadyThere,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StageError {
    OutOfOrder { from: Stage, to: Stage },
    UnknownTag(u8),
}

impl fmt::Display for StageError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::OutOfOrder { from, to } => write!(f, "can't move from {from:?} to {to:?}"),
            Self::UnknownTag(tag) => write!(f, "unknown stage tag {tag}"),
        }
    }
}

impl std::error::Error for StageError {}

impl Stage {
    /// The stage that must come directly before this one.
    fn predecessor(self) -> Option<Stage> {
        match self {
            Self::Planned => None,
            Self::Marked => Some(Self::Planned),
            Self::Swept => Some(Self::Marked),
        }
    }

    pub fn to_tag(self) -> u8 {
        self as u8
    }

    pub fn from_tag(tag: u8) -> Result<Self, StageError> {
        match tag {
            1 => Ok(Self::Planned),
            2 => Ok(Self::Marked),
            3 => Ok(Self::Swept),
            other => Err(StageError::UnknownTag(other)),
        }
    }
}

/// The only way to change a stored stage.
pub fn advance(current: Stage, to: Stage) -> Result<Advance, StageError> {
    if current == to {
        Ok(Advance::AlreadyThere)
    } else if to.predecessor() == Some(current) {
        Ok(Advance::Moved)
    } else {
        Err(StageError::OutOfOrder { from: current, to })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn transitions() {
        let cases = [
            (Stage::Planned, Stage::Marked, Ok(Advance::Moved)),
            (Stage::Marked, Stage::Marked, Ok(Advance::AlreadyThere)),
            (
                Stage::Planned,
                Stage::Swept,
                Err(StageError::OutOfOrder {
                    from: Stage::Planned,
                    to: Stage::Swept,
                }),
            ),
            (
                Stage::Swept,
                Stage::Marked,
                Err(StageError::OutOfOrder {
                    from: Stage::Swept,
                    to: Stage::Marked,
                }),
            ),
        ];
        for (from, to, expected) in cases {
            assert_eq!(advance(from, to), expected, "{from:?} -> {to:?}");
        }
    }

    #[test]
    fn tags_round_trip() {
        for stage in [Stage::Planned, Stage::Marked, Stage::Swept] {
            assert_eq!(Stage::from_tag(stage.to_tag()), Ok(stage));
        }
        assert_eq!(Stage::from_tag(0), Err(StageError::UnknownTag(0)));
    }
}
```

## Costs

Typestate is worth its cost when a wrong order is a real bug and the value
has one owner. Know the costs before you choose it:

- **Code size.** Each stage is a type with its own impl block. A state with
  many outgoing transitions that depend on runtime data multiplies the code.
  Use an enum there.
- **Storage.** A field or a collection needs an enum wrapper around the
  stages, and code must match to get a stage back.
- **Rebinding.** Callers must bind the result of each transition
  (`let conn = conn.log_in(..)?;`). A method that takes `&mut self` can't
  change the stage.
- **Compile time.** Generic marker parameters and typestate builder macros
  increase compile time, because each stage is a separate monomorphized type.
  Generated typestate builders compile slower than runtime-checked
  builders.
- **Signatures.** Generic stage parameters make signatures and error messages
  longer. Prefer one type per stage when the stages hold different data.

## Tests

- Write a `compile_fail` doctest for each method that only some stages have,
  next to a doctest that calls it on the right stage.
- Test that dropping an open transaction leaves no trace, and that a failed
  closure doesn't commit.
- For a persisted machine, write a table test that covers each legal
  transition, each repeat, and a sample of illegal transitions, and a
  round-trip test for the stored tags, including an unknown tag.
