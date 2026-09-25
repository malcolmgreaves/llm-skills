#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["ruamel.yaml>=0.18"]
# ///
"""Operate on an executable plan's graph.yaml.

Usage:
    uv run plan.py validate GRAPH              # schema, workflows, cycles, anchors
    uv run plan.py waves GRAPH                 # waves, exclusions, workflows, agent runs, simulated time
    uv run plan.py next GRAPH                  # what can start now, and why the rest waits
    uv run plan.py set GRAPH ID key=value ...  # status=, lane=, branch=, commit=, log=, answer=N:text
    uv run plan.py render GRAPH                # a status table (Markdown)
    uv run plan.py lane GRAPH ID ACTION        # print the shell command for a lane action:
                                               #   open, integrate, close, land, abandon, discard
    uv run plan.py excerpt GRAPH ID            # the task's section from the plan document
    uv run plan.py prompt GRAPH ID STAGE [--part report|fix] [--decisions FILE] [--via agent|workflow]
                                               # render a stage prompt; log the stage's start
    uv run plan.py context GRAPH ID [--note FILE]   # write the coordinator's brief for the task
    uv run plan.py findings GRAPH ID           # Beyond, Needs owner, and owner-level decisions
    uv run plan.py landed GRAPH ID [REPORT]    # paste the "As landed" text into the plan
    uv run plan.py report GRAPH                # write the final report next to graph.yaml
    uv run plan.py clean GRAPH [ID]            # reclaim scratch space (a lane's, or the campaign's)

The script runs only read-only git commands. It prints every command that
changes a repository for the coordinator to run, as one `&&` chain that
stops at the first failure, so each destructive step stays visible. The only
files it writes itself are graph.yaml, the plan document, prompt and brief
files in scratch, the report, and the timings file; `clean` removes scratch.
"""

from __future__ import annotations

import argparse
import fcntl
import html as html_lib
import json
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

STATUSES = ("planned", "running", "review", "waiting", "integrating", "done", "blocked", "skipped")
OPEN_STATUSES = ("running", "review", "waiting", "integrating")
FINISHED_STATUSES = ("done", "skipped")
KINDS = ("code", "docs", "plan", "measurement")
SIZES = ("S", "M", "L")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PLAN_REQUIRED = (
    "title", "spec", "integration_branch", "worktree_root", "scratch_root",
    "branch_prefix", "lane_cap", "autonomy", "commit_policy", "models", "gates",
)
# Stages in the only order a workflow may use them. `delegate` is added by the coordinator mode.
WORKFLOW_STAGES = ("implement", "review", "second_review", "fix")
STAGES = WORKFLOW_STAGES + ("delegate",)
TWO_PART = ("review", "second_review")  # a report prompt, then a fix prompt, to the same agent
DEFAULT_WORKFLOW = {
    "S": ["implement", "review"],
    "M": ["implement", "review", "second_review"],
    "L": ["implement", "review", "second_review"],
}
COORDINATOR_MODES = ("full", "merge", "delegate")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
ESCALATIONS = ("untrusted-input", "persistence", "security", "concurrency", "breaking-interface")
# Model-neutral minutes of agent time per stage for an S task, until measured timings exist.
# M doubles them, L quadruples them. plan.stage_minutes overrides them.
STAGE_MINUTES = {"implement": 3.0, "review": 3.5, "second_review": 3.0, "fix": 2.5, "delegate": 2.5}
SIZE_FACTOR = {"S": 1, "M": 2, "L": 4}
SELF = Path(__file__).resolve()
TEMPLATES = SELF.parent.parent / "assets" / "stage-templates.md"
REPORT_NAME = "report.md"

_yaml = YAML()  # round-trip mode: keeps the comments, quotes, and layout the drafter wrote
_yaml.preserve_quotes = True  # an unquoted `yes` is a boolean to YAML 1.1 readers
_yaml.width = 4096  # never fold a long log line
_yaml.indent(mapping=2, sequence=4, offset=2)


# ── loading and saving ─────────────────────────────────────────────────────────

def load(graph_path: Path) -> dict:
    data = _yaml.load(graph_path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise SystemExit(f"{graph_path} must be a map with `plan` and `nodes`")
    if data.get("plan") is None:
        data["plan"] = {}
    if data.get("nodes") is None:
        data["nodes"] = []
    return data


def dump(data: dict) -> str:
    buf = StringIO()
    _yaml.dump(data, buf)
    return buf.getvalue()


def _write_atomic(path: Path, text: str) -> None:
    """Write through a temporary file, so a reader never sees half a file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def save(graph_path: Path, data: dict) -> None:
    _write_atomic(graph_path, dump(data))


def git_dir(graph_path: Path) -> Path | None:
    common = _git("-C", str(graph_path.parent), "rev-parse", "--git-common-dir")
    return (graph_path.parent / common).resolve() if common else None


@contextmanager
def locked(graph_path: Path):
    """Serialize read-modify-write of the graph across processes."""
    gd = git_dir(graph_path)
    lock = gd / "executable-plan.lock" if gd else graph_path.with_name(f".{graph_path.name}.lock")
    with open(lock, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        yield


def by_id(data: dict) -> dict[str, dict]:
    return {n["id"]: n for n in data["nodes"] if isinstance(n, dict) and isinstance(n.get("id"), str)}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── workflows ──────────────────────────────────────────────────────────────────

def effective_size(node: dict) -> str:
    """The node's size, one step up when it names an escalation reason."""
    size = str(node.get("size", "M"))
    if node.get("escalate") and size in SIZES:
        return SIZES[min(SIZES.index(size) + 1, len(SIZES) - 1)]
    return size


def workflow_of(node: dict, plan: dict) -> list[str]:
    """The stages the node runs, in order."""
    if node.get("chain") == "none":
        return []
    kind = node.get("kind")
    if kind == "measurement":
        return ["implement"]
    if kind in ("docs", "plan"):
        stages = ["implement", "review"]
    else:
        table = {**DEFAULT_WORKFLOW, **{str(k): list(v) for k, v in (plan.get("workflow") or {}).items()}}
        stages = list(table.get(effective_size(node), DEFAULT_WORKFLOW["M"]))
    if plan.get("coordinator", "full") == "delegate":
        stages.append("delegate")
    return stages


def last_review(stages: list[str]) -> str | None:
    return next((s for s in ("second_review", "review") if s in stages), None)


def decider(plan: dict, stages: list[str]) -> str:
    """Who makes owner-level calls at autonomy 4: a stage name, or `coordinator`."""
    if "delegate" in stages:
        return "delegate"
    if "fix" in stages:
        return "fix"
    if plan.get("coordinator", "full") == "full":
        return "coordinator"
    return last_review(stages) or "implement"


def part_names(stage: str) -> list[str]:
    return [f"{stage}-report", f"{stage}-fix"] if stage in TWO_PART else [stage]


def prompt_name(stage: str, part: str | None) -> str:
    return f"{stage}-{part or 'report'}" if stage in TWO_PART else stage


def model_for(plan: dict, stage: str) -> str:
    models = plan.get("models") or {}
    return str(models.get(stage) or models.get("implement") or "")


def effort_for(plan: dict, stage: str) -> str:
    return str((plan.get("effort") or {}).get(stage) or "")


def runs_alone(node: dict) -> bool:
    # A measurement runs alone unless told otherwise: other lanes' builds skew its numbers.
    return bool(node.get("alone", node.get("kind") == "measurement"))


# ── paths ──────────────────────────────────────────────────────────────────────

def spec_target(node: dict, data: dict, graph_path: Path) -> tuple[Path, str]:
    """Resolve a node's `spec` to (document path, anchor)."""
    spec = str(node.get("spec", ""))
    doc, _, anchor = spec.partition("#")
    path = graph_path.parent / (doc or str(data["plan"].get("spec", "")))
    return path, anchor


def resolve_doc(rel: str, graph_path: Path) -> Path:
    """A path from graph.yaml: absolute, or relative to graph.yaml's directory, or to the repository root."""
    path = Path(os.path.expanduser(rel))
    if path.is_absolute():
        return path
    for base in (graph_path.parent, repo_root(graph_path)):
        if (base / path).exists():
            return (base / path).resolve()
    return (graph_path.parent / path).resolve()


def root_dir(plan: dict, key: str, graph_path: Path) -> Path:
    """A directory setting, with `~` expanded and a relative path taken from graph.yaml's directory."""
    path = Path(os.path.expanduser(str(plan[key])))
    return (path if path.is_absolute() else graph_path.parent / path).resolve()


def lane_scratch(plan: dict, graph_path: Path, nid: str) -> Path:
    return root_dir(plan, "scratch_root", graph_path) / nid


def report_file(scratch: Path, nid: str, name: str) -> Path:
    return scratch / f"{nid}_{name}.md"


def stage_tmp(scratch: Path, name: str) -> Path:
    return scratch / f"stage-{name}"


def timings_file(graph_path: Path, plan: dict) -> Path:
    """One timings file per repository: in the git directory, shared by every worktree."""
    if plan.get("timings"):
        return resolve_doc(str(plan["timings"]), graph_path)
    gd = git_dir(graph_path)
    return (gd / "executable-plan" / "timings.jsonl") if gd else graph_path.parent / ".timings.jsonl"


# ── anchors and excerpts ───────────────────────────────────────────────────────

class AnchorError(Exception):
    pass


HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]|$)")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
MARKER_RE = re.compile(r"^<!--\s*task:\s*(\S+?)\s*-->$")


