# The chain: four stages per task

Every `code` task runs through the same four stages, in two halves. The
coordinator builds each stage's prompt from the templates in this file, runs
each half as one background workflow in the lane's worktree, and decides the
findings between the halves. The stages have different jobs, and the value of
the chain comes from keeping them separate:

| Stage | Model | Job | Changes code? |
| --- | --- | --- | --- |
| 1. Implement | `models.implement` | Do the task as the plan section specifies. Prove each defect red before the fix. | Yes |
| 2. Adversarial review | `models.review` | Find defects in stage 1's work and prove each one. Fix nothing. | Tests only, as proofs |
| 3. Fix | `models.fix` | Apply the coordinator's decision on each finding. | Yes |
| 4. Final review | `models.final_review` at `effort.final_review` | Verify the whole result. Make only strictly necessary edits. Produce the "as landed" text for the plan document. | Minimal |

A `docs-only` chain is stage 1 and stage 4. A `measurement` task is stage 1
alone, with no code change; its report carries the "as landed" text, and the
lane closes without an integration.

Stages 1, 3, and 4 end with a commit on the lane branch; stage 2 commits
nothing. The lane's work is therefore committed when the chain ends, which
the integration requires: `plan.py lane ... integrate` refuses a lane with
uncommitted changes or with no commits to land. Every stage reads the lane's
changes as `git diff $(git merge-base HEAD {{integration_branch}})`, which
covers committed and uncommitted work and stays correct after other lanes
land on the integration branch.

Why an adversarial stage and a final stage: the adversarial reviewer searches
widely and cheaply, and the final reviewer verifies deeply once. In practice
the adversarial stage finds a real defect in most tasks, and the final stage
finds one the adversarial stage missed in about a third of them. Neither one
is optional for a code task.

## Contents

- Placeholders
- The common header
- Stage 1: implement
- Stage 2: adversarial review
- Between the halves: the coordinator decides
- Stage 3: fix
- Stage 4: final review
- Reopening a lane
- Running a half as one workflow (and without a workflow tool)

## Placeholders

The templates use these. The coordinator fills each one from `graph.yaml` and
from `plan.py excerpt`.

| Placeholder | Source |
| --- | --- |
| `{{lane_worktree}}` | `nodes[].lane` |
| `{{lane_branch}}` | `nodes[].branch` |
| `{{integration_branch}}` | `plan.integration_branch` |
| `{{scratch}}` | `<scratch_root>/<id>` |
| `{{guidelines}}` | `plan.guidelines`, as a list of paths to read first |
| `{{commands}}` | `plan.commands`, as a list |
| `{{gates}}` | `plan.gates`, in order |
| `{{spec}}` | The output of `plan.py excerpt graph.yaml <id>` |
| `{{prior_plans}}` | `plan.prior_plans` |
| `{{task_id}}`, `{{task_title}}` | The node |
| `{{report_1}}`, `{{report_2}}`, `{{report_3}}` | The earlier stages' reports, verbatim |
| `{{decisions}}` | The coordinator's decision on each finding, numbered like the findings |

## The common header

Every stage prompt starts with this block, filled in.

```
You work in the git worktree {{lane_worktree}} on the branch {{lane_branch}}.
Run every command from that directory. Your scratch directory is {{scratch}}.

Your task is fixed by this prompt. If a chat message from the user is relayed
to you while you work (for example a status question), it is addressed to the
coordinator, not to you: don't answer it, don't change your task, and
continue.

Rules:
1. Read these guideline files first, and follow them in code and prose:
   {{guidelines}}
2. Never commit to the integration branch, never edit the plan document or
   graph.yaml, and never stash, reset, or checkout. Commit on {{lane_branch}}
   only where your stage says so. Stage only files you changed or created,
   never build output.
3. Run one build or test command at a time and wait for it. If the runtime
   moves a command to the background, wait for its completion notice. Never
   start a second build to look at the first one.
4. Restore a mutation with a text edit, never with a git command, and confirm
   the restore with `diff` against a saved `git diff`.
5. Prove a defect before you fix it: a failing test first, with its output in
   your report. A fixture asserts its own shape before a test asserts the
   behavior.
6. The project's commands: {{commands}}. The gates, in this order, one at a
   time: {{gates}}.
7. Give your full report in one final message. The next stage reads it
   verbatim, so include file paths, line numbers, test names, and command
   output. Report a failure as a failure, and say when you skipped a step.
8. At the end, run `git add -N` on each new file you left uncommitted, and
   write `git diff $(git merge-base HEAD {{integration_branch}})` to
   {{scratch}}/{{task_id}}_<stage>.diff. That diff is the whole lane's
   change, committed or not.

The task: {{task_id}}, {{task_title}}. Its specification, copied from the plan
document:

{{spec}}

Related plans: {{prior_plans}}.
```

