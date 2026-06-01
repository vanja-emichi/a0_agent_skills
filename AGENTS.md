# a0_agent_skills

## Core Contract

- AGENTS.md files are binding work contracts for their directory subtrees
- Work products, source materials, instructions, records, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it
- No child doc may weaken the contracts defined in this root AGENTS.md

## Read Before Editing

1. Read this root AGENTS.md
2. Identify every file or folder you expect to touch
3. Walk from the plugin root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for plugin-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken this root contract

Do not rely on memory. Re-read the applicable AGENTS.md chain in the current session before editing.

## Update After Editing

Every meaningful change requires an AGENTS.md pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the AGENTS.md pass still must happen.

## Child DOX Index

Before modifying code in a subdirectory, read its AGENTS.md first to understand local patterns and invariants.

| Child | AGENTS.md Path | Scope |
|-------|---------------|-------|
| **Skills** | `skills/AGENTS.md` | 23 skill definitions, authoring conventions, YAML frontmatter, DAG dependencies |
| **Extensions** | `extensions/AGENTS.md` | Agent Zero extension points, bootstrapping patterns, enforcement gating |
| **Helpers** | `helpers/AGENTS.md` | Shared Python modules for state I/O, skill matching, phase governance, contracts |
| **Agents** | `agents/AGENTS.md` | 3 specialist profiles, orchestration rules, per-profile model overrides |
| **Commands** | `commands/AGENTS.md` | 7 slash commands, text/script types, artifact path resolution |
| **Tests** | `tests/AGENTS.md` | 32 test files, eval fixtures, eval runners, shared test infrastructure |
| **Prompts** | `prompts/AGENTS.md` | Routing rule templates, ship review template, placeholder contracts |

## Purpose

An Agent Zero plugin that ports the [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) development workflow toolkit into the Agent Zero plugin system. Provides 23 curated skills across a 6-phase SDLC lifecycle, 3 specialist agent profiles, 7 slash commands, and workflow governance (enforcement gate, durable state, phase governance, skill contracts).

**Owns:** Skill definitions, routing rules, enforcement, workflow state, agent profiles, and slash commands.

**Does NOT own:** Agent Zero framework internals, the commands plugin infrastructure, or downstream project code.

**Development workspace:** Specs, plans, ADRs, reports, and tasks that drive this plugin's evolution live in the project at `/a0/usr/projects/a0_agent_skills/`. See `/a0/usr/projects/a0_agent_skills/AGENTS.md` for the development workflow and cross-references.

## Entry Points

| File | Role |
|------|------|
| `__init__.py` | Plugin version; canonical `sys.path` injection for plugin root and `helpers/` |
| `hooks.py` | Plugin lifecycle (install/uninstall/pre_update); bootstraps `_plugin_loader` for pre_update cache invalidation |
| `plugin.yaml` | Plugin manifest (name, version, author, settings) |
| `default_config.yaml` | Default configuration for telemetry, enforcement, workflow state, phase governance, skill contracts |
| `extensions/python/system_prompt/_15_agent_skills_routing.py` | Injects routing rules into every session's system prompt |
| `extensions/python/tool_execute_before/_10_skill_enforcer.py` | Intercepts tool calls for enforcement gating |
| `extensions/python/tool_execute_after/_05_skill_telemetry.py` | Logs skill activations to JSONL telemetry |
| `extensions/python/tool_execute_after/_10_persist_workflow_state.py` | Persists workflow state after skill loads/phase transitions; auto-infers state from artifact path writes |
| `extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` | Rehydrates state after compaction/session resume |
| `commands/*.command.yaml` + `commands/*.txt` / `commands/ship.py` | 7 slash commands (/spec, /plan, /build, /test, /review, /code-simplify, /ship) |
| `prompts/agent.skills.routing.md` | Routing rules template injected by system_prompt extension |
| `prompts/ship_review.md` | Review prompt template used by /ship command |

## Architecture: Five Governance Slices

The plugin is organized as five incremental slices, each building on Agent Zero extension points:

