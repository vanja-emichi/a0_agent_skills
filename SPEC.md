# Spec: a0_agent_skills — Agent Zero Plugin

## Objective

A production-grade engineering skills plugin for Agent Zero. It extends Agent Zero with a complete software development lifecycle toolkit: 20 skills covering spec → plan → build → verify → review → ship, 3 specialist subordinate agents, 7 slash commands, and a simplify-ignore code protection mechanism.

**Target user:** Agent Zero developers — anyone using Agent Zero to build or maintain software.

**Primary value:** Skills are the core. Every skill is an actionable, verified workflow — not advice. Agents and commands are delivery mechanisms that activate skills.

**Success criteria:**
- Any Agent Zero developer can install the plugin and immediately use structured engineering workflows
- The 3 specialist agents (code-reviewer, test-engineer, security-auditor) can be called by agent0 via `call_subordinate` and execute their respective skills correctly
- All 7 slash commands load and activate the right skill
- The simplify-ignore extension protects marked code blocks during `/code-simplify`
- Plugin installs and works correctly on first run in any Agent Zero Docker deployment

---

## Tech Stack

- **Runtime:** Python 3.11+ inside Agent Zero Docker container (Kali Linux)
- **Framework:** Agent Zero (latest; `/a0/` root)
- **Plugin system:** Agent Zero plugin format (plugin.yaml + skills/ + agents/ + extensions/ + commands/)
- **Extensions:** Python async extensions (helpers.extension.Extension subclasses)
- **Commands:** Agent Zero Commands plugin format (.command.yaml + .txt pairs)
- **Skills:** SKILL.md format with YAML frontmatter (name + description fields)
- **No external dependencies** beyond what Agent Zero provides

---

## Commands

```bash
# Install (via Plugin Hub)
/plugin install vanja-emichi/a0_agent_skills

# Install (manual)
git clone https://github.com/vanja-emichi/a0_agent_skills.git /path/to/a0/usr/plugins/agent-skills

# Development (this repo IS the plugin)
cd /a0/usr/projects/agent_skills
git status
git add . && git commit -m "..."
git push origin main

# Validate SKILL.md frontmatter
grep -l 'name:' skills/*/SKILL.md

# Check extensions load
python3 -c "from extensions.python.agent_init._10_register_commands import RegisterCommands; print('OK')"
```

---

## Project Structure

```
a0_agent_skills/                  → Plugin root (git repo)
├── plugin.yaml                   → Agent Zero plugin manifest
├── README.md                     → Plugin documentation
├── LICENSE                       → MIT
├── .gitignore                    → Excludes .a0proj/
│
├── skills/                       → 20 engineering skills
│   └── <skill-name>/
│       └── SKILL.md              → Skill definition (YAML frontmatter + body)
│
├── agents/                       → 3 specialist subordinate profiles
│   └── <agent-name>/
│       ├── agent.yaml            → title, description, context
│       └── prompts/
│           └── agent.system.main.specifics.md  → specialist identity + skill to load
│
├── commands/                     → 7 slash commands
│   ├── <name>.command.yaml       → Command metadata
│   └── <name>.txt                → Command body (loads skill + instructs agent)
│
├── extensions/python/            → Lifecycle extensions
│   ├── simplify_ignore_utils.py  → Shared logic for block protection
│   ├── agent_init/               → Runs on agent init
│   │   └── _10_register_commands.py   → Symlinks commands into Commands plugin scopes
│   ├── tool_execute_before/      → Runs before tool execution
│   │   └── _10_simplify_ignore_before.py → Filter blocks before text_editor:read
│   ├── tool_execute_after/       → Runs after tool execution
│   │   └── _10_simplify_ignore_after.py  → Expand blocks after text_editor:patch/write
│   └── monologue_end/            → Runs when agent monologue ends
│       └── _10_simplify_ignore_restore.py → Restore all files
│
├── references/                   → Supplementary checklists (referenced by skills)
│   ├── performance-checklist.md
│   ├── security-checklist.md
│   ├── testing-patterns.md
│   └── accessibility-checklist.md
│
├── docs/                         → Human setup guides per IDE/tool
│   ├── getting-started.md
│   ├── skill-anatomy.md
│   └── <tool>-setup.md           → cursor, gemini-cli, opencode, copilot, windsurf
│
└── .a0proj/                      → NOT git-tracked (gitignored)
    └── source/                   → Upstream addyosmani/agent-skills (reference only)
```

---

## Code Style

**Skills follow the skill-anatomy.md format:**

