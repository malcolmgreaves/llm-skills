# graph.yaml schema

`graph.yaml` is the machine-readable half of an executable plan. The
coordinator and `scripts/plan.py` read and write it. The plan document is the
human-readable half; `graph.yaml` points at its task sections by anchor.

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
| `worktree_root` | path | yes | Lanes are created at `<worktree_root>/<id>`. `~` expands. |
| `scratch_root` | path | yes | Each lane's scratch directory is `<scratch_root>/<id>`. Put it on a disk with room; a lane's build directory is not here (it stays in the worktree). |
| `branch_prefix` | string | yes | Lane branches are `<branch_prefix><id>`, for example `lane/`. |
| `lane_cap` | integer ≥ 1 | yes | The most lanes that run at one time. Each lane builds with every core and owns a build directory, so the machine sets this. |
| `autonomy` | integer 0–4 | yes | When the coordinator stops for the user. See `SKILL.md`. |
| `commit_policy` | `keep` or `squash` | yes | Whether a lane's commits land as they are (fast-forward) or as one commit. |
| `models` | map | yes | `implement`, `review`, `fix`, `final_review`: the model id for each chain stage. |
| `effort` | map | no | Per-stage effort override, for example `final_review: xhigh`. |
| `commands` | map | no | `build`, `test`, `lint`, `check`, `run`: the project's commands, named in the lane prompts. |
| `gates` | list of strings | yes | The commands the coordinator runs at integration, in order. A lane runs them too before it reports. |
| `guidelines` | list of paths | no | Style, design, and architecture files every agent reads first. |
| `prior_plans` | list of paths | no | Plans the tasks cite. |
| `notes` | string | no | Free text for the coordinator (machine limits, disk rules, anything that does not fit a field). |

## `nodes[]`

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Unique. Letters, digits, `-`, `_`. It is the anchor id, the branch suffix, and the worktree name, so keep it short. |
| `title` | string | yes | One line. |
| `spec` | string | yes | Where the task's section lives: `#<anchor>` in `plan.spec`, or `<path>#<anchor>` in another document. `plan.py validate` confirms the anchor exists. |
| `kind` | `code`, `docs`, `plan`, `measurement` | yes | `code` runs the full chain. `docs` and `plan` run `docs-only`. `measurement` runs one implement stage that reports numbers and changes no code. |
| `chain` | `default`, `docs-only`, `none` | no | Overrides the chain `kind` implies. `none` means the coordinator does the task itself (a plan edit, a merge). |
| `size` | `S`, `M`, `L` | yes | S: under two hours of agent time. M: one chain of a few hours. L: the largest single chain you allow. |
| `deps` | list of ids | no | Hard dependencies. The task starts only when each one is `done`. |
| `soft_deps` | list of ids | no | Preferred order. The scheduler starts the task after them when it can, and starts it anyway when the cap has room and nothing else is ready. |
| `files` | list of paths | code: yes | Every file the task changes, tests included. Two tasks with a common file never run at the same time. A new file the task creates belongs here too. |
| `alone` | bool | no | The task runs with no other lane open. For a refactor that moves many files. |
| `owner_decisions` | list of maps | no | Each item: `question`, `default`, `answer` (empty until the user answers). At autonomy 4 the coordinator takes `default`; at 3 and below it stops until `answer` is set. |
| `status` | enum | yes | `planned` (not started; `next` decides when it can start), `running` (lane open, first half), `review` (findings decided, second half), `integrating`, `done`, `blocked` (abandoned; its dependents wait), `skipped` (counts as done for its dependents). `plan.py set` changes it. |
| `lane` | path | runtime | The worktree path while the lane is open; `close` and `abandon` clear it. |
| `branch` | string | runtime | The lane branch while the lane is open. |
| `commit` | string | runtime | The integration commit once `done`. |
| `log` | list of strings | runtime | `plan.py set` appends one timestamped line per change. |

## Anchors

The anchor is the contract between the plan document and the graph.

- **Markdown**: a heading, then the marker `<!-- task: <id> -->` on its own
  line directly after it. `plan.py excerpt` returns the text from that heading
  to the next heading of the same or a higher level. A heading with a
  `{#<id>}` attribute, an `<a id="<id>"></a>` line under a heading, or a
  heading whose slug equals the id also counts. A `#` line inside a fenced
  code block is not a heading, so code samples in a task's section are safe.
- **HTML**: `id="<id>"` on the heading element (`h1` to `h6`; the templates
  use `h3`). An `id` on any other element does not count. The excerpt runs to
  the next heading of the same or a higher level.

Never rename an anchor without changing the node's `spec`; `validate` reports
the mismatch.

## Derived facts

`plan.py` derives these; don't write them by hand:

- **Exclusion**: two nodes whose `files` intersect are mutually exclusive
  lanes. The first to start holds the other.
- **Waves**: the topological layers of the hard dependencies, which is the
  most concurrency the plan allows before exclusions and the cap.
- **Agent runs**: 4 per `default` chain, 2 per `docs-only`, 1 per
  `measurement`, 0 per `none`, before any reopened stage. `waves` prints
  the total for the unfinished tasks.
- **Ready set**: status `planned`; `deps` all `done` or `skipped`; no exclusion with a running lane; no
  running `alone` lane and (if `alone`) no other lane running; a free slot
  under `lane_cap`; no unanswered owner decision at autonomy 3 or below.

## Example

```yaml
plan:
  title: Remaining work, autumn campaign
  spec: remaining_work.html
  integration_branch: main
  worktree_root: ~/.local/state/git/worktrees/myrepo/lane
  scratch_root: /Volumes/scratch/lanes
  branch_prefix: lane/
  lane_cap: 3
  autonomy: 2
  commit_policy: keep
  models:
    implement: claude-opus-5-5
    review: claude-opus-5-5
    fix: claude-opus-5-5
    final_review: fable
  effort:
    final_review: xhigh
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
    Each lane's build directory reaches 20 GB; clean it after integration.
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