| Slice | Purpose | Extension Point | Helper Module |
|-------|---------|----------------|---------------|
| **Enforcement Gate** | Detect when agent skips skills; observe or correct | `tool_execute_before` | `skill_match` |
| **Durable State** | Persist plans, goals, phase across compaction/restart | `tool_execute_after` + `message_loop_prompts_after` | `workflow_state` |
| **Phase Governance** | 6-phase advisory model with deduplication | `tool_execute_before` | `phase_governance` |
| **Skill Contracts** | Structured metadata + runtime DAG validation | `tool_execute_after` | `skill_contracts` |
| **Artifact Path Resolution** | Canonical artifact paths with no-project fallback | Command templates | `workflow_state` |

## The 6-Phase Lifecycle

Every feature or change passes through six phases in order:

| Phase | Required Skill(s) | Purpose |
|-------|-------------------|--------|
| **DEFINE** | `interview-me` + `spec-driven-development` | Extract requirements, define what to build |
| **PLAN** | `planning-and-task-breakdown` | Break work into ordered, testable increments |
| **BUILD** | `incremental-implementation` + `test-driven-development` | Implement in slices with tests first |
| **VERIFY** | `debugging-and-error-recovery` | Prove it works, fix issues before review |
| **REVIEW** | `code-review-and-quality` | Structured quality gate before shipping |
| **SHIP** | `shipping-and-launch` | Deploy with confidence and rollback plan |

### Full Skill Catalog (23 skills)

| Phase | Skills |
|-------|--------|
| **DEFINE** | `spec-driven-development`, `interview-me`, `idea-refine` |
| **PLAN** | `planning-and-task-breakdown`, `context-engineering` |
| **BUILD** | `incremental-implementation`, `test-driven-development`, `source-driven-development`, `doubt-driven-development`, `frontend-ui-engineering`, `api-and-interface-design` |
| **VERIFY** | `browser-testing-with-devtools`, `debugging-and-error-recovery` |
| **REVIEW** | `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization` |
| **SHIP** | `shipping-and-launch`, `ci-cd-and-automation`, `git-workflow-and-versioning`, `documentation-and-adrs`, `deprecation-and-migration` |
| **META** | `using-agent-skills` |

## The 3 Agent Profiles

Specialist subordinate agents invoked via `call_subordinate` at the correct lifecycle phase:

| Profile | When Invoked | Focus |
|---------|-------------|-------|
| `code-reviewer` | REVIEW phase (/review, /ship) | Five-axis review: correctness, readability, architecture, security, performance |
| `security-auditor` | SHIP phase (/ship) | OWASP vulnerability audit, threat modeling |
| `test-engineer` | VERIFY + SHIP phase (/ship) | Test strategy, coverage analysis, Prove-It Pattern |

**Orchestration rule:** The main agent (or slash command) is the orchestrator. Personas do NOT invoke other personas. The only multi-persona pattern is parallel fan-out via `/ship`.

## The 7 Slash Commands

| Command | Loaded Skills | Output |
|---------|--------------|--------|
| `/spec` | `spec-driven-development` | Feature spec at `docs/specs/<slug>-spec.md` |
| `/plan` | `planning-and-task-breakdown` | Implementation plan + task list |
| `/build` | `incremental-implementation` + `test-driven-development` | Incremental implementation |
| `/test` | `test-driven-development` | TDD cycle or bug reproduction |
| `/review` | `code-reviewer` profile | Structured review report |
| `/code-simplify` | `code-simplification` | Simplified code preserving behavior |
| `/ship` | `code-reviewer` + `security-auditor` + `test-engineer` (parallel) | GO/NO-GO decision with rollback plan |

**Prerequisite:** The `commands` plugin must be installed and active.

## Contracts & Invariants

### Routing
- Routing rules are injected via `system_prompt` extension, NOT promptinclude files
- The extension reads `prompts/agent.skills.routing.md` with mtime-based caching
- Works universally regardless of whether a project is active

