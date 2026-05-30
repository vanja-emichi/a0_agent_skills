# TODO: a0_agent_skills Managed Fork Alignment

> Generated from:
> - `/a0/usr/projects/a0_agent_skills/docs/specs/managed-fork-alignment-spec.md`
> - `/a0/usr/projects/a0_agent_skills/docs/plans/managed-fork-alignment-plan.md`

## Current decisions

- `/ship` stays **parallel fan-out**
- telemetry stays **enabled by default**
- hooks use **selective porting + documented omission**
- parity tooling comes **before** broad drift reduction
- parity enforcement starts **report-only**

## Phase 1: Ship safety & public contract — COMPLETE ✅

- [x] Tasks 1–4: manifest, README, sanitization, /ship contract, contract tests
- [x] Full suite: **243 passed, 44 skipped, 0 failed**

---

## Phase 2: Parity infrastructure — COMPLETE ✅

- [x] Tasks 5–7: parity report script, parity tests, surface mapping doc
- [x] Full suite: **259 passed, 44 skipped, 0 failed**

---

## Phase 3: Shared skill alignment — COMPLETE ✅

### Batch 1: Planning/meta (5 skills)
- [x] interview-me — clean port, no changes needed
- [x] spec-driven-development — added context-engineering load command
- [x] planning-and-task-breakdown — clean port, no changes needed
- [x] idea-refine — re-adopted How It Works + Philosophy sections
- [x] using-agent-skills — re-adopted 4 missing sections (Core Behaviors, Failure Modes, Skill Rules, Lifecycle Sequence)

### Batch 2: Implementation-core (5 skills)
- [x] incremental-implementation — clean port
- [x] test-driven-development — restored One Assertion Per Concept, browser table rows, security boundaries
- [x] source-driven-development — full rebase: source hierarchy, citation rules, conflict detection
- [x] doubt-driven-development — clean port
- [x] context-engineering — full rebase: 5-layer stack, trust levels, confusion management, packing strategies

### Batch 3: UI/API/debug (4 skills)
- [x] frontend-ui-engineering — restored keyboard accessibility, AI Defaults rows
- [x] api-and-interface-design — restored validation lists, diamond dependency
- [x] browser-testing-with-devtools — restored security rules
- [x] debugging-and-error-recovery — full rebase: decision trees, triage, security section

### Batch 4: Review/delivery (9 skills)
- [x] code-review-and-quality — restored Review Speed, Handling Disagreements, Honesty in Review
- [x] code-simplification — restored React/JSX, TypeScript examples
- [x] security-and-hardening — restored npm audit Key Questions, file extension warning
- [x] performance-optimization — restored RUM vs Synthetic, hero image, symptom tables
- [x] shipping-and-launch — restored Error Reporting, rollback line
- [x] git-workflow-and-versioning — restored Save Point Pattern, Change Summaries, Worktrees
- [x] ci-cd-and-automation — restored Feeding CI Failures Back to Agents, Feature Flags lifecycle
- [x] documentation-and-adrs — restored Documentation for Agents section
- [x] deprecation-and-migration — restored Churn Rule, Zombie Code, core principles

### Phase 3 checkpoint — PASSED ✅

- [x] Full suite: **261 passed, 42 skipped, 0 failed**
- [x] All 23 skills reviewed and restored
- [x] Enforcement language (MUST/NEVER/MUST NOT) consistent across all skills

---

## Phase 4: Hooks and final verification — COMPLETE ✅

- [x] **Task 12: Audit upstream hooks and define A0-native hook policy**
- [x] **Task 13: Implement selected hook replacements or explicit documented stubs**
- [x] **Task 14: Final verification pass and parity refresh**

### Final release gate

- [x] Focused regression tests pass
- [x] Parity report runs successfully
- [x] Managed-fork docs and contract docs are internally consistent
- [x] No contradiction remains around `/ship`, telemetry, skill count, or hook policy

---

## Notes

- Keep changes minimal, explicit, and verified after each task.
