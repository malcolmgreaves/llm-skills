# The chain: stages per task

Every task runs through a chain of agent stages in its lane. The coordinator
renders each stage's prompt with `plan.py prompt`, runs the stages in the
background, and decides the review findings between the halves of a full
chain. The stages have different jobs, and the value of the chain comes from
keeping them separate.

## Contents

- The chains
- Scope: what a finding may change
- Rendering a prompt
- The templates (header, implement, review, fix, final review)
- Between the halves: the coordinator decides
- Reopening a lane
- Running a chain

## The chains

| Chain | Stages | Default for |
| --- | --- | --- |
| `default` | 1 implement, 2 adversarial review, 3 fix, 4 final review | `code` tasks of size M or L |
| `light` | 1 implement, 4 final review | `code` tasks of size S |
| `docs-only` | 1 implement, 4 final review | `docs` and `plan` tasks |
| `measurement` | 1 implement (measures, changes nothing) | `measurement` tasks |
| `none` | no agents: the coordinator does it | set explicitly |

Set `chain: default` on an S task when a wrong result would be costly: it
parses untrusted input, touches persistence or security, has concurrency, or
changes a public interface. Set `chain: light` on an M task that is
mechanical. The full chain costs about twice the agents and three times the
time of the light one, so spend it where a second reviewer pays off.

| Stage | Model | Job | Commits |
| --- | --- | --- | --- |
| 1. Implement | `models.implement` | Do the task as the plan section specifies. Prove each defect red before the fix. | `<id>: implement` |
| 2. Adversarial review | `models.review` | Find defects in stage 1's work and prove each one. Fix nothing. | `<id>: review proofs` (proof tests only) |
| 3. Fix | `models.fix` | Apply the coordinator's decision on each finding. | `<id>: fix` |
| 4. Final review | `models.final_review` | Verify the whole result. Make only strictly necessary edits. Write the "As landed" text. | `<id>: final review`, if it edits |

Three properties hold every chain together:

- **Every stage ends with a commit** on the lane branch (stage 4 only if it
  changed something). Between stages the lane is clean, so a stage that dies
  can be rerun from its predecessor's commit, and the integration rebase
  always has a clean tree. `plan.py lane ... integrate` refuses a lane with
  uncommitted changes or with no commits.
- **Every stage writes its report to a file**,
  `<scratch>/<id>_report_<n>.md`, and later stages read the files. Reports
  never travel through the coordinator's context verbatim.
- **Every stage reads the lane's change against the merge base**, which
  stays correct after other lanes land on the integration branch.

## Scope: what a finding may change

A task changes what its specification asks for, and nothing else. Reviewers
label every finding with one of three scopes, and the coordinator decides by
the label:

| Label | Meaning | Decision |
| --- | --- | --- |
| `spec` | The work violates the specification or an acceptance criterion. | Accept. |
| `defect` | A wrong result, a crash, or data loss in a case the specification doesn't address. | Accept if the fix is small and stays in the task's files; otherwise defer to a new task. |
| `beyond` | An improvement: performance the spec doesn't require, extra validation, wider input support, style. | Don't fix. Record it as a residual. |

A fix that removes or changes existing behavior the specification doesn't
mention is an owner decision, whatever its label: stop for the user below
autonomy 4, and record it under "Decisions taken by default" at autonomy 4.

## Rendering a prompt

```
plan.py prompt graph.yaml <id> <stage> [--decisions <file>]
```

