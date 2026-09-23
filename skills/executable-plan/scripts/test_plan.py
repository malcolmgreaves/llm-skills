#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8"]
# ///
"""Tests for plan.py. Run: uv run scripts/test_plan.py"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

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
```

**Acceptance.** This line must appear in the excerpt.

### `b`: second
<!-- task: b -->

Body of b.
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout


def make_repo(tmp: Path, policy: str = "keep", doc: str = "plan.md", doc_text: str = PLAN_MD) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    (repo / doc).write_text(doc_text, encoding="utf-8")
    (repo / "x.txt").write_text("base\n", encoding="utf-8")
    graph = {
        "plan": {
            "title": "t", "spec": doc, "integration_branch": "main",
            "worktree_root": str(tmp / "wt"), "scratch_root": str(tmp / "scratch"),
            "branch_prefix": "lane/", "lane_cap": 2, "autonomy": 2, "commit_policy": policy,
            "models": {s: "m" for s in plan.MODEL_STAGES}, "gates": ["true"],
        },
        "nodes": [
            {"id": "a", "title": "first", "spec": "#a", "kind": "code", "size": "M", "files": ["x.txt"], "status": "planned"},
            {"id": "b", "title": "second", "spec": "#b", "kind": "code", "size": "S", "deps": ["a"], "files": ["y.txt"], "status": "planned"},
        ],
    }
    (repo / "graph.yaml").write_text(yaml.safe_dump(graph, sort_keys=False), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo / "graph.yaml"


def run(cmds: str) -> None:
    for line in cmds.splitlines():
        if line and not line.startswith("#"):
            subprocess.run(line, shell=True, check=True, capture_output=True)


def open_lane(graph_path: Path, nid: str = "a") -> Path:
    run(plan.lane_commands(plan.load(graph_path), graph_path, nid, "open"))
    return Path(plan.load(graph_path)["plan"]["worktree_root"]) / nid


def test_excerpt_keeps_hash_lines_inside_code_fences(tmp_path):
    graph_path = make_repo(tmp_path)
    text = plan.excerpt(graph_path.parent / "plan.md", "a")
    assert '#[ignore = "later"]' in text
    assert "This line must appear in the excerpt." in text
    assert "Body of b." not in text


def test_validate_passes_and_rejects_a_missing_anchor(tmp_path):
    graph_path = make_repo(tmp_path)
    assert plan.validate(plan.load(graph_path), graph_path) == ([], [])
    data = plan.load(graph_path)
    data["nodes"][0]["spec"] = "#nope"
    errors, _ = plan.validate(data, graph_path)
    assert any("anchor #nope" in e for e in errors)


def test_validate_rejects_a_non_list_deps(tmp_path):
    graph_path = make_repo(tmp_path)
    data = plan.load(graph_path)
    data["nodes"][1]["deps"] = "a"
    errors, _ = plan.validate(data, graph_path)
    assert "b: deps must be a list" in errors


def test_html_anchor_must_be_on_a_heading(tmp_path):
    html = '<h2 id="tasks">Tasks</h2><div data-id="a">x</div><h3 id="b">b</h3><p>Body of b.</p>'
    doc = tmp_path / "p.html"
    doc.write_text(html, encoding="utf-8")
    assert not plan.anchor_exists(doc, "a")
    assert plan.anchor_exists(doc, "b")
    assert plan.excerpt(doc, "b").endswith("Body of b.")


def test_integrate_refuses_uncommitted_work(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    (wt / "x.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="uncommitted changes"):
        plan.lane_commands(plan.load(graph_path), graph_path, "a", "integrate")


def test_integrate_refuses_a_lane_with_no_commits(tmp_path):
    graph_path = make_repo(tmp_path)
    open_lane(graph_path)
    with pytest.raises(SystemExit, match="no commits beyond main"):
        plan.lane_commands(plan.load(graph_path), graph_path, "a", "integrate")


def test_integrate_refuses_when_main_worktree_is_elsewhere(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    (wt / "x.txt").write_text("changed\n", encoding="utf-8")
    git(wt, "commit", "-qam", "work")
    git(graph_path.parent, "checkout", "-q", "-b", "other")
    with pytest.raises(SystemExit, match="is on other, not main"):
        plan.lane_commands(plan.load(graph_path), graph_path, "a", "integrate")


@pytest.mark.parametrize("policy", ["keep", "squash"])
def test_full_lane_lands_the_work_and_closes(tmp_path, policy):
    graph_path = make_repo(tmp_path, policy=policy)
    repo = graph_path.parent
    wt = open_lane(graph_path)
    (wt / "x.txt").write_text("changed\n", encoding="utf-8")
    git(wt, "commit", "-qam", "a: stage 4 final review")
    cmds = plan.lane_commands(plan.load(graph_path), graph_path, "a", "integrate")
    cmds = cmds.replace("commit  #", "commit -qm 'a: squashed' #")
    run(cmds)
    assert (repo / "x.txt").read_text() == "changed\n"
    node = plan.by_id(plan.load(graph_path))["a"]
    assert node["status"] == "done"
    assert node["commit"] == git(repo, "rev-parse", "--short", "HEAD").strip()
    run(plan.lane_commands(plan.load(graph_path), graph_path, "a", "close"))
    assert not wt.exists()
    assert "lane/a" not in git(repo, "branch", "--list")
    assert plan.by_id(plan.load(graph_path))["a"].get("lane") is None


def test_close_refuses_an_unfinished_lane(tmp_path):
    graph_path = make_repo(tmp_path)
    open_lane(graph_path)
    with pytest.raises(SystemExit, match="use `abandon`"):
        plan.lane_commands(plan.load(graph_path), graph_path, "a", "close")


def test_abandon_saves_a_patch_and_blocks_dependents(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    (wt / "x.txt").write_text("changed\n", encoding="utf-8")
    (wt / "new.txt").write_text("new\n", encoding="utf-8")
    run(plan.lane_commands(plan.load(graph_path), graph_path, "a", "abandon"))
    patch = (tmp_path / "scratch" / "a" / "a.abandoned.patch").read_text()
    assert "+changed" in patch and "+new" in patch
    assert not wt.exists()
    data = plan.load(graph_path)
    assert plan.by_id(data)["a"]["status"] == "blocked"
    _, hold, _ = plan.next_ready(data)
    assert ("b", "waits for a (blocked)") in hold


def test_next_respects_files_and_owner_decisions(tmp_path):
    graph_path = make_repo(tmp_path)
    data = plan.load(graph_path)
    data["nodes"][1]["deps"] = []
    data["nodes"][1]["files"] = ["x.txt"]
    start, hold, _ = plan.next_ready(data)
    assert [n["id"] for n in start] == ["a"]
    assert hold[0][0] == "b" and "shares files" in hold[0][1]
    data["nodes"][0]["owner_decisions"] = [{"question": "Q?", "default": "d", "answer": ""}]
    start, hold, _ = plan.next_ready(data)
    assert ("a", "needs the owner's answer: Q?") in hold


def test_waves_counts_agent_runs(tmp_path, capsys):
    graph_path = make_repo(tmp_path)
    data = plan.load(graph_path)
    data["nodes"][1]["kind"] = "docs"
    plan.save(graph_path, data)
    assert plan.main(["waves", str(graph_path)]) == 0
    out = capsys.readouterr().out
    assert "wave 1: a" in out and "wave 2: b" in out
    assert "agent runs for the 2 unfinished tasks: 6 (2 on the final-review model)" in out


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
