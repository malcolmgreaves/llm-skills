# graph.yaml schema

`graph.yaml` is the machine-readable half of an executable plan. The
coordinator and `scripts/plan.py` read and write it. The plan document is the
human-readable half; `graph.yaml` points at its task sections by anchor.

`plan.py set` keeps comments and layout when it rewrites the file, and it
serializes concurrent writers with a lock. Quote any scalar YAML would read
as something other than a string: an id such as `"1"`, or a gate that
contains `: `.

## Top level

```yaml
plan:      # the project-wide settings (one map)
nodes:     # the tasks (a list)
```

## `plan`

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `title` | string | yes | The plan's name. |
| `spec` | path | yes | The plan document, relative to `graph.yaml`. `.md` or `.html`. A node's `spec` of the form `#id` resolves against this file. |
| `integration_branch` | string | yes | The branch every lane starts from and lands on. |
| `worktree_root` | path | yes | Lanes are created at `<worktree_root>/<id>`. `~` expands; a relative path is relative to `graph.yaml`. Default to a directory next to the repository (`../<repo>-lanes/worktrees`), or under `$TMPDIR` in a sandbox. Inside the repository, add it to `.git/info/exclude` (`validate` warns). |
| `scratch_root` | path | yes | Each lane's scratch partition is `<scratch_root>/<id>`: prompts, reports, decisions, the brief, saved patches, and one `stage-<name>` temporary directory per prompt. Default to `../<repo>-lanes/scratch`. `plan.py clean` reclaims it. |
| `branch_prefix` | string | yes | Lane branches are `<branch_prefix><id>`, for example `lane/`. |
| `lane_cap` | integer ≥ 1 | yes | The most lanes that run at one time. Each lane builds with every core and owns a build directory, so the machine sets this. |
| `autonomy` | integer 0–4 | yes | When the coordinator stops for the user. See `SKILL.md`. The user names it; `plan.py approve` records it. |
| `approved` | string | runtime | The user's approval to start: a timestamp, the autonomy level, and the user's words. `plan.py approve` writes it; `lane open` refuses without it. |
| `commit_policy` | `keep` or `squash` | yes | Whether a lane's commits land as they are (fast-forward) or as one commit. |
| `workflow` | map | no | Size (`S`, `M`, `L`) to the list of stages its tasks run, in the order `implement`, `review`, `second_review`, `fix`; `review` is required. Defaults: S `[implement, review]`; M and L `[implement, review, second_review]`. The user picks these at draft time, including whether M and L end with `fix`. |
| `models` | map | yes | Stage to model id, for every stage the workflows use: `implement`, `review`, `second_review`, `fix`, `delegate`, and `resolve` and `resolution_review` when overlap is on. The user picks them; `validate` refuses a missing one. |
| `effort` | map | no | Stage to the requested effort: `low`, `medium`, `high`, `xhigh`, `max`. Advisory where the runtime can't set it (the Agent tool can't); the log records what was applied. |
| `coordinator` | `full`, `merge`, `delegate` | no | How much the coordinator reviews (`references/coordinator.md`). Default `full`. `delegate` adds a `delegate` stage to every workflow. |
| `file_overlap` | integer ≥ 0 or `off` | no | The most open lanes that can list or change one file. Default `2`. `off` or `0` never opens two lanes on one file. With 2 or more, a landing can conflict and run the resolve stages. |
| `dependency_overlap` | `off`, `interfaces`, `all` | no | Default `off`: a task starts after its dependencies land. `interfaces`: a task can start once a dependency in its `interface_deps` has started. `all`: once any dependency has started. A task always lands after its dependencies. |
| `changes` | list of strings | runtime | `plan.py configure` appends one timestamped line per setting it changes. |
| `stage_minutes` | map | no | Model-neutral minutes per stage for an S task, used by `waves` until this repository has measured timings. Defaults: implement 3, review 3.5, second_review 3, fix 2.5, delegate 2.5. M doubles them, L quadruples them. |
| `timings` | path | no | Where measured stage timings are kept. Default: `executable-plan/timings.jsonl` in the repository's git directory, shared by every worktree and every plan in the repository. |
| `commands` | map | no | `build`, `test`, `lint`, `check`, `run`: the project's commands, named in the lane prompts. |
| `gates` | list of strings | yes | The commands every stage runs, and landing runs again, in order. Each gate is a string; quote one that contains `: `. |
| `guidelines` | list of paths | no | Style, design, and architecture files every agent reads first. |
| `prior_plans` | list of paths | no | Plans the tasks cite. |
| `notes` | string | no | Free text for the coordinator (machine limits, disk rules, anything that does not fit a field). |