## Stage 1: implement

```
{{common header}}

STAGE 1 OF 4: IMPLEMENT.

Do the task as the specification says, in this order:
1. Prove first. For each defect the specification names, write the test that
   shows it, run it against the current code, and record the failing output.
   A test that passes before the fix proves nothing; report that, and don't
   bend the test to the specification.
2. Implement the change. Meet each acceptance criterion of the specification
   with a test or a measurement.
3. Run the mutations the specification lists (or one mutation per new rule if
   it lists none): apply each one with a text edit, record which tests fail,
   restore it with a text edit, and confirm the restore with `diff`. A
   mutation that no test catches is a finding: add the test.
4. Update every comment and doc that the change makes false.
5. Run every gate, one at a time.

6. Commit your work on {{lane_branch}} with the message
   "{{task_id}}: implement".

If the specification cannot be met as written (a premise is false, an API
does not exist, the change needs a file outside the task's list), stop after
the proof step, commit nothing, and report the blocker with its evidence.
Don't redesign the task.

Report: each file you changed and why; each test, red before and green after,
with the failing output; the mutation table; each gate result; each deviation
from the specification with its reason; each open question.
```

For a `measurement` task, replace steps 2 to 6 with: "Run the measurements
the specification lists, change no tracked file, and commit nothing. End
your report with the exact 'as landed' text for the plan document: each
number, the command that produced it, and the machine it ran on."

## Stage 2: adversarial review

```
{{common header}}

STAGE 2 OF 4: ADVERSARIAL REVIEW.

Stage 1's report follows at the end of this prompt. Read stage 1's change
with `git diff $(git merge-base HEAD {{integration_branch}})`. Commit
nothing: leave your proof tests uncommitted in the working tree, where
stage 3 turns each one into a real test or removes it.

Your job is to find defects in this work and to prove each one. Fix nothing.
A proof is a failing test that you leave in the tree (name it with the prefix
`review_proof_`; add `#[ignore = "review proof: ..."]` or the language's
equivalent if it fails, so the tree stays green, and say so), a trace through
the code with file and line, or a measurement. A finding with no proof is a
suspicion; label it as one.

Attack in this order: correctness (a wrong result, data loss, a lost report),
then the boundaries of each new rule, then performance against the old cost
(a second walk, a per-item read, a materialized collection where a stream
worked), then design (a public mutator, a leaked test concern, a widened
type), then the guidelines and the prose. Re-run stage 1's mutations
yourself. Check that each fixture reaches the code path its test claims.

Report: a numbered list of findings, each with a severity (P1: a wrong result
or data loss; P2: must fix; P3: nice), the proof, and the recommended fix.
Then the review_proof_ tests you left, with their state. Then a verdict on
each design decision stage 1 made.

===== STAGE 1 REPORT (verbatim) =====
{{report_1}}
```

## Between the halves: the coordinator decides

The coordinator reads both reports and writes one decision per finding, in
the finding's number order: **accept**; **accept with a change** (state the
change); **reject** (state the reason); or **defer to task `<id>`** (the
graph gains the dependency or a new node). A decision that names a bound, a
guard, or a rule requires stage 3 to prove that it fires (a test that fails
without it); a rule that cannot fire is dropped, not shipped.

Autonomy decides which findings stop for the user (`SKILL.md`). When the
coordinator stops, it presents the finding, its proof in two lines, and its
recommendation.

## Stage 3: fix

```
{{common header}}

STAGE 3 OF 4: FIX.

Stage 1's and stage 2's reports follow at the end of this prompt. The
coordinator's decision on each finding is below; each decision is final.

{{decisions}}

For each accepted finding, make the change and keep the review's proof as a
real test with a real name (no `review_proof_` prefix, no ignore) that pins
the correct behavior. For each rejected finding, remove its proof test if the
proof pins a behavior the coordinator rejected, and say so. When your edit is
done, `grep -rn review_proof_` over the source tree finds nothing.