def _slug(text: str) -> str:
    text = re.sub(r"\{#[^}]*\}", "", text)
    text = re.sub(r"[^\w\s-]", "", text.strip().strip("#").strip().lower())
    return re.sub(r"[\s_]+", "-", text)


def _md_scan(lines: list[str]) -> tuple[dict[int, int], list[tuple[int, str]], list[bool]]:
    """Headings {line: level}, task markers [(line, id)], and which lines are live.

    A line inside a fenced code block or a multi-line HTML comment is not live:
    it is never a heading or a marker, so a code sample or a commented-out
    draft can't end a task's section or claim its anchor.
    """
    headings: dict[int, int] = {}
    markers: list[tuple[int, str]] = []
    live = [False] * len(lines)
    fence: str | None = None
    comment = False
    for i, line in enumerate(lines):
        if fence is not None:
            m = FENCE_RE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                    and not line.strip()[len(m.group(1)):].strip():
                fence = None
            continue
        if comment:
            if "-->" in line:
                comment = False
            continue
        if m := FENCE_RE.match(line):
            fence = m.group(1)
            continue
        stripped = line.strip()
        if mm := MARKER_RE.match(stripped):
            markers.append((i, mm.group(1)))
            continue
        if "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            comment = True
            continue
        live[i] = True
        if h := HEADING_RE.match(line):
            headings[i] = len(h.group(1))
        elif SETEXT_RE.match(line) and i > 0 and live[i - 1] and lines[i - 1].strip() \
                and (i - 1) not in headings and not HEADING_RE.match(lines[i - 1]):
            headings[i - 1] = 1 if stripped.startswith("=") else 2
    return headings, markers, live


def _md_bounds(text: str, anchor: str) -> tuple[int, int, list[str]]:
    """The line range [start, end) of the Markdown section that `anchor` names."""
    lines = text.splitlines()
    headings, markers, live = _md_scan(lines)
    hits = [i for i, a in markers if a == anchor]
    if len(hits) > 1:
        raise AnchorError(f"the marker <!-- task: {anchor} --> appears {len(hits)} times")
    if hits:
        prev = hits[0] - 1
        while prev >= 0 and not lines[prev].strip():
            prev -= 1
        if prev in headings:
            start = prev
        elif prev - 1 in headings and SETEXT_RE.match(lines[prev]):
            start = prev - 1
        else:
            raise AnchorError(f"the marker <!-- task: {anchor} --> is not directly after a heading")
    else:
        link = re.compile(rf"""<a\s+(?:name|id)\s*=\s*["']{re.escape(anchor)}["']""")
        rules = (
            ("a {#id} heading", [i for i in headings if f"{{#{anchor}}}" in lines[i]]),
            ("an <a id> anchor", [i for i in range(len(lines)) if live[i] and link.search(lines[i])]),
            ("a heading slug", [i for i in headings if _slug(lines[i]) == anchor]),
        )
        for what, found in rules:
            if len(found) > 1:
                raise AnchorError(f"{what} for {anchor!r} matches {len(found)} places; add a task marker")
            if found:
                before = [i for i in headings if i <= found[0]]
                if not before:
                    raise AnchorError(f"{what} for {anchor!r} is not under a heading")
                start = max(before)
                break
        else:
            raise AnchorError(f"no section for task {anchor!r}")
    level = headings[start]
    end = next((j for j in sorted(headings) if j > start and headings[j] <= level), len(lines))
    return start, end, lines


def _md_section(text: str, anchor: str) -> str:
    start, end, lines = _md_bounds(text, anchor)
    return "\n".join(lines[start:end]).strip()


