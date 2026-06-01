# Implementation Audit: Markdown Artifact and Workflow State Alignment

> **Auditor:** Senior Code Reviewer (code-reviewer profile)  
> **Date:** 2026-05-30  
> **Spec:** `docs/specs/markdown-artifact-and-state-alignment-spec.md`  
> **Plan:** `docs/plans/markdown-artifact-and-state-alignment-plan.md`  
> **Verdict:** The spec describes genuine gaps. However, several items are already partially or fully done, and some planned work is overengineered for the current state of the system.

---

## Executive Summary

The plugin has a **solid foundation** for artifact and state management. The canonical directory structure (`docs/specs/`, `docs/plans/`, `tasks/`, `docs/adrs/`, `docs/reports/`, `docs/ideas/`, `docs/intent/`) already exists and is actively used by 11 specs, 8 plans, 6 todos, 6 ADRs, 2 reports, 1 idea, and 1 intent doc. Two skills (`spec-driven-development`, `planning-and-task-breakdown`) already instruct saving to feature-scoped paths.

The **real gaps** are:
1. **No artifact path resolver** — commands hardcode legacy paths, no single source of truth
2. **No `workflow_artifacts.json`** — no tracking of active artifact set across commands
3. **No no-project fallback** — everything breaks when no project is active
4. **Command templates lag behind** — `spec.txt`, `plan.txt`, `build.txt`, `code-simplify.txt` still reference `SPEC.md` / `tasks/plan.md`
5. **Handoff/rehydration lacks artifact paths** — compaction loses artifact context

---

## Comprehensive Audit Table

### A. Path Resolution and State Model

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| `resolve_visible_root(agent)` — returns project root or workdir | **Does not exist** | ❌ | New function needed in `workflow_state.py` |
| `resolve_artifact_paths(agent, slug)` — returns canonical artifact paths | **Does not exist** | ❌ | New function needed — the core of the spec |
| `discover_feature_slug(agent)` — find active slug from state or filesystem | **Does not exist** | ❌ | New function needed |
| `save_workflow_artifacts(agent, data)` — write `workflow_artifacts.json` | **Does not exist** | ❌ | New function needed; can reuse `_safe_write_json` |
| `read_workflow_artifacts(agent)` — read `workflow_artifacts.json` | **Does not exist** | ❌ | New function needed; can reuse `_safe_read_json` |
| Canonical visible artifact locations (`docs/specs/<slug>-spec.md`, etc.) | **Directories exist and are actively used** | ✅ | No work needed — already the convention |
| Feature-scoped paths in skills | **2 skills already use them**: `spec-driven-development` → `docs/specs/[feature-name].md`, `planning-and-task-breakdown` → `docs/plans/[feature-name].md` | ✅ | Verify remaining 21 skills use consistent paths |
| Atomic writes for state | **Already implemented** via `_safe_write_json` (temp file + `os.replace`) | ✅ | No work needed |
| `_ensure_dir` for lazy directory creation | **Already implemented** | ✅ | No work needed |
| Corrupt file handling → warn + safe default | **Already implemented** in `_safe_read_json` | ✅ | No work needed |
| `resolve_state_dir(agent)` reads `default_config.yaml.workflow_state_path` | **Config key exists** but `resolve_state_dir()` does NOT read it | ⚠️ | Add config lookup to existing function |

### B. No-Project Fallback

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| `resolve_state_dir` falls back to `/a0/usr/workdir/.a0_agent_skills/state/` | **No fallback** — returns `None` when no project active | ❌ | Add fallback to existing function |
| `/a0/usr/workdir/.a0_agent_skills/` directory | **Does not exist** | ❌ | Created lazily on first write |
| Reattach extension reads from workdir fallback | **Only reads `.a0proj/state/`** | ❌ | Add fallback path in `_67_reattach_workflow_state.py` |
| Never creates fake `.a0proj` under workdir | **Not applicable** — nothing creates it today | ✅ | Verify during implementation |

### C. Event Model

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| `progress_log.jsonl` append infrastructure | **Already implemented** — `append_progress_event()` with rotation | ✅ | No work needed |
| Event types: `skill_loaded`, `phase_change`, `gate_correction`, `goal_set`, `plan_set` | **Already implemented** — `_VALID_EVENT_TYPES` includes these | ✅ | No work needed |
| Event types: `artifact_created`, `artifact_updated` | **Not in `_VALID_EVENT_TYPES`** | ❌ | Add new event types + helper function |
| Event types: `approval` | **Does not exist** | ❌ | New event type |
| Event types: `artifact_lifecycle` | **Does not exist** | ❌ | New event type |
| ISO 8601 timestamps in events | **Uses epoch timestamps** (`time.time()`) | ⚠️ | Consider dual format or keep epoch for consistency |
| Existing untyped events continue to work | **Yes** — append is format-agnostic | ✅ | No work needed |

