#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate skills in this repository against the Agent Skills specification.

Usage:
    uv run scripts/validate.py              # skills/, template/, marketplace.json, shared blocks
    uv run scripts/validate.py skills/foo   # validate specific directories
    uv run scripts/validate.py --strict     # treat warnings as failures

Spec: https://agentskills.io/specification
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Frontmatter fields defined by the open Agent Skills spec. Client-specific keys
# (Claude Code's `disable-model-invocation`, `context`, `model`, ...) are valid
# in Claude Code but cause claude.ai uploads to fail, so they are errors here.
SPEC_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
RESERVED_WORDS = ("anthropic", "claude")

XML_TAG = re.compile(r"<[a-zA-Z/][^>]*>")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# Soft limits from the progressive-disclosure guidance: SKILL.md is loaded whole
# the moment the skill triggers, so length there is a recurring context cost.
BODY_LINE_WARN = 500
REFERENCE_LINE_WARN = 300

# Skills are self-contained, so a family of related skills duplicates the text
# it shares. Each copy is wrapped in a marker pair with the same key, and every
# copy of a key must be identical, so the duplicates cannot drift apart.
SHARED_OPEN = re.compile(r"<!-- shared: ([a-z0-9][a-z0-9/_.-]*) -->")
SHARED_CLOSE = "<!-- /shared -->"
SHARED_DIFF_LINES = 20


@dataclass
class Report:
    """Findings for one skill directory."""

    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    label: str | None = None

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors and not self.warnings


def check_name(name: object, directory: Path, report: Report) -> None:
    if not isinstance(name, str):
        report.error(f"`name` must be a string, got {type(name).__name__}")
        return
    if not NAME_PATTERN.fullmatch(name):
        report.error(
            f"`name: {name}` must be lowercase a-z0-9 and hyphens, with no "
            "leading, trailing, or consecutive hyphens"
        )
    if len(name) > NAME_MAX:
        report.error(f"`name` is {len(name)} characters, max is {NAME_MAX}")
    if name != directory.name:
        report.error(f"`name: {name}` does not match directory name `{directory.name}`")
    if XML_TAG.search(name):
        report.error("`name` must not contain XML tags")
    for word in RESERVED_WORDS:
        if word in name.lower():
            report.error(f"`name` must not contain the reserved word `{word}`")


def check_description(description: object, report: Report) -> None:
    if not isinstance(description, str):
        report.error(f"`description` must be a string, got {type(description).__name__}")
        return
    text = description.strip()
    if not text:
        report.error("`description` must be non-empty")
        return
    if len(description) > DESCRIPTION_MAX:
        report.error(
            f"`description` is {len(description)} characters, max is {DESCRIPTION_MAX}"
        )
    if XML_TAG.search(description):
        report.error("`description` must not contain XML tags")
    # The description is the only text matched against a user's request, so it
    # has to carry the trigger conditions, not just the capability.
    if not re.search(r"\buse\b|\bwhen\b|\bwhenever\b", description, re.IGNORECASE):
        report.warn(
            "`description` says what the skill does but never says when to use "
            "it; agents under-trigger without explicit trigger conditions"
        )


def check_optional_fields(frontmatter: dict, report: Report) -> None:
    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            report.error("`compatibility` must be a string")
        elif len(compatibility) > COMPATIBILITY_MAX:
            report.error(
                f"`compatibility` is {len(compatibility)} characters, "
                f"max is {COMPATIBILITY_MAX}"
            )

    metadata = frontmatter.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            report.error("`metadata` must be a map of string keys to string values")
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    report.error(
                        f"`metadata.{key}` must be a string; quote it if it "
                        "looks like a number (e.g. version: \"1.0\")"
                    )

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        report.error("`allowed-tools` must be a space-separated string")

    license_field = frontmatter.get("license")
    if license_field is not None and not isinstance(license_field, str):
        report.error("`license` must be a string")


def check_links(body: str, directory: Path, report: Report) -> None:
    """Every relative path named in SKILL.md must resolve, since the agent
    follows exactly those paths and nothing else."""
    for target in MD_LINK.findall(body):
        target = target.strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        relative = target.split("#", 1)[0].split("?", 1)[0]
        if not relative:
            continue
        resolved = (directory / relative).resolve()
        if not resolved.exists():
            report.error(f"SKILL.md links to `{relative}`, which does not exist")
            continue
        if relative.count("/") > 1 and not relative.startswith("../"):
            report.warn(
                f"`{relative}` is more than one level deep; keep references flat "
                "so the agent does not have to follow a chain of files"
            )


