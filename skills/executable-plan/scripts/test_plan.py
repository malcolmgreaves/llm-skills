#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["ruamel.yaml>=0.18", "pytest>=8"]
# ///
"""Tests for plan.py. Run: uv run scripts/test_plan.py"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from ruamel.yaml import YAML

sys.path.insert(0, str(Path(__file__).parent))
import plan  # noqa: E402

PLAN_MD = """\
# Plan

## Tasks

### `a`: first
<!-- task: a -->

**Specification.** Add the attribute:

```rust
#[ignore = "later"]
# not a heading either
<!-- task: b -->
```

**Acceptance.** This line must appear in the excerpt.

### `b`: second
<!-- task: b -->

Body of b.
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout


def write_graph(path: Path, graph: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        YAML().dump(graph, fh)


def make_repo(tmp: Path, policy: str = "keep", gates: list | None = None, nodes: list | None = None) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    (repo / "plan.md").write_text(PLAN_MD, encoding="utf-8")
    (repo / "x.txt").write_text("base\n", encoding="utf-8")
    graph = {
        "plan": {
            "title": "t", "spec": "plan.md", "integration_branch": "main",
            "worktree_root": str(tmp / "wt"), "scratch_root": str(tmp / "scratch"),
            "branch_prefix": "lane/", "lane_cap": 2, "autonomy": 2, "commit_policy": policy,
            "models": {s: "m" for s in plan.MODEL_STAGES}, "gates": gates or ["true"],
        },
        "nodes": nodes or [
            {"id": "a", "title": "first", "spec": "#a", "kind": "code", "size": "M", "files": ["x.txt"], "status": "planned"},
            {"id": "b", "title": "second", "spec": "#b", "kind": "code", "size": "S", "deps": ["a"], "files": ["y.txt"], "status": "planned"},
        ],
    }
    write_graph(repo / "graph.yaml", graph)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo / "graph.yaml"


def cmds(graph_path: Path, nid: str, action: str) -> str:
    return plan.lane_commands(plan.load(graph_path), graph_path, nid, action)


def run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True)


def open_lane(graph_path: Path, nid: str = "a") -> Path:
    assert run(cmds(graph_path, nid, "open")).returncode == 0
    return plan.root_dir(plan.load(graph_path)["plan"], "worktree_root", graph_path) / nid


def commit_in_lane(wt: Path, nid: str = "a", text: str = "changed\n", name: str = "x.txt") -> None:
    (wt / name).write_text(text, encoding="utf-8")
    git(wt, "add", name)
    git(wt, "commit", "-qm", f"{nid}: implement")


def node(graph_path: Path, nid: str) -> dict:
    return plan.by_id(plan.load(graph_path))[nid]


# ── anchors ────────────────────────────────────────────────────────────────────

def test_excerpt_ignores_hash_lines_and_markers_inside_code_fences(tmp_path):
    graph_path = make_repo(tmp_path)
    text = plan.section(graph_path.parent / "plan.md", "a")
    assert '#[ignore = "later"]' in text
    assert "This line must appear in the excerpt." in text
    assert "Body of b." not in text
    assert plan.section(graph_path.parent / "plan.md", "b").endswith("Body of b.")


def md(tmp_path: Path, text: str) -> Path:
    doc = tmp_path / "p.md"
    doc.write_text(text, encoding="utf-8")
    return doc


def test_a_marker_beats_an_earlier_heading_with_the_same_slug(tmp_path):
    doc = md(tmp_path, "## schema\n<!-- task: schema -->\n#### Migration\nRun it after deploy.\n"
                       "## migration\n<!-- task: migration -->\nThe real spec.\n")
    assert plan.section(doc, "migration").endswith("The real spec.")


def test_setext_and_indented_headings_bound_a_section(tmp_path):
    doc = md(tmp_path, "Tasks\n=====\n\nTask a\n------\n<!-- task: a -->\nbody a\n\n Task b\n------\nbody b\n")
    assert plan.section(doc, "a") == "Task a\n------\n<!-- task: a -->\nbody a"
    doc = md(tmp_path, "## Tasks\n ### a\n<!-- task: a -->\nbody a\n ### b\nbody b\n")
    assert plan.section(doc, "a").endswith("body a")


