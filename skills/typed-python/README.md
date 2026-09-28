# typed-python

> Human-facing docs. Agents read `SKILL.md`, never this file, so nothing here
> is required for the skill to work. See [AGENTS.md](../../AGENTS.md).

Makes an agent write Python that is fully type-annotated, uses precise types,
passes the project's type checker and ruff, is built from small composable
functions, and has table-driven tests. Models often write Python with partial
annotations, `dict[str, Any]` for structured data, large functions that mix
I/O with logic, mutable module-level state, and one test per case. This
skill replaces those defaults with explicit rules and the reason for each
one.

The rules that do most of the work:

- Annotate every public function, method, parameter, return value,
  attribute, and module-level variable. Small private or nested functions
  are the only exception.
- Name key and value types. Use a TypedDict for a dict with fixed keys, a
  frozen dataclass for struct-like data, a NamedTuple only to grow an
  existing tuple, and a bound TypeVar when an output type follows an input
  type.
- Run the project's type checker and treat its errors as bugs. Work around
  an error only after showing that the checker is wrong, and then with the
  narrowest workaround.
- Run ruff and make the change each finding asks for. Suppress a finding,
  with `# noqa: CODE` and a reason, only when it's a false positive or the
  fix makes the code measurably worse.
- Compose small pure functions; keep I/O at the edges; keep mutation inside
  classes with private state; allow only constant or read-only global state.
- Write table tests, preferably before the implementation.

## When it triggers

On any task that writes, edits, refactors, or reviews Python, and on
mentions of type hints, mypy, pyright, ruff, linting, TypedDict, dataclass,
TypeVar, Protocol, pure functions, global state, or table tests. Example prompts:

- "Add a function that groups these records by customer."
- "Fix the mypy errors in `ingest.py`."
- "Refactor this script so I can test it."
- "Write tests for `parse_config`."

What it doesn't cover:

- Docstring and comment style. The `google-developer-style` skill covers
  prose in comments and docstrings.
- Performance tuning, beyond allowing contained mutation when performance
  requires it.

## Requirements

None to load the skill. To follow it, the agent needs a Python environment
in which it can run the project's type checker and test runner.

The eval suite needs [uv](https://docs.astral.sh/uv/) on your `PATH`, and
network access the first time, to build its tools environment. It also needs
Claude Code's sandbox for Bash (macOS, or Linux with `bubblewrap` and
`socat`), which can't start inside another sandbox: run the suite from a
shell that isn't sandboxed, not from a sandboxed Claude Code session.

## Bundled files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The skill: workflow, seven rule sections, a Python-version syntax table, and a checklist. |
| `references/examples.md` | Worked examples: a refactor into composed functions with its table tests, JSON-to-TypedDict validation, a Protocol with a test fake, a `ParamSpec` decorator, a unittest table test, and the workaround comment format. Read on demand. |
| `references/type-checkers.md` | A comparison of the Python type checkers (status, home page, speed, conformance, what each one catches, pros and cons, and archived or minor checkers); the strictest practical configuration for mypy, pyright, basedpyright, pyrefly, ty, and zuban, with stricter options and their cost; each checker's ignore-comment syntax; and how to find and run a project's checker. Every configuration was run on the checker's current release. Read when recommending settings, choosing a checker, or writing a workaround for a checker other than mypy. |
| `references/ruff.md` | The strict ruff configuration to recommend and why each setting is there, the rules that enforce the skill's rules, how to suppress a finding, and common commands. Read when the user sets up ruff or asks for stricter linting, and when deciding whether a finding applies. |
| `evals/run.sh` | Runs the suite: builds one tools environment (mypy, pytest, ruff) in `.eval-tools/`, where the agent's sandbox can read it, runs `claude plugin eval` with the flags the cases need, and deletes the environment on exit. |
| `evals/trigger-basic/` | The skill fires on a plain request for a Python function. Graded by `tool_used: Skill`. |
| `evals/no-trigger-typescript/` | A request for typed code in TypeScript must not fire the skill (`min: 0, max: 0, arm: both`). |
| `evals/silence-checker/` | The user says mypy is wrong about `return users.get(name)` and asks to make the error go away. The agent says the error is correct and fixes the code, with no `type: ignore`, `cast`, or `Any`. |
| `evals/generic-bound/` | `highest(items)` is called with three unrelated classes, and a caller reads a subclass attribute from the result. The agent writes a bound TypeVar, and mypy passes. |
| `evals/grow-tuple/` | Naming the fields of a public API's tuple return value uses a NamedTuple, so callers that unpack or index it keep working. |
| `evals/json-config/` | Loading a JSON config gives a TypedDict or dataclass, validates the decoded values instead of casting them, and has a parametrized test. |
| `evals/slugify-table-tests/` | A small pure function gets an annotated signature and a table test with an ID per row and annotated test functions, and the tests pass. |
| `evals/refactor-global-state/` | A monolithic, untyped module with mutable globals becomes separate parse, filter, aggregate, and format functions with I/O at the edge, no `global`, table tests, and a clean mypy run. |

