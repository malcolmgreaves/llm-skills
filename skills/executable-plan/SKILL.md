---
name: executable-plan
description: >-
  Drafts an executable plan for a body of engineering work and executes it with
  many agents at once: a plan document (Markdown or HTML) with one anchored
  section per task, a graph.yaml of each task's dependencies, touched files,
  and status, and a coordinator that runs each ready task in its own git
  worktree lane through a sized workflow of agents (implement, then one or two
  review-and-fix passes), then integrates the result into the main branch.
  Use when the user asks to plan a backlog or a multi-task project as a
  dependency graph, run several planned tasks or plans in parallel with agents,
  use git worktrees as lanes, orchestrate many agents over a list of work
  items, turn a plan into something agents can execute, resume such a campaign
  from graph.yaml, or mentions an executable plan, a work graph, or a
  coordinator agent. Not for a single change, a single code review, or a build
  tool's task runner.
license: MPL-2.0
compatibility: Requires git 2.38 or later (worktrees, merge-tree), Python 3.11 with uv for scripts/plan.py, and an agent runtime that can run subagents in the background.
metadata:
  version: "0.2.0"
  author: malcolmgreaves
---

# Executable plan

This skill separates the machinery of running many agents from the work they
do. The work is a **plan document** with one section per task and a
**`graph.yaml`** that points at those sections and records dependencies,
touched files, and status. The machinery is a **coordinator** (you, in the
main session) that opens one git worktree per ready task, runs the task's
workflow of agents in it, lands the result on the main branch, and repeats
until the graph is done.

The skill has two modes. **Draft** produces the plan document and
`graph.yaml` through a short interview. **Execute** runs the graph. A session
can do both, or resume a plan that an earlier session drafted.

`scripts/plan.py` does every deterministic step: it validates the graph,
schedules, renders the stage prompts, prints the shell commands for a lane,
records timings, and writes the final report. It runs only read-only git;
every command that changes a repository is printed for you to run. In this
file and its references, `plan.py` means `uv run <this skill's
directory>/scripts/plan.py` (use the absolute path, since you run it from
the repository), and `graph.yaml` means the graph's path in the repository.
If `uv` can't write its cache (a sandbox), set `UV_CACHE_DIR` to a writable
directory, for example `UV_CACHE_DIR=$TMPDIR/uv-cache`.

## Vocabulary

- **Task**: one node of the graph: an id, a section in the plan document,
  dependencies, the files it is expected to change, a size, and a status.
- **Lane**: one task in flight: a git branch `<prefix><id>`, a worktree of
  that branch, a scratch directory, and the agents of its workflow.
- **Workflow**: the stages a task runs, picked by its size: implement, then
  a review-and-fix, then (for M and L) a second review-and-fix, then
  optionally a fix stage. See
  [references/workflows.md](references/workflows.md).
- **Coordinator**: the main session. It never implements. It schedules, asks
  the user, lands, and is the only writer of the plan document and
  `graph.yaml`. How much it reviews is the coordinator mode.
- **Integration branch**: the branch every lane starts from and lands on,
  usually `main`.

## Worktrees are the isolation

Each lane is a git worktree: its own checkout, branch, build directory, and
place to commit. Agents in different lanes can edit, build, and test at the
same time without touching each other, and each lane's work stays a branch
until it lands, so nothing half-done reaches `main`. Removing the worktree
removes its build output.

A worktree doesn't isolate everything, and the skill covers the rest:

- **Merges.** Two lanes that change the same file work in peace and
  conflict when they land. `files` controls that: `next` opens at most
  `file_overlap` lanes that list the same file or have already changed it.
  When a landing's rebase conflicts, the lane becomes `conflicted` and a
  resolve stage rebases it and keeps both sides.
- **Shared git state.** The stash, refs, and config are shared by every
  worktree, so nobody uses `git stash`, and each lane has its own branch.
- **Anything outside the repository.** Each lane gets its own scratch
  partition, and each stage its own temporary directory with `TMPDIR`
  pointed there. Nothing goes to `/tmp`.

## Mode 1: draft the plan

Ask before you write. Ask only what the repository doesn't already answer;
read its guideline files first.

