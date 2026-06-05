# Agent Skills Plugin

Production-grade engineering skills, specialist agent profiles, lifecycle slash commands, and reference checklists for Agent Zero.

## What It Provides

### 23 Development-Phase Skills

Workflow-driven skills with steps, quality gates, verification criteria, and anti-rationalization tables:

- **Planning & Discovery**: `interview-me`, `idea-refine`, `planning-and-task-breakdown`, `spec-driven-development`, `source-driven-development`, `context-engineering`
- **Implementation**: `incremental-implementation`, `test-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`
- **Quality & Review**: `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization`, `browser-testing-with-devtools`
- **Operations**: `debugging-and-error-recovery`, `git-workflow-and-versioning`, `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`, `shipping-and-launch`
- **Meta**: `using-agent-skills`, `doubt-driven-development`

### 3 Specialist Agent Profiles

Subordinate agent profiles callable via `call_subordinate`:

- **code-reviewer** — Senior Staff Engineer conducting five-axis code reviews
- **security-auditor** — Security specialist for vulnerability analysis and hardening
- **test-engineer** — Test architect for comprehensive test strategy

### 7 Slash Commands

Lifecycle commands mapping to skills and agent orchestration:

| Command | Invokes |
|---------|--------|
| `/spec` | `spec-driven-development` skill |
| `/plan` | `planning-and-task-breakdown` skill |
| `/build` | `incremental-implementation` + `test-driven-development` skills |
| `/test` | `test-driven-development` skill |
| `/review` | `code-review-and-quality` skill |
| `/code-simplify` | `code-simplification` skill |
| `/ship` | Parallel fan-out to `code-reviewer`, `security-auditor`, `test-engineer` |

### 5 Reference Checklists

Bundled inside the skills that use them (self-contained via `skills_tool action=read_file`):

- `performance-checklist.md` — in `shipping-and-launch`, `code-review-and-quality`, `performance-optimization`
- `security-checklist.md` — in `shipping-and-launch`, `code-review-and-quality`, `security-and-hardening`
- `testing-patterns.md` — in `test-driven-development`
- `accessibility-checklist.md` — in `shipping-and-launch`, `frontend-ui-engineering`
- `orchestration-patterns.md` — in `doubt-driven-development`, `using-agent-skills`

### Validation

- `scripts/validate-skills.js` — Validates frontmatter and structure for all bundled skills

## Installation

This plugin is auto-discovered when placed in `/a0/usr/plugins/a0_agent_skills/`. Enable it from the Agent Zero Plugins UI.

## Plugin Structure

```
a0_agent_skills/
├── plugin.yaml                          # Plugin manifest
├── hooks.py                              # Install/uninstall lifecycle hooks
├── README.md                             # This file
├── LICENSE                               # MIT license
├── skills/                               # 23 skills (SKILL.md + supporting files per directory)
├── agents/                               # 3 agent profiles (agent.yaml + prompts/)
├── commands/                             # 7 slash commands (.command.yaml + templates)
├── extensions/python/agent_init/         # Session auto-injection
├── tests/                                # 51 pytest tests (extension, structure, ship command)
└── scripts/                              # Validation utilities
```

### Tests

The `tests/` directory contains 51 automated tests validating the plugin's runtime components:

- `test_extension_inject.py` — Session injection, path resolution, boundary validation, loop_data initialization, symlink protection
- `test_structure.py` — Plugin manifest, command/agent/skill structure, dynamic counting, frontmatter validation
- `test_ship_command.py` — Ship command phases, sanitization, synthesis output

Run with: `cd /a0/usr/plugins/a0_agent_skills && python3 -m pytest tests/ -v`

## Source

Converted from [agent-skills](https://github.com/addyosmani/agent-skills) by Addy Osmani.
