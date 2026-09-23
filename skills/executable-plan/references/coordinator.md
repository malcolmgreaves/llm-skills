# The coordinator

The coordinator is the main session. It never implements a task. It
schedules lanes, decides review findings, integrates results into the
integration branch, and keeps the plan document and `graph.yaml` true. This
file is its procedure. As in `SKILL.md`, `plan.py` means
`uv run <this skill's directory>/scripts/plan.py`, and `graph.yaml` means the
graph's path in the repository.

## Before the first iteration

1. `plan.py validate graph.yaml`. Fix every error.
2. `plan.py render graph.yaml`. Confirm the statuses match
   the repository (a resumed session finds tasks `running` whose lanes still
   exist, or `done` tasks whose commits are on the branch).
3. Check the machine: free disk (each lane's build directory grows; a Rust
   `target/` can pass 100 GB in a day), free memory (each lane's test suite
   runs with every core), and the lane cap. Lower the cap before you open a
   lane you cannot afford.
4. Confirm the model ids work: run one trivial agent per model id. A rejected
   id fails at launch, which is cheaper than a failed chain.
5. Confirm the integration branch is checked out in the main worktree,
   clean, and up to date. Uncommitted work belongs on a lane branch as a WIP
   commit, or it is lost to the first rebase.
6. Confirm the plan document and `graph.yaml` are committed on the
   integration branch. Lanes branch from it, and the coordinator's
   integration commits edit both files; an uncommitted plan has no history
   to resume from.

## One iteration

```
next = plan.py next graph.yaml
for each task in next (up to the free slots):
    plan.py lane graph.yaml <id> open       # prints the commands; run them
    plan.py set graph.yaml <id> status=running lane=<path> branch=<branch>
    spec = plan.py excerpt graph.yaml <id>
    launch half 1 (implement, adversarial review) in the background
when a half-1 workflow returns:
    save its two reports to the lane's scratch directory
    if stage 1 reported a blocker: see "Giving up on a task"
    decide each finding (see below); stop for the user per the autonomy level
    plan.py set graph.yaml <id> status=review
    launch half 2 (fix, final review) with the decisions
when a half-2 workflow returns:
    save its two reports
    plan.py set graph.yaml <id> status=integrating
    plan.py lane graph.yaml <id> integrate  # prints the steps; run them one at a time
    on success: apply the "as landed" text to the plan document,
                plan.py set graph.yaml <id> status=done commit=<hash>,
                commit the plan document and graph.yaml on the integration branch,
                plan.py lane graph.yaml <id> close
    on a gate failure: reopen the lane with the failure as the fix prompt
                       (at most twice; then see "Giving up on a task")
when a measurement task's stage 1 returns:
    save its report, paste its "as landed" text into the plan document,
    plan.py set graph.yaml <id> status=done, commit the plan document and
    graph.yaml, plan.py lane graph.yaml <id> close
```

A task with `chain: none` gets no lane: do it yourself on the integration
branch (a plan edit, a merge of two tasks), commit, and set it `done` with
that commit.

Between events, do the work that depends on nothing: draft the next task's
prompts, prepare the plan-document edits for a task that is about to land
(dry-run them on a copy), and refresh the render for the user.

## Deciding findings

Read the implement report first, then the adversarial report. For each
finding, in number order, write one of:

- **Accept.** The fix stage applies the recommended fix.
- **Accept with a change.** State the change in one or two sentences.
- **Reject.** State the reason, and tell the fix stage to remove the proof
  test if it pins the rejected behavior.
- **Defer to task `<id>`.** Add the dependency or a new node to `graph.yaml`,
  and tell the fix stage to leave the proof as an ignored test that names the
  task.

Two rules from experience:

- A bound, a guard, or a rule that you mandate must be proven to fire: the
  fix stage adds the test that fails without it. A mandated guard that no
  test can catch is a tautology; drop it rather than ship dead code.
- A finding the reviewer labeled a suspicion is not a decision item. Ask the
  fix stage to measure it if it is cheap; otherwise record it as a residual.

## Integration protocol

One lane at a time; the gate run is the serialization point.

`plan.py lane graph.yaml <id> integrate` first checks that the lane has no
uncommitted changes, that its branch has commits beyond the integration
branch, and that the main worktree is on the integration branch. It refuses
and prints the reason otherwise; a lane that fails the check never lands.
The usual cause is a stage that didn't commit: read the lane's `git status`
and the last stage's report before you commit anything on its behalf.

1. In the lane worktree: `git rebase <integration_branch>`. A conflict here
   means the exclusion rule missed a shared file; resolve it in the lane, add
   the file to both tasks' `files`, and note it.
2. Run every gate in the lane, one at a time, on the rebased tree. A lane
   already ran them, so this is a confirmation after the rebase, but never
   skip it.
