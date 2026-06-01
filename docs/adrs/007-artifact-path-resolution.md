# ADR-007: Artifact Path Resolution with No-Project Fallback

**Date**: 2026-05-30
**Status**: Accepted

## Context

The a0_agent_skills plugin had two path-related problems:

1. **Hardcoded legacy paths**: Commands like `/spec`, `/plan`, `/build`, `/review`, `/test`, and `/code-simplify` referenced `SPEC.md`, `tasks/plan.md`, and `tasks/todo.md` directly. These paths were scattered across command templates with no central authority, making it impossible to change artifact locations without editing every command.

2. **No-project mode had no state tracking**: `resolve_state_dir()` only worked when a project was selected. Without a project, there was no `.a0/state/` directory, so the entire workflow state system (phase tracking, skill activations, artifact metadata) was unavailable. This meant commands behaved differently depending on whether a project was active — a silent and confusing failure mode.

3. **No approval mechanism**: Specs and plans could be created but had no formal approval state, making it unclear whether a spec was draft or accepted.

## Decision

Add a canonical artifact path resolution layer with no-project fallback:

- **`resolve_visible_root(agent)`**: Returns project root if active, `/a0/usr/workdir` if not
- **`resolve_artifact_paths(agent, slug=None)`**: Central resolver returning all artifact paths (spec, plan, todo, idea, adr, report) using `resolve_visible_root()` + `resolve_state_dir()` under the hood
- **`resolve_state_dir()` updated**: Falls back to `/a0/usr/workdir/.a0_agent_skills/state/` when no project is selected, reads `default_config.yaml.workflow_state_path` instead of hardcoding
- **`discover_feature_slug(agent)`**: Discovers the active feature slug from state or filesystem scan
- **`save_workflow_artifacts()` / `read_workflow_artifacts()`**: Read/write `workflow_artifacts.json` for artifact metadata
- **`mark_artifact_approved()`**: Records approval state with timestamp in artifact metadata
- **Typed artifact events**: `artifact_created`, `artifact_updated`, `approval` event types for persist extension
- **Legacy fallback**: When no slug is set, `resolve_artifact_paths()` returns legacy paths (`SPEC.md`, `tasks/plan.md`, `tasks/todo.md`) for backward compatibility

## Alternatives Considered

### Option A: Keep hardcoded paths, add wrapper functions
- **Pros**: Minimal change, low risk
- **Cons**: Doesn't solve the no-project problem, still requires editing every command for future changes
- **Rejected**: Does not address the root cause — path authority is still fragmented

### Option B: Full artifact registry with lifecycle states
- **Pros**: Complete artifact tracking with active/superseded/completed states
- **Cons**: Over-engineered — no consumer for lifecycle states yet, premature abstraction
- **Rejected**: Deferred (no consumer justifies the complexity)

### Option C: Canonical resolver with legacy fallback (chosen)
- **Pros**: Single source of truth, works in both modes, backward compatible, incremental adoption
- **Cons**: Legacy fallback adds a small amount of conditional logic
- **Chosen**: Right-sized solution for current needs with clean migration path

## Rationale

The resolver pattern centralizes path authority without forcing a breaking change. Legacy paths continue to work when no slug is set, so existing workflows are uninterrupted. New workflows that use `/spec` or `/plan` with slugs get canonical paths automatically.

No-project fallback was essential because `resolve_state_dir()` was the foundation for all workflow state tracking. Without it, the entire phase-aware governance system was disabled outside of project mode — a significant feature gap.

The approval mechanism is deliberately minimal: a boolean flag and timestamp in artifact metadata. No lifecycle states, no invalidation logic, no multi-approver workflows. These can be added when real use cases demand them.

## Consequences

### Positive
- Single source of truth for artifact paths — one function to change instead of N command templates
- No-project mode has full workflow state support (phase tracking, skill activations, artifact metadata)
- Commands are decoupled from path implementation details
- Typed events enable future automation and observability
- Legacy fallback ensures zero breaking changes for existing users

### Negative
- Legacy fallback adds a conditional branch in `resolve_artifact_paths()` — this will be removed once all users migrate to slugged paths
- `workflow_artifacts.json` is another state file to manage — mitigated by using existing `_save_artifact`/`_read_artifact` infrastructure
- Approval is per-artifact, not per-user — no audit trail of who approved what (acceptable for current single-user model)

### Follow-up
- Migrate remaining state reads to use `resolve_artifact_paths()` where applicable
- Consider removing legacy fallback after a deprecation period
- Add artifact lifecycle states when a consumer exists
- Consider multi-approver approval when collaborative workflows are needed