def test_a_heading_inside_an_html_comment_does_not_end_a_section(tmp_path):
    doc = md(tmp_path, "## a\n<!-- task: a -->\nstart\n<!--\n## old draft heading\n-->\nacceptance\n## b\n")
    assert plan.section(doc, "a").endswith("acceptance")


def test_marker_rules_are_enforced(tmp_path):
    with pytest.raises(plan.AnchorError, match="appears 2 times"):
        plan.section(md(tmp_path, "## a\n<!-- task: a -->\n## c\n<!-- task: a -->\n"), "a")
    with pytest.raises(plan.AnchorError, match="not directly after a heading"):
        plan.section(md(tmp_path, "## a\ntext\n<!-- task: a -->\n"), "a")
    with pytest.raises(plan.AnchorError, match="matches 2 places"):
        plan.section(md(tmp_path, "## a\nx\n### a\ny\n"), "a")


def test_html_anchor_is_a_case_sensitive_heading_id_outside_comments(tmp_path):
    doc = tmp_path / "p.html"
    doc.write_text('<h2 id="tasks">Tasks</h2><div data-id="a">x</div>'
                   '<!-- <h3 id="b">OLD SPEC</h3> --><h3 id="B">upper</h3><h3 id="b">b</h3><p>Body of b.</p>',
                   encoding="utf-8")
    with pytest.raises(plan.AnchorError, match='no heading with id="a"'):
        plan.section(doc, "a")
    assert plan.section(doc, "b") == "b\nBody of b."
    doc.write_text('<h3 id="b">1</h3><h3 id="b">2</h3>', encoding="utf-8")
    with pytest.raises(plan.AnchorError, match="appears 2 times"):
        plan.section(doc, "b")


# ── validation ─────────────────────────────────────────────────────────────────

def test_validate_passes_and_rejects_a_missing_anchor(tmp_path):
    graph_path = make_repo(tmp_path)
    assert plan.validate(plan.load(graph_path), graph_path) == ([], [])
    data = plan.load(graph_path)
    data["nodes"][0]["spec"] = "#nope"
    errors, _ = plan.validate(data, graph_path)
    assert any("no section for task 'nope'" in e for e in errors)


def test_validate_rejects_bad_yaml_shapes(tmp_path):
    graph_path = make_repo(tmp_path, gates=[{"python3 -c 'x'": "y"}])
    data = plan.load(graph_path)
    data["nodes"][1]["deps"] = "a"
    data["nodes"].append({"id": 1, "title": "t", "spec": "#b", "kind": "code", "size": "S", "status": "planned"})
    errors, _ = plan.validate(data, graph_path)
    assert "b: deps must be a list" in errors
    assert any("every gate must be a string" in e for e in errors)
    assert "id 1 must be a string; quote it in graph.yaml" in errors
    assert any("same spec as b" in e for e in errors)


def test_set_keeps_comments_and_rejects_a_bad_answer_index(tmp_path):
    graph_path = make_repo(tmp_path)
    graph_path.write_text("# drafter's note\n" + graph_path.read_text() + "extra: \"yes\"\n", encoding="utf-8")
    plan.main(["set", str(graph_path), "a", "status=running", "log=" + "x" * 150])
    text = graph_path.read_text()
    assert text.startswith("# drafter's note\n") and 'extra: "yes"' in text
    assert "x" * 150 in text
    with pytest.raises(SystemExit, match="no owner decision at index '-1'"):
        plan.main(["set", str(graph_path), "a", "answer=-1:x"])


def test_concurrent_set_calls_lose_no_update(tmp_path):
    nodes = [{"id": f"t{i}", "title": "t", "spec": "#a" if i == 0 else f"#t{i}", "kind": "docs", "size": "S",
              "status": "planned"} for i in range(8)]
    graph_path = make_repo(tmp_path, nodes=nodes)
    procs = [subprocess.Popen([sys.executable, str(plan.SELF), "set", str(graph_path), f"t{i}", "status=running"])
             for i in range(8)]
    assert all(p.wait() == 0 for p in procs)
    assert [n["status"] for n in plan.load(graph_path)["nodes"]] == ["running"] * 8


# ── scheduling ─────────────────────────────────────────────────────────────────

