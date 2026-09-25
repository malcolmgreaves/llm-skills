# Workflows: the stages of a task

Every task runs a workflow: a fixed sequence of agent stages in its lane's
worktree. This file explains the workflows, what each stage does, who makes
which decision, and how the coordinator runs the stages. The prompts
themselves are rendered by `plan.py prompt`; you never write one.

## Contents

- The workflows
- The stages
- Scope labels
- Owner-level decisions
- Running a stage
- Mutation testing
- Scratch space and cleanup
- Resolving a conflicted landing
- Reopening a lane
- Running a workflow with or without a workflow tool

## The workflows

The user picks a workflow for each task size at draft time, in
`plan.workflow`, and can change it for tasks that haven't started. The
defaults:

| Size | Default workflow | Why |
| --- | --- | --- |
| S | implement → review | One review-and-fix is enough for a small change. |
| M | implement → review → second_review | Medium and large tasks touch more code; the second reviewer checks the first review and owns simplicity, clarity, and fit. |
| L | implement → review → second_review | As M. The user may add `fix`. |

A workflow is `implement`, then `review`, then optionally `second_review`,
then optionally `fix`, in that order. `plan.py validate` refuses anything
else. Other kinds of task don't follow the size:

- `docs` and `plan` tasks run implement → review.
- `measurement` tasks run implement alone, and change no code.
- `chain: none` tasks get no lane: the coordinator does them itself (a seam,
  a plan edit).

A task with `escalate:` set runs the workflow of the next size up. The only
reasons are `untrusted-input`, `persistence`, `security`, `concurrency`, and
`breaking-interface` (a breaking change to an existing public interface);
`validate` refuses any other. A task that fits none of them runs its size's
workflow, however important it feels.

In the `delegate` coordinator mode, every workflow ends with a `delegate`
stage (see "Owner-level decisions" and `references/coordinator.md`).

Two stages run only when a landing conflicts, whatever the workflow:
`resolve`, then `resolution_review`. See "Resolving a conflicted landing".

## The stages

| Stage | Prompts | Job | Commits | Writes "As landed" |
| --- | --- | --- | --- | --- |
| implement | 1 | Do the task as specified; prove each defect red before fixing it; run mutations. | `<id>: implement` | measurement tasks only |
| review | 2: report, then fix | Part 1 finds and proves problems and commits the proof tests. Part 2 fixes the `spec` and `defect` findings and adds the missing tests. | `<id>: review proofs`, `<id>: review fixes` | when it is the last review |
| second_review | 2: report, then fix | Checks the first review's work, removes scope creep, and makes the change simple, clear, and a good fit for the existing code and the upcoming tasks. It may refactor. | `<id>: second review proofs`, `<id>: second review fixes` | yes |
| fix | 1 | Applies the decisions made after the reviews: accepted `beyond` items and the owner's answers. At autonomy 4 it makes the owner-level calls itself. | `<id>: fix` | yes |
| delegate | 1 | Does the coordinator's review, decisions, and fixes for this task, from a brief. | `<id>: coordinator review` | yes |
| resolve | 1 | Rebases a `conflicted` lane onto the integration branch and keeps both sides; adapts the lane to landed interface changes. The only stage allowed to rebase. | the rebased commits, `<id>: resolve` | no |
| resolution_review | 2: report, then fix | Checks only the resolve stage's work: both sides kept, nothing unrelated changed, all tests present. Doesn't judge the implementation or its reviews. | `<id>: resolution fixes` | no |

A review is one agent given two prompts. It reports every problem and
commits the proofs before it is told to fix anything, so a finding can't
quietly shrink to what is easy to fix. Each prompt writes its own report:
`<scratch>/<id>_<stage>-report.md` and `<scratch>/<id>_<stage>-fix.md`.

The `fix` stage runs only when there is something to apply: a decisions file
with accepted items, or, at autonomy 4, owner-level calls for it to make.
When a workflow includes `fix` and nothing was accepted, skip it.

Every stage ends with a commit on the lane branch (or none, if it changed
nothing), so the lane is clean between stages. Every stage writes its report
to a file, and reads the earlier reports from files.

## Scope labels

Reviewers label every finding. The label decides what happens to it:

| Label | Meaning | What happens |
| --- | --- | --- |
| `spec` | The work doesn't meet the specification or an acceptance criterion. | The review fixes it. |
| `defect` | A wrong result, a crash, or data loss, including in cases the specification doesn't address, with a small fix. | The review fixes it. |
| `creep` | Something beyond the specification that crept in. | The second review removes it. |
| `quality` | Simpler, clearer, or a better fit, with no change in behavior. | The second review makes the change. |
| `beyond` | A behavior change the specification doesn't ask for. | Reported, not changed. It is applied only if the coordinator (full mode), the user, or the delegate stage accepts it, by the fix stage or the delegate stage. |

## Owner-level decisions

An owner-level decision is a behavior the specification doesn't settle, or
a change to existing behavior it doesn't mention. Below autonomy 4 no agent
makes one: the stages list each under the heading "Needs owner", the
coordinator asks the user (in every coordinator mode) and sets the task to
`waiting`, and the answers go to the fix stage as decisions. At autonomy 4
nobody waits: one actor makes the calls and reports each under
"Owner-level decisions taken", with the question, the decision, and the
reason, so the owner can review them later.

