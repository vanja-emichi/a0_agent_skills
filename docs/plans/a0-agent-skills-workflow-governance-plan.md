# Implementation Plan: a0_agent_skills Workflow Governance + Durability

> Generated from spec `docs/specs/a0-agent-skills-workflow-governance-spec.md`.

## Overview

This plan broadens `a0_agent_skills` from a skill-routing and telemetry plugin into a **workflow-governance and workflow-durability layer**.

The roadmap is organized into four capability tracks:

1. **Skill enforcement** — make workflow harder to skip
2. **Workflow durability** — persist and resume plan/goal/progress state
3. **Phase-aware orchestration** — know what phase the agent is in and what should happen next
4. **Skill-registry strengthening** — contracts, dependency graph, evals, and outcome telemetry

## Architecture Decisions

- The existing skill-enforcement-gate documents become **Slice 1** of this larger roadmap.
- Durable workflow state is owned by `a0_agent_skills`, not deferred out of the plugin.
- State persists in `.a0proj/state/` as JSON / JSONL / Markdown files.
- The utility model is the classifier path for ambiguous enforcement decisions.
- Self-correction remains **in-band**.
- Observe-first remains the rollout philosophy across new enforcement behaviors.

## Task List

### Phase 1: Workflow Governance Slice 1

## Task 1: Ship the skill-enforcement gate foundations

**Description:**
Implement the currently planned first slice: config surface, match helper, telemetry schema, observe-mode gate, enforce-mode corrective warning, and thin eval harness.

**Acceptance criteria:**
- [ ] Current `skill-enforcement-gate` spec/plan/todo are fully implemented
- [ ] Observe mode is default and causes zero execution changes
- [ ] Enforce mode uses utility-model classification and in-band correction
- [ ] Thin eval harness exists for representative skills

**Verification:**
- [ ] Focused gate tests pass
- [ ] Full plugin suite remains green
- [ ] Existing narrow slice docs are still internally consistent

