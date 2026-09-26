# The cells benchmark

This benchmark compares the executable-plan skill with a plain agent on one
backlog, under the same time limit. Every arm starts from the same small
spreadsheet engine, `cells`, and implements the same ten tasks. Hidden tests
score whatever is in each arm's checkout when its time runs out.

`claude plugin eval` can't run this benchmark: it has no grader that runs
code, it runs two arms for each case, and its sandbox blocks the directory next to
the repository that the skill uses for lanes. So the benchmark has its own
runner.

## Run it

```sh
cd skills/executable-plan/benchmark
python3 run.py --out /tmp/cells-run-1
```

The runner starts all five arms together, stops them all at once after 30
minutes at most, and then runs `score.py`, which writes `report.md` and
`scores.json` in the output directory. `--out` must be a new directory
outside this repository, so that the hidden tests and the reference
implementation aren't in any arm's directories. The arms run without a
sandbox, so an arm that searched the disk could still find them. `run.py
--help` lists the options: `--arms`, `--cap-minutes`, `--budget-usd`,
`--claude`, `--disable-user-plugins`, `--dry-run`, and `--no-score`.

Requirements:

- The `claude` CLI, signed in. Each arm is one `claude -p` session.
- `uv`, which runs pytest for the hidden tests. The first run downloads
  pytest.
- git 2.38 or later, which the skill requires.
- Python 3.12.

Each arm loads the plugins that your Claude Code settings enable, and their
hooks and skills apply to every arm. A safety hook that refuses
`git worktree remove --force`, or `rm -rf` outside the working directory,
refuses commands that the skill's lane protocol prints, so it slows the
"with" arms more than the others. `--disable-user-plugins` turns off, in each
arm's project settings, every plugin that `~/.claude/settings.json` enables.
The report's Environment table shows the plugins that each arm loaded and
the commands that hooks refused.

The "with" arms might not finish all ten tasks in 30 minutes. With this
backlog, the skill's own `plan.py waves` estimates 21 to 32 minutes of
execution if every task is sized S, before the draft and any conflict, and
more if tasks are sized M. The per-task scores and the progress table count
partial work, so a run still shows how far each arm got.

A full run takes about 30 minutes for the arms and 5 to 15 minutes of
scoring. Based on earlier tests, it costs about $70-110: about $20-30 for
each "with" arm and $5-10 for each "without" arm. Each arm stops at
`--budget-usd` (default $40).

## The arms

| Arm | Skill | Subagents | Settings |
| --- | --- | --- | --- |
| `without-solo` | no | no | One agent does everything. |
| `without-free` | no | yes | The agent can start subagents: Sonnet to implement, Opus to review. |
| `with-default` | yes | yes | `file_overlap 2`, `dependency_overlap off`, coordinator `full` |
| `with-overlap` | yes | yes | `file_overlap 4`, `dependency_overlap interfaces`, coordinator `full` |
| `with-delegate` | yes | yes | `file_overlap 2`, `dependency_overlap off`, coordinator `delegate` |

