# ADR-001: Skill Enforcement Gate Design

**Date**: 2026-05-30
**Status**: Accepted

## Context

The agent frequently bypassed the skill system, executing `code_execution_tool` or `text_editor` calls without loading a clearly relevant skill first. This undermined the 6-phase lifecycle model — agents would code without specs, debug without `debugging-and-error-recovery`, or build without `incremental-implementation`.

The skill routing rules in the system prompt extension were advisory only. There was no runtime mechanism to detect or correct skill-skip behavior.

## Decision

Implement a **non-blocking enforcement gate** as a `tool_execute_before` extension. The gate:

1. **Intercepts** `code_execution_tool` and `text_editor` calls before execution
2. **Searches** for candidate skills matching the tool call's intent
3. **Checks** whether any candidate is already loaded
4. **In observe mode** (default): logs the gate decision to telemetry, no behavior change
5. **In enforce mode**: runs the utility-model classifier to confirm the match, then appends an in-band corrective warning to `tool_args.message`

The gate never blocks execution. It only appends warnings that the agent can choose to act on.

## Alternatives Considered

### Hard pause / blocking enforcement
- **Pros**: Guarantees skill loading
- **Cons**: Breaks agent flow, causes infinite loops if classifier is wrong, poor UX
- **Rejected**: Too aggressive for a first implementation; user trust requires opt-in

### `nudge()` via tool result injection
- **Pros**: Less invasive than message mutation
- **Cons**: Tool results are not visible to the agent's reasoning in the same way as `tool_args.message`; harder to implement

### Forced `skills_tool:load` rewrite
- **Pros**: Automatically loads the skill
- **Cons**: Modifies tool arguments in a way that could break the agent's intent; unpredictable side effects
- **Rejected**: Too much autonomy in tool mutation

## Consequences

- **Non-blocking**: Agent always proceeds; corrections are advisory
- **Measurable**: Every gate decision is logged to `.a0proj/skill_activations.jsonl` with state (`no_candidate`, `already_loaded`, `should_correct`, `classifier_unavailable`, `error`)
- **User-space only**: No framework changes required; implemented entirely within the plugin's `tool_execute_before` extension
- **Configurable**: `enforcement_mode` can be set to `observe` (default) or `enforce` per-project
- **Cooldown**: `enforcement_correction_cooldown_seconds` prevents repeated warnings for the same skill within a time window