3. In the main worktree: `git merge --ff-only <lane_branch>` (`keep`), or
   `git merge --squash <lane_branch>` and one commit (`squash`). Never a
   merge commit: each lane starts from the integration branch and rebases
   onto it, so the history stays linear.
4. Apply the task's "as landed" text to the plan document and set the task's
   fields in `graph.yaml`; commit both on the integration branch as one
   commit whose message names the task and its code commit.
5. `plan.py lane graph.yaml <id> close`: remove the worktree, delete the lane
   branch (`-D` under `squash`, because a squash merge doesn't mark the
   branch merged), clear the node's `lane` and `branch`, and clean the lane's
   build directory. `close` refuses a task that isn't `done`.

A gate that fails at step 2 is a real failure, not noise: the lane's own gate
run passed on an older base, so the rebase changed behavior. Reopen the lane
with the failure output as the fix-stage prompt, run stage 3 and stage 4
again, and integrate again.

## Rules that prevent lane conflicts

- A lane touches code alone. The plan document and `graph.yaml` are the
  coordinator's, and the coordinator edits them serially at integration. This
  removes every tracker conflict.
- New tests go into new files per lane. Two lanes that append to the end of
  one test file always conflict at integration; two new files never do. When
  a task's `files` lists a large shared test file, split its new tests into
  a new file and drop the shared file from `files`.
- A task lists every file it changes, including new files, so the exclusion
  rule holds. A task that touched a file it did not list gets the file added
  before the next task starts.
- The git stash is shared between worktrees. No lane and no coordinator uses
  a bare `git stash`; work is parked as a WIP commit on the lane branch.
- Each lane has its own build directory (the worktree's own `target/`, build
  output, or cache). Two lanes sharing one build directory serialize on its
  lock and both stall.
- A task marked `alone` waits for every open lane to close, and no lane opens
  while it runs.

## Autonomy in practice

The level is `plan.autonomy` (0 to 4; the table is in `SKILL.md`). At a stop:

1. Keep every other lane running.
2. State the question in one sentence, the proof in two lines, and your
   recommendation.
3. Wait for the answer. Don't act on a timeout, and don't take the default
   unless the level is 4 or the user asks you to.

At level 4, record every default you took in the task's "as landed" text
under a heading the user can search for ("Decisions taken by default").

## Giving up on a task

Abandon a lane when stage 1 reports that the specification can't be met as
written, when a gate fails at integration for the third time, or when the
user says so. `plan.py lane graph.yaml <id> abandon` prints the steps: save
the lane's whole change as a patch in its scratch directory, remove the
worktree, delete the branch, and set the task `blocked`. Every task that
depends on it then shows `waits for <id> (blocked)` in `next`, and the rest of
the graph keeps running.

At autonomy 0 to 3, stop for the user with the blocker, its evidence, and a
recommendation: rewrite the task's specification and set it back to
`planned`, split it, or mark it `skipped`. At autonomy 4, record the blocker
in the task's section and in "Residuals", and continue with the tasks that
don't depend on it.

## Failure cases

| Case | What to do |
| --- | --- |
| A stage returns `null` (the runtime skipped or lost the agent) | Rerun that stage with the same prompt. Never invent its report. |
| A stage answers a relayed user question instead of doing its task | The prompt header guards against it; if it happens, rerun the stage and answer the user yourself. |
| A lane's worktree is dirty with work the stage did not report | Read `git diff`; if the diff is the stage's, ask the next stage to account for it; if not, stop and ask the user. |
| The machine runs out of disk or memory | Lower `lane_cap`, clean build directories of closed lanes, and continue. |
| The user changes a task's specification while its lane runs | Let the lane finish against the old spec, integrate, then open a follow-up task for the delta. |
| Two lanes conflict at rebase despite the exclusion rule | Resolve in the lane, add the file to both tasks' `files`, and continue; the rule was wrong, not the lanes. |
| `lane ... integrate` refuses the lane | Read the reason. Uncommitted changes: find which stage left them and rerun that stage's commit step, or commit them yourself if its report accounts for them. No commits: the chain produced nothing to land; read stage 1's report. |
| A task can't be done as specified | Abandon the lane; see "Giving up on a task". |

## The final report

When `plan.py next` prints nothing and no lane is open, give the user:

1. `plan.py render graph.yaml`: each task, its status, its commit.
2. Each reviewer finding of consequence with its decision and its proof, one
   line each, grouped by task.
3. Each residual: a defect found and deferred, with the task that owns it or
   the note that no task does.
4. Each owner question answered by default (level 4) or by the user.
5. The measurements worth keeping (performance numbers, counts, sizes).
6. What a later session needs to resume: the plan document, `graph.yaml`,
   and the scratch root; nothing that lives only in this session's context.
