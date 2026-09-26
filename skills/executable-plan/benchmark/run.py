#!/usr/bin/env python3
"""Runs the cells benchmark: every arm in parallel, each for at most --cap-minutes, then scores them.

    python3 run.py --out DIR                      # all five arms, 30 minutes, then score
    python3 run.py --out DIR --arms with-default  # a subset
    python3 run.py --out DIR --dry-run            # set up the arms and print their prompts

Each arm gets a fresh copy of cells/fixture as a git repository in DIR/<arm>/cells and
one headless `claude -p` session started there. The "with" arms also get this skill in
the repository's .claude/skills/. Every 5 minutes the runner copies each running arm's
checkout to DIR/<arm>/snapshots/tNN; when an arm ends, or the cap stops it, the runner
copies it to DIR/<arm>/snapshots/final. score.py then runs the hidden tests on every
snapshot. DIR must not exist, and must be outside this repository, so that the hidden
tests and the reference implementation aren't in any arm's directories.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "cells" / "fixture"
SKILL = HERE.parent  # skills/executable-plan
SNAPSHOT_EVERY = 5  # minutes
EARLY_EXIT = 120  # seconds: an arm that ends sooner probably failed to start
IGNORED = shutil.ignore_patterns(".git", ".claude", "__pycache__", "*.pyc")

BASE_PROMPT = """\
Implement every task in BACKLOG.md in this repository. README.md describes the \
existing behavior, which must keep working, and CLAUDE.md gives the project's rules.

Hidden acceptance tests score this checkout, the files in this directory on the \
`main` branch, at {deadline} UTC: {cap} minutes after you start. Work that isn't in \
this directory's files by then doesn't count. Run `date -u` to see the time.

I won't be available to answer questions. Make reasonable decisions and keep going. \
In your final message, list every decision you made where the backlog or the README \
was unclear, and every question you would have asked me."""

FREE_BLOCK = """\
You can use subagents. If you do, use Sonnet (`sonnet`) for implementation and Opus \
(`opus`) for reviews."""

WITH_BLOCK = """\
Use the executable-plan skill. Draft settings: implement with Sonnet (`sonnet`); \
review and second_review with Opus (`opus`); fix, resolve, resolution_review, and \
delegate with Sonnet (`sonnet`); effort `medium` for every stage; the default \
workflows by size; lane_cap 6; file_overlap {file_overlap}; dependency_overlap \
{dependency_overlap}; coordinator {coordinator}.

I approve the plan in advance: finish the draft, commit it, then start executing at \
autonomy level 4 without waiting for me."""

BASE_TOOLS = ["Bash", "Read", "Edit", "Write", "Glob", "Grep", "TodoWrite", "Skill"]
AGENT_TOOLS = ["Agent", "Task", "SendMessage"]
NEVER = ["Workflow", "Artifact", "WebFetch", "WebSearch"]


@dataclass(frozen=True)
class Arm:
    skill: bool  # the arm's repository carries this skill
    agents: bool  # the arm can start subagents
    block: str  # the arm's part of the prompt, after the shared part


ARMS = {
    "without-solo": Arm(False, False, ""),
    "without-free": Arm(False, True, FREE_BLOCK),
    "with-default": Arm(True, True, WITH_BLOCK.format(file_overlap=2, dependency_overlap="off", coordinator="full")),
    "with-overlap": Arm(True, True, WITH_BLOCK.format(file_overlap=4, dependency_overlap="interfaces",
                                                      coordinator="full")),
    "with-delegate": Arm(True, True, WITH_BLOCK.format(file_overlap=2, dependency_overlap="off",
                                                       coordinator="delegate")),
}


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def user_plugins() -> list[str]:
    """The plugins that the user's settings enable, as `name@marketplace`."""
    path = Path.home() / ".claude" / "settings.json"
    try:
        enabled = json.loads(path.read_text()).get("enabledPlugins") or {}
    except (OSError, json.JSONDecodeError):
        return []
    return sorted(name for name, on in enabled.items() if on)


def _skill_files(directory: str, names: list[str]) -> list[str]:
    # The skill's README.md is for people: it describes this benchmark, and agents never read it.
    ignored = {"benchmark", "evals", "__pycache__"} | ({"README.md"} if Path(directory) == SKILL else set())
    return [name for name in names if name in ignored or name.endswith(".pyc")]