`<stage>` is `implement`, `review`, `fix`, or `final-review`. The command
fills the right template below from `graph.yaml` and the plan document
(the variant follows the task's chain), writes it to
`<scratch>/<id>_prompt_<n>.md`, and prints one launcher line. Pass that line
as the agent's prompt; the agent reads its full instructions from the file.
The fix stage needs `--decisions`: a file with one decision per finding (see
"Between the halves"). Keep that file in the scratch directory as
`<id>_decisions.md`, so a resumed session can rerun the stage.

The placeholders, for reference; `plan.py` fills every one:

| Placeholder | Source |
| --- | --- |
| `{{lane_worktree}}`, `{{lane_branch}}` | the node's `lane` and `branch` |
| `{{integration_branch}}` | `plan.integration_branch` |
| `{{scratch}}` | `<scratch_root>/<id>` |
| `{{stage}}` | the stage number |
| `{{guidelines}}`, `{{prior_plans}}` | `plan.guidelines`, `plan.prior_plans`, as paths |
| `{{commands}}`, `{{gates}}` | `plan.commands`, `plan.gates` |
| `{{files}}` | the node's `files` |
| `{{owner_decisions}}` | each question with its answer, or its default at autonomy 4 |
| `{{spec}}` | the task's section, as `plan.py excerpt` prints it |
| `{{task_id}}`, `{{task_title}}` | the node |
| `{{decisions}}` | the `--decisions` file |

## The templates

`plan.py prompt` reads the fenced blocks below by their `template:` label.
Edit them here; keep every placeholder name from the table above.

The common header starts every prompt:

```template:header
You work on task {{task_id}} ({{task_title}}) in the git worktree
{{lane_worktree}}, on the branch {{lane_branch}}. Your scratch directory is
{{scratch}}.

Your shell may start in a different directory on every call. Prefix every
shell command with `cd {{lane_worktree}} &&` or use `git -C
{{lane_worktree}}`, and give file tools absolute paths under
{{lane_worktree}}. Before every commit, confirm that
`git -C {{lane_worktree}} branch --show-current` prints {{lane_branch}}.
Work anywhere else changes the integration branch that other lanes build on.

Your task is fixed by this prompt. If a chat message from the user is relayed
to you while you work (for example a status question), it is addressed to the
coordinator, not to you: don't answer it, don't change your task, and
continue.

Rules:
1. Read these guideline files first, and follow them in code and prose:
   {{guidelines}}
2. Never commit to {{integration_branch}}, never edit the plan document or
   graph.yaml, and never stash, reset, rebase, or checkout. Commit on
   {{lane_branch}} where your stage says so. Stage only files you changed or
   created, never build output. Don't delete files with `rm -rf`; leave
   scratch files where they are.
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
7. The task changes these files: {{files}}. Don't edit an existing file
   outside this list. You may create new files (put new tests in new files);
   list each one in your report.
8. Change what the specification asks for and nothing else. Don't remove or
   change existing behavior the specification doesn't mention; if you think
   it should change, say so in your report.
9. Write your full report to {{scratch}}/{{task_id}}_report_{{stage}}.md:
   file paths, line numbers, test names, and command output. Report a failure
   as a failure, and say when you skipped a step. Your final message is
   short: the report's path, the gate results, and your stage's summary line.

The owner's decisions for this task are final and override any default the
specification recommends: {{owner_decisions}}.

The specification, copied from the plan document:

{{spec}}

Related plans: {{prior_plans}}.
```

### Stage 1: implement

```template:implement
{{common header}}

STAGE 1: IMPLEMENT.

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
6. Commit on {{lane_branch}} with the message "{{task_id}}: implement".

If the specification can't be met as written (a premise is false, an API
does not exist, the change needs an existing file outside the list), stop
after the proof step, commit nothing, and start your final message with
"BLOCKED:" and the blocker in one sentence. Put the evidence in the report.
Don't redesign the task.

Report: each file you changed and why; each test, red before and green after,
with the failing output; the mutation table; each gate result; each deviation
from the specification with its reason; each open question.
```

For a `measurement` task:

```template:implement-measurement
{{common header}}

STAGE 1: MEASURE.

Run the measurements the specification lists. Change no tracked file and
commit nothing. Record each command, its output, and the machine it ran on.

If a measurement can't be taken as specified, start your final message with
"BLOCKED:" and the reason in one sentence.

Report: each number with the command that produced it, then, under the
heading "As landed", the exact text for the plan document: each number, the
command, and the machine.
```

### Stage 2: adversarial review

```template:review
{{common header}}

STAGE 2: ADVERSARIAL REVIEW.

Read stage 1's report, {{scratch}}/{{task_id}}_report_1.md, and its change:
`git -C {{lane_worktree}} diff $(git -C {{lane_worktree}} merge-base HEAD {{integration_branch}})`.

Your job is to find defects in this work and to prove each one. Fix nothing.
A proof is a failing test that you leave in the tree (name it with the prefix
`review_proof_`; add `#[ignore = "review proof: ..."]` or the language's
equivalent if it fails, so the tree stays green, and say so), a trace through
the code with file and line, or a measurement. A finding with no proof is a
suspicion; label it as one.