```markdown
---
name: skill-name
description: One sentence. Third person. Trigger conditions ("Use when...").
---

# Skill Title

## Overview
[What and why — 2-3 sentences]

## When to Use
[Bullets: when YES, when NOT]

## Process
[Numbered workflow steps]

## Common Rationalizations
[Table: rationalization → reality]

## Red Flags
[Bullets: danger signs]

## Verification
[Checklist before proceeding]
```

**Key conventions:**
- Skill directory names: `kebab-case`
- SKILL.md: always uppercase, always this exact filename
- Extensions: `_NN_` numeric prefix, 10-number increments
- Commands: `<name>.command.yaml` + `<name>.txt` pairs
- Agent prompts: `agent.system.main.specifics.md` only — no other fragment overrides
- No inline philosophy — every instruction must be actionable

---

## Testing Strategy

- **Skills:** Manual validation — load each skill with `skills_tool:load`, verify frontmatter has `name` and `description`, verify skill activates in agent context
- **Extensions:** Unit smoke tests in `simplify_ignore_utils.py`; test filter/expand/restore cycle on sample files with `simplify-ignore-start/end` markers
- **Commands:** Path validation test — verify both global and project-scoped symlinks resolve correctly and `is_in_dir` passes
- **Agents:** Load each agent profile via `call_subordinate profile=<name>`, verify `specifics.md` is loaded and skill name is correct
- **Integration:** End-to-end — trigger `/spec`, `/review`, `/code-simplify` commands in a live session; verify correct skill is loaded

**No test runner required** — this is a documentation/configuration plugin. Validation is behavioral.

---

## Boundaries

**Always:**
- Follow `skill-anatomy.md` format for every new or updated skill
- Every skill must have `name` and `description` in YAML frontmatter
- Agent profiles override only `agent.system.main.specifics.md` — no other prompt fragments
- Extensions must be silent on success (only log on register or error)
- Commands must load the corresponding skill as their first action
- Keep SKILL.md files under 500 lines — put reference material in `references/`

**Ask first:**
- Adding a new skill (verify it doesn't duplicate an existing one)
- Changing the upstream sync process or `.a0proj/source/`
- Modifying extension execution order (numeric prefix changes)
- Adding new agent profiles beyond the current 3

**Never:**
- Add skills that are vague advice instead of actionable processes
- Duplicate content between skills — reference other skills instead
- Override `role.md`, `environment.md`, `communication.md`, `solving.md`, or `tips.md` in agent profiles
- Modify files outside the plugin directory
- Hardcode paths in Python extensions (use `Path(__file__)` relative resolution)
- Commit `.a0proj/` directory contents

---

## Skills by Lifecycle Phase

| Phase | Skills |
|-------|--------|
| **Define** | `spec-driven-development` |
| **Plan** | `planning-and-task-breakdown` |
| **Build** | `incremental-implementation`, `test-driven-development`, `context-engineering`, `source-driven-development`, `frontend-ui-engineering`, `api-and-interface-design` |
| **Verify** | `browser-testing-with-devtools`, `debugging-and-error-recovery` |
| **Review** | `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization` |
| **Ship** | `git-workflow-and-versioning`, `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`, `shipping-and-launch` |
| **Meta** | `using-agent-skills`, `idea-refine` |

---

## Slash Commands

| Command | Skill Loaded | Phase |
|---------|-------------|-------|
| `/spec` | `spec-driven-development` | Define |
| `/plan` | `planning-and-task-breakdown` | Plan |
| `/build` | `incremental-implementation` + `test-driven-development` | Build |
| `/test` | `test-driven-development` | Build/Verify |
| `/review` | `code-review-and-quality` | Review |
| `/code-simplify` | `code-simplification` | Review |
| `/ship` | `shipping-and-launch` | Ship |

---

## Success Criteria

- [ ] `plugin.yaml` is valid and plugin is auto-discovered by Agent Zero
- [ ] All 20 skills appear in `skills_tool:list` output after install
- [ ] Each skill loads without error via `skills_tool:load <name>`
- [ ] `call_subordinate profile=code-reviewer` initializes correctly and loads `code-review-and-quality` skill
- [ ] `call_subordinate profile=test-engineer` initializes correctly and loads `test-driven-development` skill
- [ ] `call_subordinate profile=security-auditor` initializes correctly and loads `security-and-hardening` skill
- [ ] All 7 slash commands appear and execute without "outside scope" error
- [ ] `simplify-ignore-start/end` blocks are preserved after `/code-simplify` run
- [ ] Plugin installs cleanly via `git clone` into `/a0/usr/plugins/` with no manual steps

## Open Questions

- Upstream sync strategy: how often to pull from `addyosmani/agent-skills` and what's the merge process?
- GitHub Actions CI: add workflow to validate SKILL.md frontmatter and plugin structure on every push?
- Plugin Hub submission: ready now or wait for CI and more testing?
