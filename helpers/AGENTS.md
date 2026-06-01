# helpers/

## Core Contract

- This AGENTS.md is the binding work contract for the `helpers/` subtree
- All shared Python modules must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `helpers/AGENTS.md` before modifying any helper module
3. Identify the specific helper module you will touch
4. Read the module and its consumer extensions before editing
5. Do not rely on memory — re-read in the current session

## Update After Editing

Every meaningful change to a helper requires an AGENTS.md pass:

- Update this doc when: adding/removing helpers, changing public API contracts, altering state file formats
- Update `extensions/AGENTS.md` when: helper consumption by extensions changes
- Update parent root AGENTS.md when: architecture slice descriptions change
- Small edits that don't change behavior or contracts may leave docs unchanged, but the pass must still happen

## Purpose

Shared Python modules providing the core logic for the a0_agent_skills plugin's governance slices. Each helper owns a specific domain (skill matching, workflow state, phase governance, skill contracts, simplify-ignore) and is consumed by extension files and commands.

**Owns:** Skill search/matching, state persistence, phase transitions, contract parsing, DAG validation, simplify-ignore block caching.

**Does NOT own:** Extension lifecycle, prompt injection, command dispatch, agent profiles.

## Entry Points

| Module | Primary Consumer | Role |
|--------|-----------------|------|
| `skill_match.py` | `_10_skill_enforcer.py` (tool_execute_before) | Skill candidate detection, loaded-skill lookup, utility-model classification |
| `workflow_state.py` | `_10_persist_workflow_state.py`, `_67_reattach_workflow_state.py`, commands | Atomic file I/O for all `.a0proj/state/` artifacts |
| `phase_governance.py` | `_10_skill_enforcer.py` (tool_execute_before) | Phase model, phase-skill mapping, transition validation, correction deduplication |
| `skill_contracts.py` | `_10_persist_workflow_state.py` (tool_execute_after) | YAML frontmatter parsing from SKILL.md, dependency DAG, cycle detection, dependency resolution via `resolve_dependencies()` |
| `simplify_ignore_shared.py` | `_simplify_ignore.py` (before + after) | Block cache, hash generation, marker detection, placeholder create/expand |
| `workflow_state.py` → `mark_artifact_approved` | `_20_approval_gate.py` (tool_execute_before) | Mark an artifact (spec, plan) as approved with timestamp and mtime; emits `approval` progress event |
| `workflow_state.py` → `is_artifact_approved` | `phase_governance.check_phase_approval_gate` | Check if an artifact has been approved and file unchanged since approval (reads `approved` + `approved_mtime` from `workflow_artifacts.json`) |
| `workflow_state.py` → `_resolve_artifact_path_for_type` | `mark_artifact_approved`, `is_artifact_approved` | Resolve the canonical file path for an artifact type via slug discovery |

## Contracts & Invariants

### Fail-Safe Default
All public functions are fail-safe: exceptions return safe defaults (empty lists, None, False). Extension code never crashes due to helper failures.

### State I/O Ownership
- `workflow_state.py` is the **sole owner** of `.a0proj/state/` file I/O
- Other helpers never touch state files directly — they call workflow_state functions
- State files: `active_plan.json`, `active_goal.json`, `current_phase.json`, `loaded_skills.json`, `checkpoints.json`, `progress_log.jsonl`, `handoff.md`
- `workflow_artifacts.json` also stores `approved`, `approved_at`, and `approved_mtime` dicts per artifact type (populated by `mark_artifact_approved`). `approved_mtime` enables invalidation when the artifact file is modified after approval.
- `approval` is a valid event type in the progress log

### Module Loading
- Helpers import each other normally (they're on `sys.path` via `__init__.py` injection)
- Extensions must bootstrap `_plugin_loader` before importing helpers
- `skill_contracts.py` has its own `_bootstrap_plugin_loader()` for DAG building

### Thread Safety
- `workflow_state.py` uses a process-level `_write_lock` (threading.Lock) for atomic writes
- `simplify_ignore_shared.py` uses threading for block cache access
- No cross-process locking — state files may race in multi-process deployments

### Skill Match Result States
```python
no_candidate          # No matching skills found or non-target tool
already_loaded        # Matching skill already in agent.data['loaded_skills']
should_correct        # Classifier says a skill should have been loaded
should_not_correct    # Classifier says no skill needed
classifier_unavailable # Utility model failed or returned unusable output
```

### Target Tools
Only `code_execution_tool` and `text_editor` trigger enforcement checks (defined in `skill_match.TARGET_TOOLS`).

### Phase Model
```python
PHASE_ORDER = ["DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"]
```
Phases advance forward only; no backward transitions.

### DAG Validation
- `skill_contracts.py` builds a directed graph from skill `depends_on` frontmatter
- Cycle detection runs on build (configurable via `skill_graph_validate_on_build`)
- Dependencies must reference existing skill names in `skills/` directory

## Style

- Keep helper code concise and focused on its domain
- Document stable API contracts, not implementation history
- Prefer direct bullets with explicit names
- Delete stale comments and dead code immediately
- Write status messages to stderr, machine-readable output to stdout

## Closeout Protocol

After modifying any helper:

1. Re-check the helper's public API has not changed without updating consumers
2. Update this doc's entry point table if helpers were added/removed
3. Update `extensions/AGENTS.md` if helper consumption changed
4. Update parent root AGENTS.md if architecture slice descriptions changed
5. Run `python -m pytest tests/test_<helper_name>.py -v`
6. Report docs intentionally left unchanged and why

## Patterns

### To add a new helper module:
1. Create `helpers/<module>.py` with fail-safe public functions
2. Import from `helpers.<module>` in consumer extensions
3. Add tests in `tests/test_<module>.py`
4. No need to update `__init__.py` (it only contains sys.path injection and version)
5. Run closeout protocol

### To add a new state artifact:
1. Add read/write functions to `workflow_state.py`
2. Use atomic write pattern (write to temp, rename)
3. Document the artifact name and format
4. Add corresponding persistence in `_10_persist_workflow_state.py`
5. Run closeout protocol

### To add a new phase:
1. Update `PHASE_ORDER` and `PHASE_SKILL_MAP` in `phase_governance.py`
2. Update `prompts/agent.skills.routing.md` phase table
3. Update `skills/AGENTS.md` phase catalog
4. Update tests in `tests/test_phase_governance.py`
5. Run closeout protocol

## Anti-patterns

- **Do NOT** read/write state files directly — always go through `workflow_state.py`
- **Do NOT** raise exceptions from public helper functions — use fail-safe returns
- **Do NOT** import from `helpers.` in extension files without bootstrapping `_plugin_loader` first
- **Do NOT** add cross-process locking assumptions — state I/O is process-level only
- **Do NOT** modify `PHASE_ORDER` without updating routing rules, skills doc, and tests
- **Do NOT** skip the Read Before Editing protocol — re-read this doc and the target module before changes
- **Do NOT** skip the AGENTS.md pass after editing

## Related Context

- Parent: `AGENTS.md` (plugin root)
- Extensions: `extensions/AGENTS.md` (consumers of these helpers)
- Tests: `tests/test_*.py` (comprehensive test coverage per module)
