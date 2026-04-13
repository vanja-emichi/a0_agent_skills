# Agent Skills — Agent Zero Plugin

[![CI](https://github.com/vanja-emichi/a0_agent_skills/actions/workflows/ci.yml/badge.svg)](https://github.com/vanja-emichi/a0_agent_skills/actions/workflows/ci.yml)


**Production-grade engineering skills for Agent Zero.** 20 skills covering the full development lifecycle, 3 specialist agent personas, and 4 reference checklists.

Originally by [Addy Osmani](https://github.com/addyosmani/agent-skills), adapted for Agent Zero plugin architecture.

---

## Installation

### Via Plugin Installer (recommended)

```
/plugin install vanja-emichi/a0_agent_skills
```

### Manual

```bash
git clone https://github.com/vanja-emichi/a0_agent_skills.git /path/to/agent-zero/usr/plugins/agent-skills
```

Then restart Agent Zero. The plugin auto-registers all skills and agent profiles.

---

## What's Included

### 20 Engineering Skills

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

### 3 Agent Personas

Delegated to via `call_subordinate` with the profile name:

| Profile | Role |
|---------|-------|
| `code-reviewer` | Senior Staff Engineer — five-axis code review |
| `test-engineer` | QA Specialist — test strategy and coverage |
| `security-auditor` | Security Engineer — vulnerability detection and OWASP |

### 4 Reference Checklists

Skills pull these in automatically when needed:

- Performance checklist
- Security checklist
- Testing patterns
- Accessibility checklist

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

---

## Differences from Upstream

This is an Agent Zero plugin adaptation of [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills). Changes:

- Added `plugin.yaml` for Agent Zero plugin discovery
- Converted 3 agent personas to Agent Zero profile format (`agent.yaml` + `prompts/`)
- Structure is compatible with both the original Claude Code format and Agent Zero

For the original project (Claude Code, Cursor, Gemini CLI, etc.), see the [upstream repo](https://github.com/addyosmani/agent-skills).

---

## Credits

- **Author:** Addy Osmani ([@addyosmani](https://github.com/addyosmani))
- **Agent Zero adaptation:** Vanja Emichi ([@vanja-emichi](https://github.com/vanja-emichi))
- **License:** MIT