### Module Loading
- Extensions bootstrap helper imports via `_plugin_loader.py` using `importlib.util`
- Each extension resolves the plugin root independently (no framework changes needed)
- `pre_update()` calls `invalidate_module_cache()` so fresh code is picked up

### Enforcement Gate
- Two modes: `observe` (log only) and `enforce` (inject missing skill calls)
- Uses a utility-model classifier to detect when the agent bypasses skills
- Configurable shadow sampling rate for classification tuning

### Durable Workflow State
- State persisted to `.a0proj/state/` as JSONL files
- Survives context compaction and session breaks
- Rehydrated by `message_loop_prompts_after` extension
- Max progress entries configurable (default 10000)

### Artifact Inference
When `artifact_inference_enabled: true`, detects `text_editor` write/patch calls to known artifact paths and auto-infers workflow state. Path patterns: `docs/specs/*-spec.md` → active_goal + DEFINE phase; `docs/plans/*-plan.md` → active_plan + PLAN phase; `tasks/*-todo.md` → current_task. Phase advancement is forward-only; idempotent via mtime tracking.

### Approval Gates (WIRED — enforce mode)
- `mark_artifact_approved(agent, artifact_type)` in `helpers/workflow_state.py` records approval with timestamp and mtime; emits `approval` progress event
- `is_artifact_approved(agent, artifact_type)` checks approval + mtime invalidation (file changed → approval revoked)
- `detect_approval_in_text(text)` in `_20_approval_gate.py` detects natural language approval ("approved", "looks good", "proceed", "ship it", etc.) with word-boundary matching, negation rejection, and question rejection
- `check_phase_approval_gate(agent, from, to, mode)` in `phase_governance.py` blocks forward transitions in enforce mode when artifact is not approved; warns in observe mode
- 4 mandatory approval gates: G1 (DEFINE→PLAN: spec), G2 (PLAN→BUILD: plan), G3 (BUILD→VERIFY: todo), G4 (REVIEW→SHIP: review)
- VERIFY phase has no gate (intentional — no artifact to approve)
- `workflow_artifacts.json` stores `approved`, `approved_at`, and `approved_mtime` keys per artifact type
- Rehydration displays `(approved)` tags next to approved artifacts
- Rehydration filters specs with `Approved` or `Shipped` status from the state block
- Classifier accuracy: 93.6% (88/94 fixtures); enforcement mode active

### Phase Governance
- 6-phase advisory model with deduplication
- Correction cooldown prevents repeated enforcement for the same candidate (default 300s)

### Skill Contracts
- Skills declare metadata via YAML frontmatter in SKILL.md files
- Runtime DAG validation checks for dependency cycles
- Next-skill hints shown in rehydrated state

### Plugin Toggle
- `.toggle-1` file in plugin root signals the plugin is **enabled** (active)
- `.toggle-0` signals the plugin is **disabled** (inactive)
- These files are managed by the Agent Zero plugin system — do not create or remove manually
- Presence of `.toggle-1` is what the framework checks at startup to load the plugin

### Configuration
- `default_config.yaml` provides all defaults (shipped with plugin)
- `config.json` holds the active runtime configuration (may differ from defaults)
- Per-project configuration supported (`per_project_config: true`)
- All settings are exposed via the WebUI at `webui/config.html`
- Boolean settings use native JSON types (`true`/`false`), not strings
- The WebUI uses Alpine.js `:value` binding for boolean select compatibility

#### Settings Reference