def _strip_html(fragment: str) -> str:
    fragment = re.sub(r"(?is)<(script|style).*?</\1>", "", fragment)
    fragment = re.sub(r"(?i)<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"(?i)</(p|li|tr|h[1-6]|pre|div|blockquote)>", "\n", fragment)
    fragment = re.sub(r"(?i)<li[^>]*>", "- ", fragment)
    fragment = re.sub(r"(?i)</t[dh]>", " | ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    text = html_lib.unescape(fragment)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _html_bounds(text: str, anchor: str) -> tuple[int, int]:
    """The character range of the HTML section whose heading carries id=anchor."""
    # Blank out comments with spaces, so offsets into `clean` are offsets into `text`.
    clean = re.sub(r"(?s)<!--.*?-->", lambda m: " " * len(m.group()), text)
    id_attr = rf"""\sid\s*=\s*["']{re.escape(anchor)}["']"""  # ids are case-sensitive
    everywhere = re.findall(rf"<[A-Za-z][^>]*?{id_attr}", clean)
    if len(everywhere) > 1:
        raise AnchorError(f'id="{anchor}" appears {len(everywhere)} times')
    m = re.search(rf"<(?i:h)([1-6])\b[^>]*?{id_attr}[^>]*>", clean)
    if not m:
        where = " (it is on an element that is not a heading)" if everywhere else ""
        raise AnchorError(f'no heading with id="{anchor}"{where}')
    level = int(m.group(1))
    end = re.compile(rf"<h[1-{level}]\b", re.I).search(clean, m.end())
    return m.start(), end.start() if end else len(clean)


def _html_section(text: str, anchor: str) -> str:
    start, end = _html_bounds(text, anchor)
    clean = re.sub(r"(?s)<!--.*?-->", lambda m: " " * len(m.group()), text)
    return _strip_html(clean[start:end])


def section(doc: Path, anchor: str) -> str:
    """The task's section; raises AnchorError when the anchor is missing or ambiguous."""
    if not anchor:
        raise AnchorError("the spec has no #anchor")
    text = doc.read_text(encoding="utf-8")
    if doc.suffix.lower() in (".html", ".htm"):
        return _html_section(text, anchor)
    return _md_section(text, anchor)


# ── validation ─────────────────────────────────────────────────────────────────

def _check_workflow(size: str, stages: object) -> list[str]:
    where = f"plan.workflow.{size}"
    if size not in SIZES:
        return [f"{where}: the size must be one of {SIZES}"]
    if not isinstance(stages, list) or not stages:
        return [f"{where} must be a non-empty list of stages"]
    errors = [f"{where}: unknown stage {s!r}; use {', '.join(WORKFLOW_STAGES)}"
              for s in stages if s not in WORKFLOW_STAGES]
    if errors:
        return errors
    if stages[0] != "implement":
        errors.append(f"{where} must start with implement")
    order = [WORKFLOW_STAGES.index(s) for s in stages]
    if order != sorted(set(order)):
        errors.append(f"{where}: stages must appear once each, in the order {' -> '.join(WORKFLOW_STAGES)}")
    if "review" not in stages:
        errors.append(f"{where} must include review: every task gets one review-and-fix")
    return errors


def validate(data: dict, graph_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    plan = data["plan"]
    if not isinstance(plan, dict):
        return ["`plan` must be a map"], warnings
    if not isinstance(data["nodes"], list):
        return ["`nodes` must be a list"], warnings
    for key in PLAN_REQUIRED:
        if key not in plan:
            errors.append(f"plan.{key} is missing")
    lane_cap = plan.get("lane_cap", 1)
    if isinstance(lane_cap, bool) or not isinstance(lane_cap, int) or lane_cap < 1:
        errors.append("plan.lane_cap must be an integer >= 1")
    if plan.get("autonomy") not in (0, 1, 2, 3, 4) or isinstance(plan.get("autonomy"), bool):
        errors.append("plan.autonomy must be an integer from 0 to 4")
    if plan.get("commit_policy") not in ("keep", "squash"):
        errors.append("plan.commit_policy must be 'keep' or 'squash'")
    if plan.get("coordinator", "full") not in COORDINATOR_MODES:
        errors.append(f"plan.coordinator must be one of {COORDINATOR_MODES}")
    workflow = plan.get("workflow")
    if workflow is not None:
        if not isinstance(workflow, dict):
            errors.append("plan.workflow must map sizes (S, M, L) to lists of stages")
        else:
            for size, stages in workflow.items():
                errors += _check_workflow(str(size), stages)
    for stage, level in (plan.get("effort") or {}).items():
        if stage not in STAGES:
            errors.append(f"plan.effort: unknown stage {stage!r}")
        elif str(level) not in EFFORTS:
            warnings.append(f"plan.effort.{stage}: {level!r} is not one of {EFFORTS}")
    for stage in (plan.get("models") or {}):
        if stage not in STAGES:
            errors.append(f"plan.models: unknown stage {stage!r}; use {', '.join(STAGES)}")
    gates = plan.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("plan.gates must be a non-empty list of commands")
    elif any(not isinstance(g, str) for g in gates):
        errors.append("plan.gates: every gate must be a string; quote a command that contains `: `")
    spec_doc = graph_path.parent / str(plan.get("spec", ""))
    if not spec_doc.is_file():
        errors.append(f"plan.spec does not exist: {spec_doc}")
    for rel in plan.get("guidelines") or []:
        if not resolve_doc(str(rel), graph_path).exists():
            warnings.append(f"guideline file not found: {rel}")
    if "worktree_root" in plan:
        wt_root = root_dir(plan, "worktree_root", graph_path)
        repo = repo_root(graph_path)
        if wt_root.is_relative_to(repo):
            warnings.append(f"worktree_root is inside the repository; add "
                            f"{wt_root.relative_to(repo)}/ to .git/info/exclude so lanes don't show as untracked files")

    nodes = data["nodes"]
    if any(not isinstance(n, dict) for n in nodes):
        return errors + ["every item of `nodes` must be a map"], warnings
    ids = [n.get("id") for n in nodes]
    for n in nodes:
        if not isinstance(n.get("id"), str):
            errors.append(f"id {n.get('id')!r} must be a string; quote it in graph.yaml")
    str_ids = [i for i in ids if isinstance(i, str)]
    for d in sorted({i for i in str_ids if str_ids.count(i) > 1}):
        errors.append(f"duplicate node id: {d}")
    known = set(str_ids)
    specs: dict[tuple[str, str], str] = {}
    used_stages: set[str] = set()
    for n in nodes:
        nid = str(n.get("id", "?"))
        if isinstance(n.get("id"), str) and not ID_RE.match(nid):
            errors.append(f"{nid}: id must match {ID_RE.pattern}")
        for key in ("title", "spec", "kind", "size", "status"):
            if key not in n:
                errors.append(f"{nid}: {key} is missing")
        if n.get("kind") not in KINDS:
            errors.append(f"{nid}: kind must be one of {KINDS}")
        if "chain" in n and n.get("chain") != "none":
            errors.append(f"{nid}: chain {n.get('chain')!r} is gone; the size picks the workflow (plan.workflow), "
                          f"and `escalate` moves a task up one size. Only `chain: none` remains.")
        if n.get("escalate") is not None and n.get("escalate") not in ESCALATIONS:
            errors.append(f"{nid}: escalate must be one of {ESCALATIONS}; a task that fits none runs its size's workflow")
        if n.get("size") not in SIZES:
            errors.append(f"{nid}: size must be one of {SIZES}")
        if n.get("status") not in STATUSES:
            errors.append(f"{nid}: status must be one of {STATUSES}")
        lists_ok = True
        for key in ("deps", "soft_deps", "files", "owner_decisions"):
            value = n.get(key)
            if value is not None and not isinstance(value, list):
                errors.append(f"{nid}: {key} must be a list")
                lists_ok = False
        if lists_ok:
            for dep in (n.get("deps") or []) + (n.get("soft_deps") or []):
                if not isinstance(dep, str):
                    errors.append(f"{nid}: dependency {dep!r} must be a string; quote it")
                elif dep not in known:
                    errors.append(f"{nid}: unknown dependency {dep}")
                elif dep == nid:
                    errors.append(f"{nid}: depends on itself")
            for od in n.get("owner_decisions") or []:
                if not isinstance(od, dict) or "question" not in od or "default" not in od:
                    errors.append(f"{nid}: each owner_decisions item needs `question` and `default`")
        if n.get("kind") == "code" and not n.get("files"):
            warnings.append(f"{nid}: a code task with no `files` cannot be excluded from a conflicting lane")
        if isinstance(plan, dict) and n.get("size") in SIZES:
            used_stages |= set(workflow_of(n, plan))
        if "spec" in n:
            doc, anchor = spec_target(n, data, graph_path)
            key = (str(doc.resolve()), anchor)
            if key in specs:
                errors.append(f"{nid}: same spec as {specs[key]}")
            specs[key] = nid
            if not doc.is_file():
                errors.append(f"{nid}: spec document not found: {doc}")
            else:
                try:
                    section(doc, anchor)
                except AnchorError as exc:
                    errors.append(f"{nid}: {exc} in {doc.name}")
    models = plan.get("models") or {}
    for stage in sorted(used_stages & set(STAGES), key=STAGES.index):
        if not models.get(stage):
            errors.append(f"plan.models.{stage} is missing; the user picks a model for every stage the workflows use")
    if not errors and (cycle := find_cycle(data)):
        errors.append("dependency cycle: " + " -> ".join(cycle))
    return errors, warnings


def find_cycle(data: dict) -> list[str] | None:
    graph = {i: list(n.get("deps") or []) for i, n in by_id(data).items()}
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(v: str) -> list[str] | None:
        state[v] = 1
        stack.append(v)
        for w in graph.get(v, []):
            if w not in graph:
                continue
            if state.get(w) == 1:
                return stack[stack.index(w):] + [w]
            if state.get(w) is None and (c := visit(w)):
                return c
        stack.pop()
        state[v] = 2
        return None

    for v in graph:
        if state.get(v) is None and (c := visit(v)):
            return c
    return None


# ── timings ────────────────────────────────────────────────────────────────────

STAGE_LOG_RE = re.compile(r"^(\S+) stage=(\S+) start model=(\S*) effort=(\S*) applied=(\S*)$")


def stage_runs(node: dict, scratch: Path) -> list[dict]:
    """Each prompt started for the node (the last start per prompt), with its end from the report's mtime."""
    runs: dict[str, dict] = {}
    for line in node.get("log") or []:
        m = STAGE_LOG_RE.match(str(line))
        if m:
            runs[m.group(2)] = {"name": m.group(2), "start": datetime.fromisoformat(m.group(1)),
                                "model": m.group(3), "effort": m.group(4), "applied": m.group(5)}
    for run in runs.values():
        report = report_file(scratch, node["id"], run["name"])
        end = datetime.fromtimestamp(report.stat().st_mtime) if report.exists() else None
        run["end"] = end if end and end >= run["start"] else None
        run["minutes"] = round((run["end"] - run["start"]).total_seconds() / 60, 2) if run["end"] else None
    return list(runs.values())


def load_timings(graph_path: Path, plan: dict) -> list[dict]:
    path = timings_file(graph_path, plan)
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def record_timings(data: dict, graph_path: Path, nid: str) -> int:
    """Append the node's measured stage durations to the repository's timings file; return how many."""
    plan = data["plan"]
    node = by_id(data)[nid]
    scratch = lane_scratch(plan, graph_path, nid)
    by_stage: dict[str, dict] = {}
    for run in stage_runs(node, scratch):
        if run["minutes"] is None:
            continue
        stage = run["name"].rsplit("-", 1)[0] if run["name"].endswith(("-report", "-fix")) else run["name"]
        rec = by_stage.setdefault(stage, {"stage": stage, "size": effective_size(node), "model": run["model"],
                                          "effort": run["effort"], "applied": run["applied"], "minutes": 0.0,
                                          "task": nid, "plan": str(plan.get("title", "")),
                                          "start": run["start"].isoformat()})
        rec["minutes"] = round(rec["minutes"] + run["minutes"], 2)
    path = timings_file(graph_path, plan)
    seen = {(r.get("plan"), r.get("task"), r.get("stage"), r.get("start")) for r in load_timings(graph_path, plan)}
    new = [r for r in by_stage.values() if (r["plan"], r["task"], r["stage"], r["start"]) not in seen]
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            for r in new:
                fh.write(json.dumps(r) + "\n")
    return len(new)


def stage_estimate(plan: dict, records: list[dict], stage: str, size: str) -> tuple[float, bool]:
    """(minutes, measured?) for one stage: measured medians first, then the model-neutral defaults."""
    model, effort = model_for(plan, stage), effort_for(plan, stage)
    for match in (lambda r: (r.get("size"), r.get("model"), r.get("effort")) == (size, model, effort),
                  lambda r: (r.get("size"), r.get("model")) == (size, model)):
        xs = [float(r["minutes"]) for r in records if r.get("stage") == stage and match(r)]
        if xs:
            return statistics.median(xs), True
    xs = [float(r["minutes"]) / SIZE_FACTOR.get(r.get("size"), 1) for r in records
          if r.get("stage") == stage and r.get("model") == model]
    if xs:
        return statistics.median(xs) * SIZE_FACTOR.get(size, 1), True
    base = {**STAGE_MINUTES, **{k: float(v) for k, v in (plan.get("stage_minutes") or {}).items()}}
    return base.get(stage, 3.0) * SIZE_FACTOR.get(size, 1), False


def task_minutes(node: dict, plan: dict, records: list[dict]) -> tuple[float, int, int]:
    """(minutes, measured stages, estimated stages) for the node's workflow, without a conditional fix."""
    total, measured, estimated = 0.0, 0, 0
    for stage in workflow_of(node, plan):
        if stage == "fix":
            continue
        minutes, from_data = stage_estimate(plan, records, stage, effective_size(node))
        total += minutes
        measured += from_data
        estimated += not from_data
    return total, measured, estimated


# ── scheduling ─────────────────────────────────────────────────────────────────

def waves(data: dict) -> list[list[str]]:
    nodes = by_id(data)
    placed: set[str] = set()
    out: list[list[str]] = []
    while len(placed) < len(nodes):
        layer = sorted(i for i, n in nodes.items() if i not in placed and all(d in placed for d in n.get("deps") or []))
        if not layer:
            break  # a cycle; validate reports it
        out.append(layer)
        placed.update(layer)
    return out


def next_ready(data: dict, changed: dict[str, set[str]] | None = None) -> tuple[list[dict], list[tuple[str, str]], int]:
    """(tasks to start now, [(held task, reason)], free slots).

    `changed` maps an open lane to the files it has actually changed, which
    exclude other tasks as its listed `files` do.
    """
    plan = data["plan"]
    nodes = by_id(data)
    done = {i for i, n in nodes.items() if n.get("status") in FINISHED_STATUSES}
    blocked = {i for i, n in nodes.items() if n.get("status") == "blocked"}
    running = [n for n in nodes.values() if n.get("status") in OPEN_STATUSES]
    running_ids = {n["id"] for n in running}
    slots = int(plan.get("lane_cap", 1)) - len(running)
    hold: list[tuple[str, str]] = []

    # Prefer tasks whose soft deps are done, then larger tasks (they gate more), then id order.
    def rank(n: dict) -> tuple:
        soft_open = sum(1 for d in n.get("soft_deps") or [] if d not in done)
        return (soft_open, -{"L": 3, "M": 2, "S": 1}.get(n.get("size"), 1), n["id"])

    eligible: list[dict] = []
    for n in sorted((n for n in nodes.values() if n.get("status") == "planned"), key=rank):
        missing = [d for d in n.get("deps") or [] if d not in done]
        if missing:
            labels = [f"{d} (blocked)" if d in blocked else d for d in missing]
            hold.append((n["id"], "waits for " + ", ".join(labels)))
            continue
        unanswered = [od for od in n.get("owner_decisions") or [] if not str(od.get("answer") or "").strip()]
        if unanswered and int(plan.get("autonomy", 2)) < 4:
            hold.append((n["id"], f"needs the owner's answer: {unanswered[0]['question']}"))
            continue
        eligible.append(n)

    # A task that runs alone starts only when no lane is open, and once one is
    # eligible nothing else starts before it, so the open lanes drain for it.
    alone_open = next((n for n in running if runs_alone(n)), None)
    if alone_open is not None:
        return [], hold + [(n["id"], f"`{alone_open['id']}` runs alone") for n in eligible], slots
    alone = next((n for n in eligible if runs_alone(n)), None)
    if alone is not None:
        others = [n for n in eligible if n is not alone]
        if running:
            hold.append((alone["id"], f"runs alone; waits for {len(running)} open lane(s) to close"))
            return [], hold + [(n["id"], f"held so the open lanes drain for `{alone['id']}`") for n in others], slots
        return [alone], hold + [(n["id"], f"`{alone['id']}` runs alone") for n in others], slots

    start: list[dict] = []
    taken = {f for n in running for f in (n.get("files") or [])}
    for files in (changed or {}).values():
        taken |= files
    for n in eligible:
        shared = sorted(set(n.get("files") or []) & taken)
        if shared:
            hold.append((n["id"], "shares files with an open lane: " + ", ".join(shared[:3]) + (" ..." if len(shared) > 3 else "")))
            continue
        # A soft dependency orders work: the task waits while one is running or
        # starting, but not for one that can't start yet.
        busy = [d for d in n.get("soft_deps") or [] if d in running_ids or d in {s["id"] for s in start}]
        if busy:
            hold.append((n["id"], "starts after its soft dependencies: " + ", ".join(busy)))
            continue
        if len(start) >= max(slots, 0):
            hold.append((n["id"], "no free lane slot"))
            continue
        start.append(n)
        taken |= set(n.get("files") or [])
    return start, hold, slots


def simulate(data: dict, records: list[dict]) -> tuple[float, int, float]:
    """(minutes to finish every unfinished task, most lanes open at once, minutes back to back).

    Runs the real scheduler (dependencies, file exclusions, `alone`, the lane
    cap) against estimated task durations. Open lanes restart from zero, and
    owner questions count as answered.
    """
    plan = data["plan"]
    nodes = {i: dict(n) for i, n in by_id(data).items()}
    for n in nodes.values():
        if n.get("status") in OPEN_STATUSES:
            n["status"] = "planned"
        n["owner_decisions"] = []
    sim = {"plan": {**plan, "autonomy": 4}, "nodes": list(nodes.values())}
    minutes = {i: task_minutes(n, plan, records)[0] for i, n in nodes.items()}
    clock, running, peak = 0.0, {}, 0
    while True:
        start, _, _ = next_ready(sim)
        for n in start:
            n["status"] = "running"
            running[n["id"]] = clock + minutes[n["id"]]
        peak = max(peak, len(running))
        if not running:
            break
        first = min(running, key=running.get)
        clock = running.pop(first)
        nodes[first]["status"] = "done"
    total = sum(m for i, m in minutes.items() if by_id(data)[i].get("status") not in FINISHED_STATUSES)
    return clock, peak, total


# ── mutation of the graph file ─────────────────────────────────────────────────

def set_fields(data: dict, nid: str, assignments: list[str]) -> None:
    nodes = by_id(data)
    if nid not in nodes:
        raise SystemExit(f"unknown node id: {nid}")
    n = nodes[nid]
    changed: list[str] = []
    for a in assignments:
        key, sep, value = a.partition("=")
        if not sep:
            raise SystemExit(f"expected key=value, got {a!r}")
        if key == "status":
            if value not in STATUSES:
                raise SystemExit(f"status must be one of {STATUSES}")
            n["status"] = value
        elif key in ("lane", "branch", "commit"):
            n[key] = value or None
        elif key == "answer":
            idx, _, text = value.partition(":")
            decisions = n.get("owner_decisions") or []
            if not idx.isdigit() or int(idx) >= len(decisions):
                raise SystemExit(f"no owner decision at index {idx!r}; {nid} has {len(decisions)} (counted from 0)")
            decisions[int(idx)]["answer"] = text
        elif key == "log":
            pass  # the text lands in the log line below
        else:
            raise SystemExit(f"unknown key {key!r}; use status, lane, branch, commit, answer, log")
        changed.append(a)
    append_log(n, " ".join(changed))


def append_log(node: dict, text: str) -> None:
    if "log" not in node or node["log"] is None:
        node["log"] = []
    node["log"].append(f"{now()} {text}")


# ── rendering ──────────────────────────────────────────────────────────────────

def render(data: dict) -> str:
    plan = data["plan"]
    rows = ["| id | title | kind | size | workflow | status | deps | commit |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n in data["nodes"]:
        rows.append("| {id} | {title} | {kind} | {size} | {wf} | {status} | {deps} | {commit} |".format(
            id=n.get("id"), title=n.get("title", ""), kind=n.get("kind", ""), size=n.get("size", ""),
            wf=" → ".join(workflow_of(n, plan)) or "none", status=n.get("status", ""),
            deps=", ".join(n.get("deps") or []) or "-", commit=n.get("commit") or "-"))
    counts = Counter(n.get("status", "?") for n in data["nodes"])
    rows.append("")
    rows.append("Totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return "\n".join(rows)


# ── git and lane commands ──────────────────────────────────────────────────────

def _git(*args: str) -> str | None:
    """Run a read-only git command; return its stdout, or None if it failed."""
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def repo_root(graph_path: Path) -> Path:
    root = _git("-C", str(graph_path.parent), "rev-parse", "--show-toplevel")
    return Path(root).resolve() if root else graph_path.parent


def rebase_in_progress(wt: Path) -> bool:
    for name in ("rebase-merge", "rebase-apply"):
        p = _git("-C", str(wt), "rev-parse", "--git-path", name)
        if p and (wt / p).exists():
            return True
    return False


def lane_changes(data: dict, graph_path: Path) -> dict[str, set[str]]:
    """The files each open lane has changed so far, committed or not."""
    plan = data["plan"]
    root, main = repo_root(graph_path), str(plan.get("integration_branch", "main"))
    out: dict[str, set[str]] = {}
    for n in by_id(data).values():
        if n.get("status") not in OPEN_STATUSES or not n.get("branch"):
            continue
        files = set((_git("-C", str(root), "diff", "--name-only", f"{main}...{n['branch']}") or "").splitlines())
        wt = Path(str(n.get("lane") or ""))
        if wt.is_dir():
            for line in (_git("-C", str(wt), "status", "--porcelain") or "").splitlines():
                files.add(line[3:].split(" -> ")[-1])
        out[n["id"]] = {f for f in files if f}
    return out


def landed_commit(root: Path, nid: str, branch: str, main: str, policy: str) -> str | None:
    """The integration commit if an earlier integration already merged the lane."""
    if policy == "squash":
        return _git("-C", str(root), "log", main, "-1", "--format=%h", "--extended-regexp",
                    f"--grep=^Plan-Task: {re.escape(nid)}$") or None
    subject = _git("-C", str(root), "log", "-1", "--format=%s", branch) or ""
    ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", branch, main],
                              capture_output=True).returncode == 0
    if ancestor and subject.startswith(f"{nid}: "):
        return _git("-C", str(root), "rev-parse", "--short", branch)
    return None


def check_integrable(data: dict, graph_path: Path, nid: str, root: Path, wt: Path, branch: str, main: str) -> None:
    """Refuse to print integration steps for a lane that would land nothing, the wrong thing, or unreviewed work."""
    plan = data["plan"]
    node = by_id(data)[nid]
    if not wt.is_dir():
        raise SystemExit(f"refused: the lane worktree {wt} does not exist")
    if rebase_in_progress(wt):
        raise SystemExit(
            f"refused: a rebase is in progress in {wt}. Resolve the conflict and run "
            f"`git -C {wt} rebase --continue`, or run `git -C {wt} rebase --abort`; then integrate again")
    on = _git("-C", str(wt), "symbolic-ref", "--short", "HEAD")
    if on != branch:
        raise SystemExit(f"refused: the lane worktree is on {on or 'a detached HEAD'}, not {branch}")
    dirty = _git("-C", str(wt), "status", "--porcelain")
    if dirty is None:
        raise SystemExit(f"refused: git status failed in {wt}")
    if dirty:
        raise SystemExit(
            f"refused: the lane has uncommitted changes. Every stage ends with a commit; commit or discard "
            f"these first. If they are build output, add their pattern to .git/info/exclude:\n{dirty}")
    proofs = _git("-C", str(wt), "grep", "-l", "review_proof_")
    if proofs:
        raise SystemExit(f"refused: review_proof_ tests remain; the review's fix part turns each into a real test "
                         f"or removes it:\n{proofs}")
    scratch = lane_scratch(plan, graph_path, nid)
    started = {r["name"] for r in stage_runs(node, scratch)}
    required = [name for stage in workflow_of(node, plan) if stage != "fix" for name in part_names(stage)]
    if "fix" in started:
        required.append("fix")
        if int(plan.get("autonomy", 2)) < 4 and not decisions_file(scratch, nid).exists():
            raise SystemExit(f"refused: the fix stage ran without {decisions_file(scratch, nid)}")
    missing = [str(report_file(scratch, nid, name)) for name in required if not report_file(scratch, nid, name).exists()]
    if missing:
        raise SystemExit("refused: the workflow isn't finished; these reports are missing (run the stage):\n"
                         + "\n".join(missing))
    undecided = undecided_owner_items(node, plan, scratch)
    if undecided:
        who = ("the owner's answers" if int(plan.get("autonomy", 2)) < 4
               else "your calls, since nobody answers at autonomy 4")
        raise SystemExit(
            f"refused: {', '.join(undecided)} list \"Needs owner\" items, and no decision is recorded. Write each "
            f"one under the heading \"Owner-level decisions taken\" in {decisions_file(scratch, nid)} ({who}: the "
            f"question, the decision, who decided, and why), then land again. `plan.py findings` lists them.")
    ahead = _git("-C", str(root), "rev-list", "--count", f"{main}..{branch}")
    if ahead is None:
        raise SystemExit(f"refused: cannot compare {branch} with {main}")
    if ahead == "0":
        raise SystemExit(f"refused: {branch} has no commits beyond {main}; there is nothing to integrate")
    current = _git("-C", str(root), "symbolic-ref", "--short", "HEAD")
    if current != main:
        raise SystemExit(f"refused: the main worktree {root} is on {current or 'a detached HEAD'}, not {main}")


def _chain(lines: list[str], steps: list[str]) -> list[str]:
    return lines + [" && \\\n".join(steps)]


def lane_commands(data: dict, graph_path: Path, nid: str, action: str) -> str:
    plan = data["plan"]
    n = by_id(data).get(nid)
    if n is None:
        raise SystemExit(f"unknown node id: {nid}")
    root = repo_root(graph_path)
    wt = root_dir(plan, "worktree_root", graph_path) / nid
    scratch = lane_scratch(plan, graph_path, nid)
    branch = f"{plan['branch_prefix']}{nid}"
    main = str(plan["integration_branch"])
    policy = str(plan.get("commit_policy"))
    q = shlex.quote
    me = f"uv run {q(str(SELF))}"
    graph = q(str(graph_path))
    doc = spec_target(n, data, graph_path)[0]
    lines: list[str] = [f"# lane {nid}: {action}. Run the command below as one command; it stops at the first failure."]

    def merge_steps() -> list[str]:
        steps = [f"git -C {q(str(wt))} rebase {q(main)}"]
        steps += [f"(cd {q(str(wt))} && {gate})" for gate in plan.get("gates") or []]
        if policy == "squash":
            steps += [f"git -C {q(str(root))} merge --squash {q(branch)}",
                      f"git -C {q(str(root))} commit -m {q(f'{nid}: {n.get('title', '')}')} -m {q(f'Plan-Task: {nid}')}"]
        else:
            steps += [f"git -C {q(str(root))} merge --ff-only {q(branch)}"]
        return steps + [f"{me} set {graph} {q(nid)} status=done commit=$(git -C {q(str(root))} rev-parse --short HEAD)"]

    def close_steps() -> list[str]:
        # Tracked changes after integration (a formatter run by a gate) stop the removal;
        # untracked gate output doesn't, since `integrate` refused untracked files before the merge.
        steps = [f'test -z "$(git -C {q(str(wt))} status --porcelain --untracked-files=no)"',
                 f"git -C {q(str(root))} worktree remove --force {q(str(wt))}"] if wt.is_dir() else []
        # A squash merge does not mark the branch merged, so -d would refuse it.
        steps.append(f"git -C {q(str(root))} branch {'-D' if policy == 'squash' else '-d'} {q(branch)}")
        return steps + [f"{me} set {graph} {q(nid)} lane= branch=", f"{me} clean {graph} {q(nid)}"]

    def record_steps() -> list[str]:
        paths = " ".join(q(str(p)) for p in (doc, graph_path))
        return [f"{me} landed {graph} {q(nid)}",
                f"git -C {q(str(root))} add -- {paths}",
                f"git -C {q(str(root))} commit -q -m \"plan: {nid} landed ($(git -C {q(str(root))} rev-parse --short HEAD))\" -- {paths}"]

    if action == "open":
        if n.get("status") != "planned":
            raise SystemExit(f"refused: {nid} is {n.get('status')}, not planned")
        steps = [f"git -C {q(str(root))} worktree add {q(str(wt))} -b {q(branch)} {q(main)}",
                 f"mkdir -p {q(str(scratch))}",
                 f"{me} set {graph} {q(nid)} status=running lane={q(str(wt))} branch={q(branch)}"]
        if "delegate" in workflow_of(n, plan):
            steps.append(f"{me} context {graph} {q(nid)}")
        steps.append(f"{me} prompt {graph} {q(nid)} implement")
        return "\n".join(_chain(lines, steps))
    if action in ("integrate", "land"):
        landed = landed_commit(root, nid, branch, main, policy)
        if landed:
            lines += [f"# {branch} already landed on {main} at {landed}: an earlier integration stopped after the merge."]
            steps = [f"{me} set {graph} {q(nid)} status=done commit={landed}"]
            if action == "land":
                steps += close_steps() + record_steps()
            return "\n".join(_chain(lines, steps))
        check_integrable(data, graph_path, nid, root, wt, branch, main)
        changed = (_git("-C", str(root), "diff", "--name-only", f"{main}...{branch}") or "").splitlines()
        unlisted = sorted(set(changed) - set(n.get("files") or []))
        if unlisted:
            lines += [f"# note: the lane changed files that `files` does not list: {', '.join(unlisted)}",
                      "# add them to the task's `files` so the exclusion rule holds for the tasks still to run"]
        steps = merge_steps()
        if action == "land":
            steps += close_steps() + record_steps()
        lines = _chain(lines, steps)
        if action == "integrate":
            lines += ["# then: close the lane, apply the as-landed text, and commit the plan document and graph.yaml"]
        return "\n".join(lines)
    if action == "close":
        if n.get("status") not in FINISHED_STATUSES:
            raise SystemExit(f"refused: {nid} is {n.get('status')}, not done; use `abandon` to give up on a lane")
        if wt.is_dir():
            tracked = _git("-C", str(wt), "status", "--porcelain", "--untracked-files=no")
            if tracked:
                raise SystemExit(f"refused: tracked files changed in {wt} after integration:\n{tracked}")
        steps = close_steps()
        if not _git("-C", str(root), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"):
            steps = [s for s in steps if " branch -" not in s]
        return "\n".join(_chain(lines, steps))
    if action == "abandon":
        if not wt.is_dir():
            raise SystemExit(f"refused: the lane worktree {wt} does not exist")
        patch = scratch / f"{nid}.abandoned.patch"
        keep = f"abandoned/{nid}"
        lines += [f"# saves the lane's work as a patch, removes the worktree, and keeps every commit on {keep}"]
        steps = [f"mkdir -p {q(str(scratch))}"]
        if rebase_in_progress(wt):
            steps.append(f"git -C {q(str(wt))} rebase --abort")
        steps += [
            f"git -C {q(str(wt))} add -N .",
            f"git -C {q(str(wt))} diff $(git -C {q(str(wt))} merge-base HEAD {q(main)}) > {q(str(patch))}",
            f"git -C {q(str(root))} worktree remove --force {q(str(wt))}",
            f"git -C {q(str(root))} branch -m {q(branch)} {q(keep)}",
            f"{me} set {graph} {q(nid)} status=blocked lane= branch={q(keep)} log=abandoned:{q(str(patch))}",
            f"{me} clean {graph} {q(nid)}",
        ]
        return "\n".join(_chain(lines, steps))
    if action == "discard":
        if not wt.is_dir():
            raise SystemExit(f"refused: the lane worktree {wt} does not exist")
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        patch = scratch / f"{nid}.discarded-{stamp}.patch"
        lines += ["# saves the lane's uncommitted changes as a patch, then restores the lane to its last commit"]
        steps = [f"mkdir -p {q(str(scratch))}"]
        if rebase_in_progress(wt):
            steps.append(f"git -C {q(str(wt))} rebase --abort")
        steps += [
            f"git -C {q(str(wt))} add -N .",
            f"git -C {q(str(wt))} diff HEAD > {q(str(patch))}",
            f"git -C {q(str(wt))} reset --quiet --hard HEAD",
            f"git -C {q(str(wt))} clean -fdq",
        ]
        return "\n".join(_chain(lines, steps))
    raise SystemExit("action must be open, integrate, close, land, abandon, or discard")


# ── report sections ────────────────────────────────────────────────────────────

# "None.", "- None identified", "N/A: the spec settles it", "Nothing to report": a section with nothing in it.
EMPTY_SECTION_RE = re.compile(r"^[-*\s]*(?:none|n/a|nothing)\b", re.I)


def _heading_re(title: str) -> re.Pattern:
    return re.compile(rf"^\s*(?:(#{{1,6}})\s*|\*\*)?(?:\(?\d\)?\.?\s*)?{re.escape(title)}\b[.:*\s]*$", re.I)


def report_section(report: Path, title: str) -> str | None:
    """The text under a report's heading `title`, up to the next heading of the same or a higher level."""
    if not report.exists():
        return None
    lines = report.read_text(encoding="utf-8").splitlines()
    pattern = _heading_re(title)
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if not m:
            continue
        level = len(m.group(1)) if m.group(1) else 7
        body = []
        for nxt in lines[i + 1:]:
            h = HEADING_RE.match(nxt)
            if (h and len(h.group(1)) <= level) or (level == 7 and re.match(r"^\s*\*\*[^*]+\*\*\s*$", nxt)):
                break
            body.append(nxt)
        text = "\n".join(body).strip()
        if text and not EMPTY_SECTION_RE.match(text):
            return text
    return None


def as_landed_text(report: Path) -> str:
    text = report_section(report, "As landed")
    if not text:
        raise SystemExit(f"no \"As landed\" heading with text in {report}")
    return text


def task_reports(node: dict, plan: dict, scratch: Path) -> list[Path]:
    names = [name for stage in workflow_of(node, plan) for name in part_names(stage)]
    if "fix" not in names:
        names.append("fix")
    ordered = [n for n in ("implement", "review-report", "review-fix", "second_review-report",
                           "second_review-fix", "fix", "delegate") if n in names]
    return [report_file(scratch, node["id"], n) for n in ordered] + [decisions_file(scratch, node["id"])]


def decisions_file(scratch: Path, nid: str) -> Path:
    """The coordinator's record for a task: accepted findings, and every owner-level decision with who made it."""
    return scratch / f"{nid}_decisions.md"


def undecided_owner_items(node: dict, plan: dict, scratch: Path) -> list[str]:
    """Reports with "Needs owner" items, when no one has recorded "Owner-level decisions taken" for the task."""
    found = findings(node, plan, scratch)
    if found["Owner-level decisions taken"]:
        return []
    return [source for source, _ in found["Needs owner"]]


FINDING_SECTIONS = ("Needs owner", "Owner-level decisions taken", "Beyond", "Residuals")


def findings(node: dict, plan: dict, scratch: Path) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {s: [] for s in FINDING_SECTIONS}
    for report in task_reports(node, plan, scratch):
        for title in FINDING_SECTIONS:
            text = report_section(report, title)
            if text:
                out[title].append((report.name, text))
    return out


def apply_landed(doc: Path, anchor: str, text: str) -> None:
    """Replace the "As landed" paragraph of a task's section (or append one) with `text`."""
    source = doc.read_text(encoding="utf-8")
    if doc.suffix.lower() in (".html", ".htm"):
        start, end = _html_bounds(source, anchor)
        paras = "\n".join(f"<p>{html_lib.escape(p.strip())}</p>" for p in re.split(r"\n\s*\n", text) if p.strip())
        block = f"<p><strong>As landed.</strong></p>\n{paras}\n"
        part = source[start:end]
        m = re.search(r"(?is)<p>\s*<strong>\s*As landed\.?\s*</strong>.*?</p>\s*", part)
        part = part[:m.start()] + block + part[m.end():] if m else part.rstrip() + "\n" + block + "\n"
        result = source[:start] + part + source[end:]
    else:
        start, end, lines = _md_bounds(source, anchor)
        body = lines[start:end]
        at = next((i for i, line in enumerate(body) if line.lstrip().startswith("**As landed")), None)
        while body and not body[-1].strip():
            body.pop()
        new = ["**As landed.**", "", *text.splitlines(), ""]
        body = (body[:at] if at is not None else body + [""]) + new
        result = "\n".join(lines[:start] + body + lines[end:]) + ("\n" if source.endswith("\n") else "")
    _write_atomic(doc, result)


def landed_in_section(text: str) -> str:
    """The "As landed" text of a task section, as `section()` returns it."""
    m = re.search(r"(?is)\**As landed\.?\**\s*(.*)$", text)
    body = m.group(1).strip() if m else ""
    return "" if body.lower().startswith("empty until") else body


# ── coordinator brief ──────────────────────────────────────────────────────────

AUTONOMY_MEANING = {
    0: "the owner confirms every lane and integration, and answers every owner question",
    1: "the owner answers owner questions and rules on P1 and P2 findings",
    2: "the owner answers owner questions and rules on P1 findings",
    3: "the owner answers owner questions",
    4: "nobody answers: owner-level calls are made by the workflow and reported in full",
}
SCOPE_RULES = """- `spec`: the work violates the specification or an acceptance criterion. Fix it.
- `defect`: a wrong result, a crash, or data loss in a case the specification doesn't address. Fix it when the fix is small.
- `quality` (second review): simpler, clearer, or a better fit with the existing code and the upcoming tasks, with no change in behavior. Fix it.
- `beyond`: a behavior change the specification doesn't ask for. Report it; it is applied only when accepted.
- Removing or changing existing behavior the specification doesn't mention is an owner decision."""


def build_context(data: dict, graph_path: Path, nid: str, note: str | None) -> Path:
    plan = data["plan"]
    nodes = by_id(data)
    node = nodes[nid]
    autonomy = int(plan.get("autonomy", 2))
    parts = [f"# Coordinator's brief for task {nid}", "",
             f"Plan: {plan.get('title', '')}. Autonomy {autonomy}: {AUTONOMY_MEANING.get(autonomy, '')}. "
             f"Coordinator mode: {plan.get('coordinator', 'full')}.", "",
             "## This task", "", f"{nid}: {node.get('title', '')}. Expected files: "
             + (", ".join(str(f) for f in node.get("files") or []) or "none listed") + ".", ""]
    ods = node.get("owner_decisions") or []
    for od in ods:
        answer = str(od.get("answer") or "").strip()
        parts.append(f"- Owner question: {od['question']} Answer: {answer or od['default'] + ' (default)'}")
    parts += ["", "## Scope rules", "", SCOPE_RULES, "", "## Tasks already landed", ""]
    landed = []
    for other in nodes.values():
        if other["id"] == nid or other.get("status") != "done":
            continue
        doc, anchor = spec_target(other, data, graph_path)
        try:
            text = landed_in_section(section(doc, anchor))
        except (AnchorError, OSError):
            text = ""
        landed.append(f"- {other['id']} ({other.get('commit') or '-'}): {other.get('title', '')}. "
                      f"As landed: {text or 'not recorded'}")
    parts += landed or ["- none"]
    parts += ["", "## Tasks still to come", ""]
    upcoming = [f"- {o['id']}: {o.get('title', '')}; expected files: " + (", ".join(str(f) for f in o.get("files") or []) or "none")
                for o in nodes.values() if o["id"] != nid and o.get("status") not in FINISHED_STATUSES + ("blocked",)]
    parts += upcoming or ["- none"]
    doc = graph_path.parent / str(plan.get("spec", ""))
    try:
        residuals = section(doc, "residuals")
        residuals = "\n".join(residuals.splitlines()[1:]).strip()
    except (AnchorError, OSError):
        residuals = ""
    parts += ["", "## Open residuals", "", residuals or "none", "", "## The coordinator's note", "", note or "none", ""]
    scratch = lane_scratch(plan, graph_path, nid)
    scratch.mkdir(parents=True, exist_ok=True)
    out = scratch / f"{nid}_context.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


# ── stage prompts ──────────────────────────────────────────────────────────────

TEMPLATE_RE = re.compile(r"^```template:([\w-]+)\n(.*?)^```", re.M | re.S)
TEMPLATE_NAMES = {"header", "implement", "implement-measurement", "review-report", "review-fix",
                  "second_review-report", "second_review-fix", "fix", "delegate"}


def templates() -> dict[str, str]:
    found = dict(TEMPLATE_RE.findall(TEMPLATES.read_text(encoding="utf-8")))
    missing = TEMPLATE_NAMES - set(found)
    if missing:
        raise SystemExit(f"{TEMPLATES} lacks the templates: {', '.join(sorted(missing))}")
    return found


def _owner_decisions(node: dict, autonomy: int) -> str:
    items = []
    for od in node.get("owner_decisions") or []:
        answer = str(od.get("answer") or "").strip()
        if answer:
            items.append(f"{od['question']} -> {answer}")
        elif autonomy >= 4:
            items.append(f"{od['question']} -> {od['default']} (taken by default)")
        else:
            raise SystemExit(f"refused: the owner hasn't answered: {od['question']}")
    return "; ".join(items) or "none"


def render_prompt(data: dict, graph_path: Path, nid: str, stage: str, part: str | None = None,
                  decisions: Path | None = None, via: str = "agent") -> tuple[Path, str]:
    """Fill the stage's template, log the stage's start; return (prompt file, launcher line)."""
    plan = data["plan"]
    n = by_id(data).get(nid)
    if n is None:
        raise SystemExit(f"unknown node id: {nid}")
    stages = workflow_of(n, plan)
    autonomy = int(plan.get("autonomy", 2))
    if stage not in TWO_PART and part:
        raise SystemExit(f"refused: the {stage} stage has no parts")
    if stage == "fix":
        # The fix stage also runs outside the workflow, to apply the owner's answers or reopen a lane.
        if decisions is None and not (autonomy >= 4 and decider(plan, stages) == "fix"):
            raise SystemExit("refused: the fix stage needs --decisions FILE (accepted findings, owner answers, "
                             "or the gate failure)")
    elif stage not in stages:
        raise SystemExit(f"refused: {nid}'s workflow is {' -> '.join(stages) or 'none'}; it has no {stage} stage")
    name = prompt_name(stage, part)
    tpl_name = "implement-measurement" if stage == "implement" and n.get("kind") == "measurement" else name
    doc, anchor = spec_target(n, data, graph_path)
    try:
        spec = section(doc, anchor)
    except AnchorError as exc:
        raise SystemExit(f"{nid}: {exc} in {doc}")
    scratch = lane_scratch(plan, graph_path, nid)
    tmp = stage_tmp(scratch, name)
    tmp.mkdir(parents=True, exist_ok=True)
    context = scratch / f"{nid}_context.md"
    if stage in ("second_review", "delegate") and not context.exists():
        context = build_context(data, graph_path, nid, None)
    is_last_review = stage == last_review(stages)
    writes_landed = (name in ("fix", "delegate") or (part == "fix" and is_last_review)
                     or (stage == "implement" and n.get("kind") == "measurement"))
    decides = autonomy >= 4 and decider(plan, stages) == stage and (stage not in TWO_PART or part == "fix")
    if stage == "review":
        mutation = ("Don't re-run stage 1's mutations; the second reviewer does that."
                    if "second_review" in stages else
                    "Re-run each mutation the implementer's report lists, and confirm a test still catches it.")
    elif stage == "second_review":
        mutation = "Re-run each mutation the implementer's report lists, and confirm a test still catches it after the first review's fixes."
    else:
        mutation = ""
    owner_rule = (
        "Owner-level calls are yours, because nobody will answer: a behavior the specification doesn't "
        "settle, or a change to existing behavior it doesn't mention. Take the reading closest to the "
        "specification's words, apply it, and list each call under the heading \"Owner-level decisions "
        "taken\": the question, your decision, and why."
        if decides else
        "Owner-level calls are not yours: a behavior the specification doesn't settle, or a change to "
        "existing behavior it doesn't mention. List each under the heading \"Needs owner\", with your "
        "recommendation, and don't change it.")
    landed_duty = ("End the report with a section under the heading \"As landed\": the exact text for the plan "
                   "document (what shipped, each deviation from the specification, each residual, each "
                   "measurement worth keeping), written so that it can be pasted." if writes_landed else "")
    if decisions is not None:
        decision_text = decisions.read_text(encoding="utf-8").strip()
    elif stage == "fix":
        decision_text = ("None were given: decide each item under \"Needs owner\" and \"Beyond\" in the earlier "
                         "reports yourself, as the rule on owner-level calls says.")
    else:
        decision_text = ""
    commands = plan.get("commands") or {}
    values = {
        "task_id": nid,
        "task_title": str(n.get("title", "")),
        "lane_worktree": str(n.get("lane") or root_dir(plan, "worktree_root", graph_path) / nid),
        "lane_branch": str(n.get("branch") or f"{plan['branch_prefix']}{nid}"),
        "integration_branch": str(plan["integration_branch"]),
        "scratch": str(scratch),
        "stage_tmp": str(tmp),
        "report": str(report_file(scratch, nid, name)),
        "guidelines": ", ".join(str(resolve_doc(str(g), graph_path)) for g in plan.get("guidelines") or []) or "none",
        "prior_plans": ", ".join(str(resolve_doc(str(g), graph_path)) for g in plan.get("prior_plans") or []) or "none",
        "commands": "; ".join(f"{k}: `{v}`" for k, v in commands.items()) or "see the gates",
        "gates": ", then ".join(f"`{g}`" for g in plan.get("gates") or []),
        "files": ", ".join(str(f) for f in n.get("files") or []) or "none listed",
        "owner_decisions": _owner_decisions(n, autonomy),
        "owner_rule": owner_rule,
        "mutation_duty": mutation,
        "landed_duty": landed_duty,
        "context": str(context),
        "spec": spec,
        "decisions": decision_text,
    }
    tpl = templates()
    text = tpl[tpl_name].replace("{{common header}}", tpl["header"].rstrip("\n"))
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    text = re.sub(r"\n{3,}", "\n\n", text)
    left = sorted(set(re.findall(r"\{\{[\w ]+\}\}", text)))
    if left:
        raise SystemExit(f"template {tpl_name} has unknown placeholders: {', '.join(left)}")
    out = scratch / f"{nid}_{name}.prompt.md"
    out.write_text(text, encoding="utf-8")
    model, effort = model_for(plan, stage), effort_for(plan, stage)
    applied = effort if via == "workflow" else "session"
    with locked(graph_path):
        fresh = load(graph_path)
        append_log(by_id(fresh)[nid], f"stage={name} start model={model} effort={effort} applied={applied}")
        save(graph_path, fresh)
    if part == "fix":
        launcher = (f"Part 2 of your review of task {nid}: your instructions are in {out}. Read that file and "
                    f"follow it exactly.")
    else:
        launcher = (f"You are the {name} stage of task {nid}. Your complete instructions are in {out}. Read that "
                    f"file first and follow it exactly; it is your whole task.")
    return out, launcher


# ── final report and cleanup ───────────────────────────────────────────────────

def build_report(data: dict, graph_path: Path) -> str:
    plan = data["plan"]
    lines = [f"# Final report: {plan.get('title', '')}", "", f"Written {now()} by `plan.py report`.", "",
             render(data), ""]
    stage_totals: Counter = Counter()
    for n in by_id(data).values():
        scratch = lane_scratch(plan, graph_path, n["id"])
        lines += [f"## {n['id']}: {n.get('title', '')}", "",
                  f"Status {n.get('status')}; commit {n.get('commit') or '-'}; workflow "
                  f"{' -> '.join(workflow_of(n, plan)) or 'none'}"
                  + (f"; escalated ({n.get('escalate')})" if n.get("escalate") else "") + ".", ""]
        runs = stage_runs(n, scratch)
        if runs:
            lines += ["| prompt | model | effort requested | effort applied | minutes |", "| --- | --- | --- | --- | --- |"]
            for r in runs:
                lines.append(f"| {r['name']} | {r['model'] or '-'} | {r['effort'] or '-'} | {r['applied'] or '-'} | "
                             f"{r['minutes'] if r['minutes'] is not None else 'unfinished'} |")
                if r["minutes"] is not None:
                    stage_totals[r["name"]] += r["minutes"]
            lines.append("")
        for title, items in findings(n, plan, scratch).items():
            for source, text in items:
                lines += [f"**{title}** ({source}):", "", text, ""]
        for line in n.get("log") or []:
            if "abandoned:" in str(line):
                lines += [f"Abandoned; the lane's work is saved at {str(line).split('abandoned:', 1)[1]}.", ""]
    if stage_totals:
        lines += ["## Agent minutes by prompt", ""]
        lines += [f"- {k}: {v:.1f}" for k, v in sorted(stage_totals.items())]
        lines.append(f"- total: {sum(stage_totals.values()):.1f}")
    return "\n".join(lines).rstrip() + "\n"


def _size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def clean(data: dict, graph_path: Path, nid: str | None) -> str:
    """Remove scratch that is no longer needed; return what was reclaimed."""
    plan = data["plan"]
    root = root_dir(plan, "scratch_root", graph_path)
    freed = 0
    if nid is not None:
        scratch = lane_scratch(plan, graph_path, nid)
        for d in sorted(scratch.glob("stage-*")) if scratch.is_dir() else []:
            freed += _size(d)
            shutil.rmtree(d, ignore_errors=True)
        return f"{nid}: reclaimed {freed / 1024:.0f} KiB of stage temp files in {scratch}"
    open_lanes = [i for i, n in by_id(data).items() if n.get("status") in OPEN_STATUSES]
    if open_lanes:
        raise SystemExit(f"refused: lanes are still open: {', '.join(open_lanes)}")
    if not (graph_path.parent / REPORT_NAME).exists():
        raise SystemExit(f"refused: write the final report first (`plan.py report`); it replaces the stage reports")
    blocked = {i for i, n in by_id(data).items() if n.get("status") == "blocked"}
    kept = []
    for lane in sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        if lane.name in blocked:
            for item in lane.iterdir():
                if item.name.endswith(".abandoned.patch"):
                    kept.append(str(item))
                    continue
                freed += _size(item)
                shutil.rmtree(item, ignore_errors=True) if item.is_dir() else item.unlink(missing_ok=True)
        else:
            freed += _size(lane)
            shutil.rmtree(lane, ignore_errors=True)
    wt_root = root_dir(plan, "worktree_root", graph_path)
    for d in (root, wt_root, root.parent, wt_root.parent):
        # The lane roots and their parent directories, only when they are empty, and never the repository.
        if d.is_dir() and d != repo_root(graph_path) and not any(d.iterdir()):
            d.rmdir()
    return (f"reclaimed {freed / 1024:.0f} KiB of scratch under {root}"
            + (f"; kept the abandoned patches: {', '.join(kept)}" if kept else ""))


# ── main ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "waves", "next", "render", "report"):
        p = sub.add_parser(name)
        p.add_argument("graph", type=Path)
    p = sub.add_parser("set")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("assignments", nargs="+")
    p = sub.add_parser("lane")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("action", choices=("open", "integrate", "close", "land", "abandon", "discard"))
    for name in ("excerpt", "findings"):
        p = sub.add_parser(name)
        p.add_argument("graph", type=Path)
        p.add_argument("id")
    p = sub.add_parser("prompt")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("stage", choices=STAGES)
    p.add_argument("--part", choices=("report", "fix"))
    p.add_argument("--decisions", type=Path)
    p.add_argument("--via", choices=("agent", "workflow"), default="agent")
    p = sub.add_parser("context")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("--note", type=Path)
    p = sub.add_parser("landed")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("report", type=Path, nargs="?")
    p = sub.add_parser("clean")
    p.add_argument("graph", type=Path)
    p.add_argument("id", nargs="?")
    args = parser.parse_args(argv)

    graph_path: Path = args.graph.resolve()
    if not graph_path.is_file():
        print(f"no such file: {graph_path}", file=sys.stderr)
        return 2

    if args.cmd == "set":
        with locked(graph_path):
            data = load(graph_path)
            set_fields(data, args.id, args.assignments)
            save(graph_path, data)
        print(f"{args.id}: {' '.join(args.assignments)}")
        return 0

    data = load(graph_path)
    plan = data["plan"]
    if getattr(args, "id", None) and args.id not in by_id(data):
        print(f"unknown node id: {args.id}", file=sys.stderr)
        return 2
    if args.cmd == "validate":
        errors, warns = validate(data, graph_path)
        for w in warns:
            print(f"warning: {w}")
        for e in errors:
            print(f"error: {e}")
        print(f"{len(data['nodes'])} nodes; {len(errors)} errors; {len(warns)} warnings")
        return 1 if errors else 0
    if args.cmd == "waves":
        for i, layer in enumerate(waves(data), 1):
            print(f"wave {i}: {', '.join(layer)}")
        items = list(by_id(data).values())
        pairs = []
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                shared = set(items[a].get("files") or []) & set(items[b].get("files") or [])
                if shared:
                    pairs.append(f"{items[a]['id']} x {items[b]['id']} ({len(shared)} shared)")
        if pairs:
            print("exclusions (never at the same time): " + "; ".join(pairs))
        alone = [n["id"] for n in items if runs_alone(n)]
        if alone:
            print("runs alone: " + ", ".join(alone))
        todo = [n for n in items if n.get("status") not in FINISHED_STATUSES]
        flows: dict[str, list[str]] = {}
        for n in todo:
            flows.setdefault(" -> ".join(workflow_of(n, plan)) or "none (the coordinator)", []).append(
                n["id"] + (f" (escalated: {n['escalate']})" if n.get("escalate") else ""))
        for flow, ids in flows.items():
            print(f"workflow {flow}: {', '.join(ids)}")
        agents = sum(len([s for s in workflow_of(n, plan) if s != "fix"]) for n in todo)
        fixes = sum(1 for n in todo if "fix" in workflow_of(n, plan))
        print(f"agents for the {len(todo)} unfinished tasks: {agents} (a review stage is one agent given two prompts)"
              + (f", plus up to {fixes} fix stages if findings are accepted" if fixes else ""))
        records = load_timings(graph_path, plan)
        makespan, peak, total = simulate(data, records)
        measured = sum(task_minutes(n, plan, records)[1] for n in todo)
        estimated = sum(task_minutes(n, plan, records)[2] for n in todo)
        print(f"estimated time: {makespan:.0f} min with lane_cap {plan.get('lane_cap')} and the file exclusions, "
              f"at most {peak} lane(s) at once; {total:.0f} min back to back "
              f"({measured} stage estimates measured in this repository, {estimated} defaults)")
        hubs = Counter(f for n in todo for f in set(n.get("files") or []))
        shared = {f: [n["id"] for n in todo if f in (n.get("files") or [])] for f, k in hubs.items() if k > 1}
        if shared:
            print("hub files (tasks that list the same file never run together): "
                  + "; ".join(f"{f} ({', '.join(ids)})" for f, ids in sorted(shared.items())))
        if len(todo) >= 3 and peak <= 1:
            print("warning: the plan runs one lane at a time; dependencies or shared files serialize it. A seam "
                  "task that gives each task its own files can let them run in parallel (SKILL.md, \"Seams\").")
        return 0
    if args.cmd == "next":
        start, hold, slots = next_ready(data, lane_changes(data, graph_path))
        open_lanes = [f"{n['id']} ({n.get('status')})" for n in by_id(data).values() if n.get("status") in OPEN_STATUSES]
        print(f"free lane slots: {max(slots, 0)}; open lanes: {', '.join(open_lanes) or 'none'}")
        for n in start:
            print(f"START {n['id']}: {n.get('title', '')} [{n.get('kind')}, {n.get('size')}; workflow "
                  f"{' -> '.join(workflow_of(n, plan)) or 'none'}]")
        for nid, why in hold:
            print(f"HOLD  {nid}: {why}")
        if not start and not open_lanes:
            blocked = [i for i, n in by_id(data).items() if n.get("status") == "blocked"]
            print("FINISHED: no lane is open and nothing can start"
                  + (f"; blocked, for the user: {', '.join(blocked)}" if blocked else "")
                  + ("; the HOLD lines above need the user" if hold else "")
                  + ". Next: `plan.py report`, then `plan.py clean`.")
        return 0
    if args.cmd == "render":
        print(render(data))
        return 0
    if args.cmd == "lane":
        print(lane_commands(data, graph_path, args.id, args.action))
        return 0
    if args.cmd == "prompt":
        out, launcher = render_prompt(data, graph_path, args.id, args.stage, args.part, args.decisions, args.via)
        model, effort = model_for(plan, args.stage), effort_for(plan, args.stage)
        note = "" if args.via == "workflow" or not effort else " (the Agent tool can't set effort; the session's applies)"
        print(f"# model: {model or 'unset'}; effort requested: {effort or 'unset'}{note}")
        print(f"# prompt written to {out} ({len(out.read_text(encoding='utf-8'))} chars); give the agent this line:")
        print(launcher)
        return 0
    if args.cmd == "context":
        note = args.note.read_text(encoding="utf-8").strip() if args.note else None
        print(f"brief written to {build_context(data, graph_path, args.id, note)}")
        return 0
    if args.cmd == "findings":
        n = by_id(data)[args.id]
        found = findings(n, plan, lane_scratch(plan, graph_path, args.id))
        empty = True
        for title, items in found.items():
            for source, text in items:
                empty = False
                print(f"## {title} ({source})\n\n{text}\n")
        if empty:
            print(f"{args.id}: no Needs owner, Owner-level decisions, Beyond, or Residuals items")
        return 0
    if args.cmd == "landed":
        n = by_id(data)[args.id]
        report = args.report
        if report is None:
            scratch = lane_scratch(plan, graph_path, args.id)
            report = next((r for r in reversed(task_reports(n, plan, scratch)) if report_section(r, "As landed")), None)
            if report is None:
                print(f"{args.id}: no report of this task has an \"As landed\" section", file=sys.stderr)
                return 1
        text = as_landed_text(report)
        doc, anchor = spec_target(n, data, graph_path)
        try:
            apply_landed(doc, anchor, text)
        except AnchorError as exc:
            print(f"{args.id}: {exc} in {doc}", file=sys.stderr)
            return 1
        recorded = record_timings(data, graph_path, args.id)
        print(f"{args.id}: applied {len(text.splitlines())} lines of As landed text from {report.name} to {doc.name}; "
              f"recorded {recorded} stage timings")
        return 0
    if args.cmd == "report":
        for nid, n in by_id(data).items():
            if n.get("status") in FINISHED_STATUSES:
                record_timings(data, graph_path, nid)
        out = graph_path.parent / REPORT_NAME
        text = build_report(data, graph_path)
        _write_atomic(out, text)
        print(text)
        print(f"# written to {out}; commit it, then run `plan.py clean` to reclaim the scratch space")
        return 0
    if args.cmd == "clean":
        print(clean(data, graph_path, args.id))
        return 0
    if args.cmd == "excerpt":
        n = by_id(data)[args.id]
        doc, anchor = spec_target(n, data, graph_path)
        try:
            print(section(doc, anchor))
        except AnchorError as exc:
            print(f"{args.id}: {exc} in {doc}", file=sys.stderr)
            return 1
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