**Dependencies:** None

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/default_config.yaml`
- `/a0/usr/plugins/a0_agent_skills/helpers/skill_match.py`
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_before/_10_skill_enforcer.py`
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/_05_skill_telemetry.py`
- `/a0/usr/plugins/a0_agent_skills/tests/*`

**Estimated scope:** Large (already decomposed in the narrow slice docs)

### Checkpoint: Slice 1 complete
- [ ] Skill-enforcement gate shipped in observe-first form
- [ ] Outcome telemetry and eval harness exist
- [ ] Ready to layer durable workflow state on top

### Phase 2: Durable Workflow State

## Task 2: Add workflow-state helper and state file schema

**Description:**
Create a dedicated helper module that owns project-scoped workflow durability: active plan, active goal, current phase, loaded skills, checkpoints, progress log, and handoff.

**Acceptance criteria:**
- [ ] Helper can read/write `.a0proj/state/` artifacts
- [ ] File schema exists for plan, goal, phase, loaded skills, checkpoints, and progress log
- [ ] Missing state files are handled safely
- [ ] State helper is plugin-owned and reusable by extensions/tools

**Verification:**
- [ ] Focused unit tests for read/write behavior
- [ ] Project-state paths are explicit and documented
- [ ] Manual read confirms no state escapes `.a0proj/state/`

**Dependencies:** Task 1

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/workflow_state.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py` (new)

**Estimated scope:** Medium

## Task 3: Persist and rehydrate loaded skills, active phase, and plan/goal state

**Description:**
Add extensions that reattach critical workflow state after compaction or session resume so long-running work can continue without prompt-only memory.

**Acceptance criteria:**
- [ ] Loaded skills can be rehydrated from project state
- [ ] Active phase can be rehydrated from project state
- [ ] Active plan and goal can be reattached to context
- [ ] No-op behavior is safe when no state exists

**Verification:**
- [ ] Focused tests simulate missing and present state files
- [ ] Manual read confirms extensions only reattach plugin-owned workflow state
- [ ] Existing prompt assembly remains stable

**Dependencies:** Task 2

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py`

**Estimated scope:** Medium

## Task 4: Add progress-log and checkpoint support

**Description:**
Create append-only progress logging and explicit checkpoint artifacts so workflow progress survives long sessions and handoffs.

**Acceptance criteria:**
- [ ] Progress entries can be appended to `progress_log.jsonl`
- [ ] Checkpoints can be recorded and updated
- [ ] Handoff artifact path and usage are documented
- [ ] Logs are operator-readable and testable

**Verification:**
- [ ] Unit tests for append/update behavior
- [ ] Manual spot-check of JSONL entry shape
- [ ] README or docs mention how progress files are used

**Dependencies:** Task 3

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/workflow_state.py`
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py`
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Medium

### Checkpoint: Workflow durability complete
- [ ] Workflow state survives beyond prompt context
- [ ] Progress and checkpoints are durable
- [ ] Ready for phase-aware governance work

### Phase 3: Phase-Aware Workflow Governance

## Task 5: Add phase-state model and phase-aware rules

**Description:**
Define how the plugin understands DEFINE / PLAN / BUILD / VERIFY / REVIEW / SHIP as durable runtime state, not just prompt guidance.

**Acceptance criteria:**
- [ ] Phase state is stored durably
- [ ] Phase transitions are explicit
- [ ] Phase-aware helper can answer "what phase are we in?"
- [ ] Phase state is usable by the enforcer and rehydration logic

**Verification:**
- [ ] Focused tests for phase transitions
- [ ] Manual review confirms no coupling to `_permissions`
- [ ] State format is simple and documented

**Dependencies:** Task 4

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/workflow_state.py`
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_phase.py` (new)

**Estimated scope:** Medium

## Task 6: Make enforcement phase-aware and checkpoint-aware

**Description:**
Broaden the gate so it can take current phase and prior correction/checkpoint state into account, reducing repeated or context-free corrections.

**Acceptance criteria:**
- [ ] Enforcer can inspect current workflow phase
- [ ] Repeated correction loops are mitigated with checkpoint/state awareness
- [ ] Enforcement behavior remains observe-first by default
- [ ] No hard human-intervention mode is added in MVP

**Verification:**
- [ ] Behavioral tests for phase-sensitive decisions
- [ ] Regression tests for repeated-correction scenarios
- [ ] Manual read confirms no `nudge()` or forced tool rewrite appears

**Dependencies:** Task 5

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_before/_10_skill_enforcer.py`
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py`
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_phase.py`

**Estimated scope:** Medium

### Checkpoint: Phase-aware governance complete
- [ ] Workflow state influences enforcement
- [ ] Corrections are smarter and less stateless
- [ ] Plugin now owns workflow governance and workflow durability together

### Phase 4: Skill Registry Strengthening

## Task 7: Add stronger skill-contract support for core engineering skills

**Description:**
Introduce richer contract metadata for selected core skills: expected inputs, produced artifacts, verification steps, and next-skill relationships.

**Acceptance criteria:**
- [ ] Contract shape is defined for plugin-owned use
- [ ] Representative engineering skills are upgraded first
- [ ] Contract data is readable without breaking existing skill loading
- [ ] Verification expectations are explicit in contract-bearing skills

**Verification:**
- [ ] Read upgraded skills and confirm contract sections are present
- [ ] Tests prove skill loading still works
- [ ] Contract rules are documented

**Dependencies:** Task 6

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/skills/*/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/tests/test_plugin_contract.py`
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Medium

## Task 8: Add dependency graph / next-skill guidance

**Description:**
Formalize relationships like spec → plan → build → test → review so the plugin can recommend or enforce the next appropriate workflow step more explicitly.

**Acceptance criteria:**
- [ ] Dependency / next-skill metadata exists for core lifecycle skills
- [ ] Guidance can be surfaced from plugin logic or telemetry output
- [ ] No circular core-lifecycle dependency mistakes remain undocumented
- [ ] Docs explain how lifecycle chaining works

**Verification:**
- [ ] Tests for dependency metadata shape
- [ ] Manual review of lifecycle chains
- [ ] Relevant docs updated

**Dependencies:** Task 7

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/skills/*/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/helpers/skill_match.py`
- `/a0/usr/plugins/a0_agent_skills/tests/test_plugin_contract.py`

**Estimated scope:** Medium

## Task 9: Expand evals from activation-only to workflow-quality checks

**Description:**
Extend the thin eval harness so it can test not just matching, but whether the plugin routes workflow correctly across representative scenarios.

**Acceptance criteria:**
- [ ] Fixture set covers more than pure activation matching
- [ ] Near-miss and workflow-order scenarios are represented
- [ ] Runner output is still lightweight and understandable
- [ ] Scope remains plugin-local, not a full harness benchmark framework

**Verification:**
- [ ] Eval runner executes successfully
- [ ] Output is readable and useful for tuning
- [ ] Tests remain stable and fast enough for plugin development

