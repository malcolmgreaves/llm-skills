# executable-plan

> Human-facing docs. Agents read `SKILL.md`, never this file, so nothing here
> is required for the skill to work. See the repository's `AGENTS.md`.

Turns a body of engineering work into an executable plan and runs it with
many agents at once. The plan is two files: a plan document (Markdown or
HTML) with one anchored section per task, and a `graph.yaml` that records each
task's dependencies, the files it changes, and its status. The execution is a
coordinator loop in the main session: it opens one git worktree per ready
task, runs a four-stage chain of agents in it (implement, adversarial review,
fix, final review), decides the review findings, integrates the lane into the
main branch, and repeats until the graph is done.

The skill separates two things that are easy to tangle: the machinery (lanes,
the chain, the coordinator, the integration protocol) and the work (the plan
document and the graph). The machinery is the same for every project; the
work is what you discuss and approve before anything runs.

## When it triggers

Prompts such as:

- "Turn the remaining plans into an executable plan and run them in parallel."
- "Plan this backlog as a dependency graph with worktrees as lanes."
- "Resume the campaign from `graph.yaml`."
- "Orchestrate agents over these tasks; you coordinate, they implement."

What it doesn't cover: writing the design of a single feature (a plan section
cites a design; it does not replace one), and code review of a single pull
request outside a plan (use a review skill for that).

## Requirements

- git 2.20 or later, for worktrees.
- Python 3.11 with `uv`, for `scripts/plan.py` (`ruamel.yaml` is declared
  inline). POSIX only: `plan.py` locks the graph with `fcntl`.
- An agent runtime that can run subagents in the background, ideally with a
  model id and an effort level per agent. The chain reference shows a script
  for a `Workflow` tool whose `agent()` takes `model` and `effort`, and a
  fallback that sequences plain background subagents by hand.
- A machine with room for one full build per lane. The lane cap is a graph
  setting because the machine decides it.

## Bundled files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The skill: the two modes, the vocabulary, the iteration, the autonomy levels, the edge cases. |
| `scripts/plan.py` | `validate`, `waves`, `next`, `set`, `render`, `lane` (`open`, `integrate`, `close`, `abandon`, `discard`), `excerpt`, `prompt`, `landed` over `graph.yaml`. Runs only read-only git; prints every command that changes a repository as one `&&` chain. |
| `scripts/test_plan.py` | Tests for `plan.py`: anchors, validation, scheduling, concurrent writes, and full lanes (land, crash and recover, abandon mid-rebase) in temporary git repositories. `uv run scripts/test_plan.py`. Agents never need it. |
| `references/graph-schema.md` | Every field of `graph.yaml`, the anchor rules, the derived facts, and a full example. Read while drafting. |
| `references/chain.md` | The chains, the scope labels for findings, and the stage prompt templates that `plan.py prompt` renders (fenced as `template:<name>`), plus reopening a lane and running a chain with or without a workflow tool. Read before the first lane. |
| `references/coordinator.md` | The coordinator's procedure: pre-flight, the iteration, owner decisions, deciding findings, integration, the conflict rules, giving up, resuming, the failure cases, the final report. Read before the first iteration. |
| `assets/graph-template.yaml` | A commented skeleton of `graph.yaml`. |
| `assets/plan-template.md` | A plan document skeleton in Markdown, with the `<!-- task: id -->` marker convention. |
| `assets/plan-template.html` | The same skeleton as a self-contained HTML page, with `id` anchors on the task headings. |

## Design notes

**Why two files and not one.** A YAML graph is easy to validate, toposort,
and update from a script, and hard to read as a plan. A prose plan is the
opposite. The anchor is the contract between them: `graph.yaml` never
duplicates a specification, it points at one, and `plan.py excerpt` copies the
section into an agent prompt so the coordinator never paraphrases a spec.

**Why the lane never edits the plan or the graph.** Two lanes that both
update a tracker file conflict at every integration. Making the coordinator
the only writer of those two files, serially, at integration time, removed
that whole class of conflict in the campaign this skill came from.