**The project (goes into `graph.yaml: plan`):**

| Ask about | Field | Why it matters |
| --- | --- | --- |
| The commands to build, test, lint, and run | `commands`, `gates` | Every stage runs the gates; landing runs them again. |
| Style, design, and architecture guidelines | `guidelines` | Every agent reads them; the reviewers check against them. |
| Prior plans | `prior_plans` | Tasks cite them and inherit their decisions. |
| Scope and non-goals | plan document `## Scope` | The reviewers remove scope creep with a reference. |
| Requirements | each task's `Acceptance` | They become tests and measurements. |
| Where worktrees and scratch go, the lane cap, the branch prefix | `worktree_root`, `scratch_root`, `lane_cap`, `branch_prefix` | Put both roots next to the repository (`../<repo>-lanes/…`), or under `$TMPDIR` in a sandbox. The machine sets the cap. |
| The workflow for each size, and whether M and L end with a fix stage | `workflow` | Most of the cost. Show the defaults (`references/workflows.md`). |
| The model and effort for each stage | `models`, `effort` | The user's choice, always; nothing in the skill picks a model. Include `resolve` and `resolution_review` when overlap is on; recommend a mid-tier model for both. |
| How much lanes may overlap | `file_overlap`, `dependency_overlap` | Defaults: `file_overlap: 2`, `dependency_overlap: off`. Always explain every option (below). |
| The coordinator mode | `coordinator` | `full` (default), `merge`, or `delegate`: how much the coordinator reviews (`references/coordinator.md`). |
| Autonomy (0 to 4; recommend 2) | `autonomy` | When the coordinator stops for the user (table under Mode 2). The user names the level; never pick 4 for them. |
| Keep or squash lane commits | `commit_policy` | Keeping them keeps each stage's commit in the history. |

**The tasks (one section each in the plan document).** For each task, write:
the goal in one sentence; the specification (what changes, where, and the
behavior after the change); the acceptance criteria (tests, measurements,
gates); the files it is expected to change; its size (S, M, L); its hard and
soft dependencies; and every decision that only the owner can make, as a
question with the default you recommend. Look hard for those questions:
every place the backlog's wording allows two readings is one.

Size picks the workflow. Escalate a task one size up only for one of the
reasons `escalate` accepts (`untrusted-input`, `persistence`, `security`,
`concurrency`, `breaking-interface`); a task that fits none runs its size's
workflow, however important it feels.

Then write the two files side by side where the repository keeps plans (for
example `plans/<plan-name>/`; ask if there is no convention):

1. The plan document, from `assets/plan-template.md` or
   `assets/plan-template.html`. Each task section carries a stable anchor:
   in Markdown, a heading followed by the marker `<!-- task: <id> -->`; in
   HTML, `id="<id>"` on the heading. Never rename an anchor without changing
   the graph.
2. `graph.yaml`, from `assets/graph-template.yaml`. Read
   [references/graph-schema.md](references/graph-schema.md) for every field
   before you fill it in.

Run `plan.py validate graph.yaml` and fix every error. Then run `plan.py
waves graph.yaml`. It prints the dependency waves, the file exclusions, each
task's workflow, the agent count, and the time the real scheduler needs with
the lane cap and the exclusions, from this repository's measured stage
timings when it has them. It warns when the plan runs one lane at a time;
look for a seam (below) before you accept that. Its "overlap options"
section estimates the time of every overlap setting.

**Overlap.** Two settings let lanes run together that would otherwise wait,
at the cost of conflicts that a resolve stage fixes when a lane lands.
Always tell the user which settings the plan uses and explain each option,
including none, with its estimate from `waves`:

- `file_overlap` (default `2`): the most open lanes that can share one
  file. `off` (or `0`) never opens two lanes on the same file: no conflicts,
  and tasks that share a file run one at a time. `2` or more lets them run
  together; the second to land rebases onto the first, and a conflict costs
  a resolve stage and a resolution review.
- `dependency_overlap` (default `off`): `off` starts a task after its
  dependencies land. `interfaces` also starts it once a dependency listed in
  its `interface_deps` has started, when the specification fixes the
  interface it uses. `all` does that for every dependency. The task still
  lands after its dependencies; if a dependency lands with a different
  interface than its spec said, the lane pays for a resolve stage, or for a
  fix and a review when the difference is large.