def sched(nodes: list[dict], cap: int = 3, autonomy: int = 2) -> tuple[list[str], dict[str, str]]:
    data = {"plan": {"lane_cap": cap, "autonomy": autonomy}, "nodes": nodes}
    start, hold, _ = plan.next_ready(data)
    return [n["id"] for n in start], dict(hold)


def n(nid: str, **kw) -> dict:
    return {"id": nid, "kind": "code", "size": "S", "status": "planned", **kw}


def test_an_alone_task_starts_by_itself_and_open_lanes_drain_for_it():
    start, hold = sched([n("r", alone=True, size="L"), n("a"), n("b")])
    assert start == ["r"] and hold == {"a": "`r` runs alone", "b": "`r` runs alone"}
    start, hold = sched([n("r", alone=True), n("a"), n("x", status="running")])
    assert start == [] and hold["a"] == "held so the open lanes drain for `r`"
    start, hold = sched([n("m", kind="measurement"), n("a")])
    assert start == ["m"]


def test_a_soft_dependency_that_is_running_or_starting_holds_the_task():
    start, hold = sched([n("h"), n("a", soft_deps=["h"])])
    assert start == ["h"] and hold["a"] == "starts after its soft dependencies: h"
    start, hold = sched([n("h", deps=["z"]), n("z", status="running"), n("a", soft_deps=["h"])])
    assert start == ["a"]


def test_next_respects_files_owner_decisions_and_blocked_deps():
    start, hold = sched([n("a", files=["x"]), n("b", files=["x"])])
    assert start == ["a"] and hold["b"].startswith("shares files")
    start, hold = sched([n("a", owner_decisions=[{"question": "Q?", "default": "d", "answer": ""}])])
    assert hold == {"a": "needs the owner's answer: Q?"}
    start, _ = sched([n("a", owner_decisions=[{"question": "Q?", "default": "d", "answer": ""}])], autonomy=4)
    assert start == ["a"]
    _, hold = sched([n("a", status="blocked"), n("b", deps=["a"])])
    assert hold == {"b": "waits for a (blocked)"}


def test_next_reports_finished_with_the_blocked_tasks(tmp_path, capsys):
    graph_path = make_repo(tmp_path)
    data = plan.load(graph_path)
    data["nodes"][0]["status"] = "done"
    data["nodes"][1]["status"] = "blocked"
    plan.save(graph_path, data)
    plan.main(["next", str(graph_path)])
    assert "FINISHED: no lane is open and nothing can start; blocked, for the user: b" in capsys.readouterr().out


def test_waves_counts_agent_runs(tmp_path, capsys):
    graph_path = make_repo(tmp_path)
    data = plan.load(graph_path)
    data["nodes"][1]["kind"] = "docs"
    plan.save(graph_path, data)
    assert plan.main(["waves", str(graph_path)]) == 0
    out = capsys.readouterr().out
    assert "wave 1: a" in out and "wave 2: b" in out
    assert "agent runs for the 2 unfinished tasks: 6 (2 on the final-review model)" in out


# ── lanes ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("policy", ["keep", "squash"])
def test_full_lane_lands_the_work_and_closes(tmp_path, policy):
    graph_path = make_repo(tmp_path, policy=policy)
    repo = graph_path.parent
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    out = run(cmds(graph_path, "a", "integrate"))
    assert out.returncode == 0, out.stderr
    assert (repo / "x.txt").read_text() == "changed\n"
    assert node(graph_path, "a")["commit"] == git(repo, "rev-parse", "--short", "HEAD").strip()
    if policy == "squash":
        assert "Plan-Task: a" in git(repo, "log", "-1", "--format=%B")
    (wt / "__pycache__").mkdir()  # untracked gate output must not block the close
    assert run(cmds(graph_path, "a", "close")).returncode == 0
    assert not wt.exists() and "lane/a" not in git(repo, "branch", "--list")
    assert node(graph_path, "a").get("lane") is None


def test_integrate_stops_at_a_failing_gate(tmp_path):
    graph_path = make_repo(tmp_path, gates=["grep -q base x.txt"])
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    assert run(cmds(graph_path, "a", "integrate")).returncode != 0
    assert (graph_path.parent / "x.txt").read_text() == "base\n"
    assert node(graph_path, "a")["status"] == "running"


