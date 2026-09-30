# robust-rust

> Human-facing docs. Agents read `SKILL.md`, never this file, so nothing here
> is required for the skill to work. See [AGENTS.md](../../AGENTS.md).

Makes an agent write type-driven, functional Rust: it designs the domain as
types before it writes function bodies, so that the types decide which
values, states, and interactions the program can express. Models often write
Rust with raw integers and strings for IDs, `bool` flags and `Option` fields
for states, runtime checks for call order, one trait per backend with copied
logic, `String` error payloads, and `unwrap()` on input. This skill replaces
those defaults with explicit rules and the reason for each one.

The rules that do most of the work:

- Give each identity and constrained value a newtype with a private field
  and only the constructors its meaning allows. No `From<raw>`, no
  conversion between identity types, no `Deref` from an identity type to its
  raw type, and no `DerefMut` on a type with an invariant.
- Model states, outcomes, and policies as enums, and match them
  exhaustively. No `bool` parameters, no sentinel values, and no `_` arm on
  a domain enum.
- Encode in-process lifecycles as typestate with consuming transitions, and
  persisted lifecycles as enums with one checked transition function.
- Write traits as ML-style module signatures: associated types for what the
  implementation decides, read and write halves joined by a blanket impl,
  equality constraints between linked traits, and generic structs or blanket
  impls as functors.
- Use generic associated types (GATs) for borrowed sessions and views, and
  keep the borrow lifetime separate from the data lifetime.
- Parse raw data once, at a named boundary, into refined types, and keep each
  unchecked conversion narrow and named for its trust assumption.
- Give each boundary its own error enum with typed fields.
- Write pure functions and folds, and contain mutation, interior mutability,
  and `unsafe` in small documented containers.
- Test the type design itself: a `compile_fail` doctest for each seal and
  typestate rule, next to a doctest that does the legal thing.
- Never `unwrap()` outside test code, and use `expect()` only when nothing
  else works, with a static message that states the invariant.
- Split the instructions into rules and guidelines. A guideline is the
  default, and the agent says why when it departs from one. A rule holds
  unless the user approves an exception: the agent explains the rule, why it
  exists, and the consequences; the user explicitly confirms the exception
  for one site and acknowledges the consequences; and the agent marks that
  site with an `EXCEPTION` comment.

## When it triggers

On any task that writes, designs, reviews, or refactors Rust, and on mentions
of structs, enums, traits, generics, lifetimes, GATs, typestate, state
machines, builders, newtypes, ID or hash types, parsers, serde, error types,
backend traits, derive macros, iterators, or making illegal states
unrepresentable. Example prompts:

- "Write a client connection type that can send only after it logs in."
- "Add ID types for users, orders, and products; they're `u64`s in Postgres."
- "Design a storage trait with in-memory and file backends and a cache layer
  over any backend."
- "Write a zero-copy reader for this length-prefixed record format."
- "Review this module for type-design problems."

What it doesn't cover:

- Prose in comments and docs. The `google-developer-style` and
  `asd-ste100-simplified-technical-english` skills cover prose.
- Async runtimes, unsafe-heavy FFI design, and performance tuning, beyond
  the rules for containing effects, mutation, and `unsafe`.

## Requirements

None to load the skill. To follow it, the agent needs a Rust toolchain in
which it can run the project's build, `cargo clippy`, and tests. The skill
targets the latest stable toolchain and edition 2024 (Rust 1.85 or later),
and lists what to do differently in an edition 2021 crate.

