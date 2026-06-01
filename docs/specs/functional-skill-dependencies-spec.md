# Spec: Functional Skill Dependencies

## Objective

Make the `depends_on` frontmatter field functional. When a skill declares `depends_on: [spec-driven-development]`, the system automatically loads prerequisite skills before the requested skill. Currently `depends_on` is reserved but not consumed by any helper — this spec implements the missing consumption layer.

**User:** Plugin developers and agent operators who want skills to automatically bring in their prerequisites without manual loading.

**Success criteria:**
- When `skills_tool:load skill_name=planning-and-task-breakdown` is called, and that skill declares `depends_on: [spec-driven-development]`, the system auto-loads `spec-driven-development` first (if not already loaded)
- Cycle detection blocks or warns on circular dependencies
- Already-loaded prerequisites are skipped (no double-loading)
- Dependency resolution is transparent but logged in telemetry
- DAG validation on build still works (existing `skill_contracts.py`)
- All 658 existing tests continue to pass

## Tech Stack

- Python 3.11+ (matches Agent Zero runtime)
- Existing helpers: `skill_contracts.py` (DAG builder), `workflow_state.py` (loaded skills tracking)
- Existing extensions: `_10_persist_workflow_state.py` (runs after skill loads)

## Commands

```bash
# Run tests for skill dependencies
python -m pytest tests/test_skill_dependencies.py -v

# Run full suite to verify no regressions
python -m pytest tests/ -v --tb=short
```

## Project Structure

```
helpers/
  skill_contracts.py            # MODIFY: add resolve_dependencies() function
  workflow_state.py             # EXISTING: read_loaded_skills() for skip logic
extensions/python/tool_execute_after/
  _10_persist_workflow_state.py # MODIFY: call dependency resolution after skill load
tests/
  test_skill_dependencies.py   # NEW: dependency resolution tests
```

## Code Style

Follow existing helper conventions:
- Fail-safe functions (exceptions return safe defaults)
- `importlib.util` bootstrap for cross-module imports
- Structured logging via `logging.getLogger(__name__)`
- No external dependencies beyond Python stdlib

## Design Decisions

### Where dependency resolution lives

**Decision:** Add `resolve_dependencies()` to `skill_contracts.py` (not a new helper).

**Rationale:** `skill_contracts.py` already owns the DAG — it builds it, validates it, and queries it. Dependency resolution is a DAG traversal operation. Adding it elsewhere would create a circular dependency or duplicate the graph.

### When resolution happens

**Decision:** Resolution triggers in `_10_persist_workflow_state.py` after a `skills_tool:load` call.

**Rationale:** This extension already runs after every tool execution and checks for skill loads. Adding dependency resolution here means it runs at exactly the right time — after the agent explicitly loads a skill, but before the next turn.

### How auto-loading works

**Decision:** The extension rewrites the tool args to inject additional `skills_tool:load` calls as system-injected observations (not as agent decisions).

**Alternative considered:** Transparent background loading without agent visibility. Rejected because the agent needs to know what skills are in its context to reason correctly.

**Final approach:** After a `skills_tool:load` call completes, the extension:
1. Reads the loaded skill's `depends_on` from the DAG
2. Checks which prerequisites are already loaded via `read_loaded_skills()`
3. For each missing prerequisite, appends a system message noting the auto-load
4. Returns the dependency chain in the tool result metadata

The agent sees the prerequisite skill's content in its context on the next turn (loaded by the extension). This is transparent but observable.

### Cycle handling

**Decision:** Cycles are blocked at DAG build time (existing behavior in `skill_contracts.py`). If a cycle somehow reaches resolution, `resolve_dependencies()` detects it via visited-set tracking and returns only the non-cyclic prefix.

## Testing Strategy

### Unit tests

1. **Linear chain:** A→B→C where loading C auto-loads A and B
2. **Diamond dependency:** D depends on B and C, both depend on A. Loading D loads A, B, C (A loaded once)
3. **Already loaded:** Loading B when A is already loaded skips A
4. **No dependencies:** Loading a skill with no `depends_on` returns empty chain
5. **Cycle protection:** If DAG somehow has a cycle, resolve returns safe prefix
6. **Deep chain:** 4+ level dependency chain resolves correctly

### Integration tests

1. Full workflow: agent loads skill → extension resolves deps → telemetry logs chain → state updated
2. Idempotency: loading the same skill twice doesn't double-load dependencies

## Boundaries

### Always do
- Resolve dependencies transparently with logging
- Skip already-loaded prerequisites
- Detect and break cycles safely
- Preserve existing DAG validation behavior
- Maintain backward compatibility (skills without `depends_on` work identically)

### Ask first
- Adding transitive dependency depth limits (proposed: unlimited, rely on cycle detection)
- Changing the DAG builder's validation behavior
- Adding dependency resolution to the enforcement gate (proposed: separate concern)