| Autonomy 4, who decides | When |
| --- | --- |
| the `delegate` stage | the coordinator mode is `delegate` |
| the `fix` stage | the workflow includes `fix` |
| the coordinator | the coordinator mode is `full` |
| the last review's fix prompt | the coordinator mode is `merge` |

`plan.py findings graph.yaml <id>` prints every "Needs owner", "Owner-level
decisions taken", "Beyond", and "Residuals" item from the task's reports and
its decisions file. A task whose reports list "Needs owner" items doesn't land
until a decision is recorded under "Owner-level decisions taken", by a stage
or in the decisions file.

## Running a stage

```
plan.py prompt graph.yaml <id> <stage> [--part report|fix] [--decisions <file>] [--via agent|workflow]
```

It renders the stage's prompt from `assets/stage-templates.md` into the
lane's scratch directory, logs the stage's start with its model and effort,
and prints the model, the requested effort, and a launcher line. Launch a
background agent with the stage's model and the launcher line as its prompt.

For a review stage, launch the agent with `--part report`. When it returns,
render `--part fix` and send its launcher line to the same agent (in Claude
Code, with `SendMessage` to that agent); the agent still has the context of
its own findings. If the runtime can't message a finished agent, or the
session restarted, launch a new agent with the fix launcher: the prompt
names the report it must act on.

The user sets each stage's model and effort at draft time (`plan.models`,
`plan.effort`). The Agent tool in Claude Code sets a model but not an
effort: the session's effort applies, and `plan.py prompt` says so. Pass
`--via workflow` when the stage runs through a workflow tool that takes an
effort, so the log records the effort that was actually applied.

## Mutation testing

The implement stage runs the mutations the specification lists (or one per
new rule) and lists them in its report. One reviewer re-runs them:

- In a workflow with one review, the review re-runs them.
- In a workflow with a second review, the first review doesn't; the second
  review re-runs them after the first review's fixes.

## Scratch space and cleanup

Each lane has its own scratch directory, `<scratch_root>/<id>/`, which holds
its prompts, reports, decisions, brief, and saved patches. Each prompt has
its own temporary directory, `<scratch_root>/<id>/stage-<name>/`, and every
stage command runs with `TMPDIR` pointed there; nothing goes to `/tmp`. So
no two workflows, and no two stages, share a temporary file.

Cleanup is best effort, by `plan.py clean`:

- Closing, landing, or abandoning a lane runs `plan.py clean graph.yaml
  <id>`, which removes that lane's `stage-*` directories and keeps its
  reports.
- After the final report is written, `plan.py clean graph.yaml` removes the
  whole scratch root, except the patches of abandoned tasks.
- Removing a worktree removes its build directory.

## Resolving a conflicted landing

With `file_overlap` greater than 1 or `dependency_overlap` on, lanes run
together and the later ones conflict when they land. Before a landing
rebases, `lane land` checks with `git merge-tree` whether the rebase would
conflict. If it would, the printed command only sets the task to
`conflicted`, and no rebase starts. In the rare case that a rebase still
stops at a conflict, it stays in progress and the resolve stage continues it.
A gate that fails after a clean rebase, because landed work changed
something this lane uses, takes the same path.

1. `plan.py prompt graph.yaml <id> resolve` records where the lane stands
   and renders the resolve prompt. The resolve stage rebases, resolves each
   conflict so that both changes survive, adapts the lane to landed
   interface changes, runs the gates, and commits.
2. If every change stays in the conflicted hunks, or in the lines that use
   what the landed work changed, run the resolution review: `--part
   report`, then `--part fix` to the same agent. It sees exactly what
   resolving changed (a `git range-diff` of the lane before and after), and
   nothing else. Use a mid-tier model; it is shorter than a normal review.
3. If the fix needs more (new behavior, a redesign), the resolve stage makes
   the smallest resolution that lets the rebase finish, writes an "Escalate"
   section, and starts its final message with `ESCALATE:`. Run the fix
   stage with that section as its decisions, then the task's last review
   stage again, both parts.
4. Land again. Landing refuses until the prompts that step 2 or step 3
   requires have run after the resolve stage.

## Reopening a lane

When a gate fails at integration, or the user sends a lane back, run the fix
stage with the failure as its decisions file: the gate command, its output,
and one sentence on what to change. The fix stage runs whatever the
workflow. A lane is reopened at most twice; after the third failure the
coordinator abandons it (`references/coordinator.md`, "Giving up on a
task").

## Running a workflow with or without a workflow tool

**With a workflow tool.** A workflow can run as one background script whose
agents get the launcher lines. The two prompts of a review must reach the
same agent, so either send the fix prompt as a follow-up message to that
agent, or run the review as two agents (the fix agent reads the report).
Stop when a summary starts with `BLOCKED:`, and pass each stage's effort
when the tool accepts one.

**Without a workflow tool.** In Claude Code the `Workflow` tool runs only
when the user has asked for multi-agent orchestration. Otherwise run each
stage as one background subagent with its model, and send the review's fix
prompt with `SendMessage`. A `null` result means the runtime lost the
agent: rerun that stage. A summary that starts with `BLOCKED:` means the
task can't be done as specified (`references/coordinator.md`, "Giving up on
a task").