Each eval case is a directory with a `prompt.md` (the user's message and run
settings) and graders under `graders/`. The behavior cases also have a
`case.yaml` that names a `fixture.sh`. That script builds the case's
workspace: a Python 3.12 project with `mypy --strict` and pytest behind
`make check`, and the case's starting files. Its `.venv` is a link to one
tools environment that `evals/run.sh` builds for the whole run, in
`.eval-tools/` next to `SKILL.md`. The
project-setup block is the same in every `fixture.sh` and is marked
`# shared: typed-python/eval-project`; `scripts/validate.py` fails if the
copies differ. Eval output lands in `evals/results/`, which is gitignored.

## Running the evals

From the repository root, in a shell that isn't sandboxed:

```bash
skills/typed-python/evals/run.sh
```

`run.sh` does the following, and passes its arguments to
`claude plugin eval`:

1. Stops if the shell can't start Claude Code's OS sandbox, which the eval
   uses for the agent's shell commands. Inside another sandbox, such as a
   sandboxed Claude Code session, every Bash command in the eval would fail
   with `sandbox_apply: Operation not permitted`.
2. Builds one Python 3.12 virtual environment with pinned versions of
   mypy, pytest, and ruff in `skills/typed-python/.eval-tools/`, with its
   own interpreter. The agent's sandbox denies reads from your home
   directory and from every temporary directory (`/tmp`, `/private/tmp`,
   `/var/tmp`, and your `$TMPDIR`), and allows writes only to the run's own
   directories. In both the with-skill and the baseline arm, it allows
   reads from each directory on `PATH` that is inside your home directory,
   but not from one inside a temporary directory. So the environment lives
   in the repository and goes on `PATH`: every run can read it, and none can
   change it. Bytecode is compiled at install time, so no run needs to write
   there. `.gitignore` lists `.eval-tools/`.
3. Puts the environment's `bin` directory first on `PATH`, and the
   environment's own directory after it, so that the sandbox allows reads
   from the interpreter and the installed packages too. The agent's session
   inherits `PATH`. Then it runs `claude plugin eval
   skills/typed-python --scaffold --judge-model sonnet --allow-tools Write
   Edit Bash` with your arguments. A `--judge-model` in your arguments
   overrides `sonnet`; the default Haiku judge is unreliable on rubrics with
   several conditions. `--scaffold` runs each case's `fixture.sh` as you. The
   harness runs it from its place in the repository, so the fixture finds
   the environment relative to its own path and links its workspace's
   `.venv` to it. `--allow-tools` lets the agent write files and run mypy,
   pytest, and ruff in its sandbox.
4. Deletes the environment when it exits, including after a failure or
   Ctrl-C. A second `run.sh` refuses to start while the first one's
   environment exists.

Each case runs three times with the skill and three times without it, and
the report shows the difference in score (`Δ`). Add `--case '<glob>'` to run
a subset, `--runs 1` to run each case once per arm, `--max-cost-usd 5` to
cap spend, and `--no-publish` to keep the report local. The `llm` graders
call a judge model and cost money; the `regex` and `tool_used` graders are
free. A `fixture.sh` run without `run.sh` stops with an error, so
`claude plugin eval` on its own can run only the two trigger cases.

Read the skill's effect from the behavior cases' `Δ`, not from the suite's
mean. `trigger-basic`'s `Δ` is always +1.00: its only grader checks that
the skill fired, which can't happen in the baseline arm, and the harness
scores that grader in both arms when a case has no other grader.
`no-trigger-typescript`'s `Δ` is always 0.

The eval harness has no grader that runs a command, so the graders can't
run mypy or pytest themselves. `checker-passed` and `tests-passed` read the
session trace for the output of the agent's own runs: mypy's
`Success: no issues found`, and a pytest summary with no failures. They show
that some run in the session passed, not that the last one did.

## Design notes

- **Policy in `SKILL.md`, examples in the reference.** Models already know
  what `TypedDict` and `TypeVar` are. What they don't do by default is apply
  them every time, pick the narrow type over `Any`, or refuse to silence a
  checker. `SKILL.md` states those decisions and the reason for each; the
  reference shows complete code for the cases where a model is most likely
  to produce a weaker version.
- **The private-function exemption is narrow on purpose.** mypy skips the
  body of a function with no annotations, so every unannotated function is
  unchecked code. The exemption covers only code small enough to read at a
  glance.
- **Workarounds have an order.** A one-line `cast` or `type: ignore[code]`
  keeps the precise type for every other caller. A wider parameter type or
  `Any` weakens checking at every call site, so they come last.
- **Local accumulation is allowed.** Building a list or dict inside a
  function and returning it is not observable mutation. Forbidding it would
  force comprehension chains that are harder to read, which conflicts with
  the readability goal.
- **The examples pass the checks that the skill recommends.** Every code
  block in `SKILL.md` and `references/examples.md` passes `mypy --strict`
  and the strict ruff configuration, and the tests pass. A skill whose own
  examples fail its checks teaches the agent to ignore them. When you edit
  an example, extract the blocks and run all three again.
- **Testing.** Run a prompt such as "write a function that parses this log
  format and summarizes errors per service" with and without the skill. The
  skill is working if the with-skill output has annotations on every public
  name, a dataclass or TypedDict instead of `dict[str, Any]`, separate parse,
  aggregate, and format functions, a parametrized table test, and a type
  checker run.
