# The coordinator

The coordinator is the main session. It never implements a task. It
schedules lanes, decides review findings, integrates results into the
integration branch, and keeps the plan document and `graph.yaml` true. This
file is its procedure. As in `SKILL.md`, `plan.py` means
`uv run <this skill's directory>/scripts/plan.py`, and `graph.yaml` means the
graph's path in the repository.

## Contents

- Before the first iteration
- One iteration
- Owner decisions
- Deciding findings
- Integration
- Rules that prevent lane conflicts
- Autonomy in practice
- Giving up on a task
- Resuming a campaign
- Failure cases
- The final report

## Before the first iteration

1. `plan.py validate graph.yaml`. Fix every error.
2. `plan.py render graph.yaml`. If any task is not `planned`, `done`,
   `skipped`, or `blocked`, this is a resumed campaign: follow "Resuming a
   campaign" first.
3. Confirm the main worktree is on the integration branch and clean except
   for `graph.yaml`, and that the plan document and `graph.yaml` are
   committed there. Lanes branch from that commit.
4. Confirm build output is ignored: build and test once, then `git status
   --porcelain` must print nothing. Add each pattern it shows to
   `.git/info/exclude` (shared by every worktree). `integrate` refuses a lane
   with untracked files, because an untracked file may be source a stage
   forgot to commit.
5. Check the machine: free disk (each lane's build directory grows; a Rust
   `target/` can pass 100 GB in a day), free memory (each lane's test suite
   runs with every core), and the lane cap. Lower the cap before you open a
   lane you cannot afford.
6. Let background agents work without prompts. In Claude Code, add the
   worktree root and the scratch root to `permissions.additionalDirectories`
   (or `/add-dir`), and allow the gate and build commands; a background agent
   that hits a permission prompt stalls.
7. Confirm the model ids work: run one trivial agent per model id. A rejected
   id fails at launch, which is cheaper than a failed chain.

## One iteration

```
plan.py next graph.yaml
for each START line (the script already applied the cap, files, and alone rules):
    plan.py lane graph.yaml <id> open        # run the printed command; it records status=running
    build the half-1 prompts (references/chain.md); spec = plan.py excerpt graph.yaml <id>
    launch half 1 (implement, adversarial review) in the background
when a half-1 run returns:
    if stage 1 said BLOCKED: see "Giving up on a task"
    read report 2's findings; decide each one; stop for the user per the autonomy level
    plan.py set graph.yaml <id> status=review
    launch half 2 (fix, final review) with the decisions
when a half-2 run returns:
    plan.py set graph.yaml <id> status=integrating
    plan.py lane graph.yaml <id> integrate   # run the printed command; it ends with status=done
    on success: plan.py lane graph.yaml <id> close        # run the printed command
                paste report 4's "As landed" text into the task's section
                commit the plan document and graph.yaml: "plan: <id> landed (<commit>)"
    on a gate failure: see "Integration"
when a measurement task's stage 1 returns:
    paste its "as landed" text, plan.py set graph.yaml <id> status=done,
    plan.py lane graph.yaml <id> close, commit the plan document and graph.yaml
```

Run the `plan.py set` calls and the printed lane commands one at a time, not
as parallel tool calls: the graph file is shared, and `plan.py` serializes
its writes but not your ordering.

A task with `chain: none` gets no lane: do it yourself on the integration
branch (a plan edit, a merge of two tasks), commit, and set it `done` with
that commit.

After each half returns, check that the integration branch has not moved
since your last integration and that the main worktree has no change besides
`graph.yaml`. A stage that worked outside its lane shows up here; move its
commit to the lane branch before anything else happens.

Keep your own context small. Read the stage summaries and report 2's
findings; open the other reports only for a decision that needs them. Between
events, do the work that depends on nothing: draft the next task's prompts,
and prepare the plan-document edits for a task that is about to land.

## Owner decisions

A task's `owner_decisions` hold questions only the user can answer. Below
autonomy 4, `next` holds the task until each has an answer. Ask the user,
then record the answer by its position in the list, counted from 0:

```
plan.py set graph.yaml <id> "answer=0:<the user's answer>"
```

The answers reach the stages through `{{owner_decisions}}` in the chain
header, which overrides any default the specification recommends. At
autonomy 4, fill that placeholder with each default and say it was taken by
default.

## Deciding findings

For each finding in report 2, in number order, write one of:

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

## Integration

One lane integrates at a time; the gate run is the serialization point.
`plan.py lane graph.yaml <id> integrate` first checks the lane and refuses
with the reason if a rebase is in progress, the lane worktree is not on its
branch, the lane has uncommitted or untracked files, the lane has no commits,
or the main worktree is not on the integration branch. If an earlier
integration already merged the lane (the session died before `status=done`),
it prints only the `set` that finishes the task. It also notes changed files
that the task's `files` doesn't list; add them to `files`.

Otherwise it prints one command that stops at its first failure:

1. Rebase the lane onto the integration branch. A conflict means the
   exclusion rule missed a shared file: resolve it in the lane (`git -C
   <lane> rebase --continue`), add the file to both tasks' `files`, and
   integrate again.