### Never do
- Auto-load dependencies during skill search (only on explicit load)
- Modify existing skills' `depends_on` fields
- Break the existing 658 tests
- Add network calls (dependency resolution is purely local)
- Make dependency resolution blocking on the critical path (must be fast, <10ms)

## Implementation Plan

### Step 1: Add `resolve_dependencies()` to `skill_contracts.py`

```python
def resolve_dependencies(
    skill_name: str,
    already_loaded: set[str] | None = None,
    graph: dict | None = None,
) -> list[str]:
    """Return ordered list of prerequisite skill names that need loading.

    Uses topological sort on the skill dependency graph.
    Skills already in `already_loaded` are skipped.
    Cycles are detected and broken (cycle members excluded from result).

    Returns:
        List of skill names in load order (prerequisites first).
        Empty list if no dependencies or skill not found.
    """
    if already_loaded is None:
        already_loaded = set()
    if graph is None:
        graph = get_skill_graph()

    if skill_name not in graph:
        return []

    result: list[str] = []
    visited: set[str] = set()
    in_stack: set[str] = set()

    def _dfs(name: str) -> None:
        if name in visited:
            return
        if name in in_stack:
            # Cycle detected — skip this node
            _log.warning("Dependency cycle detected involving '%s'", name)
            return
n        in_stack.add(name)
        deps = graph.get(name, {}).get("depends_on", [])
        for dep in deps:
            if dep not in already_loaded:
                _dfs(dep)
        in_stack.discard(name)
        visited.add(name)
        if name != skill_name and name not in already_loaded:
            result.append(name)

    _dfs(skill_name)
    return result
```

### Step 2: Integrate into `_10_persist_workflow_state.py`

After detecting a `skills_tool:load` call:

```python
# After skill load is persisted
skill_name = tool_args.get("skill_name", "")
if skill_name:
    loaded_skills = read_loaded_skills(agent) or {}
    already_loaded = set(loaded_skills.get("skills", {}).keys())
    deps = resolve_dependencies(skill_name, already_loaded)
    if deps:
        _log.info("Auto-loading dependencies for '%s': %s", skill_name, deps)
        for dep in deps:
            # Trigger skill load via skills_tool
            # (implementation depends on how extensions can call tools)
            pass
```

### Step 3: Add dependency resolution telemetry

Log dependency chain to the existing telemetry JSONL:

```json
{
  "event": "dependency_resolution",
  "skill_name": "planning-and-task-breakdown",
  "resolved_deps": ["spec-driven-development"],
  "already_loaded": ["interview-me"],
  "skipped": [],
  "timestamp": "2026-05-31T01:00:00Z"
}
```

### Step 4: Populate `depends_on` in skill frontmatter

Add dependencies to relevant skills:

| Skill | depends_on | Rationale |
|-------|-----------|-----------|
| `planning-and-task-breakdown` | `[spec-driven-development]` | Planning requires a spec to plan from |
| `incremental-implementation` | `[planning-and-task-breakdown]` | Implementation follows a plan |
| `test-driven-development` | `[spec-driven-development]` | Tests verify spec criteria |
| `code-review-and-quality` | `[spec-driven-development]` | Review checks against spec |
| `shipping-and-launch` | `[code-review-and-quality]` | Ship after review |
| `code-simplification` | `[code-review-and-quality]` | Simplify after review identifies complexity |
| `security-and-hardening` | `[code-review-and-quality]` | Security review follows code review |
| `performance-optimization` | `[code-review-and-quality]` | Perf review follows code review |

This creates the dependency chain:
```
spec-driven-development
  └── planning-and-task-breakdown
        └── incremental-implementation
  └── test-driven-development
  └── code-review-and-quality
        └── shipping-and-launch
        └── code-simplification
        └── security-and-hardening
        └── performance-optimization
```

## Success Criteria

- [ ] `resolve_dependencies()` returns correct load order for any skill
- [ ] Already-loaded prerequisites are skipped
- [ ] Cycles are detected and broken safely
- [ ] Dependency resolution logs to telemetry when enabled
- [ ] Skills with `depends_on` auto-load prerequisites when explicitly loaded
- [ ] Skills without `depends_on` are unaffected
- [ ] All 658 existing tests pass without modification
- [ ] New test suite covers linear chains, diamonds, cycles, empty deps, and deep chains
- [ ] Resolution completes in <10ms for the full 23-skill graph

## Open Questions

- Should auto-loaded skills appear in the agent's `loaded_skills` state? (Proposed: yes)
- Should the agent receive a notification when dependencies are auto-loaded? (Proposed: yes, via tool result metadata)
- Should dependency resolution be configurable (on/off)? (Proposed: follow `skill_contracts_enabled` config flag)