### D. Command Alignment

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| `/spec` uses resolved spec path instead of `SPEC.md` | **Hardcodes** `"SPEC.md in the project root"` | ❌ | Update `commands/spec.txt` |
| `/plan` uses resolved plan/todo paths | **Hardcodes** `"tasks/plan.md"` and `"tasks/todo.md"` | ❌ | Update `commands/plan.txt` |
| `/build` reads active spec/todo from state | **Hardcodes** `"tasks/todo.md"` | ❌ | Update `commands/build.txt` |
| `/review` reads active spec from state | **No hardcoded paths** but no state reading either | ⚠️ | Add state-based spec lookup to `commands/review.txt` |
| `/test` reads active spec from state | **No hardcoded paths**, no state reading | ⚠️ | Minor — add optional spec lookup |
| `/ship` uses shared path resolver | **Has its own `_find_spec()`** that already searches `docs/specs/*-spec.md` | ⚠️ | Replace internal `_find_spec` with resolver call |
| `/code-simplify` references `SPEC.md` | **Hardcodes** `"SPEC.md"` | ❌ | Update `commands/code-simplify.txt` |
| Legacy `SPEC.md` fallback | **Not implemented** — if `SPEC.md` exists, nothing reads it | ❌ | Add fallback in resolver |
| Legacy `tasks/plan.md` / `tasks/todo.md` fallback | **`tasks/todo.md` exists** as a legacy file; nothing falls back to it programmatically | ⚠️ | Add fallback in resolver |

### E. Approval Model

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| `/spec --approve` marks spec as approved | **Does not exist** — no approval mechanism | ❌ | New feature |
| `/plan --approve` marks plan as approved | **Does not exist** | ❌ | New feature |
| Approval persisted in `workflow_artifacts.json` | **File doesn't exist** | ❌ | Part of new state file |
| Approval invalidated on material changes | **Does not exist** | 🗑️ | Overengineered — defer |
| Model cannot self-approve | **N/A** — no approval system exists | ✅ | Ensure in implementation |

### F. Artifact Lifecycle

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| Lifecycle states: `active`, `superseded`, `completed` | **Does not exist** | 🗑️ | Overengineered — no multi-feature concurrent use case yet |
| Old spec → `superseded` when new spec for same feature | **Does not exist** | 🗑️ | Defer — single active feature is the norm |
| `/ship` → all artifacts `completed` | **Does not exist** | 🗑️ | Defer — no one queries lifecycle state today |
| Only `active` artifacts in handoff/rehydration | **No artifact tracking at all** | ⚠️ | Will be handled by simply tracking current artifacts |

### G. Handoff and Rehydration

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| `handoff.md` includes artifact paths | **Only includes**: Project, Phase, Goal, Plan path, Current Task, Loaded Skills, Last Checkpoint | ⚠️ | Extend `write_handoff()` to include artifact paths |
| Handoff follows agents-best-practices format (objective, constraints, approval state, artifacts, errors, etc.) | **Current format is minimal** — 8 fields | ⚠️ | Extend to include: artifacts created/changed, approval state, errors, next step |
| Rehydration includes active artifact set | **Only rehydrates**: goal, phase, plan, skills, checkpoints | ⚠️ | Add `workflow_artifacts.json` to rehydration |
| Rehydration works in no-project mode | **Only works with `.a0proj/state/`** | ❌ | Add workdir fallback |

### H. markdown-documents Integration

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| `markdown-documents` loaded by document-producing commands | **Not referenced by any command** | ⚠️ | Add companion loading instructions to commands |
| `markdown-documents` NOT globally always-on | **Not enforced at all** | ✅ | Ensure it stays companion-only |
| Convention documented in `using-agent-skills` | **Not mentioned** | ⚠️ | Add note to `using-agent-skills/SKILL.md` |
| Skills that produce Markdown artifacts explicitly load it | **0 of 7 listed skills reference it** | ⚠️ | Document convention, don't enforce in all 7 skills |

### I. Testing