def check_bundled_files(directory: Path, report: Report) -> None:
    for reference in sorted(directory.glob("references/*.md")):
        lines = reference.read_text(encoding="utf-8").count("\n") + 1
        if lines > REFERENCE_LINE_WARN:
            has_toc = re.search(
                r"^#+\s*(table of contents|contents)\b",
                reference.read_text(encoding="utf-8"),
                re.IGNORECASE | re.MULTILINE,
            )
            if not has_toc:
                report.warn(
                    f"references/{reference.name} is {lines} lines and has no "
                    "table of contents"
                )


def validate_skill(directory: Path) -> Report:
    report = Report(path=directory)

    skill_file = directory / "SKILL.md"
    if not skill_file.is_file():
        report.error("missing SKILL.md")
        return report

    raw = skill_file.read_text(encoding="utf-8")
    match = FRONTMATTER.match(raw)
    if match is None:
        report.error("SKILL.md must open with YAML frontmatter delimited by `---`")
        return report

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        report.error(f"frontmatter is not valid YAML: {exc}")
        return report

    if not isinstance(frontmatter, dict):
        report.error("frontmatter must be a YAML mapping")
        return report

    for required in ("name", "description"):
        if required not in frontmatter:
            report.error(f"missing required field `{required}`")

    unknown = sorted(set(frontmatter) - SPEC_FIELDS)
    if unknown:
        report.error(
            f"non-spec frontmatter {unknown}; claude.ai rejects uploads containing "
            f"any key outside {sorted(SPEC_FIELDS)}"
        )

    if "name" in frontmatter:
        check_name(frontmatter["name"], directory, report)
    if "description" in frontmatter:
        check_description(frontmatter["description"], report)
    check_optional_fields(frontmatter, report)

    body = match.group(2)
    body_lines = body.count("\n") + 1
    if body_lines > BODY_LINE_WARN:
        report.warn(
            f"SKILL.md body is {body_lines} lines (soft limit {BODY_LINE_WARN}); "
            "move detail into references/ and point at it conditionally"
        )

    check_links(body, directory, report)
    check_bundled_files(directory, report)

    # Repo convention, not spec: every skill ships human-facing docs alongside.
    if not (directory / "README.md").is_file():
        report.warn("missing README.md (see AGENTS.md)")

    return report


def validate_marketplace(skill_dirs: list[Path]) -> Report:
    """Every skill must be its own plugin in the Claude Code marketplace, and
    every plugin must be exactly one skill. Nothing else catches a skill that
    was added to skills/ but never listed, which leaves it uninstallable."""
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    report = Report(path=path)
    if not path.is_file():
        report.error("missing .claude-plugin/marketplace.json")
        return report

    try:
        marketplace = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(f"not valid JSON: {exc}")
        return report

    plugins = marketplace.get("plugins") if isinstance(marketplace, dict) else None
    if not isinstance(plugins, list):
        report.error("`plugins` must be a list")
        return report

    listed: set[str] = set()
    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict) or not isinstance(plugin.get("name"), str):
            report.error(f"plugins[{index}] must be an object with a string `name`")
            continue
        name = plugin["name"]
        if name in listed:
            report.error(f"plugin `{name}` is listed more than once")
        listed.add(name)
        if not (REPO_ROOT / "skills" / name / "SKILL.md").is_file():
            report.error(f"plugin `{name}` has no matching skills/{name}/SKILL.md")
        # Each entry installs the whole repo and relies on `skills` to pick one
        # skill out of it; without strict: false, Claude Code would look for a
        # plugin.json instead and load every skill under skills/.
        if plugin.get("source") != "./":
            report.error(f"plugin `{name}` must have `\"source\": \"./\"`")
        if plugin.get("strict") is not False:
            report.error(f"plugin `{name}` must have `\"strict\": false`")
        if plugin.get("skills") != [f"./skills/{name}"]:
            report.error(f"plugin `{name}` must have `\"skills\": [\"./skills/{name}\"]`")
        if not isinstance(plugin.get("description"), str) or not plugin["description"].strip():
            report.error(f"plugin `{name}` needs a non-empty `description`")

    for directory in skill_dirs:
        if directory.name not in listed:
            report.error(
                f"skills/{directory.name} is not listed in marketplace.json, so "
                "Claude Code users cannot install it"
            )

    return report