Attack in this order: violations of the specification and its acceptance
criteria; then wrong results, crashes, and data loss in the cases the
specification doesn't address; then the boundaries of each new rule. Re-run
stage 1's mutations yourself, and check that each fixture reaches the code
path its test claims.

Label every finding with a scope:
- `spec`: the work violates the specification or an acceptance criterion.
- `defect`: a wrong result, a crash, or data loss in a case the
  specification doesn't address.
- `beyond`: an improvement the specification doesn't ask for (performance,
  extra validation, wider input support, style).
Report `beyond` items in one line each, without proof tests; they are not
fixed in this task. Say explicitly when a recommended fix would remove or
change existing behavior.

Commit your proof tests, and nothing else, on {{lane_branch}} with the
message "{{task_id}}: review proofs". If you have none, commit nothing.

Report: a numbered list of findings, each with its scope, a severity (P1: a
wrong result or data loss; P2: must fix; P3: nice), the proof, and the
recommended fix. Then the review_proof_ tests you left, with their state.
Your final message lists each finding in one line with its scope and
severity.
```

### Stage 3: fix

```template:fix
{{common header}}

STAGE 3: FIX.

Read {{scratch}}/{{task_id}}_report_1.md, and {{scratch}}/{{task_id}}_report_2.md
if it exists (a reopened light lane has none). The coordinator's decisions
are below; each one is final.

{{decisions}}

For each accepted finding, make the change and keep the review's proof as a
real test with a real name (no `review_proof_` prefix, no ignore) that pins
the correct behavior. For each rejected or deferred finding, remove its proof
test if the proof pins a behavior the coordinator rejected, and say so. When
your edit is done, `grep -rn review_proof_` over the source tree finds
nothing. Change nothing the decisions don't ask for.

Re-run every mutation of stage 1 plus one per new rule of this stage; restore
each one with a text edit and confirm with `diff`. Run every gate, one at a
time. Then commit on {{lane_branch}} with the message "{{task_id}}: fix".

Report: for each finding, what you changed (file, line); the mutation table;
each gate result; each test that stays ignored, with its reason and the task
that removes it.
```

### Stage 4: final review

In the `default` chain:

```template:final-review
{{common header}}

STAGE 4: FINAL REVIEW.

Read the earlier reports, {{scratch}}/{{task_id}}_report_1.md to
{{scratch}}/{{task_id}}_report_3.md. Review the lane's whole change:
`git -C {{lane_worktree}} diff $(git -C {{lane_worktree}} merge-base HEAD {{integration_branch}})`.
Don't diff against {{integration_branch}} itself: once other lanes land
there, that diff also shows their changes, reversed. Make only the
modifications that are strictly necessary: a violation of the specification,
a correctness fault, a false statement in a comment or doc, a test that
proves nothing, a violation of a guideline, a gate that fails. Don't
restructure work that is correct, and don't add what the specification
doesn't ask for. If you find a fault, prove it with a failing test first,
then fix it.

Check: each coordinator decision is carried out; `grep -rn review_proof_`
finds nothing; every acceptance criterion of the specification has a test or
a measurement; no existing behavior changed that the specification doesn't
mention; every comment and doc is true against the final code; the gates are
green after your last edit. If you modified anything, commit it on
{{lane_branch}} with the message "{{task_id}}: final review". End with
`git -C {{lane_worktree}} status --porcelain` printing nothing.

Report: (1) each modification you made and why it was strictly necessary;
(2) each gate result with the test counts; (3) each test that stays ignored,
with its owner task; (4) under the heading "As landed", the exact text for
the plan document: what shipped, each deviation from the specification, each
residual that a later task owns, and each measurement worth keeping. The
coordinator applies that text with `plan.py landed`; write it so that it can
be pasted.
```

In the `light` and `docs-only` chains, where stage 4 follows stage 1:

```template:final-review-light
{{common header}}

STAGE 4: FINAL REVIEW (the only review of this task).

