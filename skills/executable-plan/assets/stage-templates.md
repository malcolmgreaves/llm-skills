# Stage prompt templates

`scripts/plan.py prompt` fills these templates and writes each prompt to the
lane's scratch directory. The coordinator never reads this file. Each fenced
block labeled `template:<name>` is one prompt; `{{common header}}` stands for
the `header` template. Every `{{placeholder}}` is filled by `plan.py`; a
template with an unknown placeholder is refused.

```template:header
You work on task {{task_id}} ({{task_title}}) in the git worktree
{{lane_worktree}}, on the branch {{lane_branch}}. The worktree is yours alone:
other agents work in their own worktrees, so edit, build, and test freely
inside it.

Your shell may start in a different directory on every call. Start every
shell command with `cd {{lane_worktree}} && export TMPDIR={{stage_tmp}} &&`,
or use `git -C {{lane_worktree}}`, and give file tools absolute paths. Put
every temporary file (saved diffs, copies, samples, scripts) in
{{stage_tmp}}, never in /tmp: that directory is this stage's own scratch
space, and it is removed when the lane closes. Before every commit, confirm
that `git -C {{lane_worktree}} branch --show-current` prints {{lane_branch}}.

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
   created, never build output.
3. Run one build or test command at a time and wait for it. If the runtime
   moves a command to the background, wait for its completion notice.
4. Restore a mutation with a text edit, never with a git command, and confirm
   the restore with `diff` against a copy saved in {{stage_tmp}}.
5. Prove a defect before you fix it: a failing test first, with its output in
   your report. A fixture asserts its own shape before a test asserts the
   behavior.
6. The project's commands: {{commands}}. The gates, in this order, one at a
   time: {{gates}}.
7. The plan expects this task to change: {{files}}. Stay within those files
   where you can. If the work needs another file, change it, and list every
   file outside that list in your report under "Unexpected files".
8. Change what the specification asks for. {{owner_rule}}
9. Write your full report to {{report}}: file paths, line numbers, test
   names, and command output. Report a failure as a failure, and say when you
   skipped a step. Your final message is short: the report's path, the gate
   results, and a summary line.

The owner's decisions for this task are final and override any default the
specification recommends: {{owner_decisions}}.

The specification, copied from the plan document:

{{spec}}

Related plans: {{prior_plans}}.
```

```template:implement
{{common header}}

STAGE: IMPLEMENT.

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
   mutation that no test catches is a finding: add the test. List every
   mutation in your report so the reviewers can re-run them.
4. Update every comment and doc that the change makes false.
5. Run every gate, one at a time.
6. Commit on {{lane_branch}} with the message "{{task_id}}: implement".

If the specification can't be met as written (a premise is false, an API
doesn't exist), stop after the proof step, commit nothing, and start your
final message with "BLOCKED:" and the blocker in one sentence. Put the
evidence in the report. Don't redesign the task.

Report: each file you changed and why; each test, red before and green after,
with the failing output; the mutation table; each gate result; each deviation
from the specification with its reason; each open question.
{{landed_duty}}
```

```template:implement-measurement
{{common header}}

STAGE: MEASURE.

Run the measurements the specification lists. Change no tracked file and
commit nothing. Record each command, its output, and the machine it ran on.

If a measurement can't be taken as specified, start your final message with
"BLOCKED:" and the reason in one sentence.

Report: each number with the command that produced it.
{{landed_duty}}
```

```template:review-report
{{common header}}

STAGE: REVIEW, PART 1 OF 2: REPORT THE PROBLEMS.

Read the implementer's report, {{scratch}}/{{task_id}}_implement.md, and the
lane's whole change:
`git -C {{lane_worktree}} diff $(git -C {{lane_worktree}} merge-base HEAD {{integration_branch}})`.

In this part you find and prove problems; you change no product code. You
fix them in part 2, after your report is committed, so report everything you
find, not only what is easy to fix.

Look for, in this order:
1. A requirement or acceptance criterion of the specification that the work
   doesn't meet.
2. A wrong result, a crash, or data loss, including in cases the
   specification doesn't address.
3. A sentence of the specification or an acceptance criterion with no test,
   and a test that proves nothing (check that each fixture reaches the code
   path its test claims).
4. {{mutation_duty}}

Label every finding with a scope:
- `spec`: the work violates the specification or an acceptance criterion.
- `defect`: a wrong result, a crash, or data loss in a case the
  specification doesn't address, with a small fix.
- `beyond`: a behavior change the specification doesn't ask for (a feature,
  extra validation, wider input support). You won't fix these.

Prove each `spec` and `defect` finding: a failing test named with the prefix
`review_proof_` (marked skipped or expected-to-fail so the tree stays green),
a trace through the code with file and line, or a measurement. A finding
with no proof is a suspicion; label it as one.

Commit your proof tests, and nothing else, with the message
"{{task_id}}: review proofs". If you have none, commit nothing.

Report, with these headings: "Findings" (numbered; each with its scope, a
severity (P1: a wrong result or data loss; P2: must fix; P3: minor), the
proof, and the fix you intend); "Beyond" (one line each); "Needs owner".
Your final message lists each finding in one line. Then stop: your
instructions for part 2 follow.
```

