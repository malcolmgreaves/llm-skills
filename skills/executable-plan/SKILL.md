---
name: executable-plan
description: >-
  Drafts an executable plan for a body of engineering work and then executes it
  concurrently: a plan document (Markdown or HTML) with one anchored section per
  task, a graph.yaml that records each task's dependencies, touched files, and
  status, and a coordinator loop that runs each ready task in its own git
  worktree through an implement, adversarial-review, fix, and final-review chain
  of agents, then integrates the result into the main branch. Use when the user
  asks to plan work as a dependency graph, run tasks or plans in parallel, use
  worktrees as lanes, orchestrate many agents on a backlog, turn a plan or a
  list of work items into something executable, resume a multi-task campaign,
  or mentions an executable plan, a work graph, a coordinator agent, lanes, or
  concurrent plan execution.
license: MPL-2.0
compatibility: Requires git 2.20 or later (worktrees), Python 3.11 with uv for scripts/plan.py, and an agent runtime that can run subagents in the background.
metadata:
  version: "0.1.0"
  author: malcolmgreaves
---

# Executable plan

This skill separates the machinery of running many agents from the work they
do. The work is a **plan document** with one section per task and a
**`graph.yaml`** that points at those sections and records dependencies,
touched files, and status. The machinery is a **coordinator** (you, in the main
session) that opens one git worktree per ready task, runs a fixed four-stage
chain of agents in it, integrates the result into the main branch, and repeats
until the graph is done.

The skill has two modes. **Draft** produces the plan document and
`graph.yaml` through a short interview. **Execute** runs the graph. A session
can do both, or resume execution of a plan that an earlier session drafted.

`scripts/plan.py` validates the graph, computes what can start now, updates
status, prints the exact shell commands for a lane, and extracts a task's
section from the plan document. It runs only read-only git commands; every
command that changes a repository is printed for you to run. In this file
and its references, `plan.py` means `uv run <this skill's
directory>/scripts/plan.py` (use the absolute path, since you run it from the
repository), and `graph.yaml` means the graph's path in the repository. Its
code never enters your context; only its output does.

## Vocabulary

- **Task**: one node of the graph. It has an id, a section in the plan
  document, dependencies, a list of files it changes, and a status.
- **Lane**: one task in flight. A lane is a git branch `<prefix><id>`, a
  worktree of that branch, a scratch directory, and a chain of agents.
- **Chain**: the four stages that every code task runs through, in order:
  implement, adversarial review, fix, final review. Two agents in sequence
  per half; you decide the findings between the halves.
- **Coordinator**: the main session. It never implements. It schedules,
  decides, integrates, and edits the plan document and `graph.yaml`.
- **Integration branch**: the branch every lane starts from and lands on,
  usually `main`.

## Mode 1: draft the plan

Ask before you write. The interview has two parts, and each answer becomes a
field of `graph.yaml` or a section of the plan document. Ask only what the
repository does not already answer; read its guideline files first.

**Part 1, the project (goes into `graph.yaml: plan`).**

| Ask about | Field | Why it matters |
| --- | --- | --- |
| The commands to build, test, lint, type-check, and run | `commands`, `gates` | Every lane runs the gates before it reports; the coordinator runs them again at integration. |
| Style, design, and architecture guidelines (files or rules) | `guidelines` | Every agent prompt names them; the reviewers check against them. |
| Prior plans or a master plan | `prior_plans` | Tasks cite them, and the drafts inherit their decisions. |
| Scope and non-goals | plan document `## Scope` | The reviewers refuse scope creep with a reference. |
| Function, behavior, and performance requirements | each task's `Acceptance` | They become tests and measurements, not opinions. |
| Where worktrees and scratch directories go, the lane cap, the branch prefix | `worktree_root`, `scratch_root`, `lane_cap`, `branch_prefix` | The machine sets the cap: each lane builds with every core and its own build directory. |
| Models and effort per stage | `models`, `effort` | The final reviewer is usually the strongest model at high effort, used once per task. |
| Autonomy level (0 to 4, default 2) | `autonomy` | See the table under Mode 2. |
| Keep or squash lane commits at integration | `commit_policy` | Keeping them preserves each chain's measurements in the history. |