## `nodes[]`

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Unique. Letters, digits, `-`, `_`; quote an all-digit id. It is the anchor id, the branch suffix, and the worktree name, so keep it short. |
| `title` | string | yes | One line. |
| `spec` | string | yes | Where the task's section lives: `#<anchor>` in `plan.spec`, or `<path>#<anchor>` in another document. `plan.py validate` confirms the anchor exists and is unambiguous, and that no two nodes share a spec. |
| `kind` | `code`, `docs`, `plan`, `measurement` | yes | `code` runs its size's workflow; `docs` and `plan` run implement then review; `measurement` runs implement alone, changes no code, and runs alone. |
| `size` | `S`, `M`, `L` | yes | Picks the workflow. S: a small, contained change. M: several files or a new component. L: the largest single task you allow. |
| `escalate` | enum | no | Runs the workflow of the next size up. Only `untrusted-input`, `persistence`, `security`, `concurrency`, or `breaking-interface` (a breaking change to an existing public interface). |
| `chain` | `none` | no | The coordinator does the task itself, with no lane (a seam, a plan edit, a merge). |
| `deps` | list of ids | no | Hard dependencies. The task starts when each one is `done`, or earlier under `dependency_overlap`; it lands only after each one is `done`. |
| `interface_deps` | list of ids | no | The dependencies in `deps` whose specification fixes the interface this task uses. With `dependency_overlap: interfaces`, the task can start once they have started. |
| `soft_deps` | list of ids | no | Preferred order. The task doesn't start while one of them is running or starting in the same round; it doesn't wait for one that can't start yet. |
| `files` | list of paths | code: yes | The files the task is expected to change, tests included. A scheduling hint: two tasks with a common file never run at the same time. Agents may change other files when the work needs them; they report each one, and landing names it so the coordinator can add it. |
| `alone` | bool | no | The task runs with no other lane open, and no lane opens until it has run. For a refactor that moves many files. Defaults to `true` for a `measurement` task, `false` otherwise. |
| `owner_decisions` | list of maps | no | Each item: `question`, `default`, `answer` (empty until the user answers). At autonomy 4 the default is taken and reported; at 3 and below the task waits until `answer` is set. Record an answer with `plan.py set graph.yaml <id> "answer=<index from 0>:<text>"`. |
| `status` | enum | yes | `planned` (not started), `running` (the workflow is running), `review` (the coordinator is deciding, or the fix stage is running), `waiting` (an owner-level question is with the user; the lane keeps its slot), `conflicted` (the landing's rebase conflicted; the resolve stages run), `integrating`, `done`, `blocked` (abandoned; its dependents wait), `skipped` (counts as done for its dependents). `plan.py set` changes it. |
| `lane` | path | runtime | The worktree path while the lane is open; `close` and `abandon` clear it. |
| `branch` | string | runtime | The lane branch while the lane is open; after `abandon`, `abandoned/<id>`, which keeps the lane's commits. |
| `commit` | string | runtime | The integration commit once `done`. |
| `log` | list of strings | runtime | One timestamped line per change. `plan.py prompt` adds a line for each prompt it starts (`stage=<name> start model=… effort=… applied=…`); those lines and the report files give each stage's duration. |

## Anchors

The anchor is the contract between the plan document and the graph.

- **Markdown**: a heading (ATX `###` or setext), then the marker
  `<!-- task: <id> -->` on its own line directly after it (blank lines
  between are fine). `plan.py excerpt` returns the text from that heading to
  the next heading of the same or a higher level. The marker is the anchor
  to use. Without one, `plan.py` falls back, in order, to a heading with a
  `{#<id>}` attribute, an `<a id="<id>"></a>` line under a heading, and a
  heading whose slug equals the id; a fallback that matches more than one
  place is an error, so add a marker.
- **HTML**: `id="<id>"` on the heading element (`h1` to `h6`; the templates
  use `h3`). Ids are case-sensitive, an `id` on any other element does not
  count, and the id must appear once. The excerpt runs to the next heading of
  the same or a higher level.

Lines inside a fenced code block or an HTML comment are never headings or
markers, so code samples and commented-out drafts are safe in a section. A
marker that appears twice, or that is not directly after a heading, is an
error. Never rename an anchor without changing the node's `spec`; `validate`
reports the mismatch.

## Derived facts

`plan.py` derives these; don't write them by hand:

- **Exclusion**: two nodes whose `files` intersect are mutually exclusive
  lanes. The first to start holds the other.
- **Waves**: the topological layers of the hard dependencies.
- **Workflow**: `plan.workflow[size]` (the next size up with `escalate`),
  plus `delegate` in that coordinator mode.
- **Agents**: one per workflow stage (a review is one agent given two
  prompts), plus a fix stage only when findings are accepted.
- **Time**: `waves` runs the real scheduler (dependencies, file exclusions,
  `alone`, the lane cap) over estimated stage durations: the median of this
  repository's measured timings for the stage, size, model, and effort, else
  `stage_minutes`. It prints the finish time and the most lanes open at once.
- **Parallelism and its limits**: `waves` reruns the schedule without the
  file exclusions and without the lane cap, and prints how many lanes the
  dependencies alone allow, how many remain with the file exclusions, and
  how many run with the cap. It lists the file conflicts that cost time:
  task pairs that share a file and that no dependency orders. When the
  schedule never runs two lanes at once, it names the cause (a chain of
  dependencies, shared files, or the lane cap) and the fix for that cause
  (`SKILL.md`, "Seams").
- **Changed files**: `next` also excludes on the files each open lane has
  actually changed so far.
- **Ready set**: status `planned`; `deps` all `done` or `skipped`; no
  unanswered owner decision at autonomy 3 or below; no file shared with an
  open lane (listed or already changed) or another task starting this round; no soft dependency running
  or starting; a free slot under `lane_cap`. An `alone` task overrides the
  rest: when one is ready, it starts by itself if no lane is open, and
  otherwise nothing starts until the open lanes close.

## Example

```yaml
plan:
  title: Remaining work, autumn campaign
  spec: remaining_work.html
  integration_branch: main
  worktree_root: ../myrepo-lanes/worktrees
  scratch_root: ../myrepo-lanes/scratch
  branch_prefix: lane/
  lane_cap: 3
  autonomy: 2
  commit_policy: keep
  coordinator: full
  file_overlap: 2
  dependency_overlap: off
  workflow:
    S: [implement, review]
    M: [implement, review, second_review]
    L: [implement, review, second_review, fix]
  models:
    implement: sonnet
    review: opus
    second_review: opus
    fix: sonnet
    resolve: sonnet
    resolution_review: sonnet
  effort:
    implement: medium
    review: high
    second_review: xhigh
    fix: high
  commands:
    build: cargo build --workspace
    test: cargo test --no-fail-fast -p <crate>
    lint: cargo clippy --workspace --all-targets -- -D warnings
    check: cargo check --workspace
  gates:
    - cargo fmt --all -- --check
    - cargo check --workspace
    - cargo clippy --workspace --all-targets -- -D warnings
    - cargo test --no-fail-fast --workspace
  guidelines:
    - CLAUDE.md
    - docs/design-principles.md
  prior_plans:
    - plans/master.html
  notes: >-
    Each lane's build directory reaches 20 GB; landing removes it with the worktree.
nodes:
  - id: tags
    title: Lightweight tags
    spec: "#tags"
    kind: code
    size: M
    deps: []
    soft_deps: []
    files:
      - crates/repo/src/schema.rs
      - crates/cli/src/commands/tag.rs
    status: planned
  - id: conflict-dir
    title: A directory side of a conflict
    spec: "#conflict-dir"
    kind: code
    size: M
    escalate: persistence
    deps: [tags]
    files:
      - crates/repo/src/schema.rs
      - crates/merge/src/tree_merge.rs
    owner_decisions:
      - question: Drop the subtree at the path (visible, larger report) or keep it (silent in one order)?
        default: drop the subtree
        answer: ""
    status: planned
```
