# Agent Skills — Agent Zero Plugin

![v0.3.1](https://img.shields.io/badge/version-0.3.1-blue)

**Production-grade engineering skills for Agent Zero.** 23 skills covering the full development lifecycle, 3 specialist agent personas, 10 slash commands, 4 reference checklists, and a **lifecycle runtime layer** that enforces structured task execution across context compaction and subordinate delegation.

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

### 23 Engineering Skills

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
| `lifecycle-runtime` | Planning discipline with Manus principles, 5-Question Reboot, 3-Strike protocol |


| `skill-creator` | Create, test, grade, benchmark, and optimize skills |

### 3 Agent Personas

Delegated to via `call_subordinate` with the profile name:

| Profile | Role |
|---------|-------|
| `code-reviewer` | Senior Staff Engineer — five-axis code review |
| `test-engineer` | QA Specialist — test strategy and coverage |
| `security-auditor` | Security Engineer — vulnerability detection and OWASP |

### 9 Slash Commands

| Command | Skill(s) Loaded |
|---------|-----------------|
| `/spec` | `spec-driven-development` |
| `/plan` | `planning-and-task-breakdown` |
| `/build` | `incremental-implementation`, `test-driven-development` |
| `/test` | `test-driven-development`, `browser-testing-with-devtools` |
| `/review` | `code-review-and-quality`, `security-and-hardening`, `performance-optimization` |
| `/code-simplify` | `code-simplification`, `code-review-and-quality` |
| `/ship` | `shipping-and-launch` |
| `/idea` | `idea-refine` |
| `/lifecycle-status` | Show current lifecycle state |
| `/security` | `security-and-hardening` |

### 4 Reference Checklists

Skills pull these in automatically when needed:

- **Security** — OWASP Top 10 and threat modeling
- **Performance** — Profiling targets and optimization patterns
- **Testing** — Test pyramid, coverage strategy
- **Accessibility** — WCAG compliance checklist

### 14 Extension Hooks

| Hook Point | Extension | Purpose |
|------------|-----------|---------|
| `message_loop_prompts_after` | `_10_lifecycle_inject.py` | Injects lifecycle state into EXTRAS block |
| `system_prompt` | `_20_agent_skills_prompt.py` | Injects skill routing rules into system prompt |
| `system_prompt` | `_22_lifecycle_rules.py` | Injects lifecycle-aware behavioral rules |
| `tool_execute_before` | `_10_simplify_ignore_before.py` | Filters `simplify-ignore` blocks before agent reads |
| `tool_execute_before` | `_30_no_lifecycle_gate.py` | Blocks tool calls outside current phase |
| `tool_execute_before` | `_31_lifecycle_gate.py` | Enforces 3-strike error protocol |
| `tool_execute_after` | `_10_simplify_ignore_after.py` | Expands placeholders and re-filters after agent writes |
| `tool_execute_after` | `_30_lifecycle_auto_progress.py` | Auto-progresses completed phases |
| `monologue_start` | `_30_lifecycle_resume.py` | Resumes active lifecycle on conversation restart |
| `monologue_end` | `_10_simplify_ignore_restore.py` | Restores protected code after agent turn ends |
| `monologue_end` | `_30_lifecycle_verifier.py` | Verifies phase completion at end of turn |
> **Architecture note:** The original `addyosmani/agent-skills` used a `SessionStart` hook that injected the full `using-agent-skills` SKILL.md (~195 lines) **once per session**. The A0 adaptation uses `_20_agent_skills_prompt.py` in `system_prompt/` to inject skill routing rules into the system prompt, and `_72_include_plan.py` in `message_loop_prompts_after/` to inject plan state into the EXTRAS block every turn. This is more token-efficient (~300 tokens/turn vs ~1,500 tokens one-time) and keeps the routing context fresh regardless of context window pressure. The plugin requires `always_enabled: true` in `plugin.yaml` so extensions run across all projects, not just the dogfooding project.

> **Commands plugin dependency:** As of Commands plugin V4, slash commands are discovered natively from all plugins' `commands/` directories via `_discover_plugin_commands()` (precedence: Project-level → Global Commands plugin → Plugin commands). The previous `_10_register_commands.py` extension that copied commands at startup has been removed — no registration step is needed. The Commands plugin is a fork at `https://github.com/3clyp50/commands` with the V4 discovery patch.


---

## Project Structure

```
agent_skills/
├── plugin.yaml           # Plugin manifest (v0.3.1)
├── SPEC.md               # Specification (3-Tier + Planning Runtime)
├── README.md             # This file
├── CHANGELOG.md          # Version history
├── LICENSE               # MIT
├── skills/               # 23 SKILL.md files
├── agents/               # 7 agent profiles
├── commands/             # 9 slash command pairs (.yaml + .txt)
├── tools/                # lifecycle tool (v0.3.1)
├── prompts/              # Tool prompt fragments
├── extensions/           # 13 extension hooks
│   └── python/
│       ├── agent_init/
│       ├── system_prompt/
│       ├── message_loop_prompts_after/
│       ├── monologue_start/
│       ├── tool_execute_before/
│       ├── tool_execute_after/
│       ├── monologue_end/
│       ├── process_chain_end/
│       └── startup_migration/
├── lib/                  # Shared utilities (lifecycle_state, strike_tracker, simplify_ignore)
├── references/           # 4 checklists
├── scripts/              # validate.py (88 checks)
└── tests/                # 352 pytest tests
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


### Slash Commands - UI Picker vs Text/A2A

The slash commands are invoked through the **Web UI command picker**. They are NOT intercepted from raw chat text. To use skills via A2A or direct chat, load skills directly:

```
skills_tool:load idea-refine
```
## Differences from Upstream

This is an Agent Zero plugin adaptation of [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills). Key changes:

- Added `plugin.yaml` for Agent Zero plugin discovery
- 9 slash commands with native discovery via Commands plugin V4
- 14 extension hooks: skill routing, simplify-ignore protection, lifecycle state injection, enforcement gates, strike tracking
- `lib/` shared utilities: simplify_ignore, lifecycle_state, strike_tracker
- Lifecycle runtime layer: 3-method API (init/status/archive), 7-phase lifecycle, disk-persisted state, EXTRAS injection, 3-strike error protocol
- All paths derived dynamically from `__file__` — no hardcoded install paths
- CI pipeline: `validate.py` (18 checks) + `pytest` (352 tests)

---

## Credits

- **Author:** Addy Osmani ([@addyosmani](https://github.com/addyosmani))
- **Agent Zero adaptation:** Vanja Emichi ([@vanja-emichi](https://github.com/vanja-emichi))
- **License:** MIT