def prepare(root: Path, arm: Arm, disable_plugins: list[str]) -> Path:
    """Creates DIR/<arm>/cells: the fixture as a fresh repository, with the skill for "with" arms."""
    repo = root / "cells"
    shutil.copytree(FIXTURE, repo, ignore=IGNORED)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "cells benchmark")
    git(repo, "config", "user.email", "cells-benchmark@example.invalid")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Initial commit")
    # Every arm ignores .claude/: the skill, the settings below, and the worktrees that subagents may make.
    with open(repo / ".git" / "info" / "exclude", "a") as exclude:
        exclude.write(".claude/\n")
    if arm.skill:
        shutil.copytree(SKILL, repo / ".claude" / "skills" / "executable-plan", ignore=_skill_files)
    if disable_plugins:
        settings = repo / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({"enabledPlugins": {name: False for name in disable_plugins}}, indent=2) + "\n")
    return repo


def prompt_for(arm: Arm, deadline: datetime, cap: int) -> str:
    text = BASE_PROMPT.format(deadline=deadline.strftime("%H:%M:%S"), cap=cap)
    return f"{text}\n\n{arm.block}" if arm.block else text


def command(claude: str, prompt: str, arm: Arm, root: Path, budget: float) -> list[str]:
    allowed = BASE_TOOLS + (AGENT_TOOLS if arm.agents else [])
    denied = NEVER + ([] if arm.agents else AGENT_TOOLS)
    return [claude, "-p", prompt, "--model", "sonnet", "--effort", "medium",
            "--output-format", "stream-json", "--verbose", "--max-budget-usd", str(budget),
            "--permission-mode", "acceptEdits",
            "--allowedTools", *allowed, "--disallowedTools", *denied, "--add-dir", str(root)]


def snapshot(repo: Path, target: Path) -> None:
    """Copies the checkout while the arm may still be writing to it. Never raises: a failed copy
    is retried, and after the last try the snapshot keeps every file that could be copied."""
    for attempt in range(3):
        shutil.rmtree(target, ignore_errors=True)
        try:
            shutil.copytree(repo, target, ignore=IGNORED, symlinks=True)
            return
        except (shutil.Error, OSError) as error:  # a file vanished or changed during the copy
            problem = error
            time.sleep(1)
    print(f"warning: {target} is missing files that changed during the copy: {str(problem)[:300]}", flush=True)


def session_id(stream: Path) -> str | None:
    """The session ID from the stream's `init` event."""
    try:
        with open(stream) as file:
            for line in file:
                event = json.loads(line)
                if event.get("type") == "system" and event.get("subtype") == "init":
                    return event.get("session_id")
    except (OSError, json.JSONDecodeError):
        pass
    return None


