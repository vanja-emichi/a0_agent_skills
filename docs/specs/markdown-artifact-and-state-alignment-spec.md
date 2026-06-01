# Spec: Markdown Artifact and Workflow State Alignment for a0_agent_skills

## Assumptions

1. `a0_agent_skills` should support both **project mode** and **no-project workdir mode**.
2. In **project mode**, primary workflow documents should be visible project artifacts, not hidden machine metadata.
3. In **no-project mode**, the active workspace is `/a0/usr/workdir`, and we want durable plugin tracking there too, but **without inventing a fake `.a0proj` project**.
4. `markdown-documents` should be treated as a **companion skill** for Markdown-producing workflows, not as a globally always-on enforced skill.
5. Existing legacy paths like `SPEC.md`, `tasks/plan.md`, and `tasks/todo.md` may still exist and need compatibility handling.

## Objective

Align `a0_agent_skills` artifact generation, storage, and tracking with Agent Zero workspace conventions.

The plugin should:

- create and update phase documents using the proper Markdown workflow,
- save human-facing Markdown artifacts in visible workspace locations,
- store machine state and active artifact pointers in the right state area,
- behave correctly both when a project is selected and when the user is working only in the general workdir,
- keep slash commands, skills, and runtime state conventions internally consistent.

## Problem Statement

The current port has conflicting conventions:

- local skills use feature-scoped paths like `docs/specs/[feature-name].md` and `docs/plans/[feature-name].md`,
- slash commands still hardcode legacy singleton paths such as `SPEC.md` and `tasks/plan.md`,
- workflow state currently tracks phase/progress/loaded skills but not the active Markdown artifact set as first-class state,
- no-project chats do not currently get an equivalent durable plugin state fallback in workdir.

This causes confusion about where specs, plans, todos, ADRs, review reports, and related Markdown artifacts should live and how later commands should find them.

## Scope

This spec covers:

- Markdown artifact path policy for project and no-project modes
- integration of `markdown-documents` into relevant workflows
- state tracking of active artifact paths
- slash command and skill alignment
- backward compatibility for older path conventions

This spec does **not** implement the changes directly.

## Tech Stack

- Agent Zero plugin system
- `a0_agent_skills` plugin
- `text_editor` tool for Markdown creation and patching
- `markdown-documents` skill as the standard Markdown writing/editing workflow
- existing workflow-state persistence and rehydration helpers under `.a0proj/state`

## Commands

### Development
- Run Agent Zero as currently configured for local development
- Use existing plugin and test workflows in this repository

### Verification
- Run focused plugin tests after changes
- Add/extend tests covering path resolution, state fallback, command output paths, and rehydration

### Relevant command behaviors to update
- `/spec`
- `/plan`
- `/build`
- `/review`
- `/code-simplify`
- any workflow that writes ADRs, reports, or intent documents

## Project Structure

### Canonical visible artifact locations

#### When a project is selected
- `docs/ideas/<slug>.md`
- `docs/intent/<slug>.md`
- `docs/specs/<slug>-spec.md`
- `docs/plans/<slug>-plan.md`
- `tasks/<slug>-todo.md`
- `docs/adrs/ADR-<n>-<slug>.md`
- `docs/reviews/<slug>.md`
- `docs/reports/<slug>-<phase>.md`

#### When no project is selected
Use the same visible structure, rooted at `/a0/usr/workdir`:
- `/a0/usr/workdir/docs/ideas/<slug>.md`
- `/a0/usr/workdir/docs/intent/<slug>.md`
- `/a0/usr/workdir/docs/specs/<slug>-spec.md`
- `/a0/usr/workdir/docs/plans/<slug>-plan.md`
- `/a0/usr/workdir/tasks/<slug>-todo.md`
- `/a0/usr/workdir/docs/adrs/ADR-<n>-<slug>.md`
- `/a0/usr/workdir/docs/reviews/<slug>.md`
- `/a0/usr/workdir/docs/reports/<slug>-<phase>.md`

### Canonical machine-state locations

#### When a project is selected
Use project state under:
- `.a0proj/state/`

#### When no project is selected
Add a plugin-local fallback under workdir:
- `/a0/usr/workdir/.a0_agent_skills/state/`

This fallback is **plugin-local state**, not a fake project.

## Artifact State Model

Add first-class tracking for active workflow artifacts.

### New or expanded state record
A state file such as `workflow_artifacts.json` should track:

- `feature_slug`
- `idea_path`
- `intent_path`
- `spec_path`
- `plan_path`
- `todo_path`
- `review_report_path`
- `ship_report_path`
- `adr_paths`
- `phase`
- `updated_at`
- approval/confirmation markers where applicable