## Bundled files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The skill: a workflow, the rules-and-exceptions protocol, the target edition, nine rule sections, and a checklist split into rules and guidelines. |
| `references/edition-2021.md` | What to write differently in an edition 2021 crate (captured lifetimes, let chains, `if let` temporaries, `unsafe` blocks) and how `rust-version` limits APIs. Read when the crate uses edition 2021. |
| `references/typestate.md` | Choosing between typestate and enum state; one type per stage; a sealed marker parameter; storing typestate values in an enum; transactions with drop as abort; plan, then execute; persisted state machines; costs; tests. Read when the agent models a lifecycle. |
| `references/traits-as-modules.md` | The ML correspondence table; associated types or type parameters; read and write signatures, functors, and platform traits; several structures per signature despite coherence; linked traits with equality constraints; static facts and const rules; sealed traits; `impl Trait` as an abstract type; dispatch; macros that generate impls. Read when the agent designs a trait. |
| `references/gats-and-lifetimes.md` | When a GAT is warranted; lending sessions and views; separating the borrow lifetime from the data lifetime, with a failing and a fixed example; where-clauses in impls (E0195); GAT arity; type-constructor GATs for modes; pitfalls; a diagnostics table. Read before the agent writes a GAT or on a lifetime error. |
| `references/boundaries-and-errors.md` | Parsing into refined types, including `serde(try_from)`; one decoder per byte format with a validated view; the escape-hatch ladder; evidence types; error enum design; the panic policy. Read when the agent writes a parser, a conversion, or an error type. |
| `references/functional-style.md` | Iterators and combinators; value-to-value steps and monoid-style totals; checked arithmetic; stream contracts; when a loop is clearer; explicit stacks; one kernel with thin wrappers; containers for mutation; injected effects; concurrency ownership. Read when the agent writes accumulation, streaming, effects, or mutation. |
| `references/testing-types.md` | `compile_fail` doctests and their limits; trybuild with a pass case; static assertions; golden bytes and identity matrices; table tests; property and differential tests with a seeded generator; state-machine tests; tests that can fail. Read when the agent adds tests for a type-level guarantee. |
| `evals/run.sh` | Runs the eval suite with the Rust toolchain readable by the agent's sandbox (see [Running the evals](#running-the-evals)). |
| `TODO_resume_state.md` | Maintainer notes: where the work stopped, the decisions that constrain changes, how to verify and run the evals, and the next steps. `SKILL.md` doesn't point to it, so agents never read it. |
| `evals/REPORT.md` | Results of the first full eval run: per-case scores with and without the skill, what separated the arms, grader checks, and caveats. |
| `evals/check_examples.py` | Maintainer tool: compiles, lints, tests, and format-checks every Rust block in `SKILL.md` and `references/`. Not an eval case. |
| `evals/trigger-basic/`, `evals/no-trigger-go/` | The skill fires on a plain Rust request, and doesn't fire on a Go state-machine request (`min: 0, max: 0, arm: both`). |
| `evals/connection-typestate/` | Submitting before log-in must not compile: one type per stage, no `bool` state field, a `compile_fail` doctest. |
| `evals/database-ids/` | ID types keyed by `u64` are newtypes with private fields, and have no `From<u64>`, alias, or `Deref`, plus a `compile_fail` doctest. |
| `evals/storage-functor/` | Backends share a trait with an associated `Error`, and the size cap is one generic layer over any backend with a typed refusal. |
| `evals/zero-copy-reader/` | A length-prefixed binary format (which differs from the one in `references/`) is validated in one parse into a view with a typed error per failure, trailing bytes are refused, nothing panics on input, and library code has no `unwrap` or `expect`. |
| `evals/retrieve-verify/` | Reading a stored file tells missing from empty, takes verification as an enum, and reports a checksum mismatch with both values. The fixture seeds a small store. |
| `evals/length-provenance/` | Only lengths computed while hashing can enter the index, enforced by an evidence type and a `compile_fail` doctest. |
| `evals/exception-protocol/` | Asked to add `impl From<u64> for UserId`, the agent explains the rule and its consequences and asks for approval (or offers a narrower alternative) instead of adding it. |

## Design notes

- **Where the rules come from.** The rules distill the author's own Rust
  codebases, checked against the published sources below.
  Where the two disagree, the skill states the trade-off and picks a
  default. The examples are new code written for the skill; none is copied
  from those codebases.
- **Policy in `SKILL.md`, complete code in the references.** Models already
  know what an enum, a trait, and a GAT are. What they don't do by default is
  reach for them first, keep constructors sealed, or split lifetimes. The
  references show complete code for the cases where a model is most likely
  to write a weaker version.
- **Reading the references is an explicit workflow step.** Agents tend to
  skip a reference that `SKILL.md` mentions only as optional, so step 3 of
  the workflow names the reference to read before each kind of design.
