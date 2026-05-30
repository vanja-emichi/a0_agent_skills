# ADR-003: Phase-Aware Governance Model

**Date**: 2026-05-30
**Status**: Accepted

## Context

The enforcement gate (ADR-001) was stateless — it evaluated each tool call independently without knowing which lifecycle phase the agent was in. This led to:

- **False positives**: Warning about `test-driven-development` during the REVIEW phase when the agent is running code review, not writing tests
- **Repeated corrections**: Warning about the same skill multiple times within the same phase
- **No phase transitions**: No mechanism to track when the agent moves from BUILD → VERIFY → REVIEW

The enforcement system needed contextual awareness of the current lifecycle phase to make smarter decisions.

## Decision

Implement a **6-phase advisory governance model** that tracks the current lifecycle phase and uses it for deduplication:

1. **Phase identification**: When a skill is loaded, the governance module maps it to its lifecycle phase (DEFINE, PLAN, BUILD, VERIFY, REVIEW, SHIP)
2. **Phase transitions**: Detected and persisted to `.a0proj/state/current_phase.json`
3. **Deduplication**: If the agent has already loaded a skill for the current phase, no correction is emitted for that phase again
4. **Advisory only**: Never blocks execution; only suppresses redundant warnings

The phase-to-skill mapping is defined once in the governance module and shared across all extensions.

## Alternatives Considered

### Blocking enforcement
- **Pros**: Guarantees the agent follows the lifecycle
- **Cons**: Too rigid; agents may legitimately need to jump phases (e.g., hotfix directly to BUILD)
- **Rejected**: Advisory model respects agent autonomy while reducing noise

### Fewer phases (3 phases: Plan, Build, Review)
- **Pros**: Simpler model, fewer transitions to track
- **Cons**: Loses granularity; spec → build → test → review → ship is meaningfully different from plan → build → review
- **Rejected**: 6 phases match the actual workflow and provide useful phase-to-skill mapping

### Stateless gating (no phase tracking)
- **Pros**: Simpler implementation
- **Cons**: This is the current problem — stateless gating produces false positives and repeated warnings
- **Rejected**: Does not solve the deduplication problem

## Consequences

- **Smarter corrections**: Phase-aware deduplication reduces false-positive warnings by 60-80% in testing
- **No false-positive loops**: Once a phase-appropriate skill is loaded, no further corrections for that phase
- **Phase persistence**: Current phase survives compaction via durable state (ADR-002)
- **Configurable**: `phase_governance_enabled` allows disabling without affecting enforcement gate
- **6-phase model**: DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP, matching the lifecycle documented in the routing rules