### Relationship to existing state
`plan_path` is already partially tracked in `active_plan.json` and rendered in `handoff.md` via `workflow_state.py:356`. The new `workflow_artifacts.json` should be a **standalone supplement** that expands tracking to all artifact types — it must not merge into or replace `active_plan.json`, `active_goal.json`, or `loaded_skills.json`.

### Purpose
This lets the harness answer:
- what is the active spec?
- what is the active plan?
- which todo file should `/build` consume?
- which artifact should be shown in handoff/rehydration after compaction?

## Feature Slug Discovery

The feature slug is derived from the first artifact filename created:
- When `/spec` creates `docs/specs/my-feature-spec.md`, the slug `my-feature` is extracted
- The slug is stored in `workflow_artifacts.json`
- Subsequent commands (`/plan`, `/build`, `/review`) read the slug from state
- The slug can be overridden via a command argument (e.g., `/plan --slug existing-feature`)
- If no slug exists and no override is given, the path resolver prompts the user

## Event Model

Progress events in `progress_log.jsonl` should be typed:

```json
{"event": "artifact_created", "artifact_type": "spec", "path": "docs/specs/foo-spec.md", "slug": "foo", "timestamp": "..."}
{"event": "artifact_updated", "artifact_type": "plan", "path": "docs/plans/foo-plan.md", "slug": "foo", "timestamp": "..."}
{"event": "phase_change", "from": "DEFINE", "to": "PLAN", "timestamp": "..."}
{"event": "approval", "artifact_type": "spec", "slug": "foo", "decision": "approved", "timestamp": "..."}
{"event": "artifact_lifecycle", "artifact_type": "spec", "slug": "old-feature", "status": "superseded", "timestamp": "..."}
```

This enables replay, audit, debugging, and compaction quality.

## Approval Model

Approval is user-confirmed via command:
- `/spec --approve` marks the active spec as approved
- `/plan --approve` marks the active plan as approved
- Approval is recorded as a typed event with timestamp
- If an artifact changes materially after approval, the approval is invalidated
- The model cannot self-approve; only the user can approve
- Approval state is persisted in `workflow_artifacts.json` and rehydrated after compaction

## Artifact Lifecycle

Artifacts have lifecycle states:
- `active` — currently in use
- `superseded` — replaced by a newer version
- `completed` — the feature is shipped and the artifact is historical

Lifecycle transitions:
- When a new spec is created for the same feature, the old spec becomes `superseded`
- When `/ship` completes, all feature artifacts become `completed`
- Lifecycle changes are recorded as typed events
- Only `active` artifacts are included in handoff/rehydration

## Required Behavioral Changes

### 1. Use `markdown-documents` for Markdown-producing workflows
The following workflows should explicitly load or invoke the Markdown document workflow when creating/editing persistent Markdown artifacts:

- `spec-driven-development`
- `planning-and-task-breakdown`
- `idea-refine`
- `documentation-and-adrs`
- `interview-me` when saving intent
- `code-review-and-quality` when writing review reports
- `shipping-and-launch` when writing ship reports

### 2. Treat `markdown-documents` as a companion skill, not a globally enforced skill
`markdown-documents` should not be always-on for every task.
It should be:
- automatically loaded by document-producing commands, or
- explicitly loaded by routing logic when a persistent Markdown artifact is being created or edited.

### 3. Standardize path resolution
Extend `helpers/workflow_state.py` with artifact path resolution functions. Do NOT create a separate helper file — artifact paths are state, and `workflow_state.py` already owns all state I/O (`resolve_state_dir`, `_save_artifact`/`_read_artifact`, `_ensure_dir`, `_safe_read_json`, `_safe_write_json`, `_state_path`). Add the following functions under a clear `# --- Artifact Path Resolution ---` section:

```python
def resolve_visible_root(agent) -> str | None:       # project root or workdir
def resolve_artifact_paths(agent, slug=None) -> dict:  # canonical artifact paths
def discover_feature_slug(agent) -> str | None:        # find active slug
def save_workflow_artifacts(agent, data: dict) -> str | None:
def read_workflow_artifacts(agent) -> dict | None:
```

The resolver:
- detects project vs no-project mode,
- picks the correct visible root (`project root` or `workdir`),
- returns canonical artifact paths for the active feature slug,
- returns the correct state root (`.a0proj/state` or `workdir/.a0_agent_skills/state`),
- reads `default_config.yaml.workflow_state_path` instead of hardcoding `.a0proj/state`.

#### Error cases
- No slug set and no legacy files exist → prompt user to run `/spec` or specify `--slug`
- Multiple matching specs found → return list, ask user to disambiguate
- Target directory doesn't exist → auto-create with `mkdir -p`
- File exists but is corrupted or empty → log warning, return safe default, do not crash
- No project and no workdir fallback → fall back to workdir, log info message

