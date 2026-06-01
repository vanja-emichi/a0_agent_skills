# a0_agent_skills Plugin -- Comprehensive Analysis Report

*Updated 2026-06-01 — corrected errors, added artifact inference section.*

**Date:** 2026-05-31 | **Analyst:** Deep Research | **Plugin Version:** 1.0.0 | **Author:** Vanja Bunjevac

---

## Table of Contents

1. [Plugin Architecture Overview](#1-plugin-architecture-overview)
2. [Intent-Layer Analysis](#2-intent-layer-analysis)
3. [Skills Inventory](#3-skills-inventory)
4. [Comparison: Plugin vs Official Repo](#4-comparison-plugin-vs-official-repo)
5. [Governance and Enforcement](#5-governance-and-enforcement)
6. [Strengths and Gaps](#6-strengths-and-gaps)
7. [Recommendations](#7-recommendations)

---

## 1. Plugin Architecture Overview

### Identity

The `a0_agent_skills` plugin is an Agent Zero adaptation of the [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) development workflow toolkit. It ports a Claude Code-centric skill system into Agent Zero's plugin architecture, adding enforcement, durable state, and phase governance capabilities that do not exist in the upstream repository.

| Attribute | Value |
|-----------|-------|
| Name | `a0_agent_skills` |
| Title | Agent Skills |
| Version | 1.0.0 |
| Author | Vanja Bunjevac |
| Source | https://github.com/vanja-emichi/a0_agent_skills |
| Upstream | addyosmani/agent-skills |
| Config | Per-project, exposed via WebUI |

### Structural Layers

The plugin is organized as four structural layers, each with clear ownership boundaries:

```
plugin root (/a0/usr/plugins/a0_agent_skills/)
├── skills/       (23 SKILL.md definitions + reference files + scripts)
├── agents/       (3 specialist profiles: code-reviewer, security-auditor, test-engineer)
├── commands/     (7 slash commands: /spec, /plan, /build, /test, /review, /code-simplify, /ship)
├── extensions/   (Agent Zero extension hooks)
│   └── python/
│       ├── system_prompt/           → Routing injection
│       ├── tool_execute_before/     → Enforcement gate + simplify-ignore
│       ├── tool_execute_after/      → Telemetry + state persistence + simplify-ignore
│       └── message_loop_prompts_after/ → State rehydration
├── helpers/      (Shared Python: skill_match, workflow_state, phase_governance, skill_contracts)
├── prompts/      (Routing rules template + ship review template)
├── tests/        (801 tests)
└── webui/        (Config UI)
```

### Five Governance Slices

The plugin's core innovation is five incremental governance slices, each built on Agent Zero extension points:

| Slice | Extension Point | Helper Module | Purpose |
|-------|----------------|---------------|---------|
| **Enforcement Gate** | `tool_execute_before` | `skill_match` | Detect skill bypasses; observe or correct |
| **Durable State** | `tool_execute_after` + `message_loop_prompts_after` | `workflow_state` | Persist plans, goals, phase across compaction/restart |
| **Phase Governance** | `tool_execute_before` | `phase_governance` | 6-phase advisory model with deduplication |
| **Skill Contracts** | `tool_execute_after` | `skill_contracts` | YAML frontmatter metadata + runtime DAG validation |
| **Artifact Path Resolution** | Command templates | `workflow_state` | Canonical artifact paths with no-project fallback |

### Data Flow

```
User Input → Agent
  ↓
  Routing rules injected via system_prompt extension (reads agent.skills.routing.md)
  ↓
  Agent decides action → tool_execute_before:
    ├─ Enforcement gate checks if skill should be loaded
    ├─ Classifier evaluates whether correction needed
    └─ In enforce mode: rewrites tool args to inject skill load
  ↓
  Tool executes
  ↓
  tool_execute_after:
    ├─ Telemetry logs skill activation to JSONL
    ├─ Skill contracts validate YAML frontmatter + DAG
    └─ Workflow state persisted to .a0proj/state/
  ↓
  Next message loop iteration:
    └─ message_loop_prompts_after rehydrates state after compaction
```

---

## 2. Intent-Layer Analysis

### Hierarchy Overview

The plugin implements a 6-level AGENTS.md intent-layer hierarchy totaling approximately 955 lines:

| Node | Lines | Role | Quality |
|------|-------|------|---------|
| `AGENTS.md` (root) | 287 | Plugin-wide architecture, entry points, 5 governance slices, full catalog, config reference | Excellent |
| `helpers/AGENTS.md` | 95 | Shared modules, fail-safe contracts, state I/O ownership, thread safety | Excellent |
| `extensions/AGENTS.md` | 126 | Extension lifecycle, bootstrap protocol, priority numbering, per-extension invariants | Excellent |
| `skills/AGENTS.md` | 186 | 23-skill catalog, SKILL.md format, frontmatter spec, DAG validation, naming conventions | Good (has known inaccuracies) |
| `agents/AGENTS.md` | 124 | 3 profiles, orchestration rules, agent.yaml format, model overrides | Excellent |
| `commands/AGENTS.md` | 137 | 7 commands, text vs script types, artifact path resolution, template patterns | Excellent |

### Structural Pattern

Every AGENTS.md file follows the same canonical template, providing progressive disclosure from purpose to detail:

1. **Purpose** -- What this node owns and does NOT own
2. **Entry Points** -- Files and their roles
3. **Contracts & Invariants** -- Hard rules that must never be violated
4. **Patterns** -- How-to guides for common modifications
5. **Anti-patterns** -- What NOT to do and why
6. **Related Context** -- Links to parent/child/sibling nodes

### Quality Assessment

**Strengths:**
- Every node has clear ownership boundaries ("Owns" / "Does NOT own")
- Fail-safe defaults documented and enforced
- Cross-references link nodes into a navigable graph
- Anti-patterns section prevents common mistakes
- Token-efficient: each file stays under the 4k token target

**Known Inaccuracies (from prior audit):**
- `skills/AGENTS.md` documents a `triggers` field but actual frontmatter uses `trigger_patterns`
- Documents `depends_on` as functional but it was reserved/unused until recent Feature F implementation
- Omits `version` and `author` frontmatter fields that all skills actually have
- `extensions/AGENTS.md` initially documented path resolution as uniformly "3 levels up" but `system_prompt` extension uses 4 levels (this has been corrected)

### Coverage Assessment

The intent layer covers:

| Aspect | Covered By | Depth |
|--------|-----------|-------|
| Skill definitions | `skills/AGENTS.md` | Full format spec + naming + DAG |
| Extension lifecycle | `extensions/AGENTS.md` | Bootstrap + priority + per-extension invariants |
| Helper contracts | `helpers/AGENTS.md` | Fail-safe + thread safety + state ownership |
| Agent profiles | `agents/AGENTS.md` | Orchestration rules + YAML format + model overrides |
| Commands | `commands/AGENTS.md` | Text vs script + artifact resolution + template patterns |
| Plugin architecture | Root `AGENTS.md` | Full catalog + governance slices + config + testing |

---

## 3. Skills Inventory

### Complete Skills Catalog (23 skills)

| # | Phase | Skill Name | Description | Has Scripts | Has Ref Files |
|---|-------|-----------|-------------|-------------|--------------|
| 1 | DEFINE | `spec-driven-development` | Create specs before coding | No | No |
| 2 | DEFINE | `interview-me` | Extract actual requirements via structured interview | No | No |
| 3 | DEFINE | `idea-refine` | Refine raw ideas into actionable concepts | Yes | Yes (3) |
| 4 | PLAN | `planning-and-task-breakdown` | Break work into ordered, testable increments | No | No |
| 5 | PLAN | `context-engineering` | Manage agent context for large codebases | No | No |
| 6 | BUILD | `incremental-implementation` | Deliver changes in small slices | No | No |
| 7 | BUILD | `test-driven-development` | Drive development with tests | No | Yes (1) |
| 8 | BUILD | `source-driven-development` | Read official sources before implementing | No | No |
| 9 | BUILD | `doubt-driven-development` | Adversarial review before decisions stand | No | No |
| 10 | BUILD | `frontend-ui-engineering` | Build production-quality UIs | No | No |
| 11 | BUILD | `api-and-interface-design` | Design stable APIs and interfaces | No | No |
| 12 | VERIFY | `browser-testing-with-devtools` | Test in real browsers | No | No |
| 13 | VERIFY | `debugging-and-error-recovery` | Systematic bug diagnosis and recovery | No | No |
| 14 | REVIEW | `code-review-and-quality` | Five-axis structured code review | No | No |
| 15 | REVIEW | `code-simplification` | Simplify code without changing behavior | No | No |
| 16 | REVIEW | `security-and-hardening` | OWASP-style security audit | No | Yes (1) |
| 17 | REVIEW | `performance-optimization` | Optimize application performance | No | Yes (1) |
| 18 | SHIP | `shipping-and-launch` | Deploy with confidence and rollback | No | No |
| 19 | SHIP | `ci-cd-and-automation` | Implement CI/CD pipelines | No | No |
| 20 | SHIP | `git-workflow-and-versioning` | Version control best practices | No | No |
| 21 | SHIP | `documentation-and-adrs` | Write technical docs and ADRs | No | No |
| 22 | SHIP | `deprecation-and-migration` | Manage safe deprecations | No | No |
| 23 | META | `using-agent-skills` | Meta-skill for skill selection guidance | No | Yes (1) |

### Phase Distribution

```
DEFINE (3 skills): spec-driven-development, interview-me, idea-refine
PLAN    (2 skills): planning-and-task-breakdown, context-engineering
BUILD   (6 skills): incremental-implementation, test-driven-development,
                     source-driven-development, doubt-driven-development,
                     frontend-ui-engineering, api-and-interface-design
VERIFY  (2 skills): browser-testing-with-devtools, debugging-and-error-recovery
REVIEW  (4 skills): code-review-and-quality, code-simplification,
                     security-and-hardening, performance-optimization
SHIP    (5 skills): shipping-and-launch, ci-cd-and-automation,
                     git-workflow-and-versioning, documentation-and-adrs,
                     deprecation-and-migration
META    (1 skill):  using-agent-skills
```

### Skill-Command Mapping

| Command | Phase | Skills Loaded | Profile Delegated |
|---------|-------|--------------|------------------|
| `/spec` | DEFINE | `spec-driven-development` + `markdown-documents` | None |
| `/plan` | PLAN | `planning-and-task-breakdown` + `markdown-documents` | None |
| `/build` | BUILD | `incremental-implementation` + `test-driven-development` | None |
| `/test` | VERIFY | `test-driven-development` | None |
| `/review` | REVIEW | None (delegates) | `code-reviewer` |
| `/code-simplify` | -- | `code-simplification` | None |
| `/ship` | SHIP | None (delegates) | `code-reviewer` + `security-auditor` + `test-engineer` (parallel) |

---

## 4. Comparison: Plugin vs Official Repo

### Origin

The official `addyosmani/agent-skills` repository is a Claude Code / Gemini CLI / OpenCode toolkit. The a0_agent_skills plugin is a **managed fork** that adapts this toolkit to Agent Zero's plugin architecture.

### Structural Comparison

| Aspect | Official Repo | a0_agent_skills Plugin |--------|--------------|----------------------|
| **Target Platform** | Claude Code, Gemini CLI, OpenCode, Cursor, Copilot | Agent Zero framework |
| **Skill Format** | `SKILL.md` with YAML frontmatter (name, description) | `SKILL.md` with extended YAML frontmatter (name, version, author, description, tags, trigger_patterns, depends_on) |
| **Command System** | `.claude/commands/*.md` (Claude Code), `.gemini/commands/*.toml` (Gemini) | `commands/*.command.yaml` + `.txt`/`.py` (Agent Zero commands plugin) |
| **Agent Profiles** | `agents/*.md` (Markdown files, Claude Code subagents) | `agents/*/agent.yaml` + `prompts/agent.system.main.specifics.md` (Agent Zero profiles) |
| **Enforcement** | Prompt-only (AGENTS.md rules, anti-rationalization table) | Runtime enforcement gate with utility-model classifier (observe/enforce modes) |
| **State Persistence** | None (stateless) | Durable workflow state (JSONL files in `.a0proj/state/`) |
| **Phase Governance** | Implicit lifecycle mapping in AGENTS.md | Explicit 6-phase model with transition validation, deduplication, progress logging |
| **Skill Contracts** | None | YAML frontmatter + DAG validation + next-skill hints |
| **Telemetry** | None | JSONL skill activation logging (configurable) |
| **Configuration** | None | `default_config.yaml` + WebUI + per-project config |
| **Testing** | `scripts/validate-skills.js` (basic validation) | 801 pytest tests covering all modules |
| **Hooks** | `hooks/` (shell scripts for simplify-ignore, session-start, SDD-cache) | `hooks.py` (Python lifecycle hooks) + `extensions/` (Python extension points) |
| **Documentation** | `docs/` (setup guides for various platforms) | `docs/` (ADRs, reports, specs, plans) + 6-level AGENTS.md hierarchy |
| **Eval Framework** | None | 30 eval cases with 96.7% prefilter accuracy (Feature D) |
| **Artifact Inference** | None | Path inference for specs, plans, todos with canvas visibility rules |
| **Dependency Loading** | None | `depends_on` frontmatter field with DAG validation and auto-load (Feature F) |

### What Was Adapted (from upstream)

1. **23 Skill Definitions** -- All SKILL.md files ported with extended frontmatter
2. **3 Agent Personas** -- Converted from Markdown to Agent Zero agent.yaml format
3. **7 Slash Commands** -- Converted from `.claude/commands/*.md` to Agent Zero command YAML + templates
4. **Anti-Rationalization Table** -- Ported into routing rules template
5. **6-Phase Lifecycle** -- Adapted from implicit lifecycle mapping to explicit governance model
6. **Orchestration Patterns** -- Parallel fan-out pattern preserved in `/ship` command
7. **Reference Files** -- Checklists (security, performance, accessibility, testing, orchestration) ported
8. **Simplify-Ignore** -- Shell hooks converted to Python extension with shared helper module

### What Was Added (beyond upstream)

1. **Enforcement Gate** -- Runtime tool call interception with ML classifier (entirely new)
2. **Durable Workflow State** -- JSONL persistence surviving compaction/restart (entirely new)
3. **Phase Governance** -- Explicit transition validation + correction deduplication (entirely new)
4. **Skill Contracts** -- YAML frontmatter schema + DAG cycle detection (entirely new)
5. **Telemetry** -- JSONL activation logging with configurable sampling (entirely new)
6. **Configuration System** -- `default_config.yaml` + WebUI + per-project (entirely new)
7. **Test Suite** -- 801 pytest tests (entirely new)
8. **AGENTS.md Intent Layer** -- 6-level hierarchical documentation (entirely new)
9. **7 ADRs** -- Architecture decision records for major design choices (entirely new)
10. **State Rehydration** -- Automatic context restoration after compaction (entirely new)
11. **Artifact Path Inference** -- Canonical artifact paths for specs, plans, todos with canvas visibility rules for workflow artifacts (entirely new)
12. **Skill Dependency Loading** -- `depends_on` frontmatter field with DAG validation and auto-loading of prerequisite skills (Feature F, entirely new)

### What Was Dropped (from upstream)

1. **Multi-Platform Support** -- No Claude Code, Gemini CLI, Copilot, Cursor, Windsurf targets
2. **Zip Packaging** -- Skills are loaded from filesystem, not zip files
3. **Setup Guides** -- No platform-specific installation docs (windsurf, cursor, copilot, etc.)
4. **Shell Hooks** -- Replaced by Python extension system (simplify-ignore, session-start, SDD-cache)
5. **`.claude-plugin/`** -- Not applicable to Agent Zero

---

## 5. Governance and Enforcement

### Routing Injection

Routing rules are injected via the `system_prompt` extension point (`_15_agent_skills_routing.py`), NOT via promptinclude files. This is a critical architectural choice:

- Promptinclude files are invisible when a project is active (Agent Zero behavior)
- The `system_prompt` extension reads `prompts/agent.skills.routing.md` with mtime-based caching
- Works universally regardless of project context
- The routing template (117 lines) contains: skill-driven execution rules, 6-phase lifecycle table, anti-rationalization table, persona invocation rules, parallel delegation rules, skill discovery instructions

### Enforcement Gate

The enforcement gate is the plugin's most novel contribution. It operates in two modes:

**Observe Mode (default):**
- Intercepts `code_execution_tool` and `text_editor` calls
- Uses `skill_match` helper to detect if a skill should have been loaded
- Logs observations without modifying behavior
- Shadow sampling rate configurable (0.0-1.0)

**Enforce Mode:**
- When a skill bypass is detected, rewrites tool arguments to inject skill load
- Uses a utility-model classifier to determine if correction is warranted
- Respects correction cooldown (default 300s) to prevent correction loops
- Classifier model configurable (null = use Agent Zero's utility model)

**Skill Match States:**
```
no_candidate          → No matching skills found
already_loaded        → Matching skill already in agent.data['loaded_skills']
should_correct        → Classifier says a skill should have been loaded
should_not_correct    → Classifier says no skill needed
classifier_unavailable → Utility model failed or returned unusable output
```

### Phase Governance

Implemented in `helpers/phase_governance.py` (308 lines):

- **Phase Model:** `DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP`
- **Forward-only transitions:** Rewinds are allowed but logged with warnings
- **Transition types:** initial, forward, rewind, reentry, jump (each classified)
- **Correction deduplication:** `should_suppress_correction()` with configurable cooldown
- **Progress logging:** All phase changes logged as typed events to progress_log.jsonl
- **State persistence:** Delegates all I/O to `workflow_state` helper

### Durable Workflow State

Seven state artifacts persisted to `.a0proj/state/`:

| Artifact | Format | Purpose |
|----------|--------|---------|
| `active_plan.json` | JSON | Current implementation plan |
| `active_goal.json` | JSON | Current development goal |
| `current_phase.json` | JSON | Current lifecycle phase + phases completed |
| `loaded_skills.json` | JSON | Skills loaded in current session |
| `checkpoints.json` | JSON | Named checkpoints for rollback |
| `progress_log.jsonl` | JSONL | Append-only event log |
| `handoff.md` | Markdown | Context handoff for compaction recovery |

State persistence uses atomic write pattern (write to temp, rename) with process-level threading lock. Rehydration happens via `message_loop_prompts_after` extension.

> **Note:** Agent Zero includes a built-in chat compaction plugin at `/a0/plugins/_chat_compaction/` that handles context summarization when history grows too large. The plugin's durable state and rehydration layer work *on top of* this compaction mechanism to preserve workflow context across compaction cycles.

### Skill Contracts

Skills declare metadata via YAML frontmatter in SKILL.md files:

```yaml
name: skill-name
version: 1.0.0
author: Author Name
description: One-liner + "Use when" triggers
tags: [tag1, tag2, tag3]
trigger_patterns: phrase-1, phrase-2, ...
depends_on: []  # Optional: auto-loaded prerequisite skills
```

Runtime DAG validation:
- Dependencies must reference existing skill directory names
- Cycle detection runs on build (configurable)
- Next-skill hints generated from DAG for workflow state rehydration

### Configuration System

All settings in `default_config.yaml`, exposed via WebUI at `webui/config.html`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `telemetry_enabled` | `false` | Enable/disable JSONL logging |
| `enforcement_mode` | `"observe"` | observe vs enforce |
| `workflow_state_enabled` | `true` | Enable/disable state persistence |
| `phase_governance_enabled` | `true` | Enable/disable 6-phase enforcement |
| `skill_contracts_enabled` | `true` | Enable/disable DAG validation |
| `enforcement_correction_cooldown_seconds` | `300` | Min seconds between corrections |
| `skill_next_skill_hints` | `true` | Show next-skill recommendations |

---

## 6. Strengths and Gaps

### Strengths

**1. Progressive Disclosure Architecture (Exceptional)**
The 4-tier progressive disclosure model (routing rules → skills_tool:search → using-agent-skills reference → individual skills) is best-in-class. It minimizes context consumption while maintaining comprehensive coverage. The upstream repo has a simpler 2-tier model.

**2. Runtime Enforcement Gate (Novel)**
The enforcement gate with utility-model classifier is entirely novel -- neither the upstream repo nor any comparable agent framework has runtime skill-bypass detection. The observe/enforce dual-mode design allows safe rollout.

**3. Durable Workflow State (Novel)**
State persistence surviving context compaction and session breaks addresses a fundamental Agent Zero limitation. The atomic write pattern and rehydration extension are well-engineered.

**4. Comprehensive AGENTS.md Intent Layer (Excellent)**
The 6-level, 955-line AGENTS.md hierarchy with consistent template structure provides exceptional onboarding for both human developers and AI agents navigating the codebase.

**5. Test Coverage (801 tests)**
Extensive test suite covering enforcement, matching, contracts, phase governance, workflow state, telemetry, commands, and upstream parity.

**6. Configuration System (Good)**
Per-project configuration with WebUI, sensible defaults, and boolean-type safety (Alpine.js compatibility).

**7. Fail-Safe Design (Good)**
All public helper functions are fail-safe -- exceptions return safe defaults rather than crashing the agent loop.

**8. Clear Ownership Boundaries (Good)**
Every module, extension, and AGENTS.md node has explicit "Owns" / "Does NOT own" declarations.

### Gaps

**1. No Permission Engine (Acknowledged — Intentional Design Decision)**
No tool-level permission system exists. Any tool found is executed without risk assessment. No risk taxonomy, no approval workflow, no draft/commit separation for risky actions. This was flagged as the largest gap in the agents-best-practices audit, but has been acknowledged as an intentional design decision — Agent Zero's trust model delegates permission concerns to the framework and deployment layer rather than individual plugins.

**2. No Budget Gates in Core (Acknowledged — Out of Scope)**
Agent Zero's monologue loop has no step limit, token budget, cost budget, or wall-time limit. This has been acknowledged as out of scope for the plugin — it requires framework-level changes and is tracked as a framework concern rather than a plugin gap.

**3. Eval Framework (Implemented — Feature D)**
Feature D implemented a skill activation eval suite with 30 eval cases achieving 96.7% prefilter accuracy and 85.7% near-miss discrimination. JSONL telemetry logging is also available (configurable via `telemetry_enabled`). The eval infrastructure exists in `tests/run_enforcement_evals.py` and `tests/run_outcome_lift.py`.

**4. Compaction Still Loses Some State (High)**
While the plugin adds rehydration, Agent Zero's compaction replaces history with a single summary, losing active plan, goal, approval state, loaded skills, and tool call references. The plugin's rehydration only restores what was persisted -- anything not explicitly captured is lost.

**5. Phase Governance is Advisory (Medium)**
Phase governance cannot prevent the agent from ignoring phases. In observe mode, bypasses are only logged. Even in enforce mode, the classifier can decide not to correct. There is no hard gate that blocks BUILD-phase actions when DEFINE is incomplete.

**6. No Multi-Process State Safety (Medium)**
State I/O uses process-level threading locks only. In multi-process deployments (e.g., multiple Agent Zero instances sharing a project), state files may race.

**7. Intent Layer Has Known Inaccuracies (Low)**
The `skills/AGENTS.md` file documents `triggers` field instead of `trigger_patterns`, overstates `depends_on` functionality, and omits `version`/`author` fields. Some corrections have been made but residual inaccuracies may remain.

**8. Limited Upstream Sync Strategy (Low)**
No documented process for merging upstream changes from addyosmani/agent-skills into the plugin. As the upstream evolves, divergence will accumulate.

---

## 7. Recommendations

### Top 5 Priority Improvements

#### Priority 1: Implement Permission Engine with Risk Taxonomy

**Impact:** Critical | **Effort:** Medium | **Target:** New plugin + `tool.py`

Create a `_permission_engine` plugin that:
- Extends tools with `risk_class`, `side_effects`, `timeout`, `max_result_chars`
- Implements allow/deny/approval_required decisions
- Adds result size limiting in `after_execution()`
- Adds strict schema validation for tool arguments

This addresses the most critical gap identified in the agents-best-practices audit (Dimension 3: Tools & Permissions, rated 🔴).

#### Priority 2: Add Budget Gates to Monologue Loop

**Impact:** Critical | **Effort:** Small (framework change) | **Target:** `agent.py`

Add to Agent Zero's `monologue()` function:
- `max_iterations` counter with typed `StopResult` on budget exceeded
- Cumulative token tracking per monologue
- Optional wall-time and cost limits

This addresses the agentic loop gap (Dimension 2: Agentic Loop, rated 🟡). While this is a framework change, the plugin could provide a blueprint or extension-based implementation.

#### Priority 3: ~~Build Eval Framework~~ Extend Existing Eval Suite

**Impact:** High | **Status:** Partially Implemented (Feature D)

Feature D implemented a skill activation eval suite with 30 eval cases, 96.7% prefilter accuracy, and 85.7% near-miss discrimination. The eval infrastructure exists in `tests/run_enforcement_evals.py` and `tests/run_outcome_lift.py`.

Remaining work:
- Expand eval coverage to all 23 skills (currently enforcement-gate focused)
- Add regression evals to catch governance degradation
- Integrate with CI/CD for automated quality gates
- Add eval cases for tool precision, injection resistance, and task success

#### Priority 4: Fix Compaction State Preservation

**Impact:** High | **Effort:** Medium | **Target:** `compactor.py` + `workflow_state.py`

Enhance compaction to preserve:
- Active plan, goal, and loaded skills (partially addressed)
- Approval state and connector state
- Tool call references and their results
- Trust labels on rehydrated context
- Add auto-compaction trigger when tokens approach limit

This addresses the context & compaction gap (Dimension 4: Context & Compaction, rated 🟡).

#### Priority 5: ~~Establish Upstream Sync Process + Fix Intent Layer~~ Document Upstream Sync Process

**Impact:** Medium | **Status:** Intent layer inaccuracies fixed; depends_on implemented (Feature F)

Intent layer inaccuracies have been corrected:
- `triggers` → `trigger_patterns` renamed in `skills/AGENTS.md`
- `version` and `author` fields documented as required
- `depends_on` description updated to reflect Feature F implementation (functional DAG-aware auto-loading)
- Extension path resolution corrected in `extensions/AGENTS.md`

Remaining work:
- Document upstream sync process with a checklist for merging addyosmani/agent-skills changes
- Establish version pinning for upstream releases
- Expand upstream parity tests (partially exists: `test_upstream_parity.py`)

---

## Appendix A: Test Suite Summary

| Area | Test Files | Coverage Focus |
|------|-----------|----------------|
| Plugin contract | `test_plugin_contract.py` | Manifest, entry points |
| Routing extension | `test_routing_extension.py` | mtime caching, injection |
| Skill enforcement | `test_skill_enforcer.py`, `test_enforcement_*.py` | Gate logic, modes, cooldown |
| Skill matching | `test_skill_match.py` | Candidate detection, classification |
| Skill contracts | `test_skill_contracts.py`, `test_skill_graph.py` | YAML parsing, DAG, cycles |
| Phase governance | `test_phase_governance.py` | Transitions, dedup, progress |
| Workflow state | `test_workflow_state.py`, `test_persist_workflow_state.py`, `test_workflow_rehydrate.py` | I/O, atomicity, rehydration |
| Commands | `test_ship_run.py`, `test_ship_sanitization.py` | Ship script, input safety |
| Telemetry | `test_skill_telemetry.py`, `test_gate_telemetry.py`, `test_telemetry_default_and_hooks.py` | Logging, defaults |
| Simplify-ignore | `test_simplify_ignore_*.py` | Block protection/restoration |
| Upstream parity | `test_upstream_parity.py` | Fork alignment |
| Outcome evaluation | `run_enforcement_evals.py`, `run_outcome_lift.py` | Enforcement effectiveness |

## Appendix B: Architecture Decision Records

7 ADRs document major architectural decisions:

| ADR | Title | Decision |
|-----|-------|----------|
| 001 | Skill Enforcement Gate | Utility-model classifier with observe/enforce modes |
| 002 | Durable Workflow State | JSONL + atomic write + rehydration extension |
| 003 | Phase-Aware Governance | 6-phase advisory model with deduplication |
| 004 | Skill Contracts YAML Frontmatter | Structured metadata + DAG validation |
| 005 | importlib Module Loading | Bootstrap via `_plugin_loader.py` for extensions |
| 006 | Enforcement Strict Mode Decision | Dual-mode design for safe rollout |
| 007 | Artifact Path Resolution | Canonical paths with no-project fallback |

## Appendix C: Key Metrics

| Metric | Value |
|--------|-------|
| Skills | 23 |
| Agent Profiles | 3 |
| Slash Commands | 7 |
| Governance Slices | 5 |
| AGENTS.md Nodes | 6 (955 lines total) |
| ADRs | 7 |
| Test Count | 801 |
| Extension Points Used | 4 (system_prompt, tool_execute_before, tool_execute_after, message_loop_prompts_after) |
| Helper Modules | 5 (skill_match, workflow_state, phase_governance, skill_contracts, simplify_ignore_shared) |
| Config Settings | 16 |
| State Artifacts | 7 |
