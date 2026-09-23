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
- Python 3.11 with `uv`, for `scripts/plan.py` (`pyyaml` is declared inline).
- An agent runtime that can run subagents in the background, ideally with a
  model id and an effort level per agent. The chain reference shows a script
  for a `Workflow` tool whose `agent()` takes `model` and `effort`, and a
  fallback that sequences plain background subagents by hand.
- A machine with room for one full build per lane. The lane cap is a graph
  setting because the machine decides it.

## Bundled files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The skill: the two modes, the vocabulary, the autonomy levels, the rules every prompt carries. |
| `scripts/plan.py` | `validate`, `waves`, `next`, `set`, `render`, `lane` (`open`, `integrate`, `close`, `abandon`), `excerpt` over `graph.yaml`. Runs only read-only git; prints every command that changes a repository. |
| `scripts/test_plan.py` | Tests for `plan.py`, including a full lane in a temporary git repository: `uv run scripts/test_plan.py`. Agents never need it. |
| `references/graph-schema.md` | Every field of `graph.yaml`, the anchor rules, the derived facts, and a full example. Read while drafting. |
| `references/chain.md` | The four stage prompts as templates with placeholders, the decision step between the halves, and the workflow script shape. Read before the first lane. |
| `references/coordinator.md` | The coordinator's procedure: pre-flight, the iteration, deciding findings, the integration protocol, the conflict rules, the failure cases, the final report. Read before the first iteration. |
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

**Why stages commit.** Stages 1, 3, and 4 commit on the lane branch, and
stage 2 leaves its proof tests uncommitted for stage 3 to convert or remove.
The lane is clean when the chain ends, so the integration rebase works and
the merge has something to land. Every stage diffs against the merge base,
not the integration branch, so work that other lanes land doesn't show up
reversed in a review.

**Why autonomy is a number.** The same plan runs unattended overnight at
level 4 and under full control at level 0. Level 2 (stop for P1 findings,
owner decisions, and destructive actions) was the right default in practice.

**What to be careful about when editing.** The `SKILL.md` body must stay
under 500 lines; move detail into `references/`. The stage prompts in
`chain.md` carry the sentence about relayed chat messages for a reason: a
mid-turn user message reached a running agent and it answered the message
instead of doing its task. Keep that sentence first.
