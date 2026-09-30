# robust-rust eval report

The first full run of the eval suite, on 2026-09-29, at commit `16607dd`.

## Setup

| Item | Value |
| --- | --- |
| Command | `skills/robust-rust/evals/run.sh --no-publish --trust-plugin -j 4 --keep-temp --json .../full.json` |
| Harness | `claude plugin eval`, Claude Code 2.1.284, default agent model, Sonnet judge |
| Toolchain | Rust 1.98.1 (the current stable), edition 2024, offline cargo |
| Runs | 9 cases, 3 runs per arm, with the skill and without it (54 runs), 4 at a time |
| Time | 17.5 minutes |
| Cost | $20.24 for the agent runs ($12.58 with the skill, $7.66 without), plus $1.76 for the judge |

Each behavior case seeds an empty (or small) edition 2024 library crate and
asks for a realistic change. No prompt names the technique that a grader
checks. `Δ` is the with-skill score minus the without-skill score; each
score is the fraction of scored graders that passed, averaged over 3 runs.

## Results

| Case | With | Without | Δ | What separated the arms |
| --- | --- | --- | --- | --- |
| exception-protocol | 1.00 | 0.00 | **+1.00** | Asked to add `impl From<u64> for UserId`, every baseline run added it without comment (one said "this doesn't loosen any checks"). Every with-skill run added nothing, explained the consequence, offered a narrower alternative (`UserId::parse_bare`), and asked for explicit approval. |
| database-ids | 1.00 | 0.83 | +0.17 | Both arms wrote sealed ID newtypes with no `From<u64>`, alias, or `Deref`. Only the with-skill runs wrote `compile_fail` doctests that prove the seal (3/3 against 0/3). |
| zero-copy-reader | 1.00 | 0.83 | +0.17 | The with-skill runs validated the whole buffer in `parse` and returned plain `&str` records (3/3). The baseline validated only the header and returned a lazy iterator that parses each record on demand and returns a `Result` (0/3). |
| length-provenance | 0.92 | 0.75 | +0.17 | Both arms built an evidence type for computed lengths, with a `compile_fail` doctest. The baseline used two `expect` calls per run in library code (0/3 clean); the with-skill runs used none in 2 runs and one in the third. |
| storage-functor | 1.00 | 0.87 | +0.13 | Both arms built the size cap as one generic layer with a typed refusal. The with-skill runs always gave the backend trait an associated `Error` (3/3 against 1/3). |
| connection-typestate | 1.00 | 1.00 | 0.00 | Both arms made "logged in" a separate type, so submitting before log-in doesn't compile, and both wrote a `compile_fail` doctest. |
| retrieve-verify | 1.00 | 1.00 | 0.00 | Both arms told missing from empty in the return type, took verification as an enum, and reported a checksum mismatch with both values. |
| trigger-basic | 1.00 | 0.00 | +1.00 | The skill fired on a plain Rust request in 3/3 runs. (Always +1.00: the baseline arm can't load the skill.) |
| no-trigger-go | 1.00 | 1.00 | 0.00 | The skill never fired on a Go state-machine request. (Always 0.) |

Mean `Δ` over the seven behavior cases: **+0.23**. The harness's mean over
all nine cases is +0.29, which the two trigger cases inflate. The skill
never scored below the baseline.

## Findings

- **The exception protocol is the skill's largest effect.** Without the
  skill, the agent does what the user literally asked, even when it breaks
  the type's seal. With it, the agent stops, names the rule and the
  consequence, and offers a compliant alternative before it asks for
  approval for one site. A with-skill reply ended: "reply confirming you
  approve this exception for that impl in `src/lib.rs`, and that you accept
  that any code can then turn any `u64` into a `UserId`."
- **The skill adds proof, not only structure.** Without the skill, the agent
  already writes newtypes, typestate, policy enums, and outcome enums when
  the prompt describes a lifecycle or a closed set. What it adds is what the
  baseline skips: `compile_fail` doctests for seals (database-ids),
  validation in one place instead of on every access (zero-copy-reader),
  associated error types (storage-functor), and no `expect` in library code
  (length-provenance).
- **Two cases don't discriminate.** connection-typestate and retrieve-verify
  pass in both arms. Their prompts describe the stages or the outcomes
  plainly, so the baseline's defaults already fit. They still guard against
  regressions, but they don't measure the skill.
- **The skill costs more per run.** With-skill runs averaged 8.7 turns and
  87 seconds, against 6.7 turns and 63 seconds without, and cost 1.6 times as
  much. The extra turns are the skill and reference reads, and the extra
  tests and doctests.

## Grader checks

Every failing grader was checked against the run's trace, and none is a false
positive:

- The `no-unwrap` failures in length-provenance are real `expect` calls in
  library code, reconstructed from the trace's file writes (for example
  `.expect("stream length overflowed u64")`), which the skill's panic policy
  says to avoid.
- The `validated-view` failures in zero-copy-reader are a `records()`
  iterator that parses lazily and returns `Result` per record.
- The `compile-fail-doctest` and `associated-error` failures are absent
  patterns in src/lib.rs.
- The exception-protocol failures are baseline runs that added the impl.

## Caveats

- Three runs per arm is a small sample: a difference of one run moves a
  case's score by 0.33 of a grader's weight.
- `tests-passed` shows that some `cargo test` in the session passed, not
  that the last one did. The harness has no grader that runs a command.
- macOS's `xcrun` prints "couldn't create cache file ... Operation not
  permitted" in every run, because the sandbox blocks its cache in
  `/var/folders`. Builds and tests still succeed, and both arms see the same
  message.
- The runs used the harness's default agent model. A weaker model may show a
  larger difference on the cases where this one already follows the style.

## Next steps

- Make connection-typestate and retrieve-verify discriminate: for example, a
  lifecycle whose natural first draft is a `state` field (a persisted job
  with retries), or an existing store whose read method already returns
  `Ok(0)` for a missing file.
- Add a case for a GAT: a trait whose read session lends borrowed views,
  graded on `where Self: 's` and on separate borrow and data lifetimes.
- Run 5 runs per arm once the cases stabilize, to narrow the per-case
  scores.
