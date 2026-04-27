# Changelog

All notable changes to a0_agent_skills are documented in this file.

## [0.3.1] - 2026-04-26

### Fixed
- Removed all ghost method references from SKILL.md files (lifecycle-runtime, using-agent-skills, incremental-implementation, planning-and-task-breakdown, spec-driven-development)
- Fixed 3-strike tracker error extraction to match A0's `@extensible` data format (`kwargs['data']['exception']`)
- Fixed SKILL.md contradiction about editing `.a0proj/run/current/` files directly
- Fixed `call_subordinate` not being gated by lifecycle enforcement
- Fixed delegation table to follow lifecycle phases instead of delegating all work
- Fixed phase verifier hint showing duplicate `lifecycle:status` suggestion
- Fixed MagicMock project loading error in extension_base.py
- Fixed plan.txt broken template syntax

### Added
- `emit_spec` parameter in `lifecycle:archive` — generates SPEC.md from lifecycle state
- Lifecycle context in subordinate delegation messages (review.txt, test.txt, security.txt)
- Non-blocking file locking for simplify-ignore concurrent safety
- Token budget (2000 chars) for EXTRAS injection to prevent context bloat
- Auto-progress counter persistence to survive context compaction
- Ghost pattern check in validate.py

### Changed
- Unified import pattern across all 12 extensions (centralized sys.path bootstrap)
- Removed dual import mechanism in lifecycle_state.py
- Config version updated from v0.2.0 to v0.3.1
- Delegation rules updated: follow lifecycle phases yourself, delegate only specialist reviews

### Added (Quality Gates)
- `scripts/validate_skills.py` - SKILL.md validator with alias-tolerant heading matching for 7 required sections
- `lib/ship_personas.py` - system prompt templates for 3 specialist personas (security, test, code quality)
- `tests/test_validate_skills.py` - 10 unit tests for validate_skills.py
- `tests/test_ship_parallel.py` - 10 tests for ship personas and parallel flow
- Parallel `/ship` command with 3 concurrent specialist reviews via scheduler
- Trivial change detection (skip parallel for 2 or fewer files, under 50 lines, no sensitive areas)
- Fallback to `call_subordinate profile=code-reviewer` on scheduler failure
- GO/NO-GO merge decision appended to findings.md
- Lifecycle context (phase, goal, slug, spec_path) in each specialist system_prompt

### Changed (Quality Gates)
- `commands/ship.txt` - replaced sequential review with parallel fan-out plus fallback prose
- `skills/skill-creator/SKILL.md` - added Overview, When to Use, and Boundaries sections
- `tests/test_three_tier_routing.py` - ship removed from no-call-subordinate list (now hybrid command)
- Quality gates alignment score improved from 5.5/10 to target 8.0+/10

### Tests
- 352 tests passing (up from 319 in v0.3.0)
- 33 new tests added covering all fixes and features

## [0.3.0] - 2025-04-25

### BREAKING CHANGES

- **`plan:*` → `lifecycle:*`** — All tool calls renamed. No backwards compatibility layer, no aliases, no deprecation warnings. Hard cut. (`plan:init` → `lifecycle:init`, `plan:status` → `lifecycle:status`, `plan:archive` → `lifecycle:archive`)
- **7 methods removed** — `phase_start`, `phase_complete`, `extend`, `log_finding`, `log_progress`, `log_error`, `migrate`. Phase advance is now direct edit of `state.md` YAML frontmatter. Findings/progress are direct writes to markdown files. Errors are tracked automatically.
- **Templates removed entirely** — `templates/default/` and `templates/analytics/` deleted. `lifecycle:init` hardcodes the 4-file structure (state.md, findings.md, progress.md, errors.md).
- **Command filenames standardized** — All commands now use `.command.yaml` suffix per A0 convention.
- **Class renames** — `PlanState` → `LifecycleState`, `Plan` → `Lifecycle`, `PlanExtension` → `LifecycleExtension`
- **Constant renames** — All `CONTEXT_KEY_PLAN_*` → `CONTEXT_KEY_LIFECYCLE_*`
- **Skill renamed** — `skills/planning-with-files/` → `skills/lifecycle-runtime/`
- **Command renamed** — `/plan-status` → `/lifecycle-status`

### NEW

- **3-method API** — `lifecycle:init` (create), `lifecycle:status` (inspect), `lifecycle:archive` (cleanup). Down from 10 methods.
- **7-phase lifecycle model** — IDEA → SPEC → PLAN → BUILD → VERIFY → REVIEW → SHIP. Hardcoded, no user-provided phases.
- **`/idea` slash command** — New command loading `idea-refine` skill for pre-spec exploration.
- **Strike tracking extension** — New `_55_lifecycle_strike_tracker.py` at `handle_exception/end/` hook. Watches for `RepairableException` results, counts per-error occurrences, gates response at ≥3 strikes.
- **YAML frontmatter in state.md** — Phase tracked in `state.md` YAML frontmatter (replaces `metadata.json`). PyYAML primary with manual fallback parser.
- **LifecycleState.render_abandoned_brief()** — Generates brief for abandoned lifecycles.

### FIXED

- **PlanExtension shadowing bug** — All 7 plan-aware extensions had a module-level `PlanExtension = _EB.PlanExtension` alias that shadowed the base class, making all 6 enforcement extensions inert in production. Fixed by using direct `_EB.LifecycleExtension` inheritance.
- **Canonical file paths** — `tasks/plan.md` and `tasks/todo.md` at project root, not `.a0proj/tasks/`. No duplication.
- **Debug print statements** — Removed all `[PLAN-DEBUG]` print statements from extensions.

### CHANGED

- **Extension filenames** — All 7 plan-aware extensions renamed:
  - `_72_include_plan.py` → `_10_lifecycle_inject.py`
  - `_22_planning_rules.py` → `_22_lifecycle_rules.py`
  - `_30_plan_resume.py` → `_30_lifecycle_resume.py`
  - `_30_phase_verifier.py` → `_30_lifecycle_verifier.py`
  - `_31_response_gate.py` → `_31_lifecycle_gate.py`
  - `_30_no_plan_gate.py` → `_30_no_lifecycle_gate.py`
  - `_30_plan_auto_progress.py` → `_30_lifecycle_auto_progress.py`
- **SKILL.md prose** — 5 skill files updated to reference `lifecycle:*` tool calls.
- **Command prose** — All command `.txt` files updated to reference `lifecycle:*`.
- **Tool prompt** — `prompts/agent.system.tool.plan.md` → `prompts/agent.system.tool.lifecycle.md`, rewritten for 3-method API.
- **strike_tracker.py** — Updated to reference `LifecycleState` instead of `PlanState`.
- **scripts/validate.py** — Updated expected file lists and skill directory references.

### REMOVED

- `tools/plan.py` (replaced by `tools/lifecycle.py`)
- `lib/plan_state.py` (replaced by `lib/lifecycle_state.py`)
- `templates/` directory (entire tree)
- 25 old test files for removed methods and old architecture

## [0.2.3] - 2025-04-22

### FIXED
- Extension loading improvements
- Gate behavior refinements

## [0.2.2] - 2025-04-21

### ADDED
- Command wiring tests
- Architecture fix tests

## [0.2.1] - 2025-04-15

### FIXED
- Extension import path fixes
- Gate mode configuration

## [0.2.0] - 2025-04-13

### ADDED
- Initial planning runtime with 10-method API
- PlanExtension base class for plan-aware extensions
- Template support (default, analytics)
- 3-strike error tracking
- Enforcement gates (response gate, no-plan gate)
- 23 engineering skills
- 3 specialist agent personas
- 9 slash commands
