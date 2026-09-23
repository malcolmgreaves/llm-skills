# <Plan title>

> **Executable plan.** Status: Planned. The graph is `graph.yaml` beside this
> file; run `plan.py render graph.yaml` for the live status. Each task section
> below carries a marker `<!-- task: <id> -->` that `graph.yaml` points at.

## Scope

What this plan covers, in three to six sentences, and the outcome when every
task is done.

## Non-goals

- What this plan does not change, and which plan owns it instead.

## Project settings

The commands, guidelines, models, and lane rules live in `graph.yaml: plan`.
Summarize here what a reader needs without opening the graph: the gates in
order, the guideline files, the lane cap, and the autonomy level.

## Tasks

Each task follows the same shape. Keep the heading and the marker together;
`plan.py excerpt` returns the section from the heading to the next heading of
the same level.

### `<id>`: <title>
<!-- task: <id> -->

**Goal.** One sentence.

**Specification.** What changes, where (files, functions, types), and the
behavior after the change. Cite the prior plan section that decided the
design, and quote the rule the change enforces.

**Acceptance.** The tests that prove it (red before, green after), the
measurements, and the gates. Name the mutations that each new rule must fail.

**Files.** The list that `graph.yaml: files` mirrors.

**Size.** S, M, or L, with one line of reasoning.

**Depends on.** Hard dependencies, then soft dependencies, each with the
reason.

**Owner decisions.** A question only the owner can answer, and the default
you recommend. Omit the heading if there is none.

**As landed.** Empty until the task integrates. The coordinator pastes the
final review's text here: what shipped, deviations, residuals, measurements.

### `<id-2>`: <title>
<!-- task: <id-2> -->

...

## Residuals

Defects found and deferred, each with the task that owns it or the note that
no task does. The coordinator appends here at each integration.
