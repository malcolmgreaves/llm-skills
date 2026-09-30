# robust-rust: resume state and next steps

A maintainer document, not part of the skill: `SKILL.md` never points to it,
so agents that use the skill never read it. It records where the work
stopped on 2026-09-29, the decisions that constrain the next changes, and
the remaining tasks, so that the work can resume from this file alone.

## Contents

- [Where the work stands](#where-the-work-stands)
- [Constraints that every change must keep](#constraints-that-every-change-must-keep)
- [How to verify a change](#how-to-verify-a-change)
- [How to run the evals](#how-to-run-the-evals)
- [Next steps](#next-steps)
- [How to resume](#how-to-resume)

## Where the work stands

The skill is complete and has one full eval run. All work is on the branch
`mg/robust_rust` (a git worktree of the `llm-skills` repository), not merged
to `main`, and not pushed.

| Commit | What it did |
| --- | --- |
| `1f18380` | Added the skill: `SKILL.md`, six references, README, marketplace entry, root README row. |
| `e9ef258` | Applied the user's refinements (rules, guidelines, and exceptions; typestate rule cases; panic policy; `references/edition-2021.md`) and added the eval suite and `evals/check_examples.py`. |
| `823096b` | An adversarial review by a separate agent: corrected examples and compiler claims, tightened rules, fixed the graders. |
| `ee97939` | Decisions on the review's open questions (Deref scope, checked arithmetic on untrusted input, README privacy). |
| `7f654bc` | Turn and time limits for the behavior eval cases (50 turns, 1200 seconds). |
| `16607dd` | Fixed the eval scaffold: the fixture finds the toolchain record through its own path. |
| `a155408` | Added `evals/REPORT.md`, the first full eval run. |

The first eval run: the skill scored at or above the baseline in every
case, with a mean difference of +0.23 over the seven behavior cases. The
exception protocol showed the largest effect (+1.00). Two cases,
`connection-typestate` and `retrieve-verify`, didn't discriminate: the
baseline passes them too. See [evals/REPORT.md](evals/REPORT.md) for the
per-case table and the analysis.

## Constraints that every change must keep

### The user's decisions

The user made these decisions during review. Don't reverse one without
asking the user.

- **Rules and guidelines.** The checklist at the end of `SKILL.md` lists
  the rules. Every other instruction is a guideline, which the agent follows
  by default and explains when it departs from it.
- **Exception protocol.** Every rule has an escape hatch that only the user
  can open. The agent explains the rule, why it exists, and the
  consequences; the user explicitly approves the exception for one site and
  acknowledges the consequences; the agent marks the site with an
  `EXCEPTION` comment. A request for the forbidden code isn't approval. In
  a non-interactive run, the agent follows the rule and reports.
- **Typestate** is a rule for three cases (transactions and sessions end in
  a method that takes `self`; finished values that other code trusts come
  only from consuming their builder; destructive operations are plan, then
  execute) and a strong guideline for other in-process lifecycles. Persisted
  state is an enum with one checked transition function.
- **Panics.** No `unwrap()` outside test code (tests and doctests may). Avoid
  `expect()`: use it only when nothing else works, with a static message
  that states the invariant.
- **Deref.** No `Deref<Target = raw>` on an identity type (a rule); a named
  accessor is preferred on other constrained types (a guideline); no
  `DerefMut` on a type with an invariant (a rule).
- **Conversions.** A cross-crate raw-to-typed converter is an exception,
  named for its trust assumption, with a doc comment that says who may call
  it. Prefer a typed codec or `pub(crate)`. Evidence types have private
  fields and no derived `Deserialize`.
- **Checked arithmetic** on untrusted values (decoded lengths, counts,
  offsets, request fields) is a rule.
- **Edition.** Target the latest stable toolchain and edition 2024. Edition
  2021 appears only as call-outs in `references/edition-2021.md`.
- **Evals cost money.** Ask the user before any eval run. The user runs the
  evals from their own terminal (see [How to run the evals](#how-to-run-the-evals)).

### Privacy

The rules were distilled from the author's own Rust codebases, which are
private repositories. This repository is public. Never copy code, file
paths, identifiers, or design-document text from those codebases into the
skill, the evals, or the README, and never name or link them. Write new
examples, and describe the sources only as "the author's own Rust
codebases".

### Repository conventions

- `SKILL.md` must stay self-contained, and its body must stay within the
  validator's 500-line limit. It is at 499 lines now, so any addition must
  move other text into a reference first.
- References stay one level deep; a reference over about 300 lines needs a
  table of contents.
- Commits use conventional subjects scoped to the skill
  (`fix(robust-rust): ...`) and end with the co-author trailer that the
  earlier commits use.
- The block marked `# shared: robust-rust/eval-project` must stay
  byte-identical in every `evals/*/fixture.sh`; the validator checks it.

## How to verify a change

Run all three from the repository root after each change. Each must pass.

```bash
uv run scripts/validate.py --strict       # spec, links, shared blocks, line limit
claude plugin validate .                  # marketplace manifest
CARGO_NET_OFFLINE=true python3 skills/robust-rust/evals/check_examples.py
```

`check_examples.py` compiles each ```` ```rust ```` block in `SKILL.md` and
`references/` as its own crate (edition 2024, serde and thiserror
available), and runs clippy with `-D warnings`, `cargo test` (including
doctests), and `rustfmt --check`. A block whose first line is
`// Does not compile` must fail to compile; a block whose first line is
`// In <path>:` is skipped. `--fix-fmt` rewrites a block with rustfmt's
output. All 36 blocks pass as of `a155408`.

## How to run the evals

The Claude Code session that edits the skill runs inside an OS sandbox, so
it can't start the eval's own sandbox, and neither can a `!`-prefixed
command in that session. Ask the user to run the commands in a separate
terminal outside Claude Code, from the repository root:

```bash
# A smoke test: one case, one run, the with-skill arm only (about $0.50).
skills/robust-rust/evals/run.sh --case database-ids --runs 1 --ablation none \
  --no-publish --trust-plugin --keep-temp \
  --json skills/robust-rust/evals/results/smoke.json

# The full suite: 9 cases, 3 runs per arm (about $20 and 18 minutes).
skills/robust-rust/evals/run.sh --no-publish --trust-plugin -j 4 --keep-temp \
  --json skills/robust-rust/evals/results/full.json
```

Facts about the harness, each learned from a failed run:

- `run.sh` puts the toolchain's sysroot on `PATH` (the agent's session
  inherits `PATH`, and the sandbox can read directories on it) and writes
  `.eval-tools/sysroot`. The harness doesn't pass other environment
  variables to `fixture.sh`, so the fixture finds that file through its own
  path. Each run gets its own `HOME` and `TMPDIR`.
- Exit code 1 after a complete run is normal: `--threshold` defaults to 1.0.
- With `--keep-temp`, each run's workspace is sealed (mode 000). Rebuild a
  run's `src/lib.rs` from its trace (`tracePath` in the JSON) by replaying
  the `Write` and `Edit` tool inputs, as was done for `evals/REPORT.md`.
- In `full.json`, each grader has `explanation`; LLM graders also have
  `judgeVotes` and `evidence`. The results directory is gitignored.
- macOS's `xcrun` prints "couldn't create cache file ... Operation not
  permitted" in every run. It is harmless and affects both arms equally.

Rules for writing graders (from this suite and the `typed-python` suite):

- Don't name the graded technique in the prompt; the baseline then does it
  too, and the case measures nothing.
- Give a regex grader its flags in a `flags:` field, never inline (`(?m)`);
  the harness uses JavaScript regular expressions. Test a new pattern in
  Node against a passing and a failing sample.
- Give an LLM grader one condition per file. Multi-condition rubrics are
  noisy.
- Tell the agent in the prompt to put tests in `tests/`, so that the
  `no-unwrap` regex can check `src/lib.rs` for library code only.

## Next steps

Do these in order. Each ends with the three checks above and a commit. Ask
the user before steps 4 and 5, because they cost money.

### 1. Make `connection-typestate` discriminate

Both arms pass it, because the prompt describes the stages plainly. Replace
it (or add a case) with one of the typestate rule cases, where the
baseline's first draft is likely a runtime flag:

- **A write transaction** (preferred). Seed a small in-memory store, and
  ask: "Add a write transaction: callers stage puts and deletes and then
  commit; if they don't commit, nothing changes. Add a helper that runs a
  closure in a transaction." Grade on: `commit` takes `self` by value (a
  regex such as `fn\s+commit\s*\(\s*(mut\s+)?self\b`); the closure receives
  `&mut` (a regex on `FnOnce\s*\(\s*&mut`); a `compile_fail` doctest for use
  after commit; and a single-condition LLM grader that drop discards the
  staged writes, with no `committed: bool` field. Expect the baseline to
  write `commit(&mut self)` with a flag.

### 2. Make `retrieve-verify` discriminate

Both arms pass it, because the task starts from scratch. Seed the store
with an existing read method that returns `Result<u64, _>` and `Ok(0)` for
a missing file, and ask only for the checksum option. Grade on whether a
missing file is still `Ok(0)` after the change (a single-condition LLM
grader) and on the verification enum. Note the skill's scope rule: the
rules apply to code the agent writes or changes, and the agent reports
violations in other code, so a with-skill run that reports the `Ok(0)`
problem without changing it also shows the skill working; write the grader
to accept a change or an explicit report.

### 3. Add a GAT case

No case exercises section 5 of `SKILL.md` or
`references/gats-and-lifetimes.md`. The prompt must need a lending trait,
not a method that returns `&[u8]` (which needs no GAT). For example:
"Readers open a read session and look up many values from it; each lookup
returns a view with accessors for the key, the bytes, and the length,
without copying. Write the trait, an in-memory implementation, and a
generic function that returns the key of the longest value." Grade on: a
GAT with `where Self: '..` (a regex); no `&'a Self::X<'a>` (a regex that
must be absent); tests pass; and a single-condition LLM grader that the
generic function returns data that outlives each view.

### 4. Run the smoke test for each new or changed case

Use `--case <name> --runs 1 --ablation none` (about $0.50 each) to prove
that each fixture and grader works before the full run.

### 5. Run the full suite and update the report

Run the full suite with 5 runs per arm (`--runs 5`, about $35) once the
cases above are stable. Replace the table and findings in
`evals/REPORT.md` (keep the first run's numbers in a short "Previous run"
section), check every failing grader against its trace, and commit.

### Optional follow-ups

- Add `check_examples.py` to CI, or call it from the `check_code()` hook in
  `scripts/validate.py` when cargo is available.
- Stop the `xcrun` cache warning in eval runs, if a setting can do it
  without code in the fixture (not researched).
- A few examples sum in-memory lengths without checked arithmetic
  (`Hasher::update`, `Index::total`, `total_len`). The review judged them
  unreachable and left them; revisit only if the checked-arithmetic rule
  changes.
- Merge the branch to `main` when the user asks.

## How to resume

1. `cd` to the `mg/robust_rust` worktree and run `git log --oneline -8`. The
   newest commit should be `a155408` or a later one.
2. Run the three checks in [How to verify a change](#how-to-verify-a-change).
3. Read `SKILL.md`, `evals/REPORT.md`, and the case directory that the next
   step changes.
4. Do the next step that isn't done, and update this file: remove the step
   or record what changed.
