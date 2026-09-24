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

**As landed.** Empty until the task integrates.

### `b`: second
<!-- task: b -->

Body of b.

## Residuals

- curly apostrophes split words
"""

MODELS = {"implement": "sonnet", "review": "opus", "second_review": "opus", "fix": "sonnet", "delegate": "opus"}


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout


def write_graph(path: Path, graph: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        YAML().dump(graph, fh)


def make_repo(tmp: Path, policy: str = "keep", gates: list | None = None, nodes: list | None = None,
              **plan_extra) -> Path:
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
            "models": dict(MODELS), "effort": {"review": "high"}, "gates": gates or ["true"], **plan_extra,
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


def scratch_of(graph_path: Path, nid: str) -> Path:
    return plan.lane_scratch(plan.load(graph_path)["plan"], graph_path, nid)


def open_lane(graph_path: Path, nid: str = "a") -> Path:
    out = run(cmds(graph_path, nid, "open"))
    assert out.returncode == 0, out.stderr
    return plan.root_dir(plan.load(graph_path)["plan"], "worktree_root", graph_path) / nid


def commit_in_lane(wt: Path, nid: str = "a", text: str = "changed\n", name: str = "x.txt") -> None:
    (wt / name).write_text(text, encoding="utf-8")
    git(wt, "add", name)
    git(wt, "commit", "-qm", f"{nid}: implement")


def finish_workflow(graph_path: Path, nid: str = "a", landed: str = "Shipped as specified.") -> None:
    """Write the report of every workflow stage, as the stages would."""
    data = plan.load(graph_path)
    node = plan.by_id(data)[nid]
    scratch = scratch_of(graph_path, nid)
    scratch.mkdir(parents=True, exist_ok=True)
    for stage in plan.workflow_of(node, data["plan"]):
        if stage == "fix":
            continue
        for name in plan.part_names(stage):
            plan.report_file(scratch, nid, name).write_text(f"# {name}\n\n## As landed\n\n{landed}\n")


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


def test_validate_checks_workflows_escalations_and_models(tmp_path):
    graph_path = make_repo(tmp_path, workflow={"S": ["review", "implement"], "M": ["implement", "fixit"],
                                               "L": ["implement", "second_review"]}, coordinator="solo")
    data = plan.load(graph_path)
    data["nodes"][0]["chain"] = "light"
    data["nodes"][1]["escalate"] = "it feels risky"
    errors, _ = plan.validate(data, graph_path)
    assert "plan.workflow.S must start with implement" in errors
    assert any("unknown stage 'fixit'" in e for e in errors)
    assert "plan.workflow.L must include review: every task gets one review-and-fix" in errors
    assert any("plan.coordinator must be one of" in e for e in errors)
    assert any("a: chain 'light' is gone" in e for e in errors)
    assert any("b: escalate must be one of" in e for e in errors)
    data = plan.load(graph_path)
    data["plan"]["workflow"] = {"M": ["implement", "review", "fix"]}
    del data["plan"]["models"]["fix"]
    data["plan"]["coordinator"] = "full"
    assert "plan.models.fix is missing; the user picks a model for every stage the workflows use" \
        in plan.validate(data, graph_path)[0]


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


# ── workflows ──────────────────────────────────────────────────────────────────

def n(nid: str, **kw) -> dict:
    return {"id": nid, "kind": "code", "size": "S", "status": "planned", **kw}


def test_workflows_follow_size_kind_escalation_and_coordinator():
    p = {"workflow": {"L": ["implement", "review", "second_review", "fix"]}}
    assert plan.workflow_of(n("a"), p) == ["implement", "review"]
    assert plan.workflow_of(n("a", size="M"), p) == ["implement", "review", "second_review"]
    assert plan.workflow_of(n("a", size="M", escalate="security"), p) == ["implement", "review", "second_review", "fix"]
    assert plan.workflow_of(n("a", kind="docs", size="L"), p) == ["implement", "review"]
    assert plan.workflow_of(n("a", kind="measurement"), p) == ["implement"]
    assert plan.workflow_of(n("a", chain="none"), p) == []
    assert plan.workflow_of(n("a"), {"coordinator": "delegate"}) == ["implement", "review", "delegate"]


def test_who_makes_owner_level_calls_at_autonomy_4():
    assert plan.decider({"coordinator": "full"}, ["implement", "review"]) == "coordinator"
    assert plan.decider({"coordinator": "merge"}, ["implement", "review", "second_review"]) == "second_review"
    assert plan.decider({"coordinator": "merge"}, ["implement", "review", "second_review", "fix"]) == "fix"
    assert plan.decider({"coordinator": "delegate"}, ["implement", "review", "fix", "delegate"]) == "delegate"


# ── scheduling ─────────────────────────────────────────────────────────────────

def sched(nodes: list[dict], cap: int = 3, autonomy: int = 2, changed=None) -> tuple[list[str], dict[str, str]]:
    data = {"plan": {"lane_cap": cap, "autonomy": autonomy}, "nodes": nodes}
    start, hold, _ = plan.next_ready(data, changed)
    return [x["id"] for x in start], dict(hold)


def test_an_alone_task_starts_by_itself_and_open_lanes_drain_for_it():
    start, hold = sched([n("r", alone=True, size="L"), n("a"), n("b")])
    assert start == ["r"] and hold == {"a": "`r` runs alone", "b": "`r` runs alone"}
    start, hold = sched([n("r", alone=True), n("a"), n("x", status="running")])
    assert start == [] and hold["a"] == "held so the open lanes drain for `r`"
    start, _ = sched([n("m", kind="measurement"), n("a")])
    assert start == ["m"]


def test_a_soft_dependency_that_is_running_or_starting_holds_the_task():
    start, hold = sched([n("h"), n("a", soft_deps=["h"])])
    assert start == ["h"] and hold["a"] == "starts after its soft dependencies: h"
    start, _ = sched([n("h", deps=["z"]), n("z", status="running"), n("a", soft_deps=["h"])])
    assert start == ["a"]


def test_next_respects_files_changes_waiting_owner_decisions_and_blocked_deps():
    start, hold = sched([n("a", files=["x"]), n("b", files=["x"])])
    assert start == ["a"] and hold["b"].startswith("shares files")
    start, hold = sched([n("a", status="running", files=["x"]), n("b", files=["cli.py"])],
                        changed={"a": {"x", "cli.py"}})
    assert start == [] and "cli.py" in hold["b"]
    start, hold = sched([n("a", status="waiting", files=["x"]), n("b", files=["x"])], cap=1)
    assert start == [] and hold["b"].startswith("shares files")
    start, hold = sched([n("a", owner_decisions=[{"question": "Q?", "default": "d", "answer": ""}])])
    assert hold == {"a": "needs the owner's answer: Q?"}
    start, _ = sched([n("a", owner_decisions=[{"question": "Q?", "default": "d", "answer": ""}])], autonomy=4)
    assert start == ["a"]
    _, hold = sched([n("a", status="blocked"), n("b", deps=["a"])])
    assert hold == {"b": "waits for a (blocked)"}


def test_the_simulation_sees_file_exclusions_and_parallel_lanes():
    data = {"plan": {"lane_cap": 3, "autonomy": 2},
            "nodes": [n("a", files=["cli.py"]), n("b", files=["cli.py"]), n("c", files=["cli.py"])]}
    makespan, peak, total = plan.simulate(data, [])
    assert peak == 1 and makespan == pytest.approx(total) == pytest.approx(3 * 6.5)
    data["nodes"] = [n("a", files=["a.py"]), n("b", files=["b.py"]), n("c", files=["c.py"])]
    makespan, peak, _ = plan.simulate(data, [])
    assert peak == 3 and makespan == pytest.approx(6.5)


def test_waves_warns_when_shared_files_serialize_the_plan(tmp_path, capsys):
    nodes = [
        {"id": "a", "title": "t", "spec": "#a", "kind": "code", "size": "S", "files": ["cli.py"], "status": "planned"},
        {"id": "b", "title": "t", "spec": "#b", "kind": "code", "size": "M", "files": ["cli.py"], "status": "planned"},
        {"id": "c", "title": "t", "spec": "#residuals", "kind": "docs", "size": "S", "deps": ["b"], "files": ["cli.py", "README.md"], "status": "planned"},
    ]
    graph_path = make_repo(tmp_path, nodes=nodes)
    plan.main(["waves", str(graph_path)])
    out = capsys.readouterr().out
    assert "wave 1: a, b" in out
    assert "workflow implement -> review: a, c" in out and "workflow implement -> review -> second_review: b" in out
    assert "at most 1 lane(s) at once" in out and "0 stage estimates measured" in out
    assert "hub files (tasks that list the same file never run together): cli.py (a, b, c)" in out
    assert "warning: the plan runs one lane at a time" in out


# ── prompts ────────────────────────────────────────────────────────────────────

def prompt_text(graph_path: Path, nid: str, stage: str, part: str | None = None, **kw) -> str:
    out, launcher = plan.render_prompt(plan.load(graph_path), graph_path, nid, stage, part, **kw)
    text = out.read_text()
    assert "{{" not in text and str(out) in launcher
    return text


def test_prompts_render_every_part_of_an_m_workflow(tmp_path):
    graph_path = make_repo(tmp_path)
    open_lane(graph_path)
    scratch = scratch_of(graph_path, "a")
    implement = (scratch / "a_implement.prompt.md").read_text()  # `lane open` rendered it
    assert "You work on task a (first)" in implement and '#[ignore = "later"]' in implement
    assert f"export TMPDIR={scratch / 'stage-implement'}" in implement and "never in /tmp" in implement
    assert "under \"Unexpected files\"" in implement
    review = prompt_text(graph_path, "a", "review", "report")
    assert "PART 1 OF 2" in review and "Don't re-run stage 1's mutations" in review
    review_fix = prompt_text(graph_path, "a", "review", "fix")
    assert "PART 2 OF 2" in review_fix and 'heading "As landed"' not in review_fix
    second = prompt_text(graph_path, "a", "second_review", "report")
    assert "Re-run each mutation" in second and str(scratch / "a_context.md") in second
    second_fix = prompt_text(graph_path, "a", "second_review", "fix")
    assert "under the heading \"As landed\"" in second_fix
    assert "\"Needs owner\"" in second_fix  # full coordinator: stages never decide owner calls
    started = [r["name"] for r in plan.stage_runs(node(graph_path, "a"), scratch)]
    assert started == ["implement", "review-report", "review-fix", "second_review-report", "second_review-fix"]
    assert "stage=review-report start model=opus effort=high applied=session" in "\n".join(node(graph_path, "a")["log"])


def test_prompts_follow_the_workflow_autonomy_and_owner_rules(tmp_path):
    graph_path = make_repo(tmp_path, coordinator="merge")
    data = plan.load(graph_path)
    data["nodes"][0]["size"] = "S"
    data["nodes"][0]["owner_decisions"] = [{"question": "Q?", "default": "d", "answer": ""}]
    plan.save(graph_path, data)
    with pytest.raises(SystemExit, match="owner hasn't answered: Q\\?"):
        prompt_text(graph_path, "a", "implement")
    plan.main(["set", str(graph_path), "a", "answer=0:yes"])
    assert "Q? -> yes" in prompt_text(graph_path, "a", "implement")
    assert "Re-run each mutation" in prompt_text(graph_path, "a", "review", "report")
    with pytest.raises(SystemExit, match="it has no second_review stage"):
        prompt_text(graph_path, "a", "second_review")
    with pytest.raises(SystemExit, match="needs --decisions"):
        prompt_text(graph_path, "a", "fix")
    data = plan.load(graph_path)
    data["plan"]["autonomy"] = 4
    plan.save(graph_path, data)
    fix_part = prompt_text(graph_path, "a", "review", "fix")  # merge mode, S: the review's fix part decides
    assert "Owner-level calls are yours" in fix_part and "\"Owner-level decisions taken\"" in fix_part
    assert "Owner-level calls are not yours" in prompt_text(graph_path, "a", "review", "report")
    decisions = tmp_path / "d.md"
    decisions.write_text("1. Accept: the owner wants curly apostrophes kept.")
    assert "curly apostrophes kept" in prompt_text(graph_path, "a", "fix", decisions=decisions)
    prompt_text(graph_path, "a", "review", "report", via="workflow")
    assert node(graph_path, "a")["log"][-1].endswith("effort=high applied=high")


def test_context_brief_lists_landed_and_upcoming_work(tmp_path):
    graph_path = make_repo(tmp_path, coordinator="delegate")
    doc = graph_path.parent / "plan.md"
    plan.apply_landed(doc, "a", "tokenizer shipped; curly quotes are a residual")
    data = plan.load(graph_path)
    data["nodes"][0]["status"] = "done"
    data["nodes"][0]["commit"] = "abc1234"
    plan.save(graph_path, data)
    note = tmp_path / "note.md"
    note.write_text("Prefer the smaller fix.")
    plan.main(["context", str(graph_path), "b", "--note", str(note)])
    text = (scratch_of(graph_path, "b") / "b_context.md").read_text()
    assert "a (abc1234): first. As landed: tokenizer shipped; curly quotes are a residual" in text
    assert "curly apostrophes split words" in text and "Prefer the smaller fix." in text
    assert "Coordinator mode: delegate" in text
    delegate = prompt_text(graph_path, "b", "delegate")
    assert "COORDINATOR REVIEW" in delegate and "b_context.md" in delegate


REPORT = """# a: second review, part 2

