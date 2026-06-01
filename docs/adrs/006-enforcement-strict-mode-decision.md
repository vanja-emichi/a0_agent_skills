# ADR-006: Enforcement Strict Mode Decision

**Date**: 2026-05-30
**Status**: Deferred

## Context

ADR-001 established the skill enforcement gate as a **non-blocking, advisory-only** mechanism. The gate runs inside `tool_execute_before`, which constrains its design: the Agent Zero framework ignores the hook's return value (`agent.py ~927-935`), so the gate **cannot block execution by returning a Response**. It can only mutate `tool_args` in place or raise an exception.

The original idea doc (`skills-you-cant-skip.md`) identified `InterventionException` — the framework's pause-for-user substrate — as a potential future path for a "strict" enforcement mode that would be truly un-skippable. This was explicitly deferred in ADR-001 as too aggressive for MVP.

The outcome-lift evaluation runner (`tests/run_outcome_lift.py`) now provides empirical data on the advisory approach. Results across 64 eval cases (32 trigger, 32 suppress):

| Metric | Observe | Enforce | Delta |
|--------|---------|---------|-------|
| Overall correct | 68.8% (44/64) | 70.3% (45/64) | +1.6% |
| Trigger-case correct | 53.1% (17/32) | 40.6% (13/32) | −12.5% |
| Suppress-case correct | 84.4% (27/32) | 100.0% (32/32) | +15.6% |

The overall +1.6% lift is modest but positive. However, the decomposition reveals a critical trade-off: the lift comes **entirely from suppress-side improvement** (perfect 100% rejection of should-not-trigger cases), while trigger-side accuracy **regresses by 12.5 percentage points** under enforce mode. The utility-model classifier sometimes rejects valid skill matches that the prefilter alone would have allowed.

## Decision

**Defer strict (`InterventionException`) enforcement mode.** The advisory approach remains the sole enforcement mechanism for the foreseeable future.

Additionally, the enforcement limitation — that the gate is advisory, not hard-blocking — must be stated plainly in user-facing documentation (README) rather than hidden in ADRs.

## Rationale

1. **The framework constraint is unchanged.** The `tool_execute_before` hook still cannot block by returning a Response. `InterventionException` is the only path to a true hard gate, and it was correctly deferred in ADR-001.

2. **The outcome-lift data supports advisory mode, not strict mode.** The +1.6% overall lift is real but modest. More importantly, the trigger-side regression (−12.5pp) means the classifier is not yet reliable enough to justify a hard pause. A strict mode that froze agent execution on a classifier decision would amplify false negatives — blocking the agent from proceeding when it legitimately should — with no opportunity for the agent to self-correct.

3. **Suppress-case accuracy is the genuine win.** Enforce mode achieves 100% accuracy on suppress cases (zero false positives). This means the gate is excellent at *not* interfering when no skill is relevant. This is precisely the behavior you want from an advisory system — it stays out of the way when it should.

4. **InterventionException risk profile is wrong for this stage.** A hard pause for human review:
   - Breaks agent flow in autonomous operation
   - Creates loop risk if the classifier fires repeatedly on the same interaction
   - Requires human intervention, contradicting the self-correction design goal
   - Has no graceful degradation path — a misfire is a full stop, not a nudge

5. **The honest path is documentation, not escalation.** Rather than building a bigger hammer, the plugin should clearly document that enforcement is advisory. Users who need hard gates should be directed to framework-level solutions (e.g., custom tool subclasses that refuse execution), not plugin-level exceptions.

## Consequences

### Accepted

- **Enforcement remains advisory-only.** The gate can nudge, warn, and mutate arguments, but cannot prevent a tool call from executing. This is a permanent constraint given the current framework architecture.
- **Trigger-side classifier accuracy is an open improvement area.** The 40.6% trigger-case accuracy under enforce mode (vs 53.1% observe) indicates the utility-model classifier needs tuning before any consideration of stricter enforcement. Future work should focus on improving classifier precision on trigger cases.
- **Documentation updated.** The README enforcement section now explicitly states the advisory limitation and links to this ADR. Users will not discover this constraint by surprise.
- **`observe` remains the default mode.** The observe-first principle from ADR-001 is reinforced by the data — observe mode has higher trigger-side accuracy and should remain the safe default.

### Deferred

- **`InterventionException`-based strict mode** will not be implemented in the current plugin architecture. If the framework evolves to support hook-level blocking (e.g., honoring a return value from `tool_execute_before`), this decision should be revisited via a new ADR.
- **Trigger-side classifier tuning** is identified as a prerequisite for any future strict-mode consideration. The classifier must achieve ≥70% trigger-case accuracy before strict mode becomes viable.

### Not affected

- The existing `enforce` mode (advisory corrections via arg mutation) continues to function as designed.
- Telemetry, state persistence, phase governance, and skill contracts are unaffected.
- The outcome-lift eval runner (`tests/run_outcome_lift.py`) continues to serve as the canonical measurement tool for enforcement effectiveness.