def stop(processes: list[subprocess.Popen]) -> None:
    """Stops every arm's whole process group at once: SIGTERM, then SIGKILL after 20 seconds."""
    for sig, wait in ((signal.SIGTERM, 20), (signal.SIGKILL, 10)):
        alive = [process for process in processes if process.poll() is None]
        for process in alive:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + wait
        for process in alive:
            try:
                process.wait(timeout=max(0.0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="a new directory outside this repository")
    parser.add_argument("--arms", default=",".join(ARMS), help="comma-separated arm names")
    parser.add_argument("--cap-minutes", type=int, default=30)
    parser.add_argument("--budget-usd", type=float, default=40.0, help="--max-budget-usd for each arm")
    parser.add_argument("--claude", default="claude", help="the claude executable")
    parser.add_argument("--disable-user-plugins", action="store_true",
                        help="turn off, in each arm's project settings, the plugins that ~/.claude/settings.json enables")
    parser.add_argument("--dry-run", action="store_true", help="set up the arms and print prompts only")
    parser.add_argument("--no-score", action="store_true", help="skip score.py after the run")
    args = parser.parse_args(argv)

    out = args.out.resolve()
    names = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in names if name not in ARMS]
    if unknown:
        parser.error(f"unknown arms: {', '.join(unknown)}; choose from {', '.join(ARMS)}")
    if out.exists():
        parser.error(f"{out} exists; choose a new --out")
    repo_root = HERE.parents[2]
    if out == repo_root or repo_root in out.parents:
        parser.error("--out must be outside this repository, so the arms can't read the hidden tests")

    plugins = user_plugins()
    if plugins and not args.disable_user_plugins:
        print(f"note: every arm loads the plugins your settings enable ({', '.join(plugins)}); their hooks "
              "and skills apply to every arm. --disable-user-plugins turns them off.", flush=True)
    out.mkdir(parents=True)
    runs = {}
    for name in names:
        root = out / name
        root.mkdir()
        runs[name] = {"root": root, "arm": ARMS[name],
                      "repo": prepare(root, ARMS[name], plugins if args.disable_user_plugins else [])}
    # The deadline in the prompt is the moment the runner stops the arms.
    start = datetime.now(timezone.utc)
    deadline = start + timedelta(minutes=args.cap_minutes)
    for name, run in runs.items():
        run["prompt"] = prompt_for(run["arm"], deadline, args.cap_minutes)
        (run["root"] / "prompt.txt").write_text(run["prompt"] + "\n")
        print(f"== {name}\n{run['prompt']}\n")
    (out / "run.json").write_text(json.dumps({
        "arms": names, "cap_minutes": args.cap_minutes, "budget_usd": args.budget_usd,
        "started": start.isoformat(), "snapshot_every": SNAPSHOT_EVERY,
        "disabled_plugins": plugins if args.disable_user_plugins else [],
    }, indent=2) + "\n")
    if args.dry_run:
        return 0

    def finish(name: str, reason: str) -> None:
        run = runs[name]
        run["ended"] = datetime.now(timezone.utc)
        run["stdout"].close()
        run["stderr"].close()
        snapshot(run["repo"], run["root"] / "snapshots" / "final")
        meta = {
            "arm": name, "session": session_id(run["root"] / "stream.jsonl"), "reason": reason,
            "exit_code": run["process"].returncode,
            "started": run["started"].isoformat(), "ended": run["ended"].isoformat(),
            "minutes": round((run["ended"] - run["started"]).total_seconds() / 60, 2),
            "cap_minutes": args.cap_minutes, "budget_usd": args.budget_usd,
            "disabled_plugins": plugins if args.disable_user_plugins else [],
        }
        (run["root"] / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(f"{name}: {reason} after {meta['minutes']} min", flush=True)
        if reason == "finished" and (run["ended"] - run["started"]).total_seconds() < EARLY_EXIT:
            tail = (run["root"] / "stderr.txt").read_text(errors="replace")[-1500:]
            print(f"warning: {name} ended in its first {EARLY_EXIT} s with exit code "
                  f"{run['process'].returncode}; the end of its stderr:\n{tail}", flush=True)

    began = time.monotonic()
    running: set[str] = set()
    try:
        for name, run in runs.items():
            root = run["root"]
            cmd = command(args.claude, run["prompt"], run["arm"], root, args.budget_usd)
            run["stdout"] = open(root / "stream.jsonl", "w")
            run["stderr"] = open(root / "stderr.txt", "w")
            run["started"] = datetime.now(timezone.utc)
            run["process"] = subprocess.Popen(cmd, cwd=run["repo"], stdout=run["stdout"], stderr=run["stderr"],
                                              stdin=subprocess.DEVNULL, start_new_session=True)
            running.add(name)
            print(f"started {name}", flush=True)

        next_snapshot = SNAPSHOT_EVERY
        while running:
            time.sleep(5)
            minutes = (time.monotonic() - began) / 60
            for name in sorted(running):
                if runs[name]["process"].poll() is not None:
                    running.discard(name)
                    finish(name, "finished")
            if minutes >= next_snapshot and next_snapshot < args.cap_minutes:
                for name in sorted(running):
                    snapshot(runs[name]["repo"], runs[name]["root"] / "snapshots" / f"t{next_snapshot:02d}")
                print(f"snapshots at {next_snapshot} min", flush=True)
                next_snapshot += SNAPSHOT_EVERY
            if minutes >= args.cap_minutes:
                stop([runs[name]["process"] for name in running])
                for name in sorted(running):
                    running.discard(name)
                    finish(name, "cap")
    finally:
        # If the runner itself fails or is interrupted, no arm keeps running unwatched.
        if running:
            stop([runs[name]["process"] for name in running])
            for name in sorted(running):
                running.discard(name)
                finish(name, "runner stopped")

    if args.no_score:
        return 0
    import score

    return score.main([str(out), "--claude", args.claude])


if __name__ == "__main__":
    sys.exit(main())