- **The examples pass the checks that the skill asks for.** Every Rust block
  in `SKILL.md` and `references/` compiled on its own as a library crate with
  edition 2024 on Rust 1.98.1, passed `cargo clippy --all-targets -- -D
  warnings`, passed `cargo test` (unit tests and doctests, including every
  `compile_fail` doctest), and passed `rustfmt --check`. A block whose first
  line is `// Does not compile` must fail with each error code that the line
  names, and does (E0515 and E0195). Each `compile_fail` doctest was also
  checked for its intended error (E0599, E0603, E0277, E0624, E0507, E0382)
  with `RUSTC_BOOTSTRAP=1`, which makes rustdoc check error codes. A
  block whose first line is `// In <path>:` is a file of another target and
  was not compiled. When you edit an example, run all four checks again.
- **Claims about the compiler were tested, not recalled.** For example,
  stable rustdoc doesn't check an error code on a `compile_fail` block;
  omitting a trait's `where 'data: 'borrow` in an impl gives E0195; a
  higher-ranked bound on a GAT projection gives E0521; and in edition 2021
  an `if let` scrutinee's `RefCell` borrow is still alive in the `else`
  branch.
- **Typestate is a rule in three cases and a guideline elsewhere.** It is a
  rule for transactions and sessions (a terminal method that takes `self`),
  for finished values that other code trusts, and for destructive operations
  (plan, then execute). For other in-process lifecycles it is a strong
  guideline, and the agent says why when it chooses a runtime check. State
  that is persisted, received, or stored in a collection is an enum with a
  checked transition function, because its type is known only at run time.
- **Every rule has an escape hatch that only the user can open.** Some rules
  must bend at real boundaries, such as a public converter that another
  crate needs. The protocol makes each exception deliberate, informed, and
  local, and the `EXCEPTION` comment keeps a later reader or agent from
  copying it elsewhere without a new approval. In a non-interactive run, the
  agent follows the rule and reports where it would have asked.
- **Stances where sources disagree.** Consuming builders for lifecycles, but
  `&mut` builders for plain configuration (the Rust API Guidelines prefer
  the latter). `#[non_exhaustive]` only on types published to other people's
  crates, because it removes exhaustiveness checks downstream. No `Deref` from
  an identity type to its raw representation, because it lets the raw value
  flow without a visible conversion. Explicit loops when a body has several typed exits (Effective
  Rust agrees).
- **Checking the examples.** `python3 evals/check_examples.py` runs the
  four checks on every block; `--fix-fmt` rewrites a block with rustfmt's
  output.
- **Testing.** Run a prompt such as "write a module for a client connection
  that connects, logs in with a token, sends requests only after it logs in,
  and closes; include tests" with and without the skill. The skill is working
  if the with-skill output has one type per stage with consuming
  transitions, no `is_logged_in: bool`, a typed error enum, and a
  `compile_fail` doctest for `send` before log-in.

## Running the evals

From the repository root, in a shell that isn't sandboxed:

```bash
skills/robust-rust/evals/run.sh --no-publish
```

`run.sh` checks that the shell can start the OS sandbox that the eval uses
for the agent's shell commands, and that the default toolchain has cargo,
clippy, rustdoc, and rustfmt. The agent's sandbox can't read the home
directory, but it can read each directory on `PATH` that is inside it, and
the agent's session inherits `PATH`. So `run.sh` puts the toolchain's
sysroot and its `bin` directory first on `PATH` (bypassing the rustup
proxies, which read `~/.rustup`), and records the sysroot in `.eval-tools/`,
which it deletes on exit. Each run gets its own `HOME`, so cargo's default
home is writable. Then `run.sh` runs `claude plugin eval skills/robust-rust
--scaffold --judge-model sonnet --allow-tools Write Edit Bash` with your
arguments.

Each case's `fixture.sh` seeds an edition 2024 library crate named `domain`
(the block marked `# shared: robust-rust/eval-project`), sets cargo offline
in the workspace, and refuses to run outside `run.sh`. The harness doesn't
pass `run.sh`'s environment variables to it, so it finds the `.eval-tools/`
record through its own path. The graders can't run cargo, so `tests-passed` reads the
session trace for a `cargo test` summary with at least one passing test.
Most behavior prompts put the tests in `tests/`, and the `no-unwrap` regex
checks that `src/lib.rs` calls neither `unwrap` nor `expect` outside
comments and before its first `#[cfg(test)]`, including a chained call on
its own line. Read the skill's effect from the behavior cases' `Δ`;
`trigger-basic`'s `Δ` is always +1.00 and `no-trigger-go`'s is always 0.