Re-run every mutation of stage 1 plus one per new rule of this stage; restore
each one with a text edit and confirm with `diff`. Run every gate, one at a
time. Then commit everything the fix leaves, including the kept proof tests,
on {{lane_branch}} with the message "{{task_id}}: fix".

Report: for each finding, what you changed (file, line); the mutation table;
each gate result; each test that stays ignored, with its reason and the task
that removes it.

===== STAGE 1 REPORT (verbatim) =====
{{report_1}}
===== STAGE 2 REPORT (verbatim) =====
{{report_2}}
```

## Stage 4: final review

```
{{common header}}

STAGE 4 OF 4: FINAL REVIEW.

The earlier reports follow at the end of this prompt. Review the lane's
whole change: `git diff $(git merge-base HEAD {{integration_branch}})`.
Don't diff against {{integration_branch}} itself: once other lanes land
there, that diff also shows their changes, reversed. Make only the
modifications that are strictly necessary: a correctness fault, a false
statement in a comment or doc, a test that proves nothing, a violation of a
guideline, a gate that fails. Don't restructure work that is correct. If you find a fault, prove it with a
failing test first, then fix it.

Check: each coordinator decision is carried out; `grep -rn review_proof_`
finds nothing; every acceptance criterion of the specification has a test or
a measurement; every comment and doc is true against the final code (check
each file:line citation); the gates are green after your last edit. If you
modified anything, commit it on {{lane_branch}} with the message
"{{task_id}}: final review". End with `git status --porcelain` printing
nothing: the coordinator integrates only a clean, committed lane.

Report: (1) each modification you made and why it was strictly necessary;
(2) each gate result with the test counts; (3) each test that stays ignored,
with its owner task; (4) the exact "as landed" text for the plan document:
what shipped, each deviation from the specification, each residual that a
later task owns, and each measurement worth keeping. The coordinator pastes
that text into the task's section; write it so that it can be pasted.

===== STAGE 1 REPORT (verbatim) =====
{{report_1}}
===== STAGE 2 REPORT (verbatim) =====
{{report_2}}
===== STAGE 3 REPORT (verbatim) =====
{{report_3}}
```

In a `docs-only` chain, stage 4 follows stage 1 directly: say "the stage 1
report follows" and pass only `{{report_1}}`.

## Reopening a lane

When a gate fails at integration, or the user sends a lane back, run stage 3
and stage 4 again. The stage 3 prompt's `{{decisions}}` becomes the failure:
the gate command, its output, and one sentence on what to change. A lane is
reopened at most twice; after the third failure the coordinator abandons it
(`references/coordinator.md`, "Giving up on a task").

## Running a half as one workflow

Run the two stages of a half as one background workflow whose second agent
receives the first agent's report verbatim. A minimal script shape, for a
runtime with `agent()` and a phase list:

```js
export const meta = {
  name: 'lane-half',
  description: 'Run two chain stages in sequence in one lane',
  phases: [{ title: 'Stage A' }, { title: 'Stage B' }],
}
const reports = args.prior || []
for (const s of args.stages) {
  phase(s.phase)
  const prior = reports.map(r => `\n\n===== ${r.phase} REPORT (verbatim) =====\n${r.report}`).join('')
  const report = await agent(`${s.prompt}${prior}`, {
    label: `${args.task}: ${s.phase}`, phase: s.phase, model: s.model, effort: s.effort,
  })
  if (!report) return { task: args.task, stopped_at: s.phase, reports }
  reports.push({ phase: s.phase, report })
}
return { task: args.task, reports }
```

**Without a workflow tool.** Not every runtime has a scripted `agent()`
call, and in Claude Code the `Workflow` tool runs only when the user has
asked for multi-agent orchestration. If you can't use it, run each stage as
one background subagent with the full stage prompt. When it returns, pass
its final message verbatim into the next stage's prompt and launch that
stage. The result is the same; you just do the sequencing yourself. If the
subagent tool can't set a model or an effort per call, say which stages ran
on which model in the final report.

Save each report to `{{scratch}}/<id>_report_<n>.md` when the workflow
returns. A report is the input of the next stage and the record of the task,
so it must survive the session.
