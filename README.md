# a0_agent_skills

A plugin for [Agent Zero](https://github.com/frdel/agent-zero) that ports the [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) development workflow toolkit — **23 curated skills**, 3 specialist agent profiles, 7 slash commands, and **workflow governance** (enforcement gate, durable state, phase governance, skill contracts) — into the Agent Zero plugin system. It gives any Agent Zero agent access to a production-grade software engineering lifecycle: spec → plan → build → test → review → ship, with telemetry enabled by default.

---

## Quick Start

Once the plugin is installed and enabled:

```
# 1. Discover the right skill for your task
skills_tool:search  query="write a spec for a login system"

# 2. Start the engineering lifecycle
/spec Build a user authentication system

# 3. Plan the work
/plan

# 4. Implement incrementally
/build Implement the login endpoint

# 5. Test with TDD
/test Add edge case tests for login failure

# 6. Review before merging
/review

# 7. Ship with a GO/NO-GO decision
/ship v1.0 authentication system
```

Or ask naturally — the agent will detect the right skill:
- *"Let's write a spec before we start coding"* → `spec-driven-development`
- *"Break this feature into tasks"* → `planning-and-task-breakdown`
- *"Something is broken, help me debug it"* → `debugging-and-error-recovery`

---

## Prerequisites

The **`commands` plugin** must be installed and active. The 7 slash commands provided by this plugin (`/spec`, `/plan`, `/build`, `/review`, `/test`, `/code-simplify`, `/ship`) rely on the commands plugin's dispatch infrastructure.

Verify it is installed:
```
/a0/usr/plugins/commands/
```

If it is not present, install it via the Plugin Hub before enabling this plugin.

---

## Architecture Overview

The plugin is organized as **four governance slices**, each built on Agent Zero extension points:

| Slice | Purpose | Extension Point | Helper Module |
|-------|---------|----------------|---------------|
| **Enforcement Gate** | Detect when agent skips skills; observe or correct | `tool_execute_before` | `skill_match` |
| **Durable State** | Persist plans, goals, phase across compaction/restart | `tool_execute_after` + `message_loop_prompts_after` | `workflow_state` |
| **Phase Governance** | 6-phase advisory model with deduplication | `tool_execute_before` | `phase_governance` |
| **Skill Contracts** | Structured metadata + runtime DAG validation | `tool_execute_after` | `skill_contracts` |

### Extension Points Used

| Extension Point | File | Role |
|----------------|------|------|
| `system_prompt` | `_15_agent_skills_routing.py` | Injects mandatory routing rules into every session |
| `tool_execute_before` | `_10_skill_enforcer.py` | Intercepts tool calls before execution for enforcement gating |
| `tool_execute_after` | `_05_skill_telemetry.py` | Logs skill activations to JSONL telemetry |
| `tool_execute_after` | `_10_persist_workflow_state.py` | Persists workflow state after skill loads and phase transitions |
| `message_loop_prompts_after` | `_67_reattach_workflow_state.py` | Rehydrates state after compaction/session resume |

### Helper Modules

| Module | Path | Purpose |
|--------|------|----------|
| `skill_match` | `helpers/skill_match.py` | Skill search, candidate matching, loaded-skill tracking |
| `workflow_state` | `helpers/workflow_state.py` | Atomic file I/O for `.a0proj/state/` artifacts |
| `phase_governance` | `helpers/phase_governance.py` | Phase transitions, deduplication, advisory enforcement |
| `skill_contracts` | `helpers/skill_contracts.py` | YAML frontmatter parsing, DAG construction, cycle detection |

### Module Loading

Each extension bootstraps its helper imports via `_plugin_loader` (using `importlib.util`), because plugin extensions are not on `sys.path` by default. This approach requires no framework changes — each extension resolves the plugin root independently.

---

## Routing System

The plugin uses a **`system_prompt` extension** to inject mandatory routing rules into every Agent Zero session. This extension lives at:

```
/a0/usr/plugins/a0_agent_skills/extensions/python/system_prompt/_15_agent_skills_routing.py
```

It reads routing rules from:
```
/a0/usr/plugins/a0_agent_skills/prompts/agent.skills.routing.md
```

**Key advantage:** This approach works **regardless of project context**. Whether a project is active or not, the routing rules are always injected into the agent's system prompt during prompt assembly.

---

## The 6-Phase Lifecycle

Every feature or change passes through six phases in order. Each phase has a required skill:

| Phase | Required Skill(s) | Purpose |
|-------|-------------------|--------|
| **DEFINE** | `spec-driven-development` | Define what to build before building it |
| **PLAN** | `planning-and-task-breakdown` | Break work into ordered, testable increments |
| **BUILD** | `incremental-implementation` + `test-driven-development` | Implement in slices with tests first |
| **VERIFY** | `debugging-and-error-recovery` | Prove it works — fix issues before review |
| **REVIEW** | `code-review-and-quality` | Structured quality gate before shipping |
| **SHIP** | `shipping-and-launch` | Deploy with confidence and rollback plan |

### Phase-to-Skill Mapping

| Phase | Skills |
|-------|--------|
| **DEFINE** | `spec-driven-development`, `interview-me` |
| **PLAN** | `planning-and-task-breakdown`, `context-engineering` |
| **BUILD** | `incremental-implementation`, `test-driven-development`, `source-driven-development`, `frontend-ui-engineering`, `api-and-interface-design` |
| **VERIFY** | `browser-testing-with-devtools`, `debugging-and-error-recovery` |
| **REVIEW** | `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization` |
| **SHIP** | `shipping-and-launch`, `ci-cd-and-automation`, `git-workflow-and-versioning`, `documentation-and-adrs`, `deprecation-and-migration` |

---

## The 3 Agent Profiles

Specialist subordinate agents activated via `call_subordinate`. These personas are invoked at the correct lifecycle phase:

### `code-reviewer`
Senior staff engineer conducting five-axis code review: **correctness, readability, architecture, security, performance**. Produces structured `APPROVE / REQUEST CHANGES` reports with Critical / Important / Suggestion findings and `file:line` references.

**Invoked during:** REVIEW phase (via `/review`) and SHIP phase (via `/ship`).

```
call_subordinate(profile="code-reviewer")
```

### `security-auditor`
Security engineer focused on vulnerability detection and threat modeling. Covers OWASP Top 10, input handling, authentication/authorization, data protection, infrastructure, and third-party integrations. Produces severity-classified findings (Critical / High / Medium / Low / Info) with actionable mitigations.

**Invoked during:** SHIP phase (via `/ship`).

```
call_subordinate(profile="security-auditor")
```

### `test-engineer`
QA engineer for test strategy, test writing, and coverage analysis. Implements the **Prove-It Pattern** for bug reproduction. Produces Test Coverage Analysis reports with Recommended Tests and priority classification.

**Invoked during:** VERIFY phase and SHIP phase (via `/ship`).

```
call_subordinate(profile="test-engineer")
```

> **Orchestration rule:** The main agent (or a slash command) is the orchestrator. Personas do not invoke each other. The only multi-persona pattern is parallel fan-out with a merge step, used by `/ship`.

> **Per-persona model override:** Agent Zero does not support a `model` field directly in `agent.yaml`. To assign a specific LLM model to a profile (e.g. Haiku for `test-engineer`, Opus for `security-auditor`), create a `_model_config/config.json` alongside the profile:
> ```
> /a0/usr/plugins/a0_agent_skills/agents/security-auditor/plugins/_model_config/config.json
> ```
> This file must contain a complete effective configuration for `chat_model`, `utility_model`, and `embedding_model` (selected as a whole, not merged). See the `_model_config` plugin documentation for the schema.

---

## The 7 Slash Commands

| Command | When to use |
|---|---|
| `/spec` | Start a new feature or project — loads `spec-driven-development` and writes `SPEC.md`. Surfaces assumptions before writing any code. |
| `/plan` | Break confirmed spec into tasks — loads `planning-and-task-breakdown` and writes `tasks/plan.md` + `tasks/todo.md`. |
| `/build` | Implement the next task — loads `incremental-implementation` + `test-driven-development`. RED → GREEN → commit cycle. |
| `/test` | TDD workflow or bug reproduction — loads `test-driven-development`. Write failing test first; use the Prove-It Pattern for bugs. |
| `/review` | Single-perspective code review — delegates to the `code-reviewer` profile via `call_subordinate`. |
| `/code-simplify` | Reduce complexity without changing behavior — loads `code-simplification`. Applies guard clauses, splits functions, removes dead code. |
| `/ship` | Pre-launch **parallel** review — runs `code-reviewer`, `security-auditor`, and `test-engineer` concurrently via `call_subordinate_parallel`, then produces a **GO / NO-GO** decision with rollback plan. |

### Example usage

```
/spec Build a REST API for task management
/plan
/build Implement POST /tasks endpoint
/test Add tests for the task creation edge cases
/review
/ship v1.0 release — task API
```

---

## Skill Enforcement Gate

The enforcement gate detects when the agent is about to use `code_execution_tool` or `text_editor` without loading a clearly relevant skill first. It runs as a `tool_execute_before` extension, inspecting tool calls **before** they execute.

### Modes

| Mode | What it does |
|------|-------------|
| **`observe`** (default) | Logs would-fire decisions to telemetry. No behavior change, no classifier calls, no tool_args mutation. |
| **`enforce`** | Runs the utility-model classifier. When a skill should have been loaded, appends an in-band corrective warning to `tool_args.message`. |

### How it works

```
Agent calls code_execution_tool or text_editor
  → Prefilter: search_skills() finds candidate skills
  → Check: is any candidate already loaded?
  → Observe: log decision (would-fire / already_loaded / no_candidate)
  → Enforce: run classifier → append corrective warning if needed
```

### Gate decision states

| State | Meaning |
|-------|---------|
| `no_candidate` | No matching skills found — no action needed |
| `already_loaded` | A matching skill is already loaded — no action needed |
| `should_correct` | A skill should have been loaded (observe logs it, enforce acts on it) |
| `classifier_unavailable` | Utility model was unreachable — no correction attempted |
| `error` | Unexpected error during gate evaluation — logged, no correction |

### Configuration

Keys in `default_config.yaml`:

```yaml
enforcement_mode: observe           # observe | enforce
enforcement_classifier_model: null  # null = use utility model
enforcement_shadow_sample_rate: 0.0 # 0.0 = disabled
enforcement_correction_cooldown_seconds: 300  # Seconds between repeated corrections
```

To switch to enforce mode, override in your project's plugin config:
```json
// .a0proj/plugins/a0_agent_skills/config.json
{
  "enforcement_mode": "enforce"
}
```

---

## Durable Workflow State

The plugin persists active workflow context (plan, goal, phase, loaded skills, checkpoints, progress) to `.a0proj/state/` so that long-running engineering work survives **context compaction, session breaks, and agent restarts**.

### State files

| File | Format | Trigger |
|------|--------|----------|
| `.a0proj/state/active_plan.json` | JSON snapshot | Plan created or task status changes |
| `.a0proj/state/active_goal.json` | JSON snapshot | Goal set or updated |
| `.a0proj/state/current_phase.json` | JSON snapshot | Phase transition |
| `.a0proj/state/loaded_skills.json` | JSON snapshot | `skills_tool:load` call completes |
| `.a0proj/state/checkpoints.json` | JSON snapshot | Explicit checkpoint creation/update |
| `.a0proj/state/progress_log.jsonl` | JSONL append | Any tracked workflow event |
| `.a0proj/state/handoff.md` | Markdown overwrite | Any state change |

### How rehydration works

After compaction or session resume, the `_67_reattach_workflow_state` extension reads all state files and appends a consolidated context block to the agent's prompt. The agent sees its prior plan, goal, phase, loaded skills, and last checkpoint — all reconstructed from `.a0proj/state/` rather than from prompt-only context.

Rehydrated `loaded_skills` are also injected into `agent.data['loaded_skills']` for compatibility with the enforcement gate.

### Inspecting state files

```bash
# View all state files
cat .a0proj/state/*.json

# Read the progress log
cat .a0proj/state/progress_log.jsonl | python -m json.tool --no-ensure-ascii

# View the handoff summary
cat .a0proj/state/handoff.md

# Reset state (delete everything)
rm -rf .a0proj/state/
```

### Configuration

```yaml
workflow_state_enabled: true       # Set to false to disable all persistence and rehydration
workflow_state_path: .a0proj/state # Relative to project folder
```

---

## Phase-Aware Governance

Phase governance tracks the current lifecycle phase and uses it to make smarter enforcement decisions. When a skill is loaded, the governance module:

1. **Identifies the phase** from the loaded skill's phase mapping
2. **Detects phase transitions** and persists them to `.a0proj/state/current_phase.json`
3. **Deduplicates corrections** — if the agent already loaded a skill for the current phase, it won't be warned again
4. **Advisory only** — never blocks execution, only suggests via corrective warnings

### Configuration

```yaml
phase_governance_enabled: true  # Set to false to disable phase tracking
```

---

## Skill Contracts

Skills can declare structured metadata via optional YAML frontmatter in their `SKILL.md` files. The contracts system parses this frontmatter, builds a runtime DAG of skill dependencies, and validates it for cycles.

### YAML Frontmatter Format

A skill contract is declared at the top of `SKILL.md` between `---` delimiters:

```yaml
---
name: test-driven-development
version: 1.0.0
phase: BUILD
depends_on:
  - incremental-implementation
provides:
  - tdd-workflow
conflicts_with: []
optional: false
---

# Skill content continues here...
```

### Contract Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique skill identifier |
| `version` | string | No | Semantic version |
| `phase` | string | No | Lifecycle phase this skill belongs to |
| `depends_on` | list | No | Skills that should be loaded before this one |
| `provides` | list | No | Capabilities this skill contributes |
| `conflicts_with` | list | No | Skills that should not be loaded alongside this one |
| `optional` | boolean | No | Whether this skill is optional in its phase |

### Runtime DAG

When `skill_graph_validate_on_build` is enabled, the contracts module constructs a directed acyclic graph from all skill dependencies and checks for cycles on startup. If a cycle is detected, a warning is logged but the plugin continues to operate.

When `skill_next_skill_hints` is enabled, the system can suggest the next logical skill based on the current phase and loaded skills.

### Configuration

```yaml
skill_contracts_enabled: true          # Enable YAML frontmatter parsing
skill_graph_validate_on_build: true    # Validate DAG for cycles on startup
skill_next_skill_hints: true           # Suggest next skill based on phase
```

---

## Configuration Surface

All configuration lives in `default_config.yaml` and can be overridden per-project via `.a0proj/plugins/a0_agent_skills/config.json`.

### Full Config Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enforcement_mode` | string | `observe` | Enforcement gate mode: `observe` (log only) or `enforce` (corrective warnings) |
| `enforcement_classifier_model` | string\|null | `null` | Override model for skill classification. `null` = use Agent Zero utility model |
| `enforcement_shadow_sample_rate` | float | `0.0` | Fraction of observe-mode calls to also run classifier (for A/B testing). `0.0` = disabled |
| `workflow_state_enabled` | boolean | `true` | Enable durable workflow state persistence and rehydration |
| `workflow_state_path` | string | `.a0proj/state` | Directory for state files (relative to project root) |
| `phase_governance_enabled` | boolean | `true` | Enable phase tracking and deduplication |
| `enforcement_correction_cooldown_seconds` | int | `300` | Minimum seconds between repeated corrections for the same skill |
| `skill_contracts_enabled` | boolean | `true` | Enable YAML frontmatter parsing in SKILL.md files |
| `skill_graph_validate_on_build` | boolean | `true` | Validate skill dependency DAG for cycles on plugin load |
| `skill_next_skill_hints` | boolean | `true` | Provide next-skill suggestions based on current phase |
| `max_progress_entries` | int | `10000` | Maximum entries in `progress_log.jsonl` before rotation |

### Example Override

```json
// .a0proj/plugins/a0_agent_skills/config.json
{
  "enforcement_mode": "enforce",
  "workflow_state_path": ".a0proj/workflow-state",
  "skill_contracts_enabled": true,
  "max_progress_entries": 5000
}
```

---

## Telemetry

Telemetry is **enabled by default**. Every `skills_tool` activation and enforcement gate decision is logged to a JSONL file for workflow analysis.

**Log location:** `.a0proj/skill_activations.jsonl` (relative to project folder).

### Event Types

| Event Type | Trigger |
|-----------|---------|
| `skill_activated` | `skills_tool:load` completes successfully |
| `skill_deactivated` | Skill context is cleared (session end) |
| `gate_decision` | Enforcement gate evaluates a tool call |

### Telemetry Examples

**Skill activation:**
```json
{"ts": 1234567890.0, "event": "skill_activated", "tool": "skills_tool:load", "skill_name": "incremental-implementation", "query": null, "result_preview": "Skill loaded..."}
```

**Gate decision:**
```json
{"ts": 1234567890.0, "event": "gate_decision", "tool": "code_execution_tool", "mode": "observe", "state": "should_correct", "candidate": "test-driven-development", "reason": "would-fire: skill not loaded"}
```

Telemetry is fully guarded — a logging failure never interrupts agent operation.

---

## Installation

**Option A — Copy directly:**
```bash
cp -r /path/to/a0_agent_skills /a0/usr/plugins/a0_agent_skills
```

**Option B — Plugin Hub:**
Search for `a0_agent_skills` in the Agent Zero Plugin Hub and click Install.

After installation, restart Agent Zero (or use the UI restart button) so the plugin is picked up.

---

## Skill Override: Customizing at Project Scope

You can override any skill for a specific project without modifying the plugin. Copy the skill's `SKILL.md` to your project's `.a0proj` directory:

```bash
mkdir -p /a0/usr/projects/<your-project>/.a0proj/skills/<skill-name>/
cp /a0/usr/plugins/a0_agent_skills/skills/<skill-name>/SKILL.md \
   /a0/usr/projects/<your-project>/.a0proj/skills/<skill-name>/SKILL.md
```

Then edit the copy. Agent Zero's skill resolution searches project scope first, so your local version takes precedence over the plugin version for that project only.

---

## The 20-Skill Cap and `using-agent-skills`

Agent Zero's skill system works best when the agent loads skills intentionally rather than pinning everything into the system prompt permanently. The `using-agent-skills` skill explains when and how to invoke other skills — it is a **meta-skill** designed for on-demand use.

**Do not pin `using-agent-skills` as a persistent/always-loaded skill.** It should be loaded on demand only (e.g. when onboarding a new agent to the workflow).

If you are pinning skills for a project, prioritize the 7 lifecycle skills. Stay within the 20-skill context budget to maintain performance.

---

## Attribution

Skills, agent personas, and slash commands ported from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) by [Addy Osmani](https://github.com/addyosmani). Adapted for the Agent Zero plugin system.
