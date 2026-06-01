# Spec: Live Harness Persistence Fix and Enforce-Mode Proof

## Objective
Patch the a0_agent_skills workflow-state persistence bug so skill loads persist for both method-based and action-based skills_tool invocations, then prove a real enforce-mode corrective warning path using a stronger trigger without changing infection_check.

## Tech Stack
- Python plugin extension code in `/a0/usr/plugins/a0_agent_skills`
- Agent Zero tools: `skills_tool`, `text_editor`, `code_execution_tool`, `call_subordinate`
- Project evidence/logs in `/a0/usr/projects/a0_agent_skills/.a0proj`

## Commands
- Read file: `sed -n '1,220p' /a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/_10_persist_workflow_state.py`
- Verify persisted state: `ls -l /a0/usr/projects/a0_agent_skills/.a0proj/state && cat /a0/usr/projects/a0_agent_skills/.a0proj/state/loaded_skills.json`
- Inspect telemetry: `tail -n 20 /a0/usr/projects/a0_agent_skills/.a0proj/skill_activations.jsonl`

## Project Structure
- Plugin code: `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/`
- Project docs: `/a0/usr/projects/a0_agent_skills/docs/`
- Evidence/state: `/a0/usr/projects/a0_agent_skills/.a0proj/state/`
- Telemetry: `/a0/usr/projects/a0_agent_skills/.a0proj/skill_activations.jsonl`

## Code Style
Keep the fix surgical: preserve existing structure, add the minimal conditional needed, and remove temporary debug-only logging if present.

## Testing Strategy
- Reproduce with a real `skills_tool` load and verify persisted files exist and contain the loaded skill.
- Trigger enforce-mode evaluation with a stronger code/test/TDD wording in isolated context, then make a harmless `code_execution_tool` call and inspect telemetry plus any in-band warning.

## Boundaries
- Always: read before patching, use actual tool calls, verify with real filesystem/log evidence.
- Ask first: broad refactors, config changes beyond requested scope.
- Never: enable infection_check, make unrelated cleanup, leave debug-only instrumentation behind.

## Success Criteria
1. `_10_persist_workflow_state.py` persists loaded skills for both `skills_tool:load` and `skills_tool` with `action=load`.
2. After a real `skills_tool action=load skill_name='spec-driven-development'`, `loaded_skills.json` and `handoff.md` exist under `.a0proj/state` and `loaded_skills.json` includes the skill name.
3. Telemetry shows an enforce-mode `gate_decision` for the stronger proof step, preferably `state='should_correct'`.
4. Final report states PASS/FAIL for Task A and Task B with evidence.

## Open Questions
- None blocking; user provided exact target file, root cause, config constraints, and acceptance criteria.