## Gates

all green

## Beyond

- accept curly apostrophes

## Needs owner

- should --top also print chars? Recommend no.

## As landed

`words()` shipped as specified.

One residual: curly apostrophes.

## Other
not this
"""


def test_findings_and_landed_read_the_reports(tmp_path, capsys):
    graph_path = make_repo(tmp_path)
    finish_workflow(graph_path)
    report = plan.report_file(scratch_of(graph_path, "a"), "a", "second_review-fix")
    report.write_text(REPORT)
    plan.main(["findings", str(graph_path), "a"])
    out = capsys.readouterr().out
    assert "## Needs owner (a_second_review-fix.md)" in out and "Recommend no." in out
    assert "## Beyond (a_second_review-fix.md)" in out
    assert plan.main(["landed", str(graph_path), "a"]) == 0  # picks the latest report with the heading
    text = plan.section(graph_path.parent / "plan.md", "a")
    assert text.endswith("**As landed.**\n\n`words()` shipped as specified.\n\nOne residual: curly apostrophes.")
    assert "Empty until" not in text and "not this" not in text


def test_landed_in_html_and_a_report_without_the_heading(tmp_path):
    doc = tmp_path / "p.html"
    doc.write_text('<h3 id="a">a</h3><p>spec</p><p><strong>As landed.</strong> Empty.</p><h3 id="b">b</h3>')
    plan.apply_landed(doc, "a", "Shipped <all>.")
    text = doc.read_text()
    assert "<p>Shipped &lt;all&gt;.</p>" in text and "Empty." not in text and '<h3 id="b">b</h3>' in text
    bad = tmp_path / "r.md"
    bad.write_text("# report\nno such heading\n")
    with pytest.raises(SystemExit, match="no \"As landed\" heading"):
        plan.as_landed_text(bad)


def test_timings_are_recorded_once_and_calibrate_the_estimate(tmp_path):
    graph_path = make_repo(tmp_path)
    open_lane(graph_path)
    scratch = scratch_of(graph_path, "a")
    data = plan.load(graph_path)
    log = data["nodes"][0]["log"]
    log.append("2020-01-01T10:00:00 stage=review-report start model=opus effort=high applied=session")
    log.append("2020-01-01T10:04:00 stage=review-fix start model=opus effort=high applied=session")
    plan.save(graph_path, data)
    for name, stamp in (("review-report", "2020-01-01T10:04:00"), ("review-fix", "2020-01-01T10:06:00")):
        report = plan.report_file(scratch, "a", name)
        report.write_text("r")
        t = plan.datetime.fromisoformat(stamp).timestamp()
        plan.os.utime(report, (t, t))
    assert plan.record_timings(plan.load(graph_path), graph_path, "a") == 1
    assert plan.record_timings(plan.load(graph_path), graph_path, "a") == 0  # idempotent
    records = plan.load_timings(graph_path, plan.load(graph_path)["plan"])
    assert records[0]["stage"] == "review" and records[0]["minutes"] == 6.0 and records[0]["size"] == "M"
    git_dir = plan.git_dir(graph_path)
    assert plan.timings_file(graph_path, {}) == git_dir / "executable-plan" / "timings.jsonl"
    p = plan.load(graph_path)["plan"]
    assert plan.stage_estimate(p, records, "review", "M") == (6.0, True)
    assert plan.stage_estimate(p, records, "review", "S") == (3.0, True)  # scaled from M by size
    assert plan.stage_estimate(p, records, "implement", "S") == (3.0, False)


def test_report_and_clean(tmp_path):
    graph_path = make_repo(tmp_path)
    open_lane(graph_path)
    scratch = scratch_of(graph_path, "a")
    assert (scratch / "stage-implement").is_dir()
    plan.report_file(scratch, "a", "implement").write_text("## Needs owner\n\n- which quote style?\n")
    with pytest.raises(SystemExit, match="lanes are still open"):
        plan.clean(plan.load(graph_path), graph_path, None)
    assert "reclaimed" in plan.clean(plan.load(graph_path), graph_path, "a")
    assert not (scratch / "stage-implement").exists() and plan.report_file(scratch, "a", "implement").exists()
    plan.main(["set", str(graph_path), "a", "status=blocked"])
    (scratch / "a.abandoned.patch").write_text("patch")
    with pytest.raises(SystemExit, match="write the final report first"):
        plan.clean(plan.load(graph_path), graph_path, None)
    assert plan.main(["report", str(graph_path)]) == 0
    report = (graph_path.parent / "report.md").read_text()
    assert "| implement | sonnet |" in report and "which quote style?" in report
    assert "kept the abandoned patches" in plan.clean(plan.load(graph_path), graph_path, None)
    assert (scratch / "a.abandoned.patch").exists() and not plan.report_file(scratch, "a", "implement").exists()


# ── lanes ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("policy", ["keep", "squash"])
def test_land_merges_closes_records_and_commits(tmp_path, policy):
    graph_path = make_repo(tmp_path, policy=policy)
    repo = graph_path.parent
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    finish_workflow(graph_path)
    (wt / "__pycache__").mkdir()  # untracked gate output must not block the close
    out = run(cmds(graph_path, "a", "land"))
    assert out.returncode == 0, out.stderr + out.stdout
    assert (repo / "x.txt").read_text() == "changed\n"
    a = node(graph_path, "a")
    assert a["status"] == "done" and a.get("lane") is None
    assert git(repo, "log", "-1", "--format=%s").startswith(f"plan: a landed ({a['commit']})")
    assert git(repo, "status", "--porcelain") == ""
    assert "Shipped as specified." in plan.section(repo / "plan.md", "a")
    assert not wt.exists() and "lane/a" not in git(repo, "branch", "--list")
    assert not list(scratch_of(graph_path, "a").glob("stage-*"))
    if policy == "squash":
        assert "Plan-Task: a" in git(repo, "log", "-2", "--format=%B")


def test_integrate_stops_at_a_failing_gate(tmp_path):
    graph_path = make_repo(tmp_path, gates=["grep -q base x.txt"])
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    finish_workflow(graph_path)
    assert run(cmds(graph_path, "a", "integrate")).returncode != 0
    assert (graph_path.parent / "x.txt").read_text() == "base\n"
    assert node(graph_path, "a")["status"] == "running"


def test_integrate_refusals(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    finish_workflow(graph_path)
    with pytest.raises(SystemExit, match="no commits beyond main"):
        cmds(graph_path, "a", "integrate")
    (wt / "x.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="uncommitted changes"):
        cmds(graph_path, "a", "integrate")
    git(wt, "commit", "-qam", "a: implement")
    (wt / "t_review.py").write_text("def test_review_proof_x(): pass\n")
    git(wt, "add", "t_review.py")
    git(wt, "commit", "-qm", "a: review proofs")
    with pytest.raises(SystemExit, match="review_proof_ tests remain"):
        cmds(graph_path, "a", "integrate")
    git(wt, "rm", "-q", "t_review.py")
    git(wt, "commit", "-qm", "a: review fixes")
    plan.report_file(scratch_of(graph_path, "a"), "a", "second_review-fix").unlink()
    with pytest.raises(SystemExit, match="reports are missing"):
        cmds(graph_path, "a", "integrate")
    finish_workflow(graph_path)
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
    finish_workflow(graph_path)
    assert "does not list: extra.txt" in cmds(graph_path, "a", "integrate")


@pytest.mark.parametrize("policy", ["keep", "squash"])
def test_integrate_after_a_crash_following_the_merge_finishes_the_task(tmp_path, policy):
    graph_path = make_repo(tmp_path, policy=policy)
    repo = graph_path.parent
    wt = open_lane(graph_path)
    commit_in_lane(wt)
    finish_workflow(graph_path)
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
    finish_workflow(graph_path)
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
    finish_workflow(graph_path)
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
    assert not list(scratch_of(graph_path, "a").glob("stage-*"))


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


def test_lane_changes_reports_committed_and_uncommitted_files(tmp_path):
    graph_path = make_repo(tmp_path)
    wt = open_lane(graph_path)
    commit_in_lane(wt, name="cli.py")
    (wt / "other.py").write_text("x\n")
    assert plan.lane_changes(plan.load(graph_path), graph_path) == {"a": {"cli.py", "other.py"}}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
