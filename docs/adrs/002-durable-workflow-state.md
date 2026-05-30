# ADR-002: Durable Workflow State via File System

**Date**: 2026-05-30
**Status**: Accepted

## Context

Agent Zero compacts conversation history when the context window fills up. During long engineering workflows (spec → plan → build → test → review → ship), the agent could lose track of its active plan, current phase, loaded skills, and progress after compaction. This led to:

- Agents forgetting which phase they were in
- Re-loading already-loaded skills (wasting context budget)
- Losing the task plan mid-implementation
- No handoff capability between sessions

The workflow governance model requires durable state that survives context compaction and session boundaries.

## Decision

Persist workflow state to the file system in `.a0proj/state/` using atomic JSON writes. Seven artifacts are persisted:

| Artifact | File | Purpose |
|----------|------|----------|
| Active plan | `active_plan.json` | Current task plan with status |
| Active goal | `active_goal.json` | Current high-level goal |
| Current phase | `current_phase.json` | Lifecycle phase (DEFINE→SHIP) |
| Loaded skills | `loaded_skills.json` | Skills currently in context |
| Checkpoints | `checkpoints.json` | Named save points |
| Progress log | `progress_log.jsonl` | Append-only event log |
| Handoff | `handoff.md` | Human-readable summary |

State is written via `tool_execute_after` extensions after skill loads and phase transitions. State is rehydrated via a `message_loop_prompts_after` extension that reads all files and appends a consolidated context block to the agent's prompt.

## Alternatives Considered

### Database (SQLite)
- **Pros**: Queryable, structured, transactional
- **Cons**: Adds a dependency, requires schema management, harder to inspect/debug manually, overkill for key-value state
- **Rejected**: File-based approach is simpler and sufficient for the volume of data

### Memory-only (no persistence)
- **Pros**: Zero I/O overhead, simplest implementation
- **Cons**: State lost on compaction — the exact problem we're solving
- **Rejected**: Does not solve the core problem

### Framework state API
- **Pros**: First-class integration with Agent Zero
- **Cons**: Requires framework changes, not available in current Agent Zero version, coupling to framework internals
- **Rejected**: Cannot modify framework; plugin must be self-contained

## Consequences

- **Survives compaction**: State persists across context window resets and session restarts
- **Project-scoped**: State lives in `.a0proj/state/` relative to the project, so different projects have independent state
- **Simple**: JSON files are easy to inspect, debug, and manually edit if needed
- **Atomic writes**: Uses write-to-temp-then-rename pattern to prevent corruption on crash
- **No framework changes**: Entirely plugin-side via standard extension points
- **Rehydration**: After compaction, the agent sees a consolidated context block with all prior state
- **Progress rotation**: `max_progress_entries` caps the JSONL log to prevent unbounded growth
