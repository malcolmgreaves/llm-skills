#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Operate on an executable plan's graph.yaml.

Usage:
    uv run plan.py validate GRAPH              # schema, cycles, anchors, files
    uv run plan.py waves GRAPH                 # the concurrent layers, exclusions, and agent count
    uv run plan.py next GRAPH                  # what can start now, and why the rest waits
    uv run plan.py set GRAPH ID key=value ...  # status=, lane=, branch=, commit=, log=, answer=N:text
    uv run plan.py render GRAPH                # a status table (Markdown)
    uv run plan.py lane GRAPH ID open|integrate|close|abandon   # print the shell commands for the lane
    uv run plan.py excerpt GRAPH ID            # the task's section from the plan document

The script runs only read-only git commands. It prints every command that
changes a repository for the coordinator to run, so each destructive step
stays visible.
"""

from __future__ import annotations

import argparse
import html as html_lib
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

STATUSES = ("planned", "running", "review", "integrating", "done", "blocked", "skipped")
OPEN_STATUSES = ("running", "review", "integrating")
FINISHED_STATUSES = ("done", "skipped")
KINDS = ("code", "docs", "plan", "measurement")
CHAINS = ("default", "docs-only", "none")
SIZES = ("S", "M", "L")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PLAN_REQUIRED = (
    "title", "spec", "integration_branch", "worktree_root", "scratch_root",
    "branch_prefix", "lane_cap", "autonomy", "commit_policy", "models", "gates",
)
MODEL_STAGES = ("implement", "review", "fix", "final_review")
# Agents per chain; `measurement` is the implied chain of a measurement task.
CHAIN_AGENTS = {"default": 4, "docs-only": 2, "measurement": 1, "none": 0}
SELF = Path(__file__).resolve()


# ── loading ────────────────────────────────────────────────────────────────────

def load(graph_path: Path) -> dict:
    with graph_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    data.setdefault("plan", {})
    data.setdefault("nodes", [])
    return data


def save(graph_path: Path, data: dict) -> None:
    with graph_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=100)


def by_id(data: dict) -> dict[str, dict]:
    return {n.get("id"): n for n in data["nodes"] if isinstance(n, dict)}


def chain_of(node: dict) -> str:
    if node.get("chain"):
        return str(node["chain"])
    return {"docs": "docs-only", "plan": "docs-only", "measurement": "measurement"}.get(node.get("kind"), "default")


def spec_target(node: dict, data: dict, graph_path: Path) -> tuple[Path, str]:
    """Resolve a node's `spec` to (document path, anchor)."""
    spec = str(node.get("spec", ""))
    doc, _, anchor = spec.partition("#")
    base = graph_path.parent
    path = base / (doc or str(data["plan"].get("spec", "")))
    return path, anchor


# ── anchors and excerpts ───────────────────────────────────────────────────────

