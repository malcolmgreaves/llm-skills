#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["ruamel.yaml>=0.18"]
# ///
"""Operate on an executable plan's graph.yaml.

Usage:
    uv run plan.py validate GRAPH              # schema, cycles, anchors, files
    uv run plan.py waves GRAPH                 # the concurrent layers, exclusions, and agent count
    uv run plan.py next GRAPH                  # what can start now, and why the rest waits
    uv run plan.py set GRAPH ID key=value ...  # status=, lane=, branch=, commit=, log=, answer=N:text
    uv run plan.py render GRAPH                # a status table (Markdown)
    uv run plan.py lane GRAPH ID ACTION        # print the shell command for a lane action:
                                               #   open, integrate, close, abandon, discard
    uv run plan.py excerpt GRAPH ID            # the task's section from the plan document
    uv run plan.py prompt GRAPH ID STAGE [--decisions FILE]
                                               # render a stage prompt to the lane's scratch
                                               #   directory; print the launcher line
    uv run plan.py landed GRAPH ID REPORT      # paste a report's "As landed" text into the plan

The script runs only read-only git commands. It prints every command that
changes a repository for the coordinator to run, as one `&&` chain that
stops at the first failure, so each destructive step stays visible.
"""

from __future__ import annotations

import argparse
import fcntl
import html as html_lib
import os
import re
import shlex
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

STATUSES = ("planned", "running", "review", "integrating", "done", "blocked", "skipped")
OPEN_STATUSES = ("running", "review", "integrating")
FINISHED_STATUSES = ("done", "skipped")
KINDS = ("code", "docs", "plan", "measurement")
CHAINS = ("default", "light", "docs-only", "none")
SIZES = ("S", "M", "L")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PLAN_REQUIRED = (
    "title", "spec", "integration_branch", "worktree_root", "scratch_root",
    "branch_prefix", "lane_cap", "autonomy", "commit_policy", "models", "gates",
)
MODEL_STAGES = ("implement", "review", "fix", "final_review")
# The stages of each chain; `measurement` is the implied chain of a measurement task.
CHAIN_STAGES = {
    "default": ("implement", "review", "fix", "final-review"),
    "light": ("implement", "final-review"),
    "docs-only": ("implement", "final-review"),
    "measurement": ("implement",),
    "none": (),
}
STAGE_NUMBER = {"implement": 1, "review": 2, "fix": 3, "final-review": 4}
# Minutes of agent time per stage for an S task, from measured runs; M doubles, L quadruples.
# plan.stage_minutes overrides them (keys: implement, review, fix, final_review).
STAGE_MINUTES = {"implement": 3.0, "review": 4.5, "fix": 3.5, "final-review": 1.5}
SIZE_FACTOR = {"S": 1, "M": 2, "L": 4}
SELF = Path(__file__).resolve()
CHAIN_DOC = SELF.parent.parent / "references" / "chain.md"

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