All defaults below come from `default_config.yaml`. Runtime values may differ per project.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `telemetry_enabled` | bool | `false` | Enable/disable skill activation telemetry logging |
| `telemetry_log_path` | string | `.a0proj/skill_activations.jsonl` | JSONL log file path (relative to project root) |
| `telemetry_max_lines` | int | `0` | Max log lines before rotation (0 = unlimited) |
| `enforcement_mode` | string | `"observe"` | `observe` (log only) or `enforce` (inject corrections) |
| `enforcement_classifier_model` | string/null | `null` | Override model for enforcement classifier (null = utility model) |
| `enforcement_shadow_sample_rate` | float | `0.0` | Fraction of calls to classify in observe mode (0.0–1.0) |
| `workflow_state_enabled` | bool | `true` | Enable/disable durable workflow state persistence |
| `workflow_state_path` | string | `.a0proj/state` | State directory path (relative to project root) |
| `max_progress_entries` | int | `10000` | Max progress log entries before pruning oldest |
| `phase_governance_enabled` | bool | `true` | Enable/disable 6-phase lifecycle enforcement |
| `enforcement_correction_cooldown_seconds` | int | `300` | Min seconds between corrections for the same candidate |
| `skill_contracts_enabled` | bool | `true` | Enable/disable skill contract validation and DAG checking |
| `skill_graph_validate_on_build` | bool | `true` | Validate skill dependency graph for cycles on build |
| `skill_next_skill_hints` | bool | `true` | Show next-skill recommendations in rehydrated state |
| `artifact_inference_enabled` | bool | `true` | Auto-detect text_editor write/patch to spec/plan/todo paths and persist corresponding state |

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout Protocol

1. Re-check changed paths against the AGENTS.md chain
2. Update nearest owning AGENTS.md and any affected parents or children
3. Refresh the Child DOX Index if structure changed
4. Remove stale or contradictory text
5. Run existing verification when relevant (`python -m pytest tests/ -v --tb=short`)
6. Report any docs intentionally left unchanged and why

## Directory Structure

```
plugin root (/a0/usr/plugins/a0_agent_skills/)
├── plugin.yaml              # Plugin manifest
├── default_config.yaml      # Default configuration
├── hooks.py                 # Lifecycle hooks
├── _plugin_loader.py        # Module loading helper
├── README.md                # User-facing documentation
├── CHANGELOG.md             # Version history
├── LICENSE                  # MIT
├── agents/                  # Specialist agent profiles
│   ├── code-reviewer/       #   agent.yaml + prompts/
│   ├── security-auditor/    #   agent.yaml + prompts/
│   └── test-engineer/       #   agent.yaml + prompts/
├── commands/                # Slash command definitions
│   ├── *.command.yaml       #   Command configuration
│   ├── *.txt                #   Text command templates
│   └── ship.py              #   Script command (parallel fan-out)
├── extensions/              # Agent Zero extension points
│   └── python/
│       ├── system_prompt/           # Routing injection
│       ├── tool_execute_before/      # Enforcement gate
│       ├── tool_execute_after/       # Telemetry + state persistence
│       └── message_loop_prompts_after/ # State rehydration
├── helpers/                 # Shared helper modules
│   ├── skill_match.py       #   Skill search, candidate matching
│   ├── workflow_state.py    #   Atomic file I/O for state artifacts
│   ├── phase_governance.py  #   Phase transitions, deduplication
│   ├── skill_contracts.py   #   YAML frontmatter, DAG validation
│   └── simplify_ignore_shared.py # Shared simplify-ignore logic
├── prompts/                 # Prompt templates
│   ├── agent.skills.routing.md  # Routing rules
│   └── ship_review.md           # /ship review template
├── skills/                  # 23 skill definitions
│   └── <skill-name>/
│       ├── SKILL.md         # Required: skill definition
│       └── scripts/         # Optional: executable helpers
├── tests/                   # Test suite (~650+ tests)
│   ├── conftest.py          # Shared fixtures
│   ├── eval_fixtures/       # Evaluation data
│   └── test_*.py            # Unit + integration tests
└── webui/                   # Plugin UI
    ├── config.html          # Configuration page
    └── thumbnail.jpg        # Plugin thumbnail
```

## Patterns

### To add a new skill:
1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter (name, description, tags, triggers)
2. Add supporting scripts to `skills/<skill-name>/scripts/` if needed
3. Update `prompts/agent.skills.routing.md` with phase mapping and intent triggers
4. Update `helpers/skill_contracts.py` if the skill has dependencies
5. Add tests in `tests/test_skill_*.py`
6. Document in README
7. Run closeout protocol (update `skills/AGENTS.md` child index)