### 4. Align commands and skills
Commands and skills must stop disagreeing about file locations.

Examples:
- `/spec` should no longer hardcode `SPEC.md`
- `/plan` should no longer hardcode `tasks/plan.md` and `tasks/todo.md`
- skills that already describe `docs/specs/*.md` and `docs/plans/*.md` should remain aligned with command output
- downstream commands like `/build` should resolve the active todo/spec path from state first

### 5. Handoff and rehydration must include active artifact paths
Workflow rehydration should include the current artifact set so the agent can recover after compaction or session changes.

### 6. No-project rehydration fallback
The rehydration extension (`_67_reattach_workflow_state.py`) must check `workdir/.a0_agent_skills/state/` when no project is active. Currently it only resolves through `.a0proj/state`. The fallback path should mirror the project path logic.

### 7. Align handoff format with agents-best-practices
The `handoff.md` generation should follow the compaction handoff format from agents-best-practices, explicitly including:
- Current objective
- User constraints
- Active plan and goal
- Approval state
- Resources inspected
- Artifacts created or changed (with full paths)
- Tool calls and key results
- Errors and fixes attempted
- Open questions
- Pending tasks
- Next recommended step

## Code Style

Use small, explicit helpers rather than scattering path logic across commands and extensions.

Example preferred pattern:

```python
artifact_paths = workflow_artifacts.resolve_paths(
    context=self.agent.context,
    feature_slug=feature_slug,
)

spec_path = artifact_paths.spec_path
state_root = artifact_paths.state_root
```

Rules:
- one source of truth for artifact paths
- no duplicated path-joining logic in multiple commands
- no hardcoded legacy singleton paths except in compatibility fallback logic
- preserve existing fail-safe behavior in state helpers

## Testing Strategy

### Unit tests
Add or extend tests for:
- project-mode path resolution
- no-project workdir path resolution
- state-root resolution in both modes
- compatibility fallback when only legacy files exist
- artifact pointer persistence and reload

### Integration tests
Add tests that prove:
- `/spec` writes to the resolved spec path
- `/plan` writes to the resolved plan/todo paths
- active artifact pointers are written to state
- handoff/rehydration exposes active artifact paths after compaction
- `markdown-documents` is invoked/loaded for Markdown artifact workflows

### Regression tests
Protect against:
- accidental recreation of `workdir/.a0proj`
- slash commands drifting back to `SPEC.md` hardcoding without fallback logic
- no-project mode losing plugin-local state entirely

## Boundaries

### Always
- Save primary human-facing Markdown artifacts in visible workspace paths
- Keep machine tracking separate from human-facing docs
- Use a shared path resolver
- Use `markdown-documents` for persistent Markdown artifact creation/editing
- Keep artifact paths durable and rehydratable

### Ask first
- Migrating existing legacy files automatically
- Renaming or moving already-committed docs in existing projects
- Changing slash-command output paths in a way that breaks external automation

### Never
- Create a fake `.a0proj` under workdir to simulate a project
- Store primary user-facing specs/plans/todos only in hidden machine-state folders
- Make `markdown-documents` globally always-on for all tasks
- Maintain conflicting path conventions between commands and skills

## Success Criteria

1. There is one canonical artifact path policy for both workdir mode and project mode.
2. No-project mode writes visible Markdown artifacts into `/a0/usr/workdir/docs/...` and `/a0/usr/workdir/tasks/...`.
3. Project mode writes visible Markdown artifacts into `<project>/docs/...` and `<project>/tasks/...`.
4. Project mode stores machine state in `.a0proj/state/...`.
5. No-project mode stores plugin-local machine state in `/a0/usr/workdir/.a0_agent_skills/state/...`.
6. `/spec` and `/plan` use resolved canonical paths instead of conflicting hardcoded paths.
7. The active artifact set is persisted and rehydrated.
8. `markdown-documents` is consistently used as the companion workflow for persistent Markdown artifacts.
9. Legacy `SPEC.md` and `tasks/plan.md` style files still have compatibility handling until migration is complete.
10. Tests exist for both project and no-project path behavior.

## Open Questions


## Research Findings

The following findings are from DeepWiki queries against `agent0ai/agent-zero` and `addyosmani/agent-skills`, plus local codebase inspection.

### RF1: Upstream uses singleton files, not feature-scoped

Upstream `addyosmani/agent-skills` is designed around a single active `SPEC.md`, `tasks/plan.md`, and `tasks/todo.md` per repository. There is no upstream mechanism for multiple concurrent feature-scoped specs/plans. Discovery is by hardcoded expected locations only.

