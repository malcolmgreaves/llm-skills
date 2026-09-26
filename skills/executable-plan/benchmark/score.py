#!/usr/bin/env python3
"""Scores a cells benchmark run and writes DIR/report.md and DIR/scores.json.

    python3 score.py DIR              # everything
    python3 score.py DIR --no-judge   # skip the model that checks the final reports
    python3 score.py DIR --mutants 0  # skip mutation testing

For every snapshot of every arm, runs each hidden test file in its own pytest
process (through uv), with CELLS_REPO pointing at the snapshot. For each arm's final
snapshot, it also runs the arm's own tests, mutation-tests them, and reads the
session's cost, agents, environment, and git history.
"""

import argparse
import ast
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ElementTree
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
HIDDEN = HERE / "cells" / "hidden"
REFERENCE = HERE / "cells" / "reference"
FIXTURE_DOCS = {"README.md", "BACKLOG.md", "CLAUDE.md"}
PYTEST = ["uv", "run", "--no-project", "--quiet", "--with", "pytest", "python", "-m", "pytest", "-q",
          "-p", "no:cacheprovider"]
OWN_TESTS = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
# Without bytecode files, a mutant whose source has the same size and mtime can't run stale code.
NO_BYTECODE = {"PYTHONDONTWRITEBYTECODE": "1"}
FILE_TIMEOUT = 600  # seconds for one hidden test file; each test also has its own limit in conftest.py
TASKS = ["existing", "ranges", "errors", "logic", "text", "csvio", "recalc", "aggregates", "lookup", "fill",
         "cli", "cross"]
# List prices in USD per million tokens (input, output, cache read), used only to estimate the cost of a
# session that the cap stopped before it reported its own. The first entry whose key is in the model ID
# applies. A cache write costs 1.25 times input for 5 minutes and 2 times for 1 hour. With these prices,
# the estimate for an earlier finished session matched the cost it reported to the cent.
PRICES = [("opus-5-5", (4.0, 20.0, 0.20)), ("opus", (5.0, 25.0, 0.50)), ("sonnet-5", (2.0, 10.0, 0.20)),
          ("sonnet", (3.0, 15.0, 0.30)), ("haiku", (1.0, 5.0, 0.10))]


# ── hidden tests ────────────────────────────────────────────────────────────────

def expected_tests() -> dict[str, list[str]]:
    """The test IDs per hidden test file, collected from the reference, which passes all of them."""
    out = subprocess.run([*PYTEST, "--collect-only", *[p.name for p in sorted(HIDDEN.glob("test_*.py"))]],
                         cwd=HIDDEN, env=_env(REFERENCE), capture_output=True, text=True, check=True)
    tests: dict[str, list[str]] = {}
    for line in out.stdout.splitlines():
        if "::" in line:
            tests.setdefault(line.split("::")[0], []).append(line.strip())
    return tests


def _env(repo: Path) -> dict:
    return {**os.environ, "CELLS_REPO": str(repo), "PYTHONDONTWRITEBYTECODE": "1"}


def run_hidden_file(snapshot: Path, file: str, expected: list[str]) -> tuple[dict[str, bool], bool]:
    """Runs one hidden test file against a snapshot. Returns each expected test's result, and whether
    the file ran out of time. A test that didn't report counts as failed."""
    results = {test: False for test in expected}
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "result.xml"
        try:
            subprocess.run([*PYTEST, file, f"--junitxml={xml}"], cwd=HIDDEN, env=_env(snapshot),
                           capture_output=True, text=True, timeout=FILE_TIMEOUT)
        except subprocess.TimeoutExpired:
            return results, True
        if xml.exists():
            for case in ElementTree.parse(xml).iter("testcase"):
                test = f"{file}::{case.get('name')}"
                if test in results:  # a collection error reports a case that isn't a test
                    results[test] = not any(child.tag in ("failure", "error", "skipped") for child in case)
        return results, False


# ── the arm's own tests and mutation testing ────────────────────────────────────

def own_tests(snapshot: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(snapshot, copy, symlinks=True)
        started = time.monotonic()
        try:
            out = subprocess.run(OWN_TESTS, cwd=copy, capture_output=True, text=True, timeout=900,
                                 env={**os.environ, **NO_BYTECODE})
        except subprocess.TimeoutExpired:
            return {"passed": False, "tests": None, "seconds": 900}
        ran = re.search(r"Ran (\d+) tests?", out.stderr)
        return {"passed": out.returncode == 0, "tests": int(ran.group(1)) if ran else None,
                "seconds": round(time.monotonic() - started, 1)}


SWAP_BINOP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult, ast.Pow: ast.Mult,
              ast.FloorDiv: ast.Div, ast.Mod: ast.FloorDiv}
