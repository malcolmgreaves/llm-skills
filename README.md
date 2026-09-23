# llm-skills

A collection of reusable [Agent Skills](https://agentskills.io/specification) —
self-contained folders of instructions, scripts, and reference material that an
LLM agent loads on demand to get better at a specific task.

Skills here follow the open Agent Skills standard, so they work in Claude Code,
claude.ai, the Claude API, and any other agent that implements the spec.

## Skills

| Skill | What it does |
| --- | --- |
| [google-developer-style](skills/google-developer-style/) | Rewrites all prose (replies, plans, commit messages, comments, docstrings, READMEs) to follow the Google developer documentation style guide: literal, second-person, active-voice, present-tense English with no figurative language or filler. |
| [executable-plan](skills/executable-plan/) | Drafts an executable plan (a plan document with one anchored section per task plus a `graph.yaml` of dependencies, touched files, and status) and executes it concurrently: one git worktree per ready task, an implement → adversarial-review → fix → final-review chain of agents per task, and a coordinator that decides findings and integrates each lane into `main`. |

## Layout

```
skills/<skill-name>/
├── SKILL.md       # required — frontmatter + instructions (what the agent reads)
├── README.md      # human docs: when it triggers, requirements, design notes
├── scripts/       # optional — executable code, run via bash
├── references/    # optional — docs the agent reads on demand
└── assets/        # optional — templates, fonts, images used in output
template/          # starter SKILL.md + README.md for a new skill
scripts/validate.py # spec linter: uv run scripts/validate.py
AGENTS.md          # authoring guide (CLAUDE.md symlinks here)
```

`SKILL.md` is the skill. `README.md` is documentation about the skill — an agent
never reads it, so `SKILL.md` always stands on its own.

## How skills work

Agents load skills in three stages, so an installed-but-unused skill costs almost
nothing:

1. **Metadata** — `name` and `description` only, always in context (~100 tokens
   per skill). The `description` is what the agent matches your request against.
2. **Instructions** — the `SKILL.md` body, loaded only once the skill triggers.
3. **Resources** — `scripts/`, `references/`, `assets/`, loaded only when read.
   Script code never enters context; only its output does.

## Installing

### Claude Code

Symlink individual skills, personal or per-project:

```bash
# personal — available in every project on this machine
ln -s "$PWD/skills/<skill-name>" ~/.claude/skills/<skill-name>

# project — commit it to share with your team
ln -s "$PWD/skills/<skill-name>" /path/to/project/.claude/skills/<skill-name>
```

Or copy the directory instead of symlinking if you'd rather pin a version.

Verify with `/skills` in a session; invoke by name with `/<skill-name>`, or just
describe the task and let the agent trigger it.

### claude.ai

Zip a single skill directory and upload it under **Settings → Capabilities →
Skills**. Requires a paid plan with code execution enabled.

```bash
cd skills && zip -r ../<skill-name>.zip <skill-name>
```

Uploads reject any frontmatter outside the open spec (`name`, `description`,
`license`, `compatibility`, `metadata`, `allowed-tools`), which is why skills
here avoid client-specific fields.

### Claude API

Upload through the `/v1/skills` endpoints and reference the returned `skill_id`
in the `container` parameter alongside the code execution tool. See the
[Skills API guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

Note that API containers have no network access and no runtime package
installation — skills that shell out to the internet won't work there.

## Contributing

Read [AGENTS.md](AGENTS.md) — it's the authoring guide for humans and agents
alike. The short version:

```bash
cp -r template skills/<skill-name>
```

Set `name:` to match the directory, write the `description` first (it's the
trigger, and the hardest part to get right), keep `SKILL.md` under 500 lines,
and add a row to the table above.

Then lint it — no venv setup required, [uv](https://docs.astral.sh/uv/) resolves
the script's inline dependencies on the fly:

```bash
uv run scripts/validate.py
```

This checks the spec rules (name/directory agreement, field lengths, reserved
words), rejects client-specific frontmatter that would break a claude.ai upload,
and verifies every relative path `SKILL.md` points at actually resolves.

## Prior art

- [Agent Skills specification](https://agentskills.io/specification) — the open standard
- [anthropics/skills](https://github.com/anthropics/skills) — reference skills and spec source
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Using skills in Claude Code](https://code.claude.com/docs/en/skills)

## License

[MPL-2.0](LICENSE).