| Spec Requirement | Current State | Status | Gap |
|---|---|---|---|
| Unit tests for path resolution | **587 lines in `test_workflow_state.py`** — no artifact path tests | ⚠️ | Extend existing test file |
| Unit tests for no-project fallback | **None** | ❌ | New tests needed |
| Unit tests for `workflow_artifacts.json` roundtrip | **None** | ❌ | New tests needed |
| Integration tests for command output paths | **None** — commands are text templates, not Python | ⚠️ | Manual verification or integration test harness |
| Regression tests for `SPEC.md` hardcoding | **None** | ❌ | Add test that greps commands for legacy paths |
| Existing test suite | **23 test files, 10,109 lines total** | ✅ | Strong foundation to extend |

---

## Count Summary

### ✅ Already Done (12 items)
1. Canonical directory structure exists and is in active use
2. Feature-scoped paths in `spec-driven-development` and `planning-and-task-breakdown` skills
3. Atomic writes via `_safe_write_json` (temp + rename)
4. `_ensure_dir` for lazy directory creation
5. Corrupt file handling in `_safe_read_json`
6. `progress_log.jsonl` append infrastructure with rotation
7. Basic event types: `skill_loaded`, `phase_change`, `gate_correction`, `goal_set`, `plan_set`
8. State persistence extension (`_10_persist_workflow_state.py`)
9. State rehydration extension (`_67_reattach_workflow_state.py`)
10. Phase governance, skill contracts, skill match — all complete and tested
11. Comprehensive test suite (10K+ lines, 23 files)
12. Config surface (`default_config.yaml` + `config.html`)

### ⚠️ Partially Done (10 items)
1. `resolve_state_dir` — exists but no no-project fallback, doesn't read config
2. `handoff.md` — generated but missing artifact paths and expanded format
3. Progress events — infrastructure exists but missing artifact/approval/lifecycle types
4. Config key `workflow_state_path` — defined but not consumed by code
5. `/review` — no hardcoded paths but doesn't read state
6. `/test` — no hardcoded paths but doesn't read state
7. `/ship` — has `_find_spec()` but doesn't use shared resolver
8. `markdown-documents` — skill exists but not referenced by any command
9. Legacy fallback — `tasks/todo.md` exists but nothing falls back to it
10. Test coverage — strong foundation but no artifact-path-specific tests

### ❌ Genuinely New (13 items)
1. `resolve_visible_root(agent)` function
2. `resolve_artifact_paths(agent, slug)` function
3. `discover_feature_slug(agent)` function
4. `save_workflow_artifacts(agent, data)` function
5. `read_workflow_artifacts(agent)` function
6. No-project fallback in `resolve_state_dir`
7. No-project fallback in reattach extension
8. Typed artifact events (`artifact_created`, `artifact_updated`, `approval`)
9. Updated command templates (`spec.txt`, `plan.txt`, `build.txt`, `code-simplify.txt`)
10. Expanded handoff format with artifact paths
11. `workflow_artifacts.json` state file
12. Approval mechanism (`--approve` for spec/plan)
13. Legacy path fallback in resolver (`SPEC.md`, `tasks/plan.md`, `tasks/todo.md`)

### 🗑️ Overengineered / Should Defer (4 items)
1. **Artifact lifecycle states** (`active`/`superseded`/`completed`) — No multi-feature concurrent use exists. Simple "current artifact" tracking is sufficient. Adds state machine complexity without a real consumer.
2. **Approval invalidation on material changes** — Requires content hashing or diffing to detect "material changes." Premature optimization for a system where the user explicitly approves.
3. **`--slug` override in commands** — Nice-to-have but not critical. The slug will be auto-discovered from the first artifact or from state. Manual override is an edge case.
4. **Multi-spec disambiguation** — When multiple `*-spec.md` files exist, the spec says to "return list, ask user to disambiguate." This is a UX interaction that can be deferred; the current system only has one active spec at a time.

---

## Revised Scope Recommendation

### Phase 1: Core (Do Now) — ~4 files, ~200 lines of new code

1. **Add artifact path resolution functions to `workflow_state.py`**
   - `resolve_visible_root(agent)` — 10 lines
   - `resolve_artifact_paths(agent, slug)` — 30 lines
   - `discover_feature_slug(agent)` — 15 lines
   - `save_workflow_artifacts(agent, data)` — 10 lines (wraps `_safe_write_json`)
   - `read_workflow_artifacts(agent)` — 10 lines (wraps `_safe_read_json`)
   - Update `_VALID_EVENT_TYPES` to include new types — 3 lines

2. **Add no-project fallback to `resolve_state_dir`**
   - Modify existing function — ~10 lines changed
   - Reads `workflow_state_path` from config — ~5 lines