def save(graph_path: Path, data: dict) -> None:
    """Write atomically, so a reader never sees half a file."""
    fd, tmp = tempfile.mkstemp(dir=graph_path.parent, prefix=f".{graph_path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(dump(data))
        os.replace(tmp, graph_path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


@contextmanager
def locked(graph_path: Path):
    """Serialize read-modify-write of the graph across processes."""
    common = _git("-C", str(graph_path.parent), "rev-parse", "--git-common-dir")
    if common:
        lock = (graph_path.parent / common / "executable-plan.lock").resolve()
    else:
        lock = graph_path.with_name(f".{graph_path.name}.lock")
    with open(lock, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        yield


def by_id(data: dict) -> dict[str, dict]:
    return {n["id"]: n for n in data["nodes"] if isinstance(n, dict) and isinstance(n.get("id"), str)}


def chain_of(node: dict) -> str:
    """The node's chain: its `chain` field, or the default for its kind and size."""
    if node.get("chain"):
        return str(node["chain"])
    kind = node.get("kind")
    if kind in ("docs", "plan"):
        return "docs-only"
    if kind == "measurement":
        return "measurement"
    return "light" if node.get("size") == "S" else "default"


def task_minutes(node: dict, plan: dict) -> float:
    """Estimated agent minutes for the node's whole chain."""
    override = {k.replace("_", "-"): float(v) for k, v in (plan.get("stage_minutes") or {}).items()}
    per_stage = {**STAGE_MINUTES, **override}
    factor = SIZE_FACTOR.get(node.get("size"), 1)
    return sum(per_stage[s] for s in CHAIN_STAGES.get(chain_of(node), ())) * factor


def runs_alone(node: dict) -> bool:
    # A measurement runs alone unless told otherwise: other lanes' builds skew its numbers.
    return bool(node.get("alone", node.get("kind") == "measurement"))


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
    models = plan.get("models") or {}
    for stage in MODEL_STAGES:
        if not models.get(stage):
            errors.append(f"plan.models.{stage} is missing")
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
    for n in nodes:
        nid = str(n.get("id", "?"))
        if isinstance(n.get("id"), str) and not ID_RE.match(nid):
            errors.append(f"{nid}: id must match {ID_RE.pattern}")
        for key in ("title", "spec", "kind", "size", "status"):
            if key not in n:
                errors.append(f"{nid}: {key} is missing")
        if n.get("kind") not in KINDS:
            errors.append(f"{nid}: kind must be one of {KINDS}")
        if n.get("chain", "default") not in CHAINS:
            errors.append(f"{nid}: chain must be one of {CHAINS}")
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


def critical_path(data: dict) -> tuple[list[str], float, float]:
    """(the longest chain of unfinished tasks by hard deps, its minutes, the minutes of all tasks)."""
    plan = data["plan"]
    nodes = {i: n for i, n in by_id(data).items() if n.get("status") not in FINISHED_STATUSES}
    best: dict[str, tuple[float, list[str]]] = {}

    def longest(i: str) -> tuple[float, list[str]]:
        if i not in best:
            before = [longest(d) for d in nodes[i].get("deps") or [] if d in nodes]
            t, path = max(before, default=(0.0, []), key=lambda x: x[0])
            best[i] = (t + task_minutes(nodes[i], plan), path + [i])
        return best[i]

    if find_cycle(data):
        return [], 0.0, 0.0
    runs = [longest(i) for i in nodes]
    t, path = max(runs, default=(0.0, []), key=lambda x: x[0])
    return path, t, sum(task_minutes(n, plan) for n in nodes.values())


def next_ready(data: dict) -> tuple[list[dict], list[tuple[str, str]], int]:
    """(tasks to start now, [(held task, reason)], free slots)."""
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
    if "log" not in n or n["log"] is None:
        n["log"] = []
    n["log"].append(f"{datetime.now().isoformat(timespec='minutes')} {' '.join(changed)}")


# ── rendering ──────────────────────────────────────────────────────────────────

def render(data: dict) -> str:
    rows = ["| id | title | kind | size | status | deps | lane | commit |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n in data["nodes"]:
        rows.append("| {id} | {title} | {kind} | {size} | {status} | {deps} | {lane} | {commit} |".format(
            id=n.get("id"), title=n.get("title", ""), kind=n.get("kind", ""), size=n.get("size", ""),
            status=n.get("status", ""), deps=", ".join(n.get("deps") or []) or "-",
            lane=n.get("lane") or "-", commit=n.get("commit") or "-"))
    counts: dict[str, int] = {}
    for n in data["nodes"]:
        counts[n.get("status", "?")] = counts.get(n.get("status", "?"), 0) + 1
    rows.append("")
    rows.append("Totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return "\n".join(rows)


# ── lane commands ──────────────────────────────────────────────────────────────

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


def check_integrable(root: Path, wt: Path, branch: str, main: str) -> None:
    """Refuse to print integration steps for a lane that would land nothing or the wrong thing."""
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
            f"refused: the lane has uncommitted changes. Every chain stage ends with a commit "
            f"(see references/chain.md); commit or discard these first. If they are build output, "
            f"add their pattern to .git/info/exclude:\n{dirty}")
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
    scratch = root_dir(plan, "scratch_root", graph_path) / nid
    branch = f"{plan['branch_prefix']}{nid}"
    main = str(plan["integration_branch"])
    policy = str(plan.get("commit_policy"))
    q = shlex.quote
    me = f"uv run {q(str(SELF))}"
    graph = q(str(graph_path))
    lines: list[str] = [f"# lane {nid}: {action}. Run the command below as one command; it stops at the first failure."]
    if action == "open":
        if n.get("status") != "planned":
            raise SystemExit(f"refused: {nid} is {n.get('status')}, not planned")
        return "\n".join(_chain(lines, [
            f"git -C {q(str(root))} worktree add {q(str(wt))} -b {q(branch)} {q(main)}",
            f"mkdir -p {q(str(scratch))}",
            f"{me} set {graph} {q(nid)} status=running lane={q(str(wt))} branch={q(branch)}",
        ]))
    if action == "integrate":
        landed = landed_commit(root, nid, branch, main, policy)
        if landed:
            lines += [f"# {branch} already landed on {main} at {landed}: an earlier integration stopped after the merge."]
            return "\n".join(_chain(lines, [f"{me} set {graph} {q(nid)} status=done commit={landed}"]))
        check_integrable(root, wt, branch, main)
        changed = (_git("-C", str(root), "diff", "--name-only", f"{main}...{branch}") or "").splitlines()
        unlisted = sorted(set(changed) - set(n.get("files") or []))
        if unlisted:
            lines += [f"# note: the lane changed files that `files` does not list: {', '.join(unlisted)}",
                      "# add them to the task's `files` so the exclusion rule holds for the tasks still to run"]
        steps = [f"git -C {q(str(wt))} rebase {q(main)}"]
        steps += [f"(cd {q(str(wt))} && {gate})" for gate in plan.get("gates") or []]
        if policy == "squash":
            steps += [
                f"git -C {q(str(root))} merge --squash {q(branch)}",
                f"git -C {q(str(root))} commit -m {q(f'{nid}: {n.get('title', '')}')} -m {q(f'Plan-Task: {nid}')}",
            ]
        else:
            steps += [f"git -C {q(str(root))} merge --ff-only {q(branch)}"]
        steps += [f"{me} set {graph} {q(nid)} status=done commit=$(git -C {q(str(root))} rev-parse --short HEAD)"]
        lines = _chain(lines, steps)
        lines += ["# then: close the lane, apply the as-landed text, and commit the plan document and graph.yaml"]
        return "\n".join(lines)
    if action == "close":
        if n.get("status") not in FINISHED_STATUSES:
            raise SystemExit(f"refused: {nid} is {n.get('status')}, not done; use `abandon` to give up on a lane")
        steps = []
        if wt.is_dir():
            # `integrate` refused untracked files before the merge, so anything
            # untracked now is output of the gates run at integration (a cache,
            # a build directory the repository doesn't ignore). Tracked changes
            # are not, and stop the close.
            tracked = _git("-C", str(wt), "status", "--porcelain", "--untracked-files=no")
            if tracked:
                raise SystemExit(f"refused: tracked files changed in {wt} after integration:\n{tracked}")
            force = "--force " if _git("-C", str(wt), "status", "--porcelain") else ""
            steps.append(f"git -C {q(str(root))} worktree remove {force}{q(str(wt))}")
        if _git("-C", str(root), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"):
            # A squash merge does not mark the branch merged, so -d would refuse it.
            steps.append(f"git -C {q(str(root))} branch {'-D' if policy == 'squash' else '-d'} {q(branch)}")
        steps.append(f"{me} set {graph} {q(nid)} lane= branch=")
        lines = _chain(lines, steps)
        lines += ["# then clean the lane's build directory if it lives outside the worktree (project-specific)"]
        return "\n".join(lines)
    if action == "abandon":
        if not wt.is_dir():
            raise SystemExit(f"refused: the lane worktree {wt} does not exist")
        patch = scratch / f"{nid}.abandoned.patch"
        keep = f"abandoned/{nid}"
        lines += ["# saves the lane's work as a patch, removes the worktree, and keeps every commit on the branch "
                  f"{keep}"]
        steps = [f"mkdir -p {q(str(scratch))}"]
        if rebase_in_progress(wt):
            steps.append(f"git -C {q(str(wt))} rebase --abort")
        steps += [
            f"git -C {q(str(wt))} add -N .",
            f"git -C {q(str(wt))} diff $(git -C {q(str(wt))} merge-base HEAD {q(main)}) > {q(str(patch))}",
            f"git -C {q(str(root))} worktree remove --force {q(str(wt))}",
            f"git -C {q(str(root))} branch -m {q(branch)} {q(keep)}",
            f"{me} set {graph} {q(nid)} status=blocked lane= branch={q(keep)} log=abandoned:{q(str(patch))}",
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
    raise SystemExit("action must be open, integrate, close, abandon, or discard")


# ── stage prompts ──────────────────────────────────────────────────────────────

TEMPLATE_RE = re.compile(r"^```template:([\w-]+)\n(.*?)^```", re.M | re.S)


def templates() -> dict[str, str]:
    found = dict(TEMPLATE_RE.findall(CHAIN_DOC.read_text(encoding="utf-8")))
    missing = {"header", "implement", "implement-measurement", "review", "fix", "final-review",
               "final-review-light"} - set(found)
    if missing:
        raise SystemExit(f"{CHAIN_DOC} lacks the templates: {', '.join(sorted(missing))}")
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


def render_prompt(data: dict, graph_path: Path, nid: str, stage: str, decisions: Path | None) -> tuple[Path, str]:
    """Fill the stage's template; return (prompt file, launcher line)."""
    plan = data["plan"]
    n = by_id(data).get(nid)
    if n is None:
        raise SystemExit(f"unknown node id: {nid}")
    chain = chain_of(n)
    if stage == "fix" and decisions is None:
        raise SystemExit("refused: the fix stage needs --decisions FILE (one decision per finding, or the gate failure)")
    # A reopened lane runs the fix stage whatever its chain.
    if stage not in CHAIN_STAGES.get(chain, ()) and stage != "fix":
        raise SystemExit(f"refused: {nid} runs the `{chain}` chain, which has no {stage} stage")
    name = {
        "implement": "implement-measurement" if chain == "measurement" else "implement",
        "review": "review",
        "fix": "fix",
        "final-review": "final-review" if chain == "default" else "final-review-light",
    }[stage]
    doc, anchor = spec_target(n, data, graph_path)
    try:
        spec = section(doc, anchor)
    except AnchorError as exc:
        raise SystemExit(f"{nid}: {exc} in {doc}")
    scratch = root_dir(plan, "scratch_root", graph_path) / nid
    commands = plan.get("commands") or {}
    values = {
        "task_id": nid,
        "task_title": str(n.get("title", "")),
        "lane_worktree": str(n.get("lane") or root_dir(plan, "worktree_root", graph_path) / nid),
        "lane_branch": str(n.get("branch") or f"{plan['branch_prefix']}{nid}"),
        "integration_branch": str(plan["integration_branch"]),
        "scratch": str(scratch),
        "stage": str(STAGE_NUMBER[stage]),
        "guidelines": ", ".join(str(resolve_doc(str(g), graph_path)) for g in plan.get("guidelines") or []) or "none",
        "prior_plans": ", ".join(str(resolve_doc(str(g), graph_path)) for g in plan.get("prior_plans") or []) or "none",
        "commands": "; ".join(f"{k}: `{v}`" for k, v in commands.items()) or "see the gates",
        "gates": ", then ".join(f"`{g}`" for g in plan.get("gates") or []),
        "files": ", ".join(str(f) for f in n.get("files") or []) or "none listed",
        "owner_decisions": _owner_decisions(n, int(plan.get("autonomy", 2))),
        "spec": spec,
        "decisions": decisions.read_text(encoding="utf-8").strip() if decisions else "",
    }
    tpl = templates()
    text = tpl[name].replace("{{common header}}", tpl["header"].rstrip("\n"))
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    left = sorted(set(re.findall(r"\{\{[\w ]+\}\}", text)))
    if left:
        raise SystemExit(f"template {name} has unknown placeholders: {', '.join(left)}")
    scratch.mkdir(parents=True, exist_ok=True)
    out = scratch / f"{nid}_prompt_{STAGE_NUMBER[stage]}.md"
    out.write_text(text, encoding="utf-8")
    launcher = (f"You are stage {STAGE_NUMBER[stage]} ({stage}) of task {nid}. Your complete instructions are "
                f"in {out}. Read that file first and follow it exactly; it is your whole task.")
    return out, launcher


# ── as-landed text ─────────────────────────────────────────────────────────────

AS_LANDED_RE = re.compile(r"^\s*(?:(#{1,6})\s*|\*\*)?(?:\(?\d\)?\.?\s*)?As landed\b[.:*\s]*$", re.I)


def as_landed_text(report: Path) -> str:
    """The text under a report's "As landed" heading, up to the next heading of the same or a higher level."""
    lines = report.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = AS_LANDED_RE.match(line)
        if not m:
            continue
        level = len(m.group(1)) if m.group(1) else 7
        body = []
        for nxt in lines[i + 1:]:
            h = HEADING_RE.match(nxt)
            if h and len(h.group(1)) <= level:
                break
            body.append(nxt)
        text = "\n".join(body).strip()
        if text:
            return text
    raise SystemExit(f"no \"As landed\" heading with text in {report}")


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
    fd, tmp = tempfile.mkstemp(dir=doc.parent, prefix=f".{doc.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(result)
    os.replace(tmp, doc)


# ── main ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "waves", "next", "render"):
        p = sub.add_parser(name)
        p.add_argument("graph", type=Path)
    p = sub.add_parser("set")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("assignments", nargs="+")
    p = sub.add_parser("lane")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("action", choices=("open", "integrate", "close", "abandon", "discard"))
    p = sub.add_parser("excerpt")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p = sub.add_parser("prompt")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("stage", choices=tuple(STAGE_NUMBER))
    p.add_argument("--decisions", type=Path)
    p = sub.add_parser("landed")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    p.add_argument("report", type=Path)
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
        chains = Counter(chain_of(n) for n in todo)
        agents = sum(len(CHAIN_STAGES.get(c, ())) * k for c, k in chains.items())
        finals = sum(k for c, k in chains.items() if "final-review" in CHAIN_STAGES.get(c, ()))
        print(f"agent runs for the {len(todo)} unfinished tasks: {agents} "
              f"({finals} on the final-review model), before any reopened stage; chains: "
              + ", ".join(f"{c} {k}" for c, k in sorted(chains.items())))
        path, longest, total = critical_path(data)
        print(f"estimated time: {longest:.0f} min on the critical path ({' -> '.join(path) or '-'}); "
              f"{total:.0f} min if every task ran back to back")
        hubs = Counter(f for n in todo for f in set(n.get("files") or []))
        shared = {f: [n["id"] for n in todo if f in (n.get("files") or [])] for f, k in hubs.items() if k > 1}
        if shared:
            print("hub files (a seam task that lands their shared interface first lets these tasks run in parallel): "
                  + "; ".join(f"{f} ({', '.join(ids)})" for f, ids in sorted(shared.items())))
        todo_ids = {n["id"] for n in todo}
        layers = [[i for i in layer if i in todo_ids] for layer in waves(data)]
        layers = [layer for layer in layers if layer]
        if len(todo) >= 3 and all(len(layer) == 1 for layer in layers):
            print("warning: the plan is serial; every wave holds one task, so no lanes run in parallel. "
                  "Look for a seam task (SKILL.md, \"Seams\") before you execute.")
        return 0
    if args.cmd == "next":
        start, hold, slots = next_ready(data)
        open_lanes = [n["id"] for n in by_id(data).values() if n.get("status") in OPEN_STATUSES]
        print(f"free lane slots: {max(slots, 0)}; open lanes: {', '.join(open_lanes) or 'none'}")
        for n in start:
            print(f"START {n['id']}: {n.get('title', '')} [{n.get('kind')}, {n.get('size')}, chain {chain_of(n)}: "
                  f"{', '.join(CHAIN_STAGES.get(chain_of(n), ()))}]")
        for nid, why in hold:
            print(f"HOLD  {nid}: {why}")
        if not start and not open_lanes:
            blocked = [i for i, n in by_id(data).items() if n.get("status") == "blocked"]
            print("FINISHED: no lane is open and nothing can start"
                  + (f"; blocked, for the user: {', '.join(blocked)}" if blocked else "")
                  + ("; the HOLD lines above need the user" if hold else ""))
        return 0
    if args.cmd == "render":
        print(render(data))
        return 0
    if args.cmd == "lane":
        print(lane_commands(data, graph_path, args.id, args.action))
        return 0
    if args.cmd == "prompt":
        out, launcher = render_prompt(data, graph_path, args.id, args.stage, args.decisions)
        print(f"# prompt written to {out} ({len(out.read_text(encoding='utf-8'))} chars); give the agent this line:")
        print(launcher)
        return 0
    if args.cmd == "landed":
        n = by_id(data).get(args.id)
        if n is None:
            print(f"unknown node id: {args.id}", file=sys.stderr)
            return 2
        text = as_landed_text(args.report)
        doc, anchor = spec_target(n, data, graph_path)
        try:
            apply_landed(doc, anchor, text)
        except AnchorError as exc:
            print(f"{args.id}: {exc} in {doc}", file=sys.stderr)
            return 1
        print(f"{args.id}: applied {len(text.splitlines())} lines of As landed text to {doc.name}")
        return 0
    if args.cmd == "excerpt":
        n = by_id(data).get(args.id)
        if n is None:
            print(f"unknown node id: {args.id}", file=sys.stderr)
            return 2
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