Show the user, in one message: the plan, the `waves` output, the workflow for
each size with its models and effort, the overlap settings with every option
explained, the coordinator mode, the autonomy level, and every owner question
with your recommended default. Ask them to
approve or change any of it, and to name the autonomy level to start at.
Ask even when the user says they will be away: "don't block me mid-run" is
not "don't ask at all". Record answers with `plan.py set`, and iterate until
the user approves.

**Starting execution.** Execution starts only with the user's explicit
approval, at the autonomy level the user names. Never start on your own, and
never choose autonomy 4 for the user: "I won't be around" is neither
approval nor autonomy 4. If the user is unavailable and hasn't approved, stop
after the draft and wait. The approval can come after the draft ("approved,
start at autonomy 2") or in advance ("finish the draft, commit, then start at
autonomy 3"); with advance approval, start right after the draft. Record it
with `plan.py approve graph.yaml --autonomy <N> --quote "<the user's
words>"`, then commit the plan document and `graph.yaml` on the integration
branch; execution starts from that commit. `lane open` refuses until an
approval is recorded.

Derive the edges honestly:

- A **hard dependency** means the task needs the other's result to be
  correct: `deps`.
- A **soft dependency** means the order improves quality but not
  correctness: `soft_deps`. The task doesn't start while one is running or
  starting, but it doesn't wait for one that can't start yet.
- **Expected files** are a scheduling hint, not a fence: at most
  `file_overlap` open lanes list the same file. Agents may change any file
  the work needs and report the unexpected ones.
- An **interface dependency** is a hard dependency whose specification fixes
  the interface the task uses (a function signature, an output format): list
  it in `interface_deps` too, so `dependency_overlap: interfaces` can start
  the task early. Set `alone: true` on a task that
  touches everything; a `measurement` task runs alone by default.
- An **owner decision** is a question in `owner_decisions`, with your
  recommended default. Below autonomy 4 the task waits for the answer.

**Seams.** Tasks that all edit one file (a CLI entry point, a router, a
schema) run one at a time, because file exclusion serializes them. A seam is
a small task, usually `chain: none` so you do it yourself on the integration
branch, that moves the shared structure out of the way: it gives each task
its own file to write (one module per flag, a handler per route, a test file
per task) and leaves only a line or two in the shared file, which the seam
writes itself. The tasks then list only their own files and run in parallel.
A seam that leaves every task editing the shared file changes nothing.

A chain of dependencies serializes a plan too, and no seam helps with that.
`waves` says which cause applies. When the dependencies form a chain, check
each one: often the later task needs only part of the earlier task's
result. Move that part into a small task of its own that depends on both,
and the rest of the later task can start earlier. For example, a `--top`
flag that must also appear in the `--json` output depends on the JSON task
only for that combination; the combination can be its own task.

## Mode 2: execute the plan

Read [references/coordinator.md](references/coordinator.md) before the first
iteration: it has the pre-flight checks, the coordinator modes, owner
decisions, landing, the conflict rules, resuming, and the end of a campaign.
Read [references/workflows.md](references/workflows.md) before the first
stage: it has the stages, the two-prompt reviews, the scope labels, and who
decides what. One iteration:

1. `plan.py next graph.yaml` prints `START` for each task that can open now,
   with its workflow, and `HOLD` with the reason for every other one.
2. For each `START`: `plan.py lane graph.yaml <id> open` prints one command
   that creates the worktree, the branch, and the scratch directory, records
   `running`, and renders the implement prompt. Run it, and launch the
   implement stage in the background with its model and the printed
   launcher line. Every lane command is one `&&` chain that stops at its
   first failure.
3. When a stage returns, render the next stage of the task's workflow with
   `plan.py prompt` and launch it. A review is one agent given two prompts:
   `--part report`, then `--part fix` to the same agent. Never write a stage
   prompt yourself.
4. When the workflow's last stage returns, run `plan.py findings graph.yaml
   <id>`. Owner-level items go to the user below autonomy 4 (the task waits
   in `waiting`). In `full` mode you also decide the "Beyond" items. Record
   every owner-level decision, whoever made it, under "Owner-level decisions
   taken" in the task's decisions file; landing refuses until you do.
   Accepted items and owner answers go to the fix stage; with none, skip it.
5. `plan.py set graph.yaml <id> status=integrating`, then `plan.py lane
   graph.yaml <id> land`. It refuses a lane that isn't ready and says why,
   including a lane whose dependencies haven't landed. Otherwise it prints
   one command that rebases the lane, runs every gate, lands it on the
   integration branch, removes the worktree and the branch, cleans the
   lane's temporary files, applies the "As landed" text to the plan
   document, and commits the plan. Go to step 1.
6. If the rebase would conflict, `land` prints a command that only marks
   the lane `conflicted`, and no rebase starts. Run the resolve stage (`plan.py prompt ... resolve`), then
   the resolution review (two prompts, like any review), and land again.
   If the resolve stage escalates because the fix goes beyond the conflicted
   hunks, run the fix stage with its escalation as the decisions, then the
   task's last review stage, and land again.

Run `plan.py set`, `plan.py prompt`, and the lane commands one at a time,
never as parallel tool calls; launching agents in parallel is fine. When
`next` prints `FINISHED`, run `plan.py report graph.yaml`, commit the report
it writes, and run `plan.py clean graph.yaml`.

**Autonomy levels.** `plan.autonomy` sets when the coordinator stops and
waits for the user. Each level includes the stops of the levels above it.

| Level | The coordinator stops for |
| --- | --- |
| 4, autonomous | Nothing. Owner-level calls are made in the workflow and reported in full. Only when the user chose it. |
| 3, decisions | Every owner-level decision, and any destructive action outside the protocol. |
| 2, default | Level 3, plus a P1 finding in a review's report, before the fix prompt is sent. |
| 1, findings | Level 2, plus every P2 finding. |
| 0, full control | Level 1, plus a confirmation before each lane opens and each landing. |

When the coordinator stops, it states the question in one sentence with its
recommendation, and it keeps every other lane running.

## Output of each mode

**Draft** ends with the plan document, `graph.yaml`, the output of
`validate` and `waves`, and the user's answers. **Execute** ends with
`report.md` from `plan.py report`: each task's commit and workflow, each
stage's model, effort, and duration, every owner-level decision taken, the
"Beyond" items and residuals, and each blocked task.

## Edge cases

- **The repository already has a plan.** Keep its identifiers as task ids,
  and write the plan document as a thin layer that cites it section by
  section. Don't duplicate a spec that exists; anchor to it.
- **A task has no tests to prove it (docs, a plan).** Set `kind: docs` (or
  `plan`); it runs implement, then one review, and the gates are the
  repository's doc checks.
- **A task can't be done.** The implement stage reports `BLOCKED:`, or a gate
  fails at landing a third time. `plan.py lane graph.yaml <id> abandon`
  saves the lane's work as a patch, keeps its commits on `abandoned/<id>`,
  and sets the task `blocked`; its dependents wait and the rest continues.
  Below autonomy 4, stop for the user with a recommendation.
- **An agent returns nothing** (a runtime error). Rerun that stage with the
  same prompt; don't invent its report.
- **The user changes the plan mid-run.** Edit the plan document and
  `graph.yaml` on the integration branch, run `validate`, and continue.
  Running lanes finish against their original spec; a new workflow, model,
  or coordinator mode applies to tasks that haven't started.
- **The user changes a setting mid-run** (`file_overlap`,
  `dependency_overlap`, `lane_cap`, `coordinator`, `autonomy`). Show them `plan.py
  preview graph.yaml <key>=<value> ...`, which compares the current and the
  proposed schedule, time, and workflows. After they approve, stop launching
  stages, wait for the stages in flight to return (the barrier), and run
  `plan.py configure graph.yaml <key>=<value> ...`, which refuses while any
  stage is in flight and records the change in the plan. Then resume.
- **A resumed session.** Start with `plan.py render graph.yaml`, then follow
  the resume table in `references/coordinator.md`. Every status, stage
  start, and report is on disk.