## Sources

- Yaron Minsky, [Effective ML Revisited](https://blog.janestreet.com/effective-ml-revisited/) (making illegal states unrepresentable).
- Alexis King, [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) and [Names are not type safety](https://lexi-lambda.github.io/blog/2020/11/01/names-are-not-type-safety/).
- Scott Wlaschin, [Designing with types: Making illegal states unrepresentable](https://fsharpforfunandprofit.com/posts/designing-with-types-making-illegal-states-unrepresentable/).
- Cliff L. Biffle, [The Typestate Pattern in Rust](https://cliffle.com/blog/rust-typestate/).
- Ana Hobden, [Pretty State Machine Patterns in Rust](https://hoverbear.org/blog/rust-state-machine-pattern/).
- The Rust Programming Language, [Implementing an Object-Oriented Design Pattern](https://doc.rust-lang.org/book/ch18-03-oo-design-patterns.html) and [Advanced Traits](https://doc.rust-lang.org/book/ch20-02-advanced-traits.html).
- Rust API Guidelines: [Type safety](https://rust-lang.github.io/api-guidelines/type-safety.html), [Future proofing](https://rust-lang.github.io/api-guidelines/future-proofing.html), [Dependability](https://rust-lang.github.io/api-guidelines/dependability.html).
- Predrag Gruevski, [A definitive guide to sealed traits in Rust](https://predr.ag/blog/definitive-guide-to-sealed-traits-in-rust/).
- Derek Dreyer, Robert Harper, and Manuel Chakravarty, [Modular Type Classes](https://people.mpi-sws.org/~dreyer/papers/mtc/main-short.pdf) (type classes as signatures, instances as modules, polymorphic instances as functors).
- [Traits + ML modules](https://internals.rust-lang.org/t/traits-ml-modules/272), Rust internals forum.
- [RFC 0195: Associated items](https://rust-lang.github.io/rfcs/0195-associated-items.html) and [RFC 1598: Generic associated types](https://rust-lang.github.io/rfcs/1598-generic_associated_types.html).
- Jack Huey, [Generic associated types to be stable in Rust 1.65](https://blog.rust-lang.org/2022/10/28/gats-stabilization/) (including the known limitations).
- Sabrina Jewson, [The Better Alternative to Lifetime GATs](https://sabrinajewson.org/blog/the-better-alternative-to-lifetime-gats) and [Modular Errors in Rust](https://sabrinajewson.org/blog/errors).
- Rust GAT initiative, [Many modes](https://rust-lang.github.io/generic-associated-types-initiative/design_patterns/many_modes.html).
- Michael Snoyman, [Monads and GATs in nightly Rust](https://academy.fpblock.com/blog/monads-gats-nightly-rust/) (why not to build monad towers).
- David Drysdale, Effective Rust, [Item 9: Consider using iterator transforms instead of explicit loops](https://lurklurk.org/effective-rust/iterators.html).
- Niko Matsakis, [Focusing on ownership](https://smallcultfollowing.com/babysteps/blog/2014/05/13/focusing-on-ownership/).
- Nikolay Yakimov, [Rust is Not a Functional Language](https://serokell.io/blog/rust-is-not-a-functional-language).
- Tyler Neely, [Error Handling in a Correctness-Critical Rust Project](https://sled.rs/errors.html).
- Thomas Eizinger, [sans-IO: The secret to effective Rust for network services](https://www.firezone.dev/blog/sans-io).
- Brian Anderson, [Generics and Compile-Time in Rust](https://pingcap.com/blog/generics-and-compile-time-in-rust/).
- bon, [Compilation benchmarks](https://bon-rs.com/guide/benchmarks/compilation) (the compile-time cost of typestate builders).
- The rustdoc book, [Documentation tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html).
- The Rust Reference, [Influences](https://doc.rust-lang.org/reference/influences.html) and [Type system attributes](https://doc.rust-lang.org/reference/attributes/type_system.html).