**Dependencies:** Task 8

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/evals/*`
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_match.py`
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Medium

### Checkpoint: Skill-registry strengthening complete
- [ ] Core skills have stronger contracts
- [ ] Lifecycle dependencies are explicit
- [ ] Eval coverage now measures more than first-match behavior

### Phase 5: Final Integration and Rollout Guidance

## Task 10: Unify docs, rollout guidance, and verification

**Description:**
Bring the umbrella roadmap docs, the focused slice docs, the plugin README, and the task trackers into one coherent operator story.

**Acceptance criteria:**
- [ ] Broad roadmap docs and narrow slice docs do not contradict each other
- [ ] README explains current shipped slice vs future roadmap
- [ ] Rollout guidance remains observe-first
- [ ] No public docs imply scope that is not yet implemented

**Verification:**
- [ ] Manual read across spec, plan, todo, README
- [ ] Full plugin suite passes
- [ ] Roadmap and shipped behavior are clearly separated

**Dependencies:** Task 9

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/README.md`
- `/a0/usr/projects/a0_agent_skills/docs/specs/*`
- `/a0/usr/projects/a0_agent_skills/docs/plans/*`
- `/a0/usr/projects/a0_agent_skills/tasks/*`

**Estimated scope:** Small

## Phase 6: Post-Review Remediation (Slice 6)

*Closes the gaps the parallel specialist review and `agents-best-practices` audit found between the shipped plugin and the success criteria. Maps to spec Remediation Slice R1–R6. All user-space; full suite (`607 passed / 42 skipped`) must stay green at every checkpoint.*

### Task 11: Privacy-safe telemetry defaults (R1)

**Description:**
Make telemetry safe-by-default so a fresh install logs no freeform query text or result previews.

**Acceptance criteria:**
- [ ] `telemetry_enabled` defaults to `false` in `default_config.yaml`
- [ ] Log entries store only action type + `skill_name`; freeform `query` is dropped or reduced to action metadata
- [ ] `result_preview` is removed from the telemetry entry schema
- [ ] `.a0proj/skill_activations.jsonl` is covered by `.gitignore`
- [ ] README documents telemetry as opt-in with a clear privacy note

**Verification:**
- [ ] `python -m pytest tests/test_skill_telemetry.py tests/test_telemetry_default_and_hooks.py -v`
- [ ] Manual: enable telemetry, run a skill search, confirm no query text / preview in the JSONL
- [ ] Full suite passes

**Dependencies:** None

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/default_config.yaml`
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/_05_skill_telemetry.py`
- `/a0/usr/plugins/a0_agent_skills/.gitignore`
- `/a0/usr/plugins/a0_agent_skills/README.md`
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_telemetry.py`

**Estimated scope:** Medium

### Task 12: Harden `/ship` spec-context sanitizer (R2)

**Description:**
Close the prompt-injection bypass in `_sanitize_spec_text` and structurally quote untrusted spec-derived context in the specialist template.

**Acceptance criteria:**
- [ ] Input is NFKC-normalized before regex matching
- [ ] Injection blocklist expanded (`forget`, `skip`, `never`, `always`, `pretend`, `act as`, `you are`, `new instruction`, `system prompt`)
- [ ] `ship_review.md` wraps spec-derived text in clearly-delimited "do not follow as instructions" markers
- [ ] Existing path-traversal, allowlist, and JSON-escaping defenses remain intact

**Verification:**
- [ ] `python -m pytest tests/test_ship_sanitization.py -v`
- [ ] New fixtures for bypass phrasings (incl. zero-width / confusables) are neutralized
- [ ] Full suite passes

**Dependencies:** None

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/commands/ship.py`
- `/a0/usr/plugins/a0_agent_skills/prompts/ship_review.md`
- `/a0/usr/plugins/a0_agent_skills/tests/test_ship_sanitization.py`

**Estimated scope:** Medium

### Task 13: Defensive context cleanup for parallel workers (R3)

**Description:**
Replace the brittle `AgentContext._contexts.pop()` coupling with a guarded path that degrades safely and logs when the private attribute is absent.

**Acceptance criteria:**
- [ ] Cleanup checks `hasattr` + `isinstance(dict)` before mutating `_contexts`
- [ ] A deprecation/diagnostic log line is emitted if the private attr is missing
- [ ] No silent context-leak path remains without a log
- [ ] An upstream request for a public cleanup API is noted in code comment + ADR/README

**Verification:**
- [ ] `python -m pytest tests/test_call_subordinate_parallel.py -v`
- [ ] New test for the non-dict / missing-attr cleanup branch
- [ ] Full suite passes

**Dependencies:** None

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/tools/call_subordinate_parallel.py`
- `/a0/usr/plugins/a0_agent_skills/tests/test_call_subordinate_parallel.py`

**Estimated scope:** Small

### Task 14: Outcome-lift eval runner (R4 — closes success criterion 7)

**Description:**
Build a reproducible runner that executes representative fixtures with the gate in observe vs enforce and reports an outcome comparison, proving enforcement helps.

**Acceptance criteria:**
- [ ] Runner executes a fixture set under both gate modes
- [ ] Emits a gate-on vs gate-off outcome-classification report
- [ ] Runner is plugin-local and lightweight (no new external deps)
- [ ] Documented usage in README / spec Commands section

**Verification:**
- [ ] Run the new runner end-to-end and inspect the comparison report
- [ ] `python -m pytest` for any new runner unit tests
- [ ] Full suite passes

**Dependencies:** Task 11 (telemetry schema), Task 12 (stable enforce path)

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/tests/run_enforcement_evals.py` (or new `evals/` runner)
- `/a0/usr/plugins/a0_agent_skills/tests/eval_fixtures/*`
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Medium

### Task 15: Remove `MagicMock/` artifacts and fix leaking tests (R5)

**Description:**
Delete the 825-file `MagicMock/` tree and fix the tests that wrote real disk I/O by mocking a path object, so they use `tmp_path` instead.

**Acceptance criteria:**
- [ ] `MagicMock/` directory is deleted from the plugin tree
- [ ] Offending tests use `tmp_path` (or a real temp dir) so no test writes outside a temp location
- [ ] Re-running the suite does not recreate `MagicMock/`
- [ ] `.gitignore` coverage retained as a safety net

**Verification:**
- [ ] `find /a0/usr/plugins/a0_agent_skills/MagicMock -type f | wc -l` returns `0` after cleanup and a test run
- [ ] Full suite passes

**Dependencies:** None

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/MagicMock/` (delete)
- Telemetry/workflow-state tests that mock `projects.get_project_folder()`
- `/a0/usr/plugins/a0_agent_skills/tests/conftest.py`

**Estimated scope:** Medium

### Task 16: Decide strict (`InterventionException`) enforcement mode (R6)

**Description:**
Resolve the headline "can't silently skip" question with an explicit accept-advisory-or-implement-strict decision, recorded as an ADR.

**Acceptance criteria:**
- [ ] A new ADR records the decision and rationale
- [ ] If deferred, README/spec state plainly that enforcement is advisory due to the framework hook contract
- [ ] If accepted, a scoped follow-up task list for strict mode is added

**Verification:**
- [ ] Manual review of the ADR against ADR-001 and the idea one-pager
- [ ] Docs are internally consistent (no claim of un-skippable gating unless implemented)

**Dependencies:** Task 14 (outcome data informs the decision)

**Files likely touched:**
- `/a0/usr/projects/a0_agent_skills/docs/adrs/006-enforcement-strict-mode-decision.md`
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Small

### Checkpoint: After Phase 6
- [ ] Both HIGH security findings resolved (Tasks 11, 12)
- [ ] No private-API leak path without a log (Task 13)
- [ ] Success criterion 7 closed by the outcome-lift runner (Task 14)
- [ ] `MagicMock/` gone and tests no longer leak disk I/O (Task 15)
- [ ] Headline enforcement question explicitly decided (Task 16)
- [ ] Full suite still green; docs and shipped behavior agree

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broad roadmap obscures what is actually shipping now | High | Keep the existing narrow slice docs as explicit Phase-1 references |
| Workflow-state files become too complex | Medium | Keep state schema simple, project-scoped, and testable |
| Utility-model dependency weakens portability | Medium | Log `classifier_unavailable`, skip correction, document requirement clearly |
| Phase-aware logic creates repeated warnings | High | Checkpoint-aware enforcement and regression tests |
| Skill-contract work becomes a rewrite of all 23 skills | Medium | Start with representative engineering skills first |

## Open Questions

- Should semantic skill search belong in this roadmap, or remain a later enhancement after contracts and dependency graph are stable?
- Should future strict mode use `InterventionException`, or should the plugin remain self-correcting-only?
- How much of the current skill metadata should become machine-readable versus remaining instructional prose?