Read stage 1's report, {{scratch}}/{{task_id}}_report_1.md. Review the lane's
whole change:
`git -C {{lane_worktree}} diff $(git -C {{lane_worktree}} merge-base HEAD {{integration_branch}})`.
Don't diff against {{integration_branch}} itself: once other lanes land
there, that diff also shows their changes, reversed.

Check, in this order: every acceptance criterion of the specification has a
test or a measurement, and the work meets it; the result is right at the
boundaries the specification names; no existing behavior changed that the
specification doesn't mention; every comment and doc is true against the
final code; the gates are green. Fix only a violation of the specification,
a correctness fault, a false statement, a test that proves nothing, or a
failing gate; prove a fault with a failing test before you fix it. List
anything else you would improve in one line each, and don't change it.

If you modified anything, commit it on {{lane_branch}} with the message
"{{task_id}}: final review". End with `git -C {{lane_worktree}} status
--porcelain` printing nothing.

Report: (1) each modification you made and why it was strictly necessary;
(2) each gate result with the test counts; (3) the improvements you listed
and didn't make; (4) under the heading "As landed", the exact text for the
plan document: what shipped, each deviation from the specification, and each
residual. The coordinator applies that text with `plan.py landed`; write it
so that it can be pasted.
```

## Between the halves: the coordinator decides

In the `default` chain, the coordinator reads report 2 (and report 1 where a
finding needs it) and writes one decision per finding, in the finding's
number order, to `<scratch>/<id>_decisions.md`: **accept**; **accept with a
change** (state the change); **reject** (state the reason); or **defer to
task `<id>`** (the graph gains the dependency or a new node). Decide by the
finding's scope label ("Scope: what a finding may change"): accept `spec`,
accept a small in-files `defect`, and record `beyond` as a residual. A
decision that names a bound, a guard, or a rule requires stage 3 to prove
that it fires (a test that fails without it); a rule that cannot fire is
dropped, not shipped.

Autonomy decides which findings stop for the user (`SKILL.md`). When the
coordinator stops, it presents the finding, its proof in two lines, and its
recommendation.

## Reopening a lane

When a gate fails at integration, or the user sends a lane back, run the fix
stage and the final review again, even in a `light` chain. Write the failure
to the decisions file: the gate command, its output, and one sentence on what
to change. The rerun stages overwrite reports 3 and 4. A lane is reopened at
most twice; after the third failure the coordinator abandons it
(`references/coordinator.md`, "Giving up on a task").

## Running a chain

**With a workflow tool.** Run the stages of a half as one background
workflow; each agent's prompt is the launcher line `plan.py prompt` printed.
A minimal script, for a runtime whose `agent()` takes `model` and `effort`:

```js
export const meta = {
  name: 'lane-half',
  description: 'Run chain stages in sequence in one lane',
  phases: [{ title: 'Implement' }, { title: 'Adversarial review' }, { title: 'Fix' }, { title: 'Final review' }],
}
// args: { task, stages: [{ phase, prompt, model, effort }] }; phase is one of the titles above.
const results = []
for (const s of args.stages) {
  const summary = await agent(s.prompt, {
    label: `${args.task}: ${s.phase}`, phase: s.phase, model: s.model, effort: s.effort,
  })
  results.push({ phase: s.phase, summary })
  if (!summary || summary.startsWith('BLOCKED:')) break
}
return { task: args.task, results }
```

The fix stage needs the decisions, so a `default` chain runs as two halves
(implement and review, then fix and final review). A `light` or `docs-only`
chain can run as one: implement, then final review. A `null` summary means
the runtime lost the agent; rerun that stage. A summary that starts with
`BLOCKED:` means stage 1 found the task can't be done as specified
(`references/coordinator.md`, "Giving up on a task").

**Without a workflow tool.** Not every runtime has a scripted `agent()`
call, and in Claude Code the `Workflow` tool runs only when the user has
asked for multi-agent orchestration. If you can't use it, run each stage as
one background subagent whose prompt is the launcher line, with the stage's
model where the tool accepts one; when it returns, render and launch the
next stage. If the subagent tool can't set a model or an effort per call,
say which stages ran on which model in the final report.