2. Run every gate in the lane, in order, on the rebased tree.
3. Fast-forward the integration branch (`keep`), or squash-merge and commit
   with a `Plan-Task: <id>` trailer (`squash`). Never a merge commit: each
   lane starts from the integration branch and rebases onto it, so the
   history stays linear.
4. Record `status=done commit=<hash>`.

Then close the lane (`plan.py lane graph.yaml <id> close`: remove the
worktree, delete the branch, clear `lane` and `branch`), paste the "As
landed" text into the plan document, and commit the plan document and
`graph.yaml` together. Closing before the commit keeps the committed graph
free of dead lane paths.

A gate that fails at integration ran while other lanes were building, so
first rerun that one gate by itself. If it fails again, the rebase changed
behavior: reopen the lane with the failure output as the fix-stage prompt
(`references/chain.md`, "Reopening a lane"), then integrate again.

## Rules that prevent lane conflicts

- A lane touches code alone. The plan document and `graph.yaml` are the
  coordinator's, and the coordinator edits them serially. This removes every
  tracker conflict.
- New tests go into new files per lane. Two lanes that append to the end of
  one test file always conflict at integration; two new files never do. When
  a task's `files` lists a large shared test file, split its new tests into
  a new file and drop the shared file from `files`.
- A task lists every existing file it changes. When `integrate` notes an
  unlisted file, add it to `files` before the next task starts.
- The git stash is shared between worktrees. Nobody uses `git stash`; the
  coordinator parks work with `plan.py lane ... discard`, which saves a patch.
- Each lane has its own build directory (the worktree's own `target/`, build
  output, or cache). Two lanes sharing one build directory serialize on its
  lock and both stall.
- A task marked `alone`, and every `measurement` task, runs with no other
  lane open. `next` stops opening lanes until the open ones close.

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

Abandon a lane when stage 1 reports `BLOCKED:`, when a gate fails at
integration for the third time, or when the user says so.
`plan.py lane graph.yaml <id> abandon` prints the steps: abort a rebase in
progress, save the lane's whole change as a patch in its scratch directory,
remove the worktree, rename the branch to `abandoned/<id>` (no commit is
lost), and set the task `blocked`. Every task that depends on it then shows
`waits for <id> (blocked)` in `next`, and the rest of the graph keeps running.

At autonomy 0 to 3, stop for the user with the blocker, its evidence, and a
recommendation: rewrite the task's specification and set it back to
`planned`, split it, or mark it `skipped`. At autonomy 4, record the blocker
in the task's section and in "Residuals", and continue with the tasks that
don't depend on it.

## Resuming a campaign

Everything a campaign needs is in the repository, the plan document,
`graph.yaml`, and the scratch root. For each task that `render` shows open:

| Status | State of the lane | What to do |
| --- | --- | --- |
| `running` or `review` | Uncommitted changes | A stage died mid-edit. `plan.py lane graph.yaml <id> discard` (saves a patch), then continue below. |
| `running` | Report files 1 and 2 | Half 1 finished: decide the findings. |
| `running` | Fewer report files | Rerun the first stage whose report is missing. |
| `review` | Report files 3 and 4 | Half 2 finished: integrate. |
| `review` | Fewer report files | Rerun the first stage of half 2 whose report is missing, with the same decisions (they are in the stage 3 prompt you saved, or ask again). |
| `integrating` | Any | Run `integrate` again. It reports a rebase in progress, finishes a lane that already landed, or prints the full integration. |
| `done` with `lane` set | Any | Run `close`. |

A stage that committed but died before writing its report is rerun; it
finds its own commit and verifies it.

## Failure cases

| Case | What to do |
| --- | --- |
| A stage returns `null` (the runtime skipped or lost the agent) | Rerun that stage with the same prompt. Never invent its report. |
| A stage answers a relayed user question instead of doing its task | The prompt header guards against it; if it happens, rerun the stage and answer the user yourself. |
| A stage committed on the integration branch | Stop opening lanes. Move the commit to the lane branch (`cherry-pick` there, then reset the integration branch to your last integration commit), and rerun the stage. |
| `integrate` refuses the lane | Read the reason; the refusal names the fix. Uncommitted changes: find which stage left them and rerun that stage, or commit them if its report accounts for them. |
| The machine runs out of disk or memory | Lower `lane_cap`, clean build directories of closed lanes, and continue. |
| The user changes a task's specification while its lane runs | Let the lane finish against the old spec, integrate, then open a follow-up task for the delta. |
| Two lanes conflict at rebase despite the exclusion rule | Resolve in the lane, add the file to both tasks' `files`, and continue; the rule was wrong, not the lanes. |

## The final report

When `next` prints `FINISHED`, give the user:

1. `plan.py render graph.yaml`: each task, its status, its commit.
2. Each reviewer finding of consequence with its decision and its proof, one
   line each, grouped by task.
3. Each residual and each blocked task: the defect or blocker, and the task
   that owns it or the note that no task does.
4. Each owner question answered by default (level 4) or by the user.
5. The measurements worth keeping (performance numbers, counts, sizes).
6. What a later session needs to resume: the plan document, `graph.yaml`,
   and the scratch root; nothing that lives only in this session's context.