def validate_shared_blocks(skill_dirs: list[Path]) -> Report:
    """Every copy of a shared block must match the others byte for byte.

    A block is the lines between `<!-- shared: KEY -->` and `<!-- /shared -->`,
    each on a line of its own, in any Markdown file under a skill directory."""
    report = Report(path=REPO_ROOT / "skills", label="shared blocks")
    copies: dict[str, list[tuple[Path, str]]] = defaultdict(list)

    for directory in skill_dirs:
        for path in sorted(directory.rglob("*.md")):
            relative = path.relative_to(REPO_ROOT)
            if "results" in path.relative_to(directory).parts:
                continue  # eval output, not authored content
            key: str | None = None
            start = 0
            seen: set[str] = set()
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            for number, line in enumerate(lines, start=1):
                opened = SHARED_OPEN.fullmatch(line.strip())
                if opened:
                    if key is not None:
                        report.error(
                            f"{relative}:{number}: shared block `{opened.group(1)}` "
                            f"opens inside shared block `{key}`"
                        )
                        continue
                    key, start = opened.group(1), number
                    if key in seen:
                        report.error(f"{relative}:{number}: shared block `{key}` appears twice")
                    seen.add(key)
                elif line.strip() == SHARED_CLOSE:
                    if key is None:
                        report.error(f"{relative}:{number}: `{SHARED_CLOSE}` has no opening marker")
                        continue
                    copies[key].append((relative, "".join(lines[start : number - 1])))
                    key = None
            if key is not None:
                report.error(f"{relative}:{start}: shared block `{key}` is never closed")

    for key, found in sorted(copies.items()):
        if len(found) == 1:
            report.warn(f"shared block `{key}` has only one copy ({found[0][0]})")
            continue
        reference_path, reference_text = found[0]
        for path, text in found[1:]:
            if text == reference_text:
                continue
            diff = list(
                difflib.unified_diff(
                    reference_text.splitlines(),
                    text.splitlines(),
                    fromfile=str(reference_path),
                    tofile=str(path),
                    lineterm="",
                )
            )
            shown = "\n".join(f"        {line}" for line in diff[:SHARED_DIFF_LINES])
            hidden = len(diff) - SHARED_DIFF_LINES
            more = f"\n        ... {hidden} more diff lines" if hidden > 0 else ""
            report.error(
                f"shared block `{key}` differs between {reference_path} and {path}:\n{shown}{more}"
            )

    return report


def discover(targets: list[str]) -> list[Path]:
    if targets:
        return [Path(t).resolve() for t in targets]

    directories = []
    skills_dir = REPO_ROOT / "skills"
    if skills_dir.is_dir():
        directories.extend(sorted(p for p in skills_dir.iterdir() if p.is_dir()))
    template_dir = REPO_ROOT / "template"
    if template_dir.is_dir():
        directories.append(template_dir)
    return directories


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "targets",
        nargs="*",
        help="skill directories to validate (default: skills/* and template/)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero on warnings as well as errors",
    )
    args = parser.parse_args()

    directories = discover(args.targets)
    if not directories:
        print("no skills found under skills/ — nothing to validate")
        return 0

    reports = [validate_skill(d) for d in directories]
    if not args.targets:
        skills_dir = REPO_ROOT / "skills"
        skill_dirs = [d for d in directories if d.parent == skills_dir]
        reports.append(validate_marketplace(skill_dirs))
        reports.append(validate_shared_blocks(skill_dirs))
    error_count = sum(len(r.errors) for r in reports)
    warning_count = sum(len(r.warnings) for r in reports)

    for report in reports:
        label = report.label or (
            report.path.relative_to(REPO_ROOT)
            if report.path.is_relative_to(REPO_ROOT)
            else report.path
        )
        if report.ok:
            print(f"ok    {label}")
            continue
        print(f"FAIL  {label}" if report.errors else f"warn  {label}")
        for message in report.errors:
            print(f"      error: {message}")
        for message in report.warnings:
            print(f"      warn:  {message}")

    print(
        f"\n{len(directories)} skill(s) checked, "
        f"{error_count} error(s), {warning_count} warning(s)"
    )

    if error_count:
        return 1
    if warning_count and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