Every arm runs on Sonnet at effort `medium`, with the same budget cap, the same
tools apart from subagents, and the same prompt apart from one block. The
shared prompt names the deadline, to the second, and says that only the
checkout's files count. It also says the user isn't available, and asks the
agent to list its decisions and open questions at the end. `without-free`
adds a block that allows subagents: Sonnet to implement, Opus to review. The
"with" arms add a block with the draft settings (Sonnet implements, Opus
reviews, `lane_cap 6`, and the arm's overlap and coordinator settings) and
the user's approval in advance to start at autonomy level 4. `run.py` holds
the exact text, and each arm's `prompt.txt` records it. The "with" arms get
the skill without its `README.md` and without this benchmark.

## The backlog

`cells/fixture/` is the starting repository: about 500 lines of Python with a
formula parser, an evaluator, a function registry, a `Sheet` class, a CLI,
and 27 tests. `BACKLOG.md` holds ten tasks in two layers:

| Layer | Tasks | Depends on |
| --- | --- | --- |
| 1 | `ranges`, `errors`, `logic`, `text`, `csvio`, `recalc` | nothing |
| 2 | `aggregates` | `ranges`, `errors` |
| 2 | `lookup` | `ranges`, `logic`, `errors` |
| 2 | `fill` | `ranges`, `errors` |
| 2 | `cli` | `csvio` |

Both a plain agent and the skill face the same interactions between tasks:

- **Shared files.** `ranges`, `logic`, `text`, and `fill` all change the
  lexer and the parser, and most tasks change `README.md`.
- **Rules that cross tasks.** Every function must follow the error rules.
  Cached values must update through ranges, fills, and file loads.
  Comparisons and `&` have to take their places in one precedence table.
- **One registry.** `ranges` and `errors` each add an option to the function
  decorator that later tasks use.
- **Work that is hard to get right.** Recalculation must evaluate a
  10,000-cell chain without recursion errors and within a time limit. Fill has to move
  references past column Z and leave text literals alone.

The starting code has three planted defects that its own tests miss. An
example in `README.md` exposes each one, and the backlog's examples lead to
them:

- Column `AA` parses as column 1 instead of 27.
- `ROUND` rounds halves to even instead of away from zero.
- Numbers display with 6 significant digits instead of 15.

The backlog also leaves two questions open, on purpose, and the hidden tests
avoid both:

- What happens when a count or position argument, such as `LEFT`'s count, isn't
  a whole number?
- Is content with spaces around a number, such as `" 12 "`, a number or text?

## Scoring

`score.py` produces these measures:

- **Hidden tests.** 120 tests in `cells/hidden/`: one file for the existing
  behavior, one for each task, and one for behavior that needs several tasks.
  Each test names, in a `spec:` comment, the README section or backlog rule
  it checks, and uses only interfaces that the documents require. Each file
  runs in its own pytest process, with a 30-second limit for each test and
  10 minutes for the file. A file that runs out of time counts all its tests
  as failed, and the report says so.
- **Progress.** The runner copies each arm's checkout every 5 minutes, and
  the report shows how many hidden tests each copy passes.
- **The arm's own tests.** Whether `python3 -m unittest` passes, and how many
  tests the arm has.
- **Mutation score.** 40 mutants of the arm's own `cells` package, chosen by
  a fixed seed: swapped arithmetic operators and comparisons, `and` and `or`
  swapped, `not` removed, flipped booleans, and integer constants plus one.
  The score is the fraction of mutants that make the arm's own tests fail.
  The scorer tests one arm at a time, so that a timing test in an arm's own
  suite doesn't fail from load alone. Arms write different code, so the
  mutants differ from arm to arm; compare the scores as rough measures.
- **Ambiguities raised.** Haiku reads the final message, plus every Markdown
  or HTML file that the arm added to the repository (the skill's plan and
  report, or an agent's notes), and says whether each open question was
  raised. An arm that the cap stops has no final message, so its plan is
  what the judge reads.
- **Process.** When the arm ended, and why. Also its minutes, cost, number of
  subagents, commits and merge commits, uncommitted files, and leftover
  worktrees, branches, and lane directories. For the "with" arms, the report
  also shows task statuses and conflicted landings from `graph.yaml`.
- **Environment.** From each session's first event: the Claude Code version,
  whether the executable-plan skill loaded, the plugins, and the tool calls
  that hooks or permissions refused. The report warns when a "without" arm
  loaded the skill, a "with" arm didn't, or an arm didn't start.

The correctness score counts only the files in the arm's checkout. Linear
history, cleanup, and similar process measures are reported separately.

## Keep the benchmark fair

- **Traceable tests.** Every hidden test must trace to a sentence in
  `README.md` or `BACKLOG.md`. A test that needs a behavior no document
  states doesn't belong in the benchmark.
- **Rerun after changes.** If you change the backlog or the tests after
  seeing results, rerun every arm.
- **Validate against the reference.** After changing the hidden tests, check
  that `cells/reference/` still passes all of them:

  ```sh
  CELLS_REPO=$PWD/cells/reference uv run --no-project --with pytest \
    python -m pytest cells/hidden -q -p no:cacheprovider
  ```

- **Check the starting code.** `cells/fixture/` must pass only
  `test_existing.py`, apart from its three planted-defect tests.

## Files

| Path | Purpose |
| --- | --- |
| `run.py` | Sets up the arms, runs them in parallel with the cap, takes snapshots, then scores. |
| `score.py` | Runs the hidden tests on every snapshot, runs the arms' own tests and mutation tests, reads the sessions and repositories, asks the judge, and writes the report. |
| `cells/fixture/` | The starting repository each arm receives: the `cells` package, its tests, `README.md`, `CLAUDE.md`, and `BACKLOG.md`. |
| `cells/reference/` | A complete implementation of the backlog that passes every hidden test. The runner never gives it to an arm. |
| `cells/hidden/` | The hidden tests and their `conftest.py`. |