3. **Add no-project fallback to reattach extension**
   - Modify `_67_reattach_workflow_state.py` — ~15 lines

4. **Update command templates** (text edits, no Python)
   - `spec.txt`: Replace `SPEC.md` with resolver instructions
   - `plan.txt`: Replace `tasks/plan.md` with resolver instructions
   - `build.txt`: Replace `tasks/todo.md` with state lookup
   - `code-simplify.txt`: Replace `SPEC.md` with state lookup

### Phase 2: Enhancement (Do Next) — ~3 files, ~100 lines

5. **Extend handoff format** — add artifact paths section to `write_handoff()`
6. **Extend rehydration** — include `workflow_artifacts.json` in state block
7. **Add typed event emission** — `emit_artifact_event()` helper + integration into save functions

### Phase 3: Polish (Do Later) — documentation and testing

8. **Document `markdown-documents` companion convention** in `using-agent-skills`
9. **Add approval mechanism** (`--approve` for spec/plan commands)
10. **Extend tests** for new path resolution, no-project fallback, artifact state roundtrip

### Explicitly Deferred

- Artifact lifecycle state machine (active/superseded/completed)
- Approval invalidation on material changes
- `--slug` override in commands
- Multi-spec disambiguation
- `markdown-documents` enforcement in all 7 skills (document convention instead)

---

## Files Audit Summary

| File | Lines | Changes Needed |
|------|-------|---------------|
| `helpers/workflow_state.py` | ~350 | **Extend** — add ~80 lines (path resolution, artifact state, event types) |
| `helpers/phase_governance.py` | ~200 | None — complete |
| `helpers/skill_contracts.py` | ~350 | None — complete |
| `helpers/skill_match.py` | ~250 | None — complete |
| `commands/spec.txt` | ~15 | **Edit** — replace hardcoded paths |
| `commands/plan.txt` | ~15 | **Edit** — replace hardcoded paths |
| `commands/build.txt` | ~20 | **Edit** — replace hardcoded paths |
| `commands/review.txt` | ~15 | **Edit** — add state lookup |
| `commands/test.txt` | ~20 | **Edit** — add optional state lookup |
| `commands/ship.py` | ~332 | **Edit** — replace `_find_spec` with resolver call |
| `commands/code-simplify.txt` | ~15 | **Edit** — replace hardcoded paths |
| `extensions/python/tool_execute_after/_10_persist_workflow_state.py` | ~200 | None (or minor — emit artifact events) |
| `extensions/python/tool_execute_before/_10_skill_enforcer.py` | ~350 | None — complete |
| `extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` | ~200 | **Edit** — add workdir fallback + artifact state |
| `default_config.yaml` | ~20 | None — already has needed keys |
| `webui/config.html` | ~200 | None — already has needed UI |
| `tests/test_workflow_state.py` | ~587 | **Extend** — add ~100 lines of artifact path tests |

---

## Key Architectural Observations

### 1. ship.py is already ahead of other commands

`ship.py` has `_find_spec()` that searches `docs/specs/*-spec.md`, `_parse_project_structure()` that extracts file trees from specs, and `_resolve_code_path()` that handles plugin path resolution. This is the most mature command in terms of spec-aware behavior. The plan's Task 3.6 to replace `_find_spec` with the resolver is correct, but the existing code is solid.

### 2. Skills already have the right convention

Both `spec-driven-development` and `planning-and-task-breakdown` already instruct:
- `text_editor:write` to `docs/specs/[feature-name].md`
- `text_editor:write` to `docs/plans/[feature-name].md`

The gap is in **commands**, not skills.

### 3. The test suite is excellent

10,109 lines across 23 test files with clean conftest.py infrastructure. Extending `test_workflow_state.py` (currently 587 lines) with artifact path tests will be straightforward.

### 4. The state infrastructure is well-designed

Atomic writes, path traversal prevention, symlink protection, lock-based concurrent writes, corrupt file handling, and rotation are all battle-tested. The new artifact functions inherit all of this for free by reusing `_safe_write_json` and `_safe_read_json`.

---

## Verification

- [x] Spec fully read (409 lines)
- [x] Plan fully read (736 lines)
- [x] All 4 helper files audited
- [x] All 7 command files audited
- [x] All 7 extensions audited
- [x] State files inspected
- [x] Config inspected
- [x] UI inspected
- [x] 23 test files catalogued
- [x] Skill markdown-documents references checked
- [x] Existing artifact paths verified
- [x] No workdir state directory confirmed
- [x] `workflow_artifacts` grep confirmed zero existing references