SWAP_COMPARE = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq,
                ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}


class Mutator(ast.NodeTransformer):
    """Counts mutation points in a module, or applies the one at index `target`."""

    def __init__(self, target: int = -1):
        self.target = target
        self.count = 0
        self.applied = ""

    def _hit(self) -> bool:
        hit = self.count == self.target
        self.count += 1
        return hit

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if type(node.op) in SWAP_BINOP and self._hit():
            self.applied = f"line {node.lineno}: {type(node.op).__name__} -> {SWAP_BINOP[type(node.op)].__name__}"
            node.op = SWAP_BINOP[type(node.op)]()
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        for i, op in enumerate(node.ops):
            if type(op) in SWAP_COMPARE and self._hit():
                self.applied = f"line {node.lineno}: {type(op).__name__} -> {SWAP_COMPARE[type(op)].__name__}"
                node.ops[i] = SWAP_COMPARE[type(op)]()
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if self._hit():
            self.applied = f"line {node.lineno}: and/or swapped"
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Not) and self._hit():
            self.applied = f"line {node.lineno}: `not` removed"
            return ast.copy_location(ast.Call(ast.Name("bool", ast.Load()), [node.operand], []), node)
        return node

    def visit_ClassDef(self, node):
        # Skip class decorators: flipping `@dataclass(frozen=True)` rarely changes behavior.
        decorators, node.decorator_list = node.decorator_list, []
        self.generic_visit(node)
        node.decorator_list = decorators
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            if self._hit():
                self.applied = f"line {node.lineno}: {node.value} -> {not node.value}"
                node.value = not node.value
        elif isinstance(node.value, int) and self._hit():
            self.applied = f"line {node.lineno}: {node.value} -> {node.value + 1}"
            node.value = node.value + 1
        return node


def mutation_points(package: Path) -> list[tuple[str, int]]:
    points = []
    for path in sorted(package.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        counter = Mutator()
        counter.visit(tree)
        points += [(str(path.relative_to(package.parent)), i) for i in range(counter.count)]
    return points


def mutate(snapshot: Path, count: int, baseline: dict, workers: int = 3) -> dict:
    """Mutation-tests the arm's own tests against the arm's own `cells` package."""
    if not baseline["passed"]:
        return {"score": None, "why": "the arm's own tests fail without mutations", "mutants": 0}
    points = mutation_points(snapshot / "cells")
    chosen = random.Random(20260925).sample(points, min(count, len(points)))
    limit = max(60.0, 5 * baseline["seconds"])
    results = []

    def run(batch):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(snapshot, copy, symlinks=True)
            for relative, index in batch:
                # A test that starts Python with its own environment can still write bytecode.
                for cache in list(copy.rglob("__pycache__")):
                    shutil.rmtree(cache, ignore_errors=True)
                path = copy / relative
                original = path.read_text()
                mutator = Mutator(index)
                tree = mutator.visit(ast.parse(original))
                path.write_text(ast.unparse(ast.fix_missing_locations(tree)))
                try:
                    out = subprocess.run(OWN_TESTS, cwd=copy, capture_output=True, text=True, timeout=limit,
                                         env={**os.environ, **NO_BYTECODE})
                    killed = out.returncode != 0
                except subprocess.TimeoutExpired:
                    killed = True
                path.write_text(original)
                results.append({"file": relative, "mutation": mutator.applied, "killed": killed})

    batches = [chosen[i::workers] for i in range(workers)]
    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(run, batches))
    killed = sum(r["killed"] for r in results)
    return {"score": round(killed / len(results), 3) if results else None, "mutants": len(results),
            "killed": killed, "points": len(points), "survivors": [r for r in results if not r["killed"]]}


# ── the session and the repository ──────────────────────────────────────────────

