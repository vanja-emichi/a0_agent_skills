# Agent Skills — Agent Zero Plugin

[![CI](https://github.com/vanja-emichi/a0_agent_skills/actions/workflows/ci.yml/badge.svg)](https://github.com/vanja-emichi/a0_agent_skills/actions/workflows/ci.yml) ![v1.0.0](https://img.shields.io/badge/version-1.0.0-blue)

**Production-grade engineering skills for Agent Zero.** 21 skills covering the full development lifecycle, 3 specialist agent personas, 7 slash commands, and 4 reference checklists.

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## Installation

### Via Plugin Installer (recommended)

```
/plugin install vanja-emichi/a0_agent_skills
```

### Manual

```bash
git clone https://github.com/vanja-emichi/a0_agent_skills.git /path/to/agent-zero/usr/plugins/agent_skills
```

Then restart Agent Zero. The plugin auto-registers skills, agents, and commands.

---

## What's Included

### 21 Engineering Skills

Skills activate automatically based on context — no configuration needed.

**Define:**

| Skill | Purpose |
|-------|----------|
| `idea-refine` | Structured divergent/convergent thinking |
| `spec-driven-development` | Write PRD before any code |

**Plan:**

| Skill | Purpose |
|-------|----------|
| `planning-and-task-breakdown` | Decompose specs into verifiable tasks |

**Build:**

| Skill | Purpose |
|-------|----------|
| `incremental-implementation` | Thin vertical slices, feature flags |
| `test-driven-development` | Red-Green-Refactor, test pyramid |
| `context-engineering` | Feed agents the right context |
| `source-driven-development` | Ground decisions in official docs |
| `frontend-ui-engineering` | Component architecture, accessibility |
| `api-and-interface-design` | Contract-first API design |

**Verify:**

| Skill | Purpose |
|-------|----------|
| `browser-testing-with-devtools` | Live runtime browser data via playwright-cli |
| `debugging-and-error-recovery` | Systematic root-cause debugging |

**Review:**

| Skill | Purpose |
|-------|----------|
| `code-review-and-quality` | Five-axis review before merge |
| `code-simplification` | Reduce complexity, preserve behavior |
| `security-and-hardening` | OWASP Top 10 prevention |
| `performance-optimization` | Measure-first optimization |

**Ship:**

| Skill | Purpose |
|-------|----------|
| `git-workflow-and-versioning` | Trunk-based, atomic commits |
| `ci-cd-and-automation` | Quality gate pipelines |
| `deprecation-and-migration` | Safe migration patterns |
| `documentation-and-adrs` | Architecture Decision Records |
| `shipping-and-launch` | Pre-launch checklists, staged rollouts |

**Meta:**

| Skill | Purpose |
|-------|----------|
| `using-agent-skills` | Discover which skill applies to your task |

### 3 Agent Personas

Delegated to via `call_subordinate` with the profile name:

| Profile | Role |
|---------|-------|
| `code-reviewer` | Senior Staff Engineer — five-axis code review |
| `test-engineer` | QA Specialist — test strategy and coverage |
| `security-auditor` | Security Engineer — vulnerability detection and OWASP |

### 7 Slash Commands

| Command | Skill(s) Loaded |
|---------|-----------------|
| `/spec` | `spec-driven-development` |
| `/plan` | `planning-and-task-breakdown` |
| `/build` | `incremental-implementation`, `test-driven-development` |
| `/test` | `test-driven-development`, `browser-testing-with-devtools` |
| `/review` | `code-review-and-quality`, `security-and-hardening`, `performance-optimization` |
| `/code-simplify` | `code-simplification`, `code-review-and-quality` |
| `/ship` | `shipping-and-launch` |

### 4 Reference Checklists

Skills pull these in automatically when needed:

- **Security** — OWASP Top 10 and threat modeling
- **Performance** — Profiling targets and optimization patterns
- **Testing** — Test pyramid, coverage strategy
- **Accessibility** — WCAG compliance checklist

### 5 Extension Hooks

| Hook Point | Extension | Purpose |
|------------|-----------|---------|
| `agent_init` | `_10_register_commands.py` | Symlinks slash commands to global and project scopes |
| `message_loop_prompts_after` | `_20_inject_meta_skill.py` | Injects skill routing table into every turn |
| `tool_execute_before` | `_10_simplify_ignore_before.py` | Filters `simplify-ignore` blocks before agent reads |
| `tool_execute_after` | `_10_simplify_ignore_after.py` | Expands placeholders and re-filters after agent writes |
| `monologue_end` | `_10_simplify_ignore_restore.py` | Restores protected code after agent turn ends |

---

## Project Structure

```
agent_skills/
├── plugin.yaml           # Plugin manifest
├── README.md             # This file
├── CHANGELOG.md          # Version history
├── LICENSE               # MIT
├── skills/               # 21 SKILL.md files
├── agents/               # 3 agent profiles
├── commands/             # 7 slash command pairs (.yaml + .txt)
├── extensions/           # 5 extension hooks
│   └── python/
│       ├── agent_init/
│       ├── message_loop_prompts_after/
│       ├── tool_execute_before/
│       ├── tool_execute_after/
│       └── monologue_end/
├── lib/                  # Shared utilities
│   └── simplify_ignore_utils.py
├── references/           # 4 checklists
├── scripts/              # validate.py (44 checks)
├── tests/                # 174 pytest tests
└── docs/                 # Setup and anatomy guides
```

---

## Usage

Skills load automatically based on context. You can also load them explicitly:

```
skills_tool:load code-review-and-quality
```

Delegate to agent personas:

```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "code-reviewer",
    "message": "Review the changes in src/auth.py for security issues"
  }
}
```

Use slash commands to activate skill workflows:

```
/spec     → Start with a PRD
/plan     → Break it into tasks
/build    → Implement incrementally with TDD
/test     → Write and run tests
/review   → Full multi-axis review
/code-simplify → Reduce complexity
/ship     → Launch checklist
```

---

## Differences from Upstream

This is an Agent Zero plugin adaptation of [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills). Key changes:

- Added `plugin.yaml` for Agent Zero plugin discovery
- Converted 3 agent personas to Agent Zero profile format (`agent.yaml` + `prompts/`)
- 7 slash commands with automatic global/project scope registration
- 5 extension hooks: command registration, skill routing, simplify-ignore protection
- `lib/simplify_ignore_utils.py` shared utility for extension hooks
- All paths derived dynamically from `__file__` — no hardcoded install paths
- CI pipeline: `validate.py` (44 checks) + `pytest` (174 tests)

---

## Credits

- **Author:** Addy Osmani ([@addyosmani](https://github.com/addyosmani))
- **Agent Zero adaptation:** Vanja Emichi ([@vanja-emichi](https://github.com/vanja-emichi))
- **License:** MIT
