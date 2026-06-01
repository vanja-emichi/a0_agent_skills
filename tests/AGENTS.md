# tests/

## Core Contract

- This AGENTS.md is the binding work contract for the `tests/` subtree
- All test files, fixtures, and eval runners must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `tests/AGENTS.md` before modifying any test
3. Read `conftest.py` to understand shared fixtures and module stubs
4. Read the target test file before editing
5. Re-read every session — do not rely on memory

## Update After Editing

- Update this doc when: adding/removing test categories, changing eval infrastructure, altering shared fixtures
- Update `conftest.py` docstring when: adding/removing shared fixtures, changing module stub strategy
- Update parent root AGENTS.md when: test categories affect architecture documentation

## Purpose

Test suite for the a0_agent_skills plugin. Validates enforcement gates, workflow state, phase governance, skill contracts, routing, telemetry, artifact inference, and ship command behavior.

**Owns:** Unit tests, integration tests, eval fixtures, eval runners, shared test infrastructure (`conftest.py`).

**Does NOT own:** Production code (in `extensions/`, `helpers/`, `agents/`, `commands/`).

## Test Categories

| Category | Files | Validates |
|----------|-------|----------|
| **Enforcement** | `test_enforcement_*.py` | Skill enforcement gate, guardrails, language patterns |
| **Skill Matching** | `test_skill_match.py`, `test_skill_graph.py`, `test_skill_contracts.py`, `test_skill_dependencies.py` | Skill search, DAG validation, frontmatter parsing |
| **Enforcer Runtime** | `test_skill_enforcer.py` | Full enforcement pipeline with mocked agent |
| **Workflow State** | `test_workflow_state.py`, `test_workflow_rehydrate.py`, `test_persist_workflow_state.py` | Durable state persistence and rehydration |
| **Phase Governance** | `test_phase_governance.py` | 6-phase advisory model, deduplication |
| **Routing** | `test_routing_extension.py`, `test_routing_rules_refactor.py` | System prompt injection, routing template |
| **Telemetry** | `test_skill_telemetry.py`, `test_telemetry_default_and_hooks.py`, `test_gate_telemetry.py` | Activation logging, hooks |
| **Artifact Inference** | `test_artifact_inference.py`, `test_artifact_inference_integration.py` | Auto-infer workflow state from file writes |
| **Ship Command** | `test_ship_run.py`, `test_ship_sanitization.py` | `/ship` slash command execution and input safety |
| **Code Simplify** | `test_simplify_ignore_*.py` | Simplify-ignore shared cache behavior |
| **Plugin Contract** | `test_plugin_contract.py` | Plugin install/uninstall lifecycle |
| **Outcome Lift** | `test_outcome_lift.py` | Skill enforcement outcome improvement metrics |
| **Upstream Parity** | `test_upstream_parity.py` | Compatibility with upstream addyosmani/agent-skills |
| **Evals** | `test_skill_activation_evals.py`, `test_enforcement_config.py` | Fixture-driven enforcement accuracy, config validation |

## Eval Infrastructure

- **`eval_fixtures/skill-activation-evals.json`** — JSON fixtures for enforcement ON/OFF comparison tests
- **`eval_runner.py`** — Standalone runner comparing enforcement pipeline with settings ON vs OFF
- **`run_enforcement_evals.py`** — Full enforcement evaluation suite
- **`run_outcome_lift.py`** — Outcome lift measurement runner

## Shared Infrastructure (`conftest.py`)

- `_clean_sys_modules` fixture: save/restore `sys.modules` around each test
- Module stubs: `helpers`, `helpers.extension`, `helpers.tool`, `helpers.plugins`, `helpers.projects`
- `_make_extension` factory: creates `SkillTelemetry` instances with mocked agent
- Parallel tool stubs: `_Response`, `_Tool`, `_install_parallel_tool_stubs` for `call_subordinate_parallel` tests
- Preserves singleton modules across `sys.modules` resets (simplify_ignore_shared, skill_match, phase_governance, workflow_state)

## Conventions

- All test files use `pytest` conventions
- Mocks via `unittest.mock.MagicMock` — no external mock libraries
- Module stubs prevent real Agent Zero framework imports
- No network calls — all tests are local and deterministic

## Style

- Concise, operational doc — no diary entries
- Test names describe what they validate
- Fixtures are composable and documented in `conftest.py`

## Closeout Protocol

1. Run full suite: `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ -v`
2. Verify no regressions in existing tests
3. Update this doc if new test categories or eval infrastructure was added
4. Update `conftest.py` docstring if shared fixtures changed

## Anti-patterns

- Do NOT import real Agent Zero framework modules in tests — use `conftest.py` stubs
- Do NOT create network-dependent tests
- Do NOT modify production code to make tests pass — fix the test or the feature
- Do NOT add eval fixtures without corresponding test coverage
- Do NOT bypass the `_clean_sys_modules` fixture for isolation-sensitive tests

## Related Context

- **Parent:** `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
- **Helpers under test:** `helpers/AGENTS.md`
- **Extensions under test:** `extensions/AGENTS.md`
