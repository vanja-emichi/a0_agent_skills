# extensions/

## Core Contract

- This AGENTS.md is the binding work contract for the `extensions/` subtree
- All extension implementations must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `extensions/AGENTS.md` before modifying any extension
3. Identify the specific extension file you will touch
4. Read the extension file and its helper dependencies before editing
5. Do not rely on memory — re-read in the current session

## Update After Editing

Every meaningful change to an extension requires an AGENTS.md pass:

- Update this doc when: adding/removing extensions, changing extension point wiring, altering bootstrap patterns
- Update parent root AGENTS.md when: entry points table changes, architecture slice descriptions change
- Update `helpers/AGENTS.md` when: helper contracts consumed by extensions change
- Small edits that don't change behavior or contracts may leave docs unchanged, but the pass must still happen

## Purpose

Agent Zero extension points that implement the plugin's governance slices. Each extension hooks into the agent's tool execution lifecycle (before/after) or prompt assembly to inject routing, enforce skill usage, persist state, and rehydrate workflow context.

**Owns:** Routing injection, enforcement gating, telemetry logging, state persistence, state rehydration, simplify-ignore protection.

**Does NOT own:** Helper logic (delegated to `helpers/`), skill definitions, command dispatch.

## Entry Points

Extensions are organized by Agent Zero's extension point directories:

```
extensions/python/
├── system_prompt/
│   └── _15_agent_skills_routing.py      # Routing rules injection
├── tool_execute_before/
│   ├── _10_skill_enforcer.py            # Enforcement gate
│   ├── _20_approval_gate.py            # Natural language approval detection
│   └── _simplify_ignore.py             # Pre-execution block protection
├── tool_execute_after/
│   ├── _05_skill_telemetry.py          # Telemetry logging
│   ├── _10_persist_workflow_state.py   # State persistence
│   └── _simplify_ignore.py            # Post-execution block restoration
└── message_loop_prompts_after/
    └── _67_reattach_workflow_state.py   # State rehydration
```

| Extension | Extension Point | Helper Dependencies |
|-----------|----------------|-------------------|
| `_15_agent_skills_routing.py` | `system_prompt` | None (reads prompt template directly) |
| `_10_skill_enforcer.py` | `tool_execute_before` | `skill_match`, `phase_governance`, `skill_contracts` |
| `_20_approval_gate.py` | `tool_execute_before` | `workflow_state`, `phase_governance` |
| `_simplify_ignore.py` (before) | `tool_execute_before` | `simplify_ignore_shared` |
| `_05_skill_telemetry.py` | `tool_execute_after` | None (writes JSONL directly) |
| `_10_persist_workflow_state.py` | `tool_execute_after` | `workflow_state`, `skill_contracts` |
| `_simplify_ignore.py` (after) | `tool_execute_after` | `simplify_ignore_shared` |
| `_67_reattach_workflow_state.py` | `message_loop_prompts_after` | `workflow_state` |

## Contracts & Invariants

### Module Bootstrap
Every extension MUST bootstrap `_plugin_loader` before importing from `helpers/`:
```python
def _bootstrap_plugin_loader():
    if '_plugin_loader' not in sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    return sys.modules['_plugin_loader']
```
Path depth varies by extension point:
- `system_prompt/_15_agent_skills_routing.py` → 4 levels up (`parent.parent.parent.parent`)
- `tool_execute_*/*.py` → 3 levels up
- `message_loop_prompts_after/*.py` → 3 levels up

Always verify the correct depth for the specific extension point when writing new extensions.

### Routing Extension
- Reads `prompts/agent.skills.routing.md` with mtime-based caching
- Appends content to `system_prompt` list during prompt assembly
- Works regardless of project context (unlike promptinclude files)

### Enforcement Gate
- Intercepts `code_execution_tool` and `text_editor` calls before execution
- Uses `skill_match` to detect if a skill should have been loaded
- In `observe` mode: logs only
- In `enforce` mode: rewrites tool args to inject skill load
- Respects correction cooldown from `phase_governance`

### Telemetry
- Logs every `skills_tool` activation to JSONL file
- Path configured via `telemetry_log_path` (default `.a0proj/skill_activations.jsonl`)
- Disabled by default for privacy

### State Persistence
- After `skills_tool:load` calls, persists current workflow state
- Also detects `text_editor` write/patch to known artifact paths and auto-infers state
- Path patterns detected: `docs/specs/*-spec.md`, `docs/plans/*-plan.md`, `tasks/*-todo.md`
- Inferred state includes: active_goal, active_plan, current_phase (with forward-only advancement)
- Config flag: `artifact_inference_enabled`
- Artifacts: active_plan, active_goal, current_phase, loaded_skills, checkpoints, progress_log
- Delegates all file I/O to `workflow_state` helper

### State Rehydration
- Runs at `message_loop_prompts_after` to rehydrate state after compaction
- Reads persisted state and injects context into the conversation
- Shows next-skill hints based on skill contract DAG
- Displays `(approved)` tags next to artifacts that have been approved via `mark_artifact_approved`
- Filters out specs with `Approved` or `Shipped` status from the rehydrated state block

### Simplify-Ignore
- Before execution: replaces marked blocks with `BLOCK_<hash>` placeholders
- After execution: restores original content from placeholders
- Shared logic in `simplify_ignore_shared` helper
- Marker syntax: `simplify-ignore-start` / `simplify-ignore-end`

## Style

- Keep extension code concise and focused on its governance slice
- Document stable contracts and invariants, not implementation history
- Prefer direct bullets with explicit names
- Delete stale comments and dead code immediately

## Closeout Protocol

After modifying any extension:

1. Re-check the extension's bootstrap path depth is correct
2. Update this doc's entry point table if extensions were added/removed
3. Update parent root AGENTS.md entry points table if wiring changed
4. Update `helpers/AGENTS.md` if helper consumption changed
5. Run `python -m pytest tests/test_<extension_name>.py -v`
6. Report docs intentionally left unchanged and why

## Patterns

### To add a new extension:
1. Create file in the appropriate `extensions/python/<point>/` directory
2. Follow naming convention: `_NN_descriptive_name.py` (NN = priority order)
3. Bootstrap `_plugin_loader` at the top of the file
4. Import helpers via `from helpers.<module> import ...`
5. Implement the Extension class with `async def execute(self, **kwargs)`
6. Add tests in `tests/test_<descriptive_name>.py`
7. Run closeout protocol

### Priority numbering convention:
- Lower numbers run first within the same extension point
- `_05_` = early (telemetry)
- `_10_` = normal (enforcement, persistence)
- `_15_` = later (routing)
- `_67_` = late (state rehydration, runs near end of loop)

## Anti-patterns

- **Do NOT** skip the `_plugin_loader` bootstrap — imports from `helpers/` will fail
- **Do NOT** read/write state files directly from extensions — use `workflow_state` helper
- **Do NOT** modify tool args destructively in enforcement — always return a modified copy
- **Do NOT** hardcode paths — resolve plugin root dynamically from `__file__`
- **Do NOT** cache state across calls without mtime invalidation — files may change
- **Do NOT** raise exceptions from extensions — use fail-safe returns (exceptions break the agent loop)
- **Do NOT** skip the Read Before Editing protocol — re-read this doc and the target extension before changes
- **Do NOT** skip the AGENTS.md pass after editing

## Related Context

- Parent: `AGENTS.md` (plugin root)
- Helpers: `helpers/AGENTS.md` (shared logic consumed by extensions)
- Tests: `tests/test_*.py` (each extension has dedicated test files)