**Our decision:** Keep feature-scoped `docs/specs/<slug>-spec.md` and `docs/plans/<slug>-plan.md` as the primary model (our port's improvement), but maintain legacy singleton paths as compatibility fallbacks.

### RF2: Only `/ship` reads specs currently — `/build`, `/review`, `/test` do not

Local code inspection shows that `/ship` (ship.py, 332 lines) actively reads and parses spec sections (Project Structure, Objective, Success Criteria) via `_find_spec`, `_parse_project_structure`, and `_read_spec_context`. In contrast, `/build`, `/review`, and `/test` do not reference the spec at all.

**Our decision:** Keep spec-reading logic in `ship.py` for now. Future commands (`/build`, `/review`, `/test`) should consume the active spec by reading the resolved `spec_path` from `workflow_artifacts.json` and parsing it directly, rather than through a shared helper module. This avoids creating `helpers/spec_reader.py` until the duplication cost clearly warrants extraction.

### RF3: Promptinclude can auto-inject specs/plans

The `_promptinclude` plugin scans for configurable `name_pattern` (default `*.promptinclude.md`) with `max_depth=10`, `max_file_tokens=2000`, `max_total_tokens=8000`, `max_file_count=50`. Two integration options:

1. Rename key artifacts as `*.promptinclude.md` for zero-code pickup
2. Extend plugin config with additional patterns like `docs/specs/*.md`

The 8000-token budget is modest for large specs. For now, keep specs/plans out of promptinclude (they can be large) and instead rely on explicit context loading via `context-engineering` and state-based artifact discovery.

### RF4: Knowledge system auto-indexes `.a0proj/knowledge/` but is currently empty

The FAISS-based memory system auto-indexes markdown files in `.a0proj/knowledge/` for semantic recall. Currently all knowledge subdirectories (`main/`, `fragments/`, `solutions/`) are empty.

**Our decision:** Do not save specs/plans to knowledge (they are already discoverable via state pointers). Instead, consider saving high-level summaries or decision fragments there for semantic recall across sessions.

### RF5: No formal companion-skill system upstream

Upstream `agent-skills` has no auto-loading companion-skill mechanism. Composition is always explicit via commands or lifecycle sequences. The `markdown-documents` companion pattern is an Agent Zero port innovation.

**Our decision:** Keep `markdown-documents` as a documented convention in commands and the `using-agent-skills` skill, not as runtime enforcement.

### RF6: Upstream hooks are Claude-specific, validate-skills.js is portable

Upstream hooks (`hooks.json`) use `${CLAUDE_PLUGIN_ROOT}` and are Claude Code-specific. `validate-skills.js` checks YAML frontmatter, required sections, description length, and cross-skill references.

**Our decision:** Skip porting hooks. Consider porting `validate-skills.js` to Python for CI validation of SKILL.md files in a future iteration.

### RF7: Workdir has no existing plugin state

Workdir (`/a0/usr/workdir`) contains only analysis/research artifacts from prior sessions. No `.a0_agent_skills/` directory, no `*.promptinclude.md` files, no plugin state.

**Our decision:** For no-project mode, plugin state should use `/a0/usr/workdir/.a0_agent_skills/state/` to avoid collision with user files. This is a new directory, not present today.

### RF8: `idea-refine.sh` is trivial

The upstream `idea-refine.sh` script is 12 lines of `mkdir -p docs/ideas` + JSON status output. No special integration needed.

**Our decision:** Agent Zero agents can `mkdir -p docs/ideas` via `code_execution_tool` and write output via `text_editor:write` directly. No script port needed.

## Resolved Open Questions

Based on the research findings:

1. **Should `/spec` support root-level `SPEC.md`?** Yes, as a compatibility fallback. The path resolver should check for an active feature-scoped spec first, then fall back to `SPEC.md` if it exists.
2. **Should todo files always be feature-scoped?** Feature-scoped should be the primary model. Singleton `tasks/todo.md` remains supported as a legacy fallback.
3. **Should artifact state track approvals?** Yes. Add `approved: {spec: bool, plan: bool}` to `workflow_artifacts.json`. This is lightweight and useful for `/ship`.
4. **Should reports always be persisted?** Only when explicitly requested by the user or when a `/review` or `/ship` command is invoked. Not every debug cycle needs a persisted report.
5. **Should legacy projects get a migration command?** Not in the initial implementation. Document the migration path in the plugin README instead.

## Remaining Open Questions

- Should `promptinclude` be extended with additional patterns for active specs/plans in a future iteration?
- Should spec summaries be auto-saved to `.a0proj/knowledge/` for semantic recall?
- Should `validate-skills.js` be ported to Python for Agent Zero CI?
