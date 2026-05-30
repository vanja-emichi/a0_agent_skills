# TODO: a0_agent_skills Workflow Governance + Durability

> Generated from:
> - `/a0/usr/projects/a0_agent_skills/docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `/a0/usr/projects/a0_agent_skills/docs/plans/a0-agent-skills-workflow-governance-plan.md`

## Current decisions

- `a0_agent_skills` owns **workflow governance** and **workflow durability**
- `_permissions` owns safety governance
- `_tracing` owns cross-harness tracing/eval infrastructure
- Existing `skill-enforcement-gate` docs remain **Phase 1 slice** docs
- Utility model is the classifier path
- Observe-first remains the default rollout philosophy
- Durable workflow state belongs in the plugin, not mostly deferred out of it

## Phase 1: Workflow Governance Slice 1

### Task 1: Ship current skill-enforcement gate slice
- [ ] Implement config surface
- [ ] Implement `helpers/skill_match.py`
- [ ] Extend telemetry
- [ ] Ship observe-mode gate
- [ ] Ship enforce-mode corrective warning
- [ ] Add thin eval harness
- [ ] Verify focused slice docs remain accurate

### Phase 1 checkpoint
- [ ] Slice-1 spec, plan, and todo are implemented
- [ ] Observe-first gate is real
- [ ] Outcome telemetry exists
- [ ] Thin eval harness exists

---

## Phase 2: Durable workflow state

### Task 2: Add workflow-state helper
- [ ] Create plugin-owned workflow-state helper
- [ ] Define `.a0proj/state/` file schema
- [ ] Support active plan
- [ ] Support active goal
- [ ] Support current phase
- [ ] Support loaded skills
- [ ] Support checkpoints
- [ ] Support progress log
- [ ] Support handoff artifact

### Task 3: Add rehydration support
- [ ] Reattach loaded skills after context turnover
- [ ] Reattach current phase after context turnover
- [ ] Reattach active plan after context turnover
- [ ] Reattach active goal after context turnover
- [ ] Safe no-op when state files do not exist

### Task 4: Add progress and checkpoint behavior
- [ ] Append progress events durably
- [ ] Update checkpoints durably
- [ ] Document handoff/progress usage

### Phase 2 checkpoint
- [ ] Workflow state survives beyond prompt context
- [ ] Long-running work can be resumed cleanly
- [ ] Plugin now owns durable workflow artifacts

---

## Phase 3: Phase-aware workflow governance

### Task 5: Add explicit phase model
- [ ] Define durable phase states
- [ ] Define phase transitions
- [ ] Make current phase queryable by plugin logic

### Task 6: Make enforcement phase-aware
- [ ] Use phase state in the enforcer
- [ ] Use checkpoint state to avoid repeated corrections
- [ ] Keep observe-first behavior intact
- [ ] Do not add hard human-intervention mode in MVP

### Phase 3 checkpoint
- [ ] Enforcement is informed by workflow phase
- [ ] Enforcement is less stateless and less repetitive

---

## Phase 4: Skill registry strengthening

### Task 7: Add stronger skill contracts
- [ ] Define contract shape
- [ ] Upgrade representative engineering skills first
- [ ] Include inputs
- [ ] Include produced artifacts
- [ ] Include verification expectations

### Task 8: Add dependency graph / next-skill metadata
- [ ] Define next-skill relationships for core lifecycle skills
- [ ] Add dependency metadata where useful
- [ ] Document lifecycle chaining

### Task 9: Expand eval coverage
- [ ] Keep activation fixtures
- [ ] Add workflow-order fixtures
- [ ] Keep runner lightweight and plugin-local

### Phase 4 checkpoint
- [ ] Core skills have stronger contracts
- [ ] Lifecycle dependencies are explicit
- [ ] Eval coverage measures workflow quality better

---

## Phase 5: Final integration

### Task 10: Unify roadmap docs and rollout guidance
- [ ] Keep umbrella docs and slice docs consistent
- [ ] Update README for current shipped slice vs future roadmap
- [ ] Keep observe-first rollout guidance explicit
- [ ] Verify no roadmap/shipped-behavior contradiction remains

### Final release gate
- [ ] Broad roadmap docs are in place
- [ ] Narrow slice docs remain valid as Phase-1 references
- [ ] Plugin README is consistent with actual shipped behavior
- [ ] Ready to implement in dependency order

---

## Notes

- Planning/spec/docs live in **`/a0/usr/projects/a0_agent_skills`**
- Implementation lives in **`/a0/usr/plugins/a0_agent_skills`**
- Do not confuse the umbrella roadmap with the current shipped slice
- Do not broaden scope into `_permissions` or `_tracing`
