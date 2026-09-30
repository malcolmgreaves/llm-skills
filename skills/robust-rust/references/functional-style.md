# Functional style

Read this when you write accumulation, streaming, effects, concurrency, or
code that mutates.

## Contents

- [Expressions and bindings](#expressions-and-bindings)
- [Iterators and combinators](#iterators-and-combinators)
- [Value-to-value steps](#value-to-value-steps)
- [Checked arithmetic](#checked-arithmetic)
- [Streams](#streams)
- [When a loop is clearer](#when-a-loop-is-clearer)
- [One kernel, thin wrappers](#one-kernel-thin-wrappers)
- [Contain mutation](#contain-mutation)
- [Pass effects in](#pass-effects-in)
- [Concurrency](#concurrency)

## Expressions and bindings

Rust has no enforced purity and no guaranteed tail calls, so a functional
style is a discipline that the code keeps by its structure. What makes
mutation dangerous is mutation of a value that other code can also see.
Rust's borrow rules already forbid that for plain references, so local
mutation that no caller can see is not the problem this style avoids.

- Use `if`, `match`, and blocks as expressions that produce a value:
  `let kind = match byte { .. };`.
- Refine a value by shadowing it (`let input = input.trim();`) instead of
  declaring it `mut` and changing it.
- Declare a binding `mut` only when its value changes after it is built.

## Iterators and combinators

- Transform collections with adapters (`map`, `filter`, `filter_map`,
  `flat_map`, `take_while`, `enumerate`) and finish with a consumer (`sum`,
  `max_by_key`, `fold`, `collect`).
- Collect fallible items with `collect::<Result<Vec<_>, _>>()`, which stops at
  the first error. Use `try_fold` for a fallible fold.
- Chain `Option` and `Result` with `map`, `and_then`, `ok_or`, `map_err`, and
  `?`. Use `let ... else` to leave early when a pattern doesn't match.
- Name an intermediate value when the chain becomes hard to read.

```rust
use std::collections::BTreeMap;
use std::fmt;

/// A sale with a non-empty customer name.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Sale {
    customer: String,
    cents: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SaleError {
    MissingComma,
    EmptyCustomer,
    BadCents,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LineError {
    pub line: usize,
    pub cause: SaleError,
}

impl fmt::Display for SaleError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::MissingComma => "missing comma",
            Self::EmptyCustomer => "empty customer",
            Self::BadCents => "cents isn't a whole number",
        })
    }
}

impl fmt::Display for LineError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "line {}: {}", self.line, self.cause)
    }
}

impl std::error::Error for SaleError {}

impl std::error::Error for LineError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        Some(&self.cause)
    }
}

impl Sale {
    /// Parses `customer,cents`.
    pub fn parse(line: &str) -> Result<Sale, SaleError> {
        let (customer, cents) = line.split_once(',').ok_or(SaleError::MissingComma)?;
        let customer = customer.trim();
        if customer.is_empty() {
            return Err(SaleError::EmptyCustomer);
        }
        let cents = cents.trim().parse().map_err(|_| SaleError::BadCents)?;
        Ok(Sale {
            customer: customer.to_string(),
            cents,
        })
    }

    pub fn customer(&self) -> &str {
        &self.customer
    }

    pub fn cents(&self) -> u64 {
        self.cents
    }
}

/// Parses every non-blank line, and stops at the first bad one.
pub fn parse_sales(input: &str) -> Result<Vec<Sale>, LineError> {
    input
        .lines()
        .enumerate()
        .filter(|(_, line)| !line.trim().is_empty())
        .map(|(index, line)| {
            Sale::parse(line).map_err(|cause| LineError {
                line: index + 1,
                cause,
            })
        })
        .collect()
}

/// Totals per customer. `None` if a total overflows.
pub fn totals(sales: &[Sale]) -> Option<BTreeMap<&str, u64>> {
    sales.iter().try_fold(BTreeMap::new(), |mut totals, sale| {
        let total: &mut u64 = totals.entry(sale.customer()).or_default();
        *total = total.checked_add(sale.cents())?;
        Some(totals)
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_and_totals() {
        let sales = parse_sales("ann, 250\n\nbob,100\nann,50\n").unwrap();
        let totals = totals(&sales).unwrap();
        assert_eq!(totals.get("ann"), Some(&300));
        assert_eq!(totals.get("bob"), Some(&100));
    }

    #[test]
    fn reports_the_bad_line() {
        let error = parse_sales("ann,1\nbob\n").unwrap_err();
        assert_eq!(error.cause, SaleError::MissingComma);
        assert_eq!(error.to_string(), "line 2: missing comma");
    }
}
```

The accumulator inside `try_fold` is mutated, but no caller can see it until
the fold returns it. That is local accumulation, not shared state.

## Value-to-value steps

Write each step of an accumulation as a function that takes a value and
returns the next value. Steps then compose with `fold`, and each one has a
table test.

- `fn add_to(self, total: Total) -> Total` adds one item to a running total.
- `fn merged(self, other: Self) -> Self` with a `ZERO` constant combines two
  partial results, so the same code totals one list, several lists, or the
  results of several threads.
- `fn with_limit(self, limit: u32) -> Self` changes one setting of a `Copy`
  configuration value.
- Mark these methods `#[must_use]`, so that a call whose result is dropped
  is a warning.

An out-parameter (`fn add(&self, total: &mut Total)`) can't be used in a
`fold`, `map`, or `merged`, and hides which calls change what.

```rust
/// Where a length came from.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Len {
    Verified(u64),
    Claimed(u64),
}

/// A total that remembers whether every part was verified.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Total {
    pub bytes: u64,
    pub all_verified: bool,
}

impl Total {
    pub const ZERO: Total = Total {
        bytes: 0,
        all_verified: true,
    };

    #[must_use]
    pub fn merged(self, other: Total) -> Total {
        Total {
            bytes: self.bytes.saturating_add(other.bytes),
            all_verified: self.all_verified && other.all_verified,
        }
    }
}

impl Len {
    #[must_use]
    pub fn add_to(self, total: Total) -> Total {
        let part = match self {
            Len::Verified(bytes) => Total {
                bytes,
                all_verified: true,
            },
            Len::Claimed(bytes) => Total {
                bytes,
                all_verified: false,
            },
        };
        total.merged(part)
    }
}

pub fn total(lens: &[Len]) -> Total {
    lens.iter()
        .fold(Total::ZERO, |total, len| len.add_to(total))
}

/// Settings for a scan. A `Copy` value, changed by returning a new one.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ScanConfig {
    pub limit: u32,
    pub follow_links: bool,
}

impl Default for ScanConfig {
    fn default() -> Self {
        ScanConfig {
            limit: 1000,
            follow_links: false,
        }
    }
}

impl ScanConfig {
    #[must_use]
    pub fn with_limit(self, limit: u32) -> Self {
        ScanConfig { limit, ..self }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn totals_compose() {
        let a = [Len::Verified(3), Len::Verified(4)];
        let b = [Len::Claimed(5)];
        assert_eq!(
            total(&a),
            Total {
                bytes: 7,
                all_verified: true
            }
        );
        assert_eq!(
            total(&a).merged(total(&b)),
            total(&[&a[..], &b[..]].concat())
        );
        assert_eq!(ScanConfig::default().with_limit(5).limit, 5);
    }
}
```

The example uses `saturating_add` because a byte total that reaches
`u64::MAX` is already meaningless as a display value. Where an overflow must
be an error, use `checked_add`.

## Checked arithmetic

Arithmetic on a value that comes from input (a declared length, a count, an
offset) can overflow. In a debug build, overflow panics; in a release build,
it wraps silently. Use checked operations and convert integer types with
`try_from`:

```rust
/// The byte length of `count` records of `record` bytes after a header.
/// `None` if the size doesn't fit in memory.
pub fn value_len(count: u64, record: u64, header: u64) -> Option<usize> {
    let total = count.checked_mul(record)?.checked_add(header)?;
    usize::try_from(total).ok()
}
```

Use `wrapping_*` for hash functions and other arithmetic that is defined
modulo 2^n, and `saturating_*` where a clamped value is correct. Write a
comment that says why.

## Streams

- Return `impl Iterator<Item = T>` instead of a `Vec` when the caller can
  consume items one at a time. The caller can stop early, and memory stays
  flat.
- A batch lookup yields exactly one item per input, in input order. A
  missing key is an item (`None` or `Ok(None)`), not the end of the
  stream. Otherwise the caller can't tell which inputs had no result.
- When a stream must match a declared count, don't pair the two with `zip`.
  `zip` stops at the shorter side, so it hides a truncated stream and extra
  items. Walk the expected items, report an early end as truncation, and
  then check that the stream is empty.
- A function that collects a whole stream takes a limit, and refuses before
  it allocates past the limit.

```rust
use std::collections::HashMap;

/// One result per key, in key order. A missing key yields `None`.
pub fn lookup_all(
    table: &HashMap<u64, String>,
    keys: impl IntoIterator<Item = u64>,
) -> impl Iterator<Item = Option<&str>> {
    keys.into_iter()
        .map(|key| table.get(&key).map(String::as_str))
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StreamError {
    Truncated {
        index: usize,
    },
    Mismatch {
        index: usize,
        expected: u64,
        actual: u64,
    },
    Overrun {
        expected: usize,
    },
}

/// Checks that `actual` yields exactly the `expected` items.
pub fn check_exact(
    expected: &[u64],
    mut actual: impl Iterator<Item = u64>,
) -> Result<(), StreamError> {
    for (index, &want) in expected.iter().enumerate() {
        match actual.next() {
            None => return Err(StreamError::Truncated { index }),
            Some(got) if got != want => {
                return Err(StreamError::Mismatch {
                    index,
                    expected: want,
                    actual: got,
                });
            }
            Some(_) => {}
        }
    }
    match actual.next() {
        None => Ok(()),
        Some(_) => Err(StreamError::Overrun {
            expected: expected.len(),
        }),
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TooMany {
    pub limit: usize,
}

/// Collects at most `limit` items, and refuses a longer stream.
pub fn collect_at_most<T>(items: impl Iterator<Item = T>, limit: usize) -> Result<Vec<T>, TooMany> {
    let collected: Vec<T> = items.take(limit.saturating_add(1)).collect();
    if collected.len() > limit {
        Err(TooMany { limit })
    } else {
        Ok(collected)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_streams() {
        let expected = [1, 2, 3];
        let cases = [
            (vec![1, 2, 3], Ok(())),
            (vec![1, 2], Err(StreamError::Truncated { index: 2 })),
            (vec![1, 2, 3, 4], Err(StreamError::Overrun { expected: 3 })),
            (
                vec![1, 9, 3],
                Err(StreamError::Mismatch {
                    index: 1,
                    expected: 2,
                    actual: 9,
                }),
            ),
        ];
        for (actual, result) in cases {
            assert_eq!(check_exact(&expected, actual.into_iter()), result);
        }
    }

    #[test]
    fn missing_keys_keep_their_place() {
        let table = HashMap::from([(1, "one".to_string())]);
        let found: Vec<_> = lookup_all(&table, [2, 1]).collect();
        assert_eq!(found, [None, Some("one")]);
        assert_eq!(collect_at_most(0..10, 3), Err(TooMany { limit: 3 }));
    }
}
```

## When a loop is clearer

Iterator chains aren't always the clearer form. Use a `for` loop when:

- The body has several early exits with different typed errors, as
  `check_exact` does.
- Each step has several effects, such as a write and a progress report.
- A closure would need to borrow something mutably that the surrounding code
  also uses.

Rust doesn't guarantee tail calls, so deep recursion can overflow the stack
on large inputs. Walk a deep structure with an explicit stack. Wrap the walk
in `std::iter::from_fn` to keep it lazy:

```rust
pub enum Tree {
    Leaf(u64),
    Node(Vec<Tree>),
}

impl Tree {
    /// The leaves, left to right, without recursion.
    pub fn leaves(&self) -> impl Iterator<Item = u64> {
        let mut stack = vec![self];
        std::iter::from_fn(move || {
            while let Some(tree) = stack.pop() {
                match tree {
                    Tree::Leaf(value) => return Some(*value),
                    Tree::Node(children) => stack.extend(children.iter().rev()),
                }
            }
            None
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn leaves_in_order() {
        let tree = Tree::Node(vec![
            Tree::Leaf(1),
            Tree::Node(vec![Tree::Leaf(2), Tree::Leaf(3)]),
            Tree::Leaf(4),
        ]);
        assert!(tree.leaves().eq([1, 2, 3, 4]));
    }
}
```

## One kernel, thin wrappers

Implement each algorithm once, as its most general function: generic over
its input, taking every option as a parameter, and returning the richest
result. Write each convenience entry point as a wrapper of a few lines that
fixes some parameters or drops part of the result. Two copies of an
algorithm drift apart, and a bug fixed in one stays in the other.

When several iterators walk the same structure with different filters,
share one private step function and make each iterator a filter over it.

## Contain mutation

Mutate only inside a container that callers can't observe while it changes:

- **A consuming builder.** An incremental hasher or encoder mutates its own
  state, and `finish(self)` consumes it. Test that feeding the input in
  pieces gives the same result as the one-shot function.
- **A pure entry point.** Hide a `&mut` builder behind a function from
  `impl IntoIterator` to the finished value, so callers never see the
  builder.
- **Local accumulation.** A `Vec` or map that a function builds and returns
  is not shared state.
- **A move-only value behind `&mut self`.** Prefer typestate, so that the
  owner changes type when it gives the value up. When a long-lived struct
  must hold the value instead, keep it in a private `Option`, call `take()`
  in exactly one method, and return a typed error (such as
  `AlreadyFinished`) when the value is gone, not an `expect`.
- **Interior mutability** (`Cell`, `RefCell`, `Mutex`, `OnceLock`) only for
  caches and memoization whose contents can be rebuilt from the
  authoritative data. State that in the doc comment.
- **`unsafe`** in one small function per use, with a `// SAFETY:` comment
  that states the invariant the code relies on. Convert an OS error code to
  a typed enum. When the safe operation isn't available, return a typed
  refusal instead of falling back to a weaker operation silently. Assert
  layout facts with `const _: () = assert!(..);`.

## Pass effects in

Take each ambient effect (the current time, randomness, the environment,
the filesystem) as an argument: a value when the function needs one reading,
or a small trait when it needs to call the effect. The logic is then
deterministic, and a test controls the effect without sleeping or touching
the disk.

```rust
use std::time::{Duration, SystemTime};

/// The current time, as a capability.
pub trait Clock: Send + Sync {
    fn now(&self) -> SystemTime;
}

pub struct SystemClock;

impl Clock for SystemClock {
    fn now(&self) -> SystemTime {
        SystemTime::now()
    }
}

/// A pure decision: the clock is an argument.
pub fn is_expired(clock: &dyn Clock, created: SystemTime, ttl: Duration) -> bool {
    clock
        .now()
        .duration_since(created)
        .is_ok_and(|age| age > ttl)
}

#[cfg(test)]
mod tests {
    use super::*;

    struct FixedClock(SystemTime);

    impl Clock for FixedClock {
        fn now(&self) -> SystemTime {
            self.0
        }
    }

    #[test]
    fn expiry_without_sleeping() {
        let created = SystemTime::UNIX_EPOCH;
        let ttl = Duration::from_secs(60);
        let later = |secs| FixedClock(created + Duration::from_secs(secs));
        assert!(!is_expired(&later(60), created, ttl));
        assert!(is_expired(&later(61), created, ttl));
    }
}
```

For protocol code, the same idea scales to a sans-IO design: the core is a
state machine that takes events (bytes received, a timer fired) and returns
actions (bytes to send, a timer to set), and a thin shell does the IO. It
costs more code than a sequential `async fn`, so use it when the protocol
logic needs tests that run without a network.

Keep test doubles in `#[cfg(test)]` modules. When other crates' tests need
them, put them behind a `test-support` feature, and check that no
production build turns that feature on.

## Concurrency

- Run pure computation (hashing, parsing, compression) on worker threads, and
  give each mutable or `!Send` resource (a database transaction, a file
  writer) to exactly one thread. Workers send results to that thread over a
  channel.
- Use `std::thread::scope` so that every worker joins before the function
  returns, including on an early return.
- Use persistent collections (the `im` or `rpds` crates) only when the
  domain needs cheap snapshots of a changing collection. They are slower
  than the standard collections for other uses.
