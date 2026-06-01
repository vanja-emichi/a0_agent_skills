# Implementation Plan: Live Harness Persistence Fix and Enforce Proof

## Overview
Apply a surgical fix to the workflow-state persistence extension so it recognizes both method-based and action-based skill loads, remove investigation-only debug logging from that file, then verify persistence and enforcement telemetry with live tool calls.

## Architecture Decisions
- Keep the change local to `_10_persist_workflow_state.py`.
- Detect skill loads via a single boolean covering both `skills_tool:load` and `tool_name='skills_tool'` with `action='load'`.
- Remove temporary `_append_debug` instrumentation rather than leaving dormant debug code behind.

## Task List

### Phase 1: Patch
- [ ] Task 1: Read and surgically patch `_10_persist_workflow_state.py`
  - Acceptance: file supports both skill-load forms and no temp debug helper/calls remain
  - Verify: reread relevant sections and confirm conditional logic + removed debug code

### Checkpoint: Patch
- [ ] Source inspection shows only the intended logic change and debug cleanup

### Phase 2: Prove persistence
- [ ] Task 2: Trigger a real `skills_tool action=load skill_name='spec-driven-development'`
  - Acceptance: `.a0proj/state/loaded_skills.json` and `handoff.md` exist; loaded skill appears in JSON
  - Verify: `ls`, `cat`

### Phase 3: Prove enforce-mode correction path
- [ ] Task 3: In an isolated subordinate context, use strong bugfix/TDD wording without preloading TDD, then call harmless `code_execution_tool`
  - Acceptance: telemetry records enforce-mode `gate_decision`; preferred state `should_correct`
  - Verify: subordinate in-band result plus `tail` of `skill_activations.jsonl`

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Extension code not reloaded in current process | Medium | Verify via live behavior and explain if runtime still uses cached code |
| Strong trigger still misses matcher | Medium | Use explicit bugfix/TDD/test-first wording in isolated subordinate context |

## Open Questions
- None blocking; proceed with live verification and report exact observed behavior.
