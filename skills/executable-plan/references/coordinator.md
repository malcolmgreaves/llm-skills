# The coordinator

The coordinator is the main session. It never implements a task. It
schedules lanes, runs each task's workflow, asks the user what only the user
can answer, integrates results into the integration branch, and keeps the
plan document and `graph.yaml` true. How much it reviews and decides depends
on the coordinator mode the user chose. As in `SKILL.md`, `plan.py` means
`uv run <this skill's directory>/scripts/plan.py`, and `graph.yaml` means the
graph's path in the repository.

## Contents

- Before the first iteration
- The coordinator modes
- One iteration
- Owner decisions and the `waiting` status
- Deciding findings (full mode)
- Landing a lane
- Rules that prevent lane conflicts
- Autonomy in practice
- Giving up on a task
- Resuming a campaign
- Failure cases
- The end of a campaign

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
   `.git/info/exclude` (shared by every worktree). Integration refuses a lane
   with untracked files, because an untracked file may be source a stage
   forgot to commit.
5. Check the machine: free disk (each lane's worktree has its own build
   directory), free memory (each lane's tests run with every core), and the
   lane cap. Lower the cap before you open a lane you can't afford.
6. Let background agents work without prompts. In Claude Code, add the
   worktree root and the scratch root to `permissions.additionalDirectories`
   (or `/add-dir`), and allow the gate and build commands; a background agent
   that hits a permission prompt stalls.
7. Confirm the model ids work: run one trivial agent per model id. A rejected
   id fails at launch, which is cheaper than a failed stage.

## The coordinator modes

The user picks one at draft time (`plan.coordinator`) and can change it for
tasks that haven't started.

| Mode | After a workflow finishes, the coordinator | Beyond items are decided by | Cost |
| --- | --- | --- | --- |
| `full` (default) | reads the findings, decides, asks the user, runs `fix` if anything was accepted, lands | the coordinator | highest: the coordinator reviews every task |
| `merge` | asks the user about owner-level items, lands | the user, when the workflow has a `fix` stage; otherwise they become residuals | lowest |
| `delegate` | asks the user about owner-level items, lands | the `delegate` stage, from the coordinator's brief | low: the review runs in the lane, not in the coordinator's context |

In every mode, owner-level decisions go to the user below autonomy 4, and
the coordinator waits for the answer (see "Owner decisions").

In `delegate` mode, `lane open` writes the brief with `plan.py context`:
the task's owner answers, the scope rules, the tasks already landed with
their "As landed" text, the tasks still to come, and the open residuals. Add
your own judgment with `plan.py context graph.yaml <id> --note <file>`
before the delegate stage starts: anything you would have weighed that the
graph doesn't hold. The second review reads the same brief.

## One iteration

```
plan.py next graph.yaml                      # START lines name each task's workflow
for each START line (the script applied deps, files, changed files, alone, and the cap):
    plan.py lane graph.yaml <id> open        # run it; it records running and renders the implement prompt
    launch the implement stage in the background with its model
when a stage returns:
    BLOCKED: -> see "Giving up on a task"
    otherwise render and launch the next stage of the task's workflow:
        a review: --part report, then --part fix to the same agent
        fix: only if there are decisions (see below); skip it otherwise
when the task's last stage returns:
    plan.py findings graph.yaml <id>         # Needs owner, Beyond, owner-level decisions taken
    Needs owner items and autonomy < 4 -> ask the user, set waiting (see "Owner decisions")
    full mode: decide the Beyond items (see "Deciding findings")
    accepted items -> write <scratch>/<id>_decisions.md, set review, run fix --decisions <file>
    then: plan.py set graph.yaml <id> status=integrating
          plan.py lane graph.yaml <id> land  # run it: integrate, close, record As landed, commit the plan
    on a gate failure: see "Landing a lane"
when a measurement task's stage returns:
    plan.py set graph.yaml <id> status=done, plan.py lane graph.yaml <id> close,
    plan.py landed graph.yaml <id>, commit the plan document and graph.yaml
```

Run `plan.py set`, `plan.py prompt`, and the printed lane commands one at a
time, not as parallel tool calls: the graph file is shared, and `plan.py`
serializes its writes but not your ordering. Launching the agents
themselves in parallel is fine.

A task with `chain: none` gets no lane: do it yourself on the integration
branch (a seam, a plan edit), commit, and set it `done` with that commit.

After each stage returns, check that the integration branch has not moved
since your last landing and that the main worktree has no change besides
`graph.yaml`. A stage that worked outside its lane shows up here; move its
commit to the lane branch before anything else happens.

Keep your own context small. Read the stages' short final messages and
`plan.py findings`; open a full report only for a decision that needs it.
Prompts and reports never pass through your context.

## Owner decisions and the `waiting` status

Owner-level questions come from two places: the task's `owner_decisions`,
asked at draft time, and the "Needs owner" items stages report while they
work.

- **Draft time.** Ask every `owner_decisions` question in one message
  before the first lane opens, with your recommended default for each.
  Record each answer by its position, counted from 0:
  `plan.py set graph.yaml <id> "answer=0:<the user's answer>"`. Below
  autonomy 4, `next` holds a task until its questions are answered, and
  `plan.py prompt` refuses to render its stages.
- **During the run, below autonomy 4.** When a task's workflow reports
  "Needs owner" items, `plan.py set graph.yaml <id> status=waiting`, ask the
  user (batch the questions of every waiting task into one message), and
  wait for the answer. A `waiting` lane keeps its slot and its files, and
  `next` keeps other lanes running. When the user answers, write the answers
  to the decisions file, set `review`, and run the fix stage. If an answer
  needs no change, go straight to landing.
- **At autonomy 4.** Nobody waits. The actor in the table under
  `references/workflows.md`, "Owner-level decisions", makes each call and
  reports it under "Owner-level decisions taken", and `plan.py report`
  collects them for the owner to review later. When that actor is you
  (`full` mode), your report is the decisions file.

Every decision is recorded. Write each one to `<scratch>/<id>_decisions.md`
under the heading "Owner-level decisions taken": the question, the decision,
who made it (the owner, or you at autonomy 4), and why. A decision said only
in chat is lost: landing refuses a lane whose reports list "Needs owner"
items until one is recorded, and `plan.py report` reads the file.

## Deciding findings (full mode)

Each finding carries a scope label (`references/workflows.md`, "Scope
labels"). The reviews already fixed the `spec`, `defect`, `creep`, and
`quality` findings. What's left for you is every "Beyond" item: accept it
only when it is small, serves the task's intent, and changes no behavior
the specification settles; otherwise record it as a residual. Apply the
same rule to every item. A change to existing behavior the specification
doesn't mention is an owner decision, not yours.

Write one decision per accepted item to `<scratch>/<id>_decisions.md`, with
any owner answers, and run the fix stage with `--decisions`. A decision
that names a bound, a guard, or a rule requires the fix stage to prove that
it fires (a test that fails without it); a rule that cannot fire is dropped,
not shipped. With nothing accepted, skip the fix stage.

## Landing a lane

One lane lands at a time; the gate run is the serialization point.
`plan.py lane graph.yaml <id> land` first checks the lane and refuses, with
the reason, if:

- a rebase is in progress
- the worktree is not on its branch
- the lane has uncommitted or untracked files
- a `review_proof_` test remains
- a report of a stage in the workflow is missing
- the fix stage ran without a decisions file (below autonomy 4)
- a report lists "Needs owner" items and no "Owner-level decisions taken" is
  recorded
- the lane has no commits
- the main worktree is not on the integration branch

If an earlier landing already merged the lane (the session died before
`status=done`), it prints only the steps that finish the job. It notes
changed files the task's `files` doesn't list; add them to `files`.

Otherwise it prints one command that stops at its first failure: rebase the
lane onto the integration branch, run every gate in the lane, fast-forward
the integration branch (or squash-merge with a `Plan-Task: <id>` trailer),
record `status=done commit=<hash>`, remove the worktree and the branch,
clean the lane's stage temp directories, apply the "As landed" text from the
workflow's last report, and commit the plan document and `graph.yaml`. The
history stays linear: every lane starts from the integration branch and
rebases onto it. `plan.py lane ... integrate` and `close` run the halves
separately when you need them.

A rebase conflict means two lanes changed the same file: resolve it in the
lane (`git -C <lane> rebase --continue`), add the file to both tasks'
`files`, and land again. A gate that fails at landing ran while other lanes
were building, so first rerun that one gate by itself. If it fails again,
the rebase changed behavior: reopen the lane (`references/workflows.md`,
"Reopening a lane"), then land again.

## Rules that prevent lane conflicts

- **The worktree isolates a lane while it works, not when it lands.** Two
  lanes that change the same file conflict at the rebase. `files` exists so
  that `next` never opens two such lanes at once, and `next` also excludes
  on the files each open lane has actually changed so far.
- Agents may change any file the work needs. They report every file outside
  the task's `files` under "Unexpected files", and landing names them; add
  each to `files` before the next task starts.
- A lane touches code alone. The plan document and `graph.yaml` are the
  coordinator's, and the coordinator edits them serially.
- New tests go into new files per lane. Two lanes that append to one test
  file always conflict; two new files never do.
- The git stash, refs, and config are shared between worktrees. Nobody uses
  `git stash`; the coordinator parks work with `plan.py lane ... discard`,
  which saves a patch.
- Each lane has its own build directory (the worktree's own `target/`,
  build output, or cache) and its own scratch partition. Nothing goes to
  `/tmp`.
- A task marked `alone`, and every `measurement` task, runs with no other
  lane open. `next` stops opening lanes until the open ones close.

## Autonomy in practice

The level is `plan.autonomy` (0 to 4; the table is in `SKILL.md`). At
level 2 or lower, read each review's report-part summary before you send the
fix prompt: a P1 finding (or a P2, at level 1) is a stop, and the fix prompt
waits for the user's ruling. At a stop:

1. Keep every other lane running.
2. State the question in one sentence, the evidence in two lines, and your
   recommendation.
3. Wait for the answer. Don't act on a timeout, and don't take the default
   unless the level is 4 or the user asks you to.

## Giving up on a task

Abandon a lane when the implement stage reports `BLOCKED:`, when a gate
fails at landing for the third time, or when the user says so.
`plan.py lane graph.yaml <id> abandon` prints the steps: abort a rebase in
progress, save the lane's whole change as a patch in its scratch directory,
remove the worktree, rename the branch to `abandoned/<id>` (no commit is
lost), set the task `blocked`, and clean its stage temp directories. Every
task that depends on it then shows `waits for <id> (blocked)` in `next`, and
the rest of the graph keeps running.

At autonomy 0 to 3, stop for the user with the blocker, its evidence, and a
recommendation: rewrite the task's specification and set it back to
`planned`, split it, or mark it `skipped`. At autonomy 4, record the blocker
in the task's section and in "Residuals", and continue with the tasks that
don't depend on it.

## Resuming a campaign

Everything a campaign needs is in the repository, the plan document,
`graph.yaml`, and the scratch root. The node's log records each prompt that
started; each report in the lane's scratch directory marks a prompt that
finished. For each task that `render` shows open:

| Status | State of the lane | What to do |
| --- | --- | --- |
| `running` or `review` | Uncommitted changes | A stage died mid-edit. `plan.py lane graph.yaml <id> discard` (saves a patch), then continue below. |
| `running` | A started prompt has no report | Rerun that prompt (`plan.py prompt` rewrites it). A review's fix part goes to a new agent, which reads the report of part 1. |
| `running` | Every workflow report exists | The workflow finished: read `plan.py findings` and continue with "when the task's last stage returns". |
| `waiting` | Any | Ask the user again; the questions are in `plan.py findings`. |
| `review` | The fix report is missing | Rerun the fix stage with `--decisions <scratch>/<id>_decisions.md`. |
| `review` or `integrating` | Every report exists | Run `plan.py lane graph.yaml <id> land`. It reports a rebase in progress, finishes a lane that already landed, or prints the full landing. |
| `done` with `lane` set | Any | Run `close`, then `plan.py landed`, and commit. |

## Failure cases

| Case | What to do |
| --- | --- |
| A stage returns `null` (the runtime lost the agent) | Rerun that stage with the same prompt. Never invent its report. |
| A stage answers a relayed user question instead of doing its task | The prompt guards against it; if it happens, rerun the stage and answer the user yourself. |
| A stage committed on the integration branch | Stop opening lanes. Move the commit to the lane branch (`cherry-pick` there, then reset the integration branch to your last landing commit), and rerun the stage. |
| Landing refuses the lane | Read the reason; the refusal names the fix. |
| The machine runs out of disk or memory | Lower `lane_cap`, run `plan.py clean graph.yaml <id>` for closed lanes, and continue. |
| The user changes a task's specification while its lane runs | Let the lane finish against the old spec, land it, then open a follow-up task for the delta. |

## The end of a campaign

When `next` prints `FINISHED`:

1. `plan.py report graph.yaml` writes `report.md` next to `graph.yaml` and
   prints it. It holds each task's status and commit, and each stage's
   model, requested and applied effort, and duration. It also lists every
   "Needs owner", "Owner-level decisions taken", "Beyond", and "Residuals"
   item, and each abandoned task's patch. It records the stage timings in
   the repository's timings file, which later plans' `waves` estimates use.
2. Commit `report.md` with the plan.
3. `plan.py clean graph.yaml` removes the scratch root, keeping only the
   patches of abandoned tasks, and removes the lane directories once they
   are empty.
4. Give the user the report's summary: what landed, what is blocked, and
   every owner-level decision taken without them.