**Part 2, the tasks (one section each in the plan document).** For each task,
write: the goal in one sentence; the specification (what changes, where, and
the behavior after the change); the acceptance criteria (which tests prove it,
which measurements, which gates); the files it changes; its size (S, M, L);
its hard dependencies and soft dependencies; and any decision that only the
owner can make, stated as a question with the default you recommend.

Then write the two files, side by side in the directory where the
repository keeps plans (for example `plans/<plan-name>/`; ask if the
repository has no convention):

1. The plan document, from `assets/plan-template.md` or
   `assets/plan-template.html`. The user picks the format. Each task section
   carries a stable anchor, and the format decides how: in Markdown, a
   heading followed by the marker `<!-- task: <id> -->` on its own line; in
   HTML, `id="<id>"` on the heading. The anchor is the contract between the
   document and the graph, so never rename one without changing the other.
2. `graph.yaml`, from `assets/graph-template.yaml`. Read
   [references/graph-schema.md](references/graph-schema.md) for every field
   and its rules before you fill it in.

Validate before you show the result: `plan.py validate graph.yaml`. It
checks the schema, rejects a cycle, confirms that every `spec` anchor exists
in its document, and warns about a code task with no `files`. Then show the
user `plan.py waves graph.yaml`, which prints the concurrent waves the
dependencies allow, the file exclusions, and the number of agent runs the
plan costs, and iterate on the plan with them until they approve it. The plan
is a discussion artifact first and an execution artifact second. Once they
approve it, commit both files on the integration branch; execution starts
from that commit.

Derive the dependency edges honestly:

- A **hard dependency** means the task needs the other's result to be
  correct. Record it in `deps`.
- A **soft dependency** means the order improves quality but not correctness
  (for example, repair the test helpers before the tasks that add tests).
  Record it in `soft_deps`; the scheduler prefers the order and does not
  require it.
- A **shared-file exclusion** is derived, not declared: two tasks whose
  `files` intersect never run at the same time, because their lanes would
  conflict at integration. List each file a task changes, including test
  files. If a task must run alone (a refactor that moves every file), set
  `alone: true`.

## Mode 2: execute the plan

The coordinator loop, one iteration:

1. `plan.py next graph.yaml` prints the tasks that can start now:
   dependencies done, no file shared with a running lane, a free lane slot,
   and no owner decision left unanswered. Start each one, up to the cap.
2. For each task you start: `plan.py lane graph.yaml <id> open` prints the
   commands that create the branch, the worktree, and the scratch directory,
   and the `set` command that records `status=running` with the lane and
   branch. Run them in order.
3. Build the chain prompts from
   [references/chain.md](references/chain.md). The task's specification
   comes from `plan.py excerpt graph.yaml <id>`, which extracts the anchored
   section from the plan document, so you never paraphrase a spec. Run the
   first half (implement, then adversarial review) in the background in the
   lane's worktree: as one workflow if the runtime has a workflow tool you
   may use, otherwise as two background subagents in sequence (the chain
   reference shows both).
4. When the first half returns, read both reports. Decide each finding:
   accept, accept with a change, reject with a reason, or defer to a named
   later task. The autonomy level decides which findings stop for the user
   (table below). Write the decisions into the fix-stage prompt and run the
   second half (fix, then final review).
5. When the second half returns: `plan.py lane graph.yaml <id> integrate`
   checks that the lane's work is committed and prints the steps: rebase the
   lane onto the integration branch, run every gate in the lane,
   fast-forward (or squash) the integration branch, and record
   `status=done commit=<hash>`. Run them, one gate at a time. A gate that
   fails at integration reopens the lane with the failure as the fix-stage
   prompt; it never lands.