def _tool_result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def stream_facts(root: Path) -> dict:
    tools: Counter = Counter()
    agents, texts, results, init = [], [], [], {}
    blocked = 0
    path = root / "stream.jsonl"
    for line in path.read_text(errors="replace").splitlines() if path.exists() else []:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init" and not init:
            init = event
        if kind == "result":
            results.append(event)
        if kind == "user":  # tool results, the arm's subagents included
            content = (event.get("message") or {}).get("content")
            for part in content if isinstance(content, list) else []:
                if (part.get("type") == "tool_result" and part.get("is_error")
                        and "hook error" in _tool_result_text(part.get("content"))):
                    blocked += 1
        if kind != "assistant" or event.get("parent_tool_use_id") is not None:
            continue
        for content in (event.get("message") or {}).get("content") or []:
            if content.get("type") == "tool_use":
                tools[content["name"]] += 1
                if content["name"] in ("Agent", "Task"):
                    agents.append(content.get("input", {}).get("description", ""))
            elif content.get("type") == "text" and content["text"].strip():
                texts.append(content["text"])
    last = results[-1] if results else {}
    denied = {d.get("tool_use_id") for r in results for d in r.get("permission_denials") or []}
    return {"session": init.get("session_id"), "claude_code_version": init.get("claude_code_version"),
            "model": init.get("model"), "skill_loaded": "executable-plan" in (init.get("skills") or []),
            "plugins": sorted(p.get("source", p.get("name", "")) for p in init.get("plugins") or []
                              if p.get("path") != "builtin"),
            "hook_blocks": blocked, "permission_denials": len(denied),
            "reported_cost_usd": last.get("total_cost_usd"), "result": last.get("subtype"),
            "agents": len(agents), "agent_descriptions": agents, "tools": dict(tools),
            "final_text": texts[-1] if texts else ""}


def estimated_cost(session: str) -> float | None:
    """Estimates a session's cost, subagents included, from its transcripts' token counts."""
    projects = Path.home() / ".claude" / "projects"
    main = next(projects.glob(f"*/{session}.jsonl"), None)
    if main is None:
        return None
    files = [main, *main.parent.glob(f"{session}/**/*.jsonl")]
    # A transcript records a message once per content block as it streams; the last record has the
    # message's final usage.
    usages: dict[str, tuple[str, dict]] = {}
    for file in files:
        for line in file.read_text(errors="replace").splitlines():
            try:
                message = json.loads(line).get("message") or {}
            except json.JSONDecodeError:
                continue
            if message.get("usage") and message.get("id"):
                usages[message["id"]] = (message.get("model") or "", message["usage"])
    total = 0.0
    for model, usage in usages.values():
        price_in, price_out, price_read = next((p for name, p in PRICES if name in model), dict(PRICES)["sonnet"])
        split = usage.get("cache_creation") or {}
        if split:
            written = (split.get("ephemeral_5m_input_tokens", 0) * 1.25
                       + split.get("ephemeral_1h_input_tokens", 0) * 2) * price_in
        else:
            written = usage.get("cache_creation_input_tokens", 0) * price_in * 1.25
        total += (usage.get("input_tokens", 0) * price_in + written
                  + usage.get("cache_read_input_tokens", 0) * price_read
                  + usage.get("output_tokens", 0) * price_out) / 1e6
    return round(total, 2)