def test_integrate_refusals(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    with pytest.raises(SystemExit, match="no commits beyond main"):
        cmds(graph_path, "a", "integrate")
    (wt / "x.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="uncommitted changes"):
        cmds(graph_path, "a", "integrate")
    git(wt, "commit", "-qam", "a: implement")
    git(wt, "checkout", "-q", "-b", "elsewhere")
    with pytest.raises(SystemExit, match="is on elsewhere, not lane/a"):
        cmds(graph_path, "a", "integrate")
    git(wt, "checkout", "-q", "lane/a")
    git(graph_path.parent, "checkout", "-q", "-b", "other")
    with pytest.raises(SystemExit, match="is on other, not main"):
        cmds(graph_path, "a", "integrate")


def test_integrate_names_files_the_task_does_not_list(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    commit_in_lane(wt, name="extra.txt")
    assert "does not list: extra.txt" in cmds(graph_path, "a", "integrate")


@pytest.mark.parametrize("policy", ["keep", "squash"])
def test_integrate_after_a_crash_following_the_merge_finishes_the_task(tmp_path, policy):
    graph_path = make_repo(tmp_path, policy=policy)
    repo = graph_path.parent
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    chain = "\n".join(line for line in cmds(graph_path, "a", "integrate").splitlines() if not line.startswith("#"))
    steps = chain.split(" && \\\n")
    assert run(" && ".join(steps[:-1])).returncode == 0  # the session dies before the final `set`
    again = cmds(graph_path, "a", "integrate")
    assert "already landed" in again
    assert run(again).returncode == 0
    assert node(graph_path, "a")["status"] == "done"
    assert node(graph_path, "a")["commit"] == git(repo, "rev-parse", "--short", "HEAD").strip()


def test_close_refusals(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    with pytest.raises(SystemExit, match="use `abandon`"):
        cmds(graph_path, "a", "close")
    commit_in_lane(wt)
    assert run(cmds(graph_path, "a", "integrate")).returncode == 0
    (wt / "x.txt").write_text("formatter rewrote me\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="tracked files changed"):
        cmds(graph_path, "a", "close")


def test_abandon_mid_rebase_keeps_every_commit(tmp_path):
    graph_path = make_repo(tmp_path)
    repo = graph_path.parent
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    commit_in_lane(wt, name="t.txt", text="test\n")
    (repo / "x.txt").write_text("main moved\n", encoding="utf-8")
    git(repo, "commit", "-qam", "unlisted edit")
    assert run(cmds(graph_path, "a", "integrate")).returncode != 0  # the rebase conflicts
    with pytest.raises(SystemExit, match="a rebase is in progress"):
        cmds(graph_path, "a", "integrate")
    out = run(cmds(graph_path, "a", "abandon"))
    assert out.returncode == 0, out.stderr
    patch = (tmp_path / "scratch" / "a" / "a.abandoned.patch").read_text()
    assert "<<<<<<<" not in patch and "+test" in patch
    assert "t.txt" in git(repo, "show", "--stat", "abandoned/a")
    assert node(graph_path, "a")["status"] == "blocked"
    assert node(graph_path, "a")["branch"] == "abandoned/a"


def test_discard_saves_and_removes_uncommitted_work(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    (wt / "x.txt").write_text("half done\n", encoding="utf-8")
    (wt / "new.txt").write_text("new\n", encoding="utf-8")
    assert run(cmds(graph_path, "a", "discard")).returncode == 0
    assert git(wt, "status", "--porcelain") == ""
    assert (wt / "x.txt").read_text() == "changed\n"
    [patch] = (tmp_path / "scratch" / "a").glob("a.discarded-*.patch")
    assert "+half done" in patch.read_text() and "+new" in patch.read_text()


def test_relative_roots_resolve_against_the_graph_directory(tmp_path):
    graph_path = make_repo(tmp_path)
    data = plan.load(graph_path)
    data["plan"]["worktree_root"] = ".worktrees"
    data["plan"]["scratch_root"] = "../scratch"
    plan.save(graph_path, data)
    text = cmds(graph_path, "a", "open")
    assert str(graph_path.parent / ".worktrees" / "a") in text
    assert str(tmp_path / "scratch" / "a") in text
    _, warnings = plan.validate(plan.load(graph_path), graph_path)
    assert any("inside the repository" in w for w in warnings)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