### To add a new slash command:
1. Create `commands/<name>.command.yaml` with name, description, type
2. Create companion `commands/<name>.txt` (text commands) or `commands/<name>.py` with `run(payload)` (script commands)
3. Use `{raw}` placeholder for trailing user input in text templates
4. Add skill loading instructions: `skills_tool:load skill_name=<name>`
5. Ensure the commands plugin is installed
6. Run closeout protocol (update `commands/AGENTS.md` child index)

### To add a new agent profile:
1. Create `agents/<profile-name>/agent.yaml` with name, description, context
2. Create `agents/<profile-name>/prompts/agent.system.main.specifics.md` with the profile's system prompt
3. Update routing rules to reference the profile
4. For per-profile model override, create `_model_config/config.json` alongside the profile
5. Run closeout protocol (update `agents/AGENTS.md` child index)

### To modify enforcement behavior:
1. Edit `extensions/python/tool_execute_before/_10_skill_enforcer.py`
2. Update `helpers/skill_match.py` for matching logic changes
3. Adjust `default_config.yaml` for mode/rate changes
4. Test with `tests/test_skill_enforcer.py`
5. Run closeout protocol (update `extensions/AGENTS.md` and `helpers/AGENTS.md`)

## Anti-patterns

- **Do NOT** use promptinclude files for routing — they are invisible when a project is active; use the `system_prompt` extension instead
- **Do NOT** import helpers directly with normal imports — use `_plugin_loader.py` bootstrap or `sys.path` injection
- **Do NOT** let personas invoke other personas — the orchestrator (main agent or slash command) is the only caller
- **Do NOT** use `call_subordinate_parallel` for general research or same-profile tasks — it is specialist-only fan-out
- **Do NOT** skip the YAML frontmatter in SKILL.md files — skill contracts and DAG validation depend on it
- **Do NOT** hardcode artifact paths — use `workflow_state` helpers for canonical path resolution
- **Do NOT** modify the routing template without testing the mtime cache invalidation
- **Do NOT** skip the Read Before Editing protocol — re-read the AGENTS.md chain before making changes
- **Do NOT** skip the AGENTS.md pass after editing — update owning docs and affected parents/children
- **Do NOT** weaken this root contract from a child AGENTS.md

## Testing

The test suite lives in `tests/` with ~650+ tests covering:

| Area | Test Files |
|------|-----------|
| Plugin contract | `test_plugin_contract.py` |
| Routing extension | `test_routing_extension.py` |
| Skill enforcement | `test_skill_enforcer.py`, `test_enforcement_*.py` |
| Skill matching | `test_skill_match.py` |
| Skill contracts | `test_skill_contracts.py`, `test_skill_graph.py` |
| Phase governance | `test_phase_governance.py` |
| Workflow state | `test_workflow_state.py`, `test_persist_workflow_state.py`, `test_workflow_rehydrate.py`, `test_artifact_inference.py` |
| Commands | `test_ship_run.py`, `test_ship_sanitization.py` |
| Telemetry | `test_skill_telemetry.py`, `test_gate_telemetry.py`, `test_telemetry_default_and_hooks.py` |
| Simplify-ignore | `test_simplify_ignore_*.py` |
| Upstream parity | `test_upstream_parity.py` |
| Outcome evaluation | `run_enforcement_evals.py`, `run_outcome_lift.py` |

Run tests:
```bash
cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ -v --tb=short
```

## Related Context

- Upstream source: [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)
- DOX framework: [agent0ai/dox](https://github.com/agent0ai/dox)
- Agent Zero framework: `/a0/` (main agent codebase)
- Commands plugin: `/a0/usr/plugins/commands/`
- Plugin development project: `/a0/usr/projects/a0_agent_skills/`
- ADRs: `docs/adrs/` (7 ADRs covering major architectural decisions)
