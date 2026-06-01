# Artifact Inference Fix Spec

## Goal
Verify that the fix for the tool_execute_after early-exit bug works correctly.

## Scope
- Spec write should set goal and DEFINE phase
- Plan write should advance to PLAN phase
- Todo write should extract current task

## Acceptance Criteria
1. handoff.md updates after each artifact write
2. active_goal.json slug matches spec filename
3. current_phase.json reflects correct phase transitions