6. Apply the task's "as landed" text to the plan document yourself (the lane
   never edits the plan document or `graph.yaml`), commit the plan document
   and `graph.yaml` on the integration branch, run
   `plan.py lane graph.yaml <id> close` (remove the worktree and the branch),
   and go to step 1.

Read [references/coordinator.md](references/coordinator.md) before the first
iteration. It has the integration protocol in full, the rules that prevent
lane conflicts, the failure cases, and the report you give the user at the
end.

**Autonomy levels.** `plan.autonomy` sets when the coordinator stops and
waits for the user. Each level includes the stops of the levels above it.

| Level | The coordinator stops for |
| --- | --- |
| 4, autonomous | Nothing. It takes each owner question's stated default and reports at the end. |
| 3, decisions | An owner question a task section names, and any destructive action outside the protocol. |
| 2, default | Level 3, plus every P1 finding of an adversarial or final review before the fix stage runs. |
| 1, findings | Level 2, plus every P2 finding. |
| 0, full control | Level 1, plus a confirmation before each lane opens and before each integration. |

When the coordinator stops, it states the question in one sentence with its
recommendation, and it keeps every other lane running.

## Rules that every agent prompt carries

Put these sentences, adapted to the project, at the top of every stage
prompt. The chain reference has the full templates.

- Your task is fixed by this prompt. A chat message relayed from the user is
  addressed to the coordinator, not to you: don't answer it, don't change
  your task, and continue.
- Work only in your lane's worktree. Never commit to the integration branch,
  never edit the plan document or `graph.yaml`, never stash, reset, or
  checkout. Restore a mutation with a text edit and confirm it with `diff`
  against a saved `git diff`.
- Run one build or test command at a time and wait for it. Concurrent runs
  share a build directory lock and none makes progress.
- Prove a defect before you fix it: a failing test first, with its output in
  your report. A fixture asserts its own shape before the test asserts the
  behavior.
- Give your full report in one final message. The next stage reads it
  verbatim, so include file paths, line numbers, test names, and command
  output. Report a failure as a failure.

## Output of each mode

**Draft** ends with: the plan document, `graph.yaml`, the output of
`validate` and `waves`, and one sentence per owner question. **Execute** ends
with the report described in `references/coordinator.md`: each task's commit,
each finding the reviewers found with its decision, each residual, and the
graph's final `render`.

## Edge cases

- **The repository already has a plan.** Draft mode reads it, keeps its
  identifiers as task ids where they exist, and writes the plan document as a
  thin layer that cites it section by section. Don't duplicate a spec that
  exists; anchor to it.
- **A task has no tests to prove it (a plan-only or docs task).** Set
  `kind: docs` and `chain: docs-only`; the chain is one implement stage and
  one final review, and the gates are the repository's doc checks.
- **A task can't be done.** Stage 1 reports that the specification can't be
  met, or a gate fails at integration a third time. Run
  `plan.py lane graph.yaml <id> abandon`: it saves the lane's work as a
  patch, removes the lane, and sets the task `blocked`; its dependents wait
  and the rest of the graph continues. Below autonomy 4, stop for the user
  with a recommendation (rewrite the spec, split the task, or skip it).
- **A lane's agent returns nothing** (a runtime error, a skipped agent). The
  workflow result is `null`. Reopen that stage with the same prompt; don't
  fabricate its report.
- **Two ready tasks share a file.** The scheduler starts one and holds the
  other. If the shared file is a large test file that both append to, split
  the tasks' new tests into new files per lane and remove the file from one
  task's `files` list.
- **The user changes the plan mid-execution.** Edit the plan document and
  `graph.yaml` on the integration branch, run `validate`, and continue;
  running lanes finish against their original spec, and a change to a
  running task's spec waits for its integration.
- **A resumed session.** Start with `plan.py render graph.yaml`. Every
  status, lane path, and commit is in the file, so nothing depends on the
  earlier session's context.