HEADING_RE = re.compile(r"^(#{1,6})(?:[ \t]|$)")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _slug(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[\s_]+", "-", text)


def _md_headings(lines: list[str]) -> list[tuple[int, int]]:
    """(line index, level) of each ATX heading outside a fenced code block.

    A `#` line inside a fence (a shell comment, a Rust `#[attribute]`) is not
    a heading, so it must never end a task's section.
    """
    out: list[tuple[int, int]] = []
    fence: str | None = None
    for i, line in enumerate(lines):
        if m := FENCE_RE.match(line):
            marker = m.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is None and (h := HEADING_RE.match(line)):
            out.append((i, len(h.group(1))))
    return out


def _md_section(text: str, anchor: str) -> tuple[int, int, list[str]] | None:
    """The line range [start, end) of the Markdown section that `anchor` names."""
    lines = text.splitlines()
    headings = _md_headings(lines)
    heading_at = dict(headings)
    link = re.compile(rf"""<a\s+(?:name|id)\s*=\s*["']{re.escape(anchor)}["']""")
    mark = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == f"<!-- task: {anchor} -->" or link.search(line):
            mark = i
            break
        if i in heading_at and (f"{{#{anchor}}}" in line or _slug(line.lstrip("#")) == anchor):
            mark = i
            break
    if mark is None:
        return None
    before = [(i, lvl) for i, lvl in headings if i <= mark]
    if not before:
        return None
    start, level = before[-1]
    end = next((i for i, lvl in headings if i > start and lvl <= level), len(lines))
    return start, end, lines


def _html_section(text: str, anchor: str) -> tuple[int, int] | None:
    """The character range of the HTML section whose heading carries id=anchor."""
    m = re.search(rf"""<h([1-6])\b[^>]*?\sid\s*=\s*["']{re.escape(anchor)}["'][^>]*>""", text, re.I)
    if not m:
        return None
    level = int(m.group(1))
    end = re.compile(rf"<h[1-{level}]\b", re.I).search(text, m.end())
    return m.start(), end.start() if end else len(text)


def _is_html(doc: Path) -> bool:
    return doc.suffix.lower() in (".html", ".htm")


def anchor_exists(doc: Path, anchor: str) -> bool:
    if not doc.is_file() or not anchor:
        return False
    text = doc.read_text(encoding="utf-8")
    return (_html_section(text, anchor) if _is_html(doc) else _md_section(text, anchor)) is not None


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


def excerpt(doc: Path, anchor: str) -> str:
    text = doc.read_text(encoding="utf-8")
    if _is_html(doc):
        span = _html_section(text, anchor)
        if span is None:
            raise SystemExit(f"no heading with id=\"{anchor}\" in {doc}")
        return _strip_html(text[span[0]:span[1]])
    section = _md_section(text, anchor)
    if section is None:
        raise SystemExit(f"no section for task {anchor!r} in {doc}")
    start, end, lines = section
    return "\n".join(lines[start:end]).strip()


# ── validation ─────────────────────────────────────────────────────────────────

def validate(data: dict, graph_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    plan = data["plan"]
    for key in PLAN_REQUIRED:
        if key not in plan:
            errors.append(f"plan.{key} is missing")
    lane_cap = plan.get("lane_cap", 1)
    if isinstance(lane_cap, bool) or not isinstance(lane_cap, int) or lane_cap < 1:
        errors.append("plan.lane_cap must be an integer >= 1")
    if plan.get("autonomy") not in (0, 1, 2, 3, 4):
        errors.append("plan.autonomy must be an integer from 0 to 4")
    if plan.get("commit_policy") not in ("keep", "squash"):
        errors.append("plan.commit_policy must be 'keep' or 'squash'")
    models = plan.get("models") or {}
    for stage in MODEL_STAGES:
        if not models.get(stage):
            errors.append(f"plan.models.{stage} is missing")
    if not isinstance(plan.get("gates"), list) or not plan.get("gates"):
        errors.append("plan.gates must be a non-empty list of commands")
    spec_doc = graph_path.parent / str(plan.get("spec", ""))
    if not spec_doc.is_file():
        errors.append(f"plan.spec does not exist: {spec_doc}")
    for rel in plan.get("guidelines") or []:
        if not (graph_path.parent / rel).exists() and not Path(rel).expanduser().exists():
            warnings.append(f"guideline file not found: {rel}")

    nodes = data["nodes"]
    ids = [n.get("id") for n in nodes]
    dupes = {i for i in ids if ids.count(i) > 1}
    for d in dupes:
        errors.append(f"duplicate node id: {d}")
    known = set(ids)
    for n in nodes:
        nid = str(n.get("id", "?"))
        if not ID_RE.match(nid):
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
        for key in ("deps", "soft_deps", "files"):
            if n.get(key) is not None and not isinstance(n.get(key), list):
                errors.append(f"{nid}: {key} must be a list")
                lists_ok = False
        if lists_ok:
            for dep in (n.get("deps") or []) + (n.get("soft_deps") or []):
                if dep not in known:
                    errors.append(f"{nid}: unknown dependency {dep}")
                if dep == nid:
                    errors.append(f"{nid}: depends on itself")
        if n.get("kind") == "code" and not n.get("files"):
            warnings.append(f"{nid}: a code task with no `files` cannot be excluded from a conflicting lane")
        for od in n.get("owner_decisions") or []:
            if not isinstance(od, dict) or "question" not in od or "default" not in od:
                errors.append(f"{nid}: each owner_decisions item needs `question` and `default`")
        if "spec" in n:
            doc, anchor = spec_target(n, data, graph_path)
            if not doc.is_file():
                errors.append(f"{nid}: spec document not found: {doc}")
            elif not anchor_exists(doc, anchor):
                errors.append(f"{nid}: anchor #{anchor} not found in {doc.name}")
    if not errors and (cycle := find_cycle(data)):
        errors.append("dependency cycle: " + " -> ".join(cycle))
    return errors, warnings


def find_cycle(data: dict) -> list[str] | None:
    graph = {n["id"]: list(n.get("deps") or []) for n in data["nodes"] if "id" in n}
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


def next_ready(data: dict) -> tuple[list[dict], list[tuple[str, str]], int]:
    plan = data["plan"]
    nodes = by_id(data)
    done = {i for i, n in nodes.items() if n.get("status") in FINISHED_STATUSES}
    blocked = {i for i, n in nodes.items() if n.get("status") == "blocked"}
    running = [n for n in nodes.values() if n.get("status") in OPEN_STATUSES]
    running_files = {f for n in running for f in (n.get("files") or [])}
    slots = int(plan.get("lane_cap", 1)) - len(running)
    start: list[dict] = []
    hold: list[tuple[str, str]] = []
    candidates = [n for n in nodes.values() if n.get("status") == "planned"]
    if any(n.get("alone") for n in running):
        return [], [(n["id"], "an `alone` lane is running") for n in candidates], slots
    # Prefer tasks whose soft deps are done, then larger tasks (they gate more), then id order.
    def rank(n: dict) -> tuple:
        soft_open = sum(1 for d in n.get("soft_deps") or [] if d not in done)
        return (soft_open, -{"L": 3, "M": 2, "S": 1}.get(n.get("size"), 1), n["id"])
    for n in sorted(candidates, key=rank):
        nid = n["id"]
        missing = [d for d in n.get("deps") or [] if d not in done]
        if missing:
            labels = [f"{d} (blocked)" if d in blocked else d for d in missing]
            hold.append((nid, "waits for " + ", ".join(labels)))
            continue
        if n.get("alone") and (running or start):
            hold.append((nid, "runs alone; lanes are open"))
            continue
        shared = sorted(set(n.get("files") or []) & (running_files | {f for s in start for f in (s.get("files") or [])}))
        if shared:
            hold.append((nid, "shares files with an open lane: " + ", ".join(shared[:3]) + (" ..." if len(shared) > 3 else "")))
            continue
        unanswered = [od for od in n.get("owner_decisions") or [] if not str(od.get("answer") or "").strip()]
        if unanswered and int(plan.get("autonomy", 2)) < 4:
            hold.append((nid, f"needs the owner's answer: {unanswered[0]['question']}"))
            continue
        if len(start) >= max(slots, 0):
            hold.append((nid, "no free lane slot"))
            continue
        start.append(n)
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
            try:
                decisions[int(idx)]["answer"] = text
            except (ValueError, IndexError):
                raise SystemExit(f"no owner decision at index {idx!r}")
        elif key == "log":
            pass  # the text lands in the log line below
        else:
            raise SystemExit(f"unknown key {key!r}; use status, lane, branch, commit, answer, log")
        changed.append(a)
    n.setdefault("log", []).append(f"{datetime.now().isoformat(timespec='minutes')} {' '.join(changed)}")


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
    return Path(root) if root else graph_path.parent


def check_integrable(root: Path, wt: Path, branch: str, main: str) -> None:
    """Refuse to print integration steps for a lane that would land nothing."""
    if not wt.is_dir():
        raise SystemExit(f"refused: the lane worktree {wt} does not exist")
    dirty = _git("-C", str(wt), "status", "--porcelain")
    if dirty is None:
        raise SystemExit(f"refused: git status failed in {wt}")
    if dirty:
        raise SystemExit(
            f"refused: the lane has uncommitted changes. The chain's last stage commits its work "
            f"(see references/chain.md); commit or discard these first:\n{dirty}")
    ahead = _git("-C", str(root), "rev-list", "--count", f"{main}..{branch}")
    if ahead is None:
        raise SystemExit(f"refused: cannot compare {branch} with {main}")
    if ahead == "0":
        raise SystemExit(f"refused: {branch} has no commits beyond {main}; there is nothing to integrate")
    current = _git("-C", str(root), "symbolic-ref", "--short", "HEAD")
    if current != main:
        raise SystemExit(f"refused: the main worktree {root} is on {current or 'a detached HEAD'}, not {main}")


def lane_commands(data: dict, graph_path: Path, nid: str, action: str) -> str:
    plan = data["plan"]
    n = by_id(data).get(nid)
    if n is None:
        raise SystemExit(f"unknown node id: {nid}")
    root = repo_root(graph_path)
    wt = Path(os.path.expanduser(str(plan["worktree_root"]))) / nid
    scratch = Path(os.path.expanduser(str(plan["scratch_root"]))) / nid
    branch = f"{plan['branch_prefix']}{nid}"
    main = str(plan["integration_branch"])
    q = shlex.quote
    me = f"uv run {q(str(SELF))}"
    graph = q(str(graph_path))
    lines: list[str] = [f"# lane {nid}: {action}"]
    if action == "open":
        lines += [
            f"git -C {q(str(root))} worktree add {q(str(wt))} -b {q(branch)} {q(main)}",
            f"mkdir -p {q(str(scratch))}",
            f"{me} set {graph} {q(nid)} status=running lane={q(str(wt))} branch={q(branch)}",
        ]
    elif action == "integrate":
        check_integrable(root, wt, branch, main)
        lines += [f"git -C {q(str(wt))} rebase {q(main)}"]
        lines += [f"(cd {q(str(wt))} && {gate})" for gate in plan.get("gates") or []]
        if plan.get("commit_policy") == "squash":
            lines += [
                f"git -C {q(str(root))} merge --squash {q(branch)}",
                f"git -C {q(str(root))} commit  # one message that names the task and what it changed",
            ]
        else:
            lines += [f"git -C {q(str(root))} merge --ff-only {q(branch)}"]
        lines += [
            "# then: apply the task's as-landed text to the plan document, and",
            f"{me} set {graph} {q(nid)} status=done commit=$(git -C {q(str(root))} rev-parse --short HEAD)",
            "# then commit the plan document and graph.yaml on the integration branch, and close the lane",
        ]
    elif action == "close":
        if n.get("status") not in FINISHED_STATUSES:
            raise SystemExit(f"refused: {nid} is {n.get('status')}, not done; use `abandon` to give up on a lane")
        # A squash merge does not mark the branch merged, so -d would refuse it.
        delete = "-D" if plan.get("commit_policy") == "squash" else "-d"
        lines += [
            f"git -C {q(str(root))} worktree remove {q(str(wt))}",
            f"git -C {q(str(root))} branch {delete} {q(branch)}",
            f"{me} set {graph} {q(nid)} lane= branch=",
            "# then clean the lane's build directory if the worktree removal did not (project-specific)",
        ]
    elif action == "abandon":
        patch = scratch / f"{nid}.abandoned.patch"
        lines += [
            "# saves the lane's work as a patch, then deletes the worktree and the branch",
            f"git -C {q(str(wt))} add -N .",
            f"git -C {q(str(wt))} diff $(git -C {q(str(wt))} merge-base HEAD {q(main)}) > {q(str(patch))}",
            f"git -C {q(str(root))} worktree remove --force {q(str(wt))}",
            f"git -C {q(str(root))} branch -D {q(branch)}",
            f"{me} set {graph} {q(nid)} status=blocked lane= branch= log=abandoned:{q(str(patch))}",
        ]
    else:
        raise SystemExit("action must be open, integrate, close, or abandon")
    return "\n".join(lines)


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
    p.add_argument("action", choices=("open", "integrate", "close", "abandon"))
    p = sub.add_parser("excerpt")
    p.add_argument("graph", type=Path)
    p.add_argument("id")
    args = parser.parse_args(argv)

    graph_path: Path = args.graph.resolve()
    if not graph_path.is_file():
        print(f"no such file: {graph_path}", file=sys.stderr)
        return 2
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
        nodes = by_id(data)
        pairs = []
        items = list(nodes.values())
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                shared = set(items[a].get("files") or []) & set(items[b].get("files") or [])
                if shared:
                    pairs.append(f"{items[a]['id']} x {items[b]['id']} ({len(shared)} shared)")
        if pairs:
            print("exclusions (never at the same time): " + "; ".join(pairs))
        todo = [n for n in items if n.get("status") not in FINISHED_STATUSES]
        agents = sum(CHAIN_AGENTS.get(chain_of(n), 0) for n in todo)
        finals = sum(1 for n in todo if chain_of(n) in ("default", "docs-only"))
        print(f"agent runs for the {len(todo)} unfinished tasks: {agents} "
              f"({finals} on the final-review model), before any reopened stage")
        return 0
    if args.cmd == "next":
        start, hold, slots = next_ready(data)
        print(f"free lane slots: {max(slots, 0)}")
        for n in start:
            print(f"START {n['id']}: {n.get('title', '')} [{n.get('kind')}, {n.get('size')}, chain {chain_of(n)}]")
        for nid, why in hold:
            print(f"HOLD  {nid}: {why}")
        if not start and not hold:
            print("nothing left to schedule")
        return 0
    if args.cmd == "set":
        set_fields(data, args.id, args.assignments)
        save(graph_path, data)
        print(f"{args.id}: {' '.join(args.assignments)}")
        return 0
    if args.cmd == "render":
        print(render(data))
        return 0
    if args.cmd == "lane":
        print(lane_commands(data, graph_path, args.id, args.action))
        return 0
    if args.cmd == "excerpt":
        n = by_id(data).get(args.id)
        if n is None:
            print(f"unknown node id: {args.id}", file=sys.stderr)
            return 2
        doc, anchor = spec_target(n, data, graph_path)
        print(excerpt(doc, anchor))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