```template:review-fix
{{common header}}

STAGE: REVIEW, PART 2 OF 2: FIX.

Fix the `spec` and `defect` findings in your report,
{{scratch}}/{{task_id}}_review-report.md. Add a test for each missing
coverage item. Fix nothing listed under "Beyond" or "Needs owner", and change
nothing else.

For each fixed finding, turn its `review_proof_` test into a real test with a
real name (no prefix, no skip) that pins the correct behavior. When you are
done, `grep -rn review_proof_` over the source tree finds nothing: remove a
proof test you decided not to act on, and say why.

Run every gate, one at a time. Commit on {{lane_branch}} with the message
"{{task_id}}: review fixes" if anything changed. End with
`git -C {{lane_worktree}} status --porcelain` printing nothing.

Report: for each finding, what you changed (file, line) and the test that
pins it; each gate result with the test counts; the "Beyond" and "Needs
owner" items again, so the coordinator reads them in one place.
{{landed_duty}}
```

```template:second_review-report
{{common header}}

STAGE: SECOND REVIEW, PART 1 OF 2: REPORT THE PROBLEMS.

You are the second and last reviewer of this task. Read the coordinator's
brief first, {{context}}: the tasks already landed, the tasks still to come,
and the open residuals. Then read the earlier reports in {{scratch}}
({{task_id}}_implement.md, {{task_id}}_review-report.md,
{{task_id}}_review-fix.md) and the lane's whole change:
`git -C {{lane_worktree}} diff $(git -C {{lane_worktree}} merge-base HEAD {{integration_branch}})`.

In this part you change no product code. Check, in this order:
1. The first review: each finding it fixed is fixed correctly, its tests pin
   the right behavior, and it missed nothing the specification requires.
   {{mutation_duty}}
2. Scope: nothing beyond the specification crept in, in the implementation
   or in the first review's fixes.
3. Quality: the change is as simple and clear as it can be, follows the
   existing code's conventions, and fits the project and the tasks still to
   come (it doesn't make an upcoming task harder). Name each refactor you'd
   make and why.

Label every finding with a scope: `spec` and `defect` as the first review
used them; `creep` for something beyond the specification that should come
out; `quality` for a simplification, a clarity change, or a refactor that
keeps behavior the same; `beyond` for a behavior change the specification
doesn't ask for (you won't make these).

Prove each `spec` and `defect` finding as the first review did, with
`review_proof_` tests (skipped or expected-to-fail), and commit them, and
nothing else, with the message "{{task_id}}: second review proofs".

Report, with these headings: "Findings" (numbered, each with its scope,
severity, evidence, and intended change); "Beyond"; "Needs owner". Your final
message lists each finding in one line. Then stop: your instructions for
part 2 follow.
```

```template:second_review-fix
{{common header}}

STAGE: SECOND REVIEW, PART 2 OF 2: FIX.

Act on your report, {{scratch}}/{{task_id}}_second_review-report.md: fix the
`spec` and `defect` findings, remove the `creep`, and make the `quality`
changes. A refactor keeps behavior the same: the tests stay green without
changes to what they assert. Change nothing listed under "Beyond" or "Needs
owner".

Turn each `review_proof_` test into a real test with a real name, or remove
it and say why; `grep -rn review_proof_` must find nothing. Run every gate,
one at a time. Commit on {{lane_branch}} with the message
"{{task_id}}: second review fixes" if anything changed. End with
`git -C {{lane_worktree}} status --porcelain` printing nothing.

Report: each change (file, line) and why; each gate result with the test
counts; the "Beyond" and "Needs owner" items again.
{{landed_duty}}
```

```template:fix
{{common header}}

STAGE: FIX.

Read the earlier reports of this task in {{scratch}}. These decisions are
final:

{{decisions}}

Apply each accepted item. Prove a defect with a failing test before you fix
it, and give every behavior change a test that pins it. Change nothing the
decisions don't ask for. Run every gate, one at a time. Commit on
{{lane_branch}} with the message "{{task_id}}: fix" if anything changed. End
with `git -C {{lane_worktree}} status --porcelain` printing nothing.

Report: for each decision, what you changed (file, line) and the test that
pins it; each gate result with the test counts.
{{landed_duty}}
```

```template:delegate
{{common header}}

STAGE: COORDINATOR REVIEW (delegated).

The coordinator has handed you its review of this task. Read its brief
first, {{context}}, then every report of this task in {{scratch}}, then the
lane's whole change:
`git -C {{lane_worktree}} diff $(git -C {{lane_worktree}} merge-base HEAD {{integration_branch}})`.

Do the coordinator's job for this one task:
1. Review the change against the specification and the brief: correctness,
   scope, and fit with the tasks already landed and still to come.
2. Decide each item the reports list under "Beyond": apply it only when it
   is small, serves the task's intent, and nothing in the brief rules it
   out; otherwise record it under "Residuals" with the reason.
3. Fix what your review finds: prove a defect with a failing test first,
   and give every change a test.
4. Run every gate, one at a time. Commit on {{lane_branch}} with the message
   "{{task_id}}: coordinator review" if anything changed. End with
   `git -C {{lane_worktree}} status --porcelain` printing nothing.

Report: your decision on each "Beyond" item; each change (file, line) and
why; each gate result; "Residuals".
{{landed_duty}}
```