**Why exclusions are derived from `files` instead of declared.** People
forget to declare an edge; they rarely forget which files a task touches. The
list is also what makes the "new tests in new files per lane" rule checkable.

**Why four stages and a human decision in the middle.** In the originating
campaign, the adversarial review found a real defect in most tasks, and the
final review found a further one that the adversarial review missed in about
a third of them. The decision step between the halves is where the owner's
rules enter (which finding is a real defect, which is scope creep, which
becomes a new task). A bound or guard the coordinator mandates must be proven
to fire by a test, because one mandated guard turned out to be a tautology
that no test could catch.

**Why `plan.py` prints commands instead of running them.** Every destructive
step (worktree removal, branch deletion, fast-forward) stays in the
coordinator's view and under the runtime's own permission checks. The script
does run read-only git: `lane integrate` refuses a lane with uncommitted
changes or no commits, because the failure it prevents is silent (the task
is marked done and nothing lands).

**Why every stage commits.** Each stage ends with a commit on the lane
branch, so the lane is clean between stages. A stage that dies is rerun from
its predecessor's commit after `lane ... discard` saves and drops its partial
edits, the integration rebase always has a clean tree, and the merge always
has something to land. Every stage diffs against the merge base, not the
integration branch, so work that other lanes land doesn't show up reversed in
a review.

**Why reports are files.** Each stage writes its report to the lane's scratch
directory and later stages read it there. Passing reports verbatim through
the coordinator costs about six report copies per task; over a 30-task
campaign that is about a million tokens of coordinator context.

**Why stages bind every command to the lane.** In Claude Code a subagent's
shell can return to the session's directory between calls, which is the main
worktree on the integration branch. A stage that ran `cd` once and committed
later would commit to `main`. The header makes every command `cd <lane> &&`
or `git -C <lane>`, and `integrate` refuses a lane whose worktree is not on
its branch.

**Why the graph is locked.** Two `plan.py set` calls at once used to lose an
update: a lane's `running` status vanished and its files stopped excluding
other tasks. `set` now takes a lock in the git directory and writes through a
temporary file. It uses `ruamel.yaml`, so comments the drafter wrote survive.

**What the behavioral test taught.** The same prompt ran on a four-item
backlog with the skill and without it. Both arms passed 9 of 11 hidden
acceptance tests, failing on the same ambiguous sentence. The skill's arm
cost 8× as much and took 11× as long: every S task ran the full four-stage
chain on the strongest model, the plan was a straight line of dependencies,
and the reviewers' mostly beyond-spec findings were accepted. The arm
without the skill landed a small seam commit first and ran two tasks in
parallel. The changes that followed: S tasks default to the `light` chain;
the drafting guidance prefers a cheaper implementing model; `waves` estimates
time, names hub files, and warns about serial plans, with a "Seams" section
in `SKILL.md`; findings carry scope labels that decide them; owner questions
are asked before execution; and `plan.py prompt` and `plan.py landed` replace
two error-prone manual steps.

**What the adversarial review of this skill found.** An Opus review at xhigh
effort walked the protocol literally in scratch repositories. Besides the
items above, it found: `alone` tasks started in the same batch as others;
soft dependencies had no effect; anchors could resolve to the wrong section;
the owner's answer never reached the stages; a crash between the merge and
`status=done` could not be recovered; and `abandon` during a stopped rebase
deleted commits. Each has a regression test in `scripts/test_plan.py`.

**Why autonomy is a number.** The same plan runs unattended overnight at
level 4 and under full control at level 0. Level 2 (stop for P1 findings,
owner decisions, and destructive actions) was the right default in practice.

**What to be careful about when editing.** The `SKILL.md` body must stay
under 500 lines; move detail into `references/`. The stage prompts in
`chain.md` carry the sentence about relayed chat messages for a reason: a
mid-turn user message reached a running agent and it answered the message
instead of doing its task. Keep that sentence first.