def git_out(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return out.stdout.strip()


def repo_facts(root: Path) -> dict:
    repo = root / "cells"
    facts = {
        "commits": int(git_out(repo, "rev-list", "--count", "main") or 0) - 1,
        "merge_commits": int(git_out(repo, "rev-list", "--merges", "--count", "main") or 0),
        "worktrees_left": max(0, len(git_out(repo, "worktree", "list").splitlines()) - 1),
        "branches_left": max(0, len(git_out(repo, "branch", "--list").splitlines()) - 1),
        "uncommitted_files": len(git_out(repo, "status", "--porcelain").splitlines()),
    }
    graphs = [p for p in repo.rglob("graph.yaml") if ".claude" not in p.parts]
    if graphs:
        text = graphs[0].read_text()
        statuses = Counter(re.findall(r"^\s+status: (\w+)", text, re.M))
        facts["graph"] = str(graphs[0].relative_to(repo))
        facts["task_statuses"] = dict(statuses)
        facts["conflicted_landings"] = len(re.findall(r"status=conflicted", text))
        facts["settings"] = {key: (re.search(rf"^\s+{key}: (\S+)", text, re.M) or [None, None])[1]
                             for key in ("file_overlap", "dependency_overlap", "coordinator", "lane_cap", "autonomy")}
    lanes = root / "cells-lanes"
    facts["lane_dirs_left"] = sorted(p.name for p in lanes.iterdir()) if lanes.exists() else []
    return facts


# ── the report judge ────────────────────────────────────────────────────────────

JUDGE = """You check whether a coding agent's report to its user raised two specific \
open questions. Read the report, then answer with one JSON object and nothing else:
{{"fractional": {{"raised": true or false, "quote": "the sentence that raises it, or empty"}},
 "whitespace": {{"raised": true or false, "quote": "..."}}}}

"fractional": the backlog doesn't say what happens when a count or position argument \
(of LEFT, RIGHT, MID, INDEX, VLOOKUP's column, or ROUND's digits) isn't a whole number. \
Raised means the report names this gap, or states how the agent decided it.

"whitespace": the README doesn't say whether cell content with spaces around a number, \
such as " 12 ", is a number or text. Raised means the report names this gap, or states \
how the agent decided it.

<report>
{report}
</report>"""


def added_documents(repo: Path) -> list[Path]:
    """The Markdown and HTML files, committed or not, that the arm wrote for its user: a plan, a
    report, or notes. The fixture's own documents, which every arm edits, don't count."""
    listed = git_out(repo, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    found = [repo / name for name in listed
             if name.endswith((".md", ".html")) and name not in FIXTURE_DOCS and (repo / name).is_file()]
    # The skill's report first, then the plan: the judge's input is cut to fit after them.
    return sorted(found, key=lambda p: (p.name != "report.md", str(p)))


def judge(root: Path, final_text: str, claude: str) -> dict:
    parts = [final_text]
    repo = root / "cells"
    for document in added_documents(repo):
        parts.append(f"--- {document.relative_to(repo)} ---\n{document.read_text(errors='replace')}")
    text = "\n\n".join(parts)[:40000]
    try:
        out = subprocess.run([claude, "-p", JUDGE.format(report=text), "--model", "haiku", "--output-format", "json",
                              "--max-budget-usd", "1", "--disallowedTools", "Bash", "Edit", "Write", "Read"],
                             capture_output=True, text=True, timeout=300, cwd=root)
        answer = json.loads(out.stdout).get("result", "")
        return json.loads(re.search(r"\{.*\}", answer, re.S).group())
    except (subprocess.TimeoutExpired, json.JSONDecodeError, AttributeError) as error:
        return {"error": str(error)}


# ── the report ──────────────────────────────────────────────────────────────────

def fraction(passed: int, total: int) -> str:
    return f"{passed}/{total}" if total else "-"


def write_report(out: Path, data: dict) -> str:
    arms = list(data["arms"])
    lines = [f"# cells benchmark: {out.name}", "",
             f"Cap {data['cap_minutes']} min per arm. Hidden tests: {data['total_tests']}. "
             "Cost is the session's own report when it finished, and an estimate from token counts at "
             "assumed list prices when the cap stopped it.", ""]
    warnings = []
    for arm in arms:
        a = data["arms"][arm]
        should_load = arm.startswith("with-")
        if a["stream"]["session"] and a["stream"]["skill_loaded"] != should_load:
            warnings.append(f"{arm} {'did not load' if should_load else 'loaded'} the executable-plan skill.")
        for snap, timed_out in sorted(a.get("timeouts", {}).items()):
            warnings.append(f"{arm}, snapshot {snap}: {', '.join(timed_out)} ran out of time; "
                            "every test in it counts as failed.")
    started = [arm for arm in arms if data["arms"][arm]["stream"]["session"]]
    for arm in sorted(set(arms) - set(started)):
        warnings.append(f"{arm} has no session: it didn't start. Its stderr.txt says why.")
    if len({tuple(data["arms"][arm]["stream"]["plugins"]) for arm in started}) > 1:
        warnings.append("The arms loaded different plugins; see the Environment table.")
    if warnings:
        lines += ["## Warnings", ""] + [f"- {w}" for w in warnings] + [""]
    lines += ["## Summary", "",
              "| Arm | Hidden tests | Planted defects | Performance | Cross-task | Ended | Minutes | Cost (USD) "
              "| Agents | Own tests | Mutation score |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for arm in arms:
        a = data["arms"][arm]
        final = a["snapshots"].get("final", {})
        cost = a["stream"]["reported_cost_usd"]
        reason = a["meta"].get("reason", "-")
        ended = f"{reason} ({a['stream']['result']})" if reason == "finished" and a["stream"]["result"] else reason
        cost_text = f"{cost:.2f}" if cost is not None and reason == "finished" else (
            f"~{a['estimated_cost_usd']:.2f} (est.)" if a.get("estimated_cost_usd") is not None else "-")
        own = a.get("own_tests", {})
        mutation = a.get("mutation", {})
        lines.append(
            f"| {arm} | {fraction(final.get('passed', 0), data['total_tests'])} "
            f"| {fraction(*final.get('planted', (0, 0)))} | {fraction(*final.get('performance', (0, 0)))} "
            f"| {fraction(*final.get('tasks', {}).get('cross', (0, 0)))} | {ended} "
            f"| {a['meta'].get('minutes', '-')} | {cost_text} | {a['stream']['agents']} "
            f"| {'pass' if own.get('passed') else 'FAIL'} ({own.get('tests')}) "
            f"| {mutation.get('score') if mutation.get('score') is not None else '-'} "
            f"({mutation.get('killed', 0)}/{mutation.get('mutants', 0)}) |")
    lines += ["", "## Hidden tests by task (final snapshot)", "",
              "| Arm | " + " | ".join(TASKS) + " |", "| --- |" + " --- |" * len(TASKS)]
    for arm in arms:
        tasks = data["arms"][arm]["snapshots"].get("final", {}).get("tasks", {})
        lines.append(f"| {arm} | " + " | ".join(fraction(*tasks.get(t, (0, 0))) for t in TASKS) + " |")
    times = sorted({s for a in data["arms"].values() for s in a["snapshots"] if s != "final"})
    lines += ["", "## Progress: hidden tests passing over time", "",
              "An arm that ended before a column's time shows its final count there.", "",
              "| Arm | " + "".join(f"{t[1:]} min | " for t in times) + "final |",
              "| --- |" + " --- |" * (len(times) + 1)]
    for arm in arms:
        snaps = data["arms"][arm]["snapshots"]
        cells = [str(snaps[t]["passed"]) if t in snaps else str(snaps.get("final", {}).get("passed", "-"))
                 for t in times]
        lines.append(f"| {arm} | " + "".join(f"{c} | " for c in cells) + f"{snaps.get('final', {}).get('passed', '-')} |")
    lines += ["", "## Process", "",
              "| Arm | Commits | Merge commits | Uncommitted files | Worktrees left | Branches left | Lane dirs left "
              "| Task statuses | Conflicted landings |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for arm in arms:
        r = data["arms"][arm]["repo"]
        lines.append(f"| {arm} | {r['commits']} | {r['merge_commits']} | {r['uncommitted_files']} "
                     f"| {r['worktrees_left']} | {r['branches_left']} | {len(r['lane_dirs_left'])} "
                     f"| {r.get('task_statuses', '-')} | {r.get('conflicted_landings', '-')} |")
    lines += ["", "## Environment", "",
              "Hook blocks are tool calls that a plugin's hook refused, such as a safety hook refusing "
              "`git worktree remove --force`. Permission denials include them.", "",
              "| Arm | Claude Code | Skill loaded | Plugins | Hook blocks | Permission denials |",
              "| --- | --- | --- | --- | --- | --- |"]
    for arm in arms:
        s = data["arms"][arm]["stream"]
        lines.append(f"| {arm} | {s['claude_code_version'] or '-'} | {'yes' if s['skill_loaded'] else 'no'} "
                     f"| {', '.join(s['plugins']) or 'none'} | {s['hook_blocks']} | {s['permission_denials']} |")
    if any("judge" in a for a in data["arms"].values()):
        lines += ["", "## Ambiguities raised in the final report", "",
                  "| Arm | Fractional counts | Spaces around numbers |", "| --- | --- | --- |"]
        for arm in arms:
            j = data["arms"][arm].get("judge", {})
            cell = lambda key: ("yes" if j.get(key, {}).get("raised") else "no") if key in j else "-"  # noqa: E731
            lines.append(f"| {arm} | {cell('fractional')} | {cell('whitespace')} |")
    lines += ["", "## Failing hidden tests (final snapshot)", "",
              "Tasks with no passing tests are listed by name only.", ""]
    for arm in arms:
        final = data["arms"][arm]["snapshots"].get("final", {})
        failing, tasks = final.get("failing", []), final.get("tasks", {})
        none_pass = [t for t, (passed, total) in tasks.items() if passed == 0 and total]
        partial = [t for t in failing if t.split("::")[0].removeprefix("test_").removesuffix(".py") not in none_pass]
        parts = ([f"no tests pass in {', '.join(sorted(none_pass))}"] if none_pass else []) + [f"`{t}`" for t in partial]
        lines.append(f"- **{arm}** ({len(failing)} failing): " + ("; ".join(parts) or "none"))
    return "\n".join(lines) + "\n"


def summarize(results: dict[str, bool]) -> dict:
    tasks: dict[str, list[int]] = {}
    for test, passed in results.items():
        task = test.split("::")[0].removeprefix("test_").removesuffix(".py")
        counts = tasks.setdefault(task, [0, 0])
        counts[0] += passed
        counts[1] += 1
    planted = [p for t, p in results.items() if "::test_planted_" in t]
    performance = [p for t, p in results.items() if "::test_long_chain_" in t]
    return {"passed": sum(results.values()), "total": len(results),
            "tasks": {t: tuple(c) for t, c in tasks.items()},
            "planted": (sum(planted), len(planted)), "performance": (sum(performance), len(performance)),
            "failing": sorted(t for t, p in results.items() if not p)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    parser.add_argument("--mutants", type=int, default=40, help="mutants per arm; 0 skips mutation testing")
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--claude", default="claude")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    run = json.loads((out / "run.json").read_text())

    expected = expected_tests()
    total = sum(len(tests) for tests in expected.values())
    arms = [arm for arm in run["arms"] if (out / arm / "snapshots").is_dir()]
    for arm in sorted(set(run["arms"]) - set(arms)):
        print(f"warning: {arm} has no snapshots; it isn't scored", flush=True)
    jobs = []
    for arm in arms:
        for snap in sorted((out / arm / "snapshots").iterdir()):
            for file, tests in expected.items():
                jobs.append((arm, snap.name, snap, file, tests))
    print(f"running {len(jobs)} hidden test files", flush=True)
    with ThreadPoolExecutor(args.workers) as pool:
        outcomes = list(pool.map(lambda job: run_hidden_file(job[2], job[3], job[4]), jobs))
    merged: dict[tuple[str, str], dict[str, bool]] = {}
    timeouts: dict[str, dict[str, list[str]]] = {}
    for (arm, snap, _, file, _), (outcome, timed_out) in zip(jobs, outcomes):
        merged.setdefault((arm, snap), {}).update(outcome)
        if timed_out:
            timeouts.setdefault(arm, {}).setdefault(snap, []).append(file)

    data = {"cap_minutes": run["cap_minutes"], "total_tests": total, "arms": {}}
    for arm in arms:
        root = out / arm
        meta = json.loads((root / "meta.json").read_text()) if (root / "meta.json").exists() else {}
        stream = stream_facts(root)
        session = stream["session"] or meta.get("session")
        entry = {"meta": meta, "stream": stream, "repo": repo_facts(root), "timeouts": timeouts.get(arm, {}),
                 "snapshots": {snap: summarize(results) for (a, snap), results in merged.items() if a == arm}}
        entry["estimated_cost_usd"] = estimated_cost(session) if session else None
        data["arms"][arm] = entry

    finals = [(arm, out / arm / "snapshots" / "final") for arm in arms if (out / arm / "snapshots" / "final").is_dir()]
    print("running each arm's own tests" + (" and mutation tests" if args.mutants else ""), flush=True)
    with ThreadPoolExecutor(len(finals) or 1) as pool:
        owns = list(pool.map(lambda item: own_tests(item[1]), finals))
    for (arm, final), own in zip(finals, owns):
        data["arms"][arm]["own_tests"] = own
        # One arm at a time: the arms' own tests may time themselves (K5), and a crowded machine
        # would fail them for every mutant alike.
        if args.mutants:
            data["arms"][arm]["mutation"] = mutate(final, args.mutants, own)
    if not args.no_judge:
        print("judging the final reports", flush=True)
        with ThreadPoolExecutor(len(finals) or 1) as pool:
            verdicts = list(pool.map(lambda item: judge(out / item[0], data["arms"][item[0]]["stream"]["final_text"],
                                                        args.claude), finals))
        for (arm, _), verdict in zip(finals, verdicts):
            data["arms"][arm]["judge"] = verdict

    (out / "scores.json").write_text(json.dumps(data, indent=2, default=str) + "\n")
    report = write_report(out, data)
    (out / "report.md").write_text(report)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
