# TODO: Skill Enforcement Gate + Outcome Eval Harness

> Generated from:
> - `/a0/usr/projects/a0_agent_skills/docs/specs/skill-enforcement-gate-spec.md`
> - `/a0/usr/projects/a0_agent_skills/docs/plans/skill-enforcement-gate-plan.md`
>
> **Status in broader roadmap:** This file tracks **Phase 1 / Slice 1** only.
> The umbrella roadmap tracker is:
> - `/a0/usr/projects/a0_agent_skills/tasks/a0-agent-skills-workflow-governance-todo.md`

## Current decisions

- Gate lives in **`/a0/usr/plugins/a0_agent_skills`** only
- Default mode is **`observe`**
- Classifier uses **Agent Zero utility model** via `agent.call_utility_model(...)`
- If utility model is unavailable, log **`classifier_unavailable`** and skip correction
- Correction is an **in-band warning/observation**
- Do **not** use `nudge()`
- Do **not** rewrite target tool calls into forced `skills_tool` invocations
- MVP target tools: **`code_execution_tool`** and **`text_editor`** only
- Shadow sampling is **out of MVP**; placeholder config stays at `0.0`

## Phase 1: Foundations and safe instrumentation

### Task 1: Add config surface ✅
- [x] Add `enforcement_mode: observe` to plugin config
- [x] Add utility-classifier policy keys
- [x] Add `enforcement_shadow_sample_rate: 0.0`
- [x] Preserve existing telemetry defaults
- [x] Verify config loads cleanly
- 9 new tests in `tests/test_enforcement_config.py` — all green
- Full suite: 301 passed, 42 skipped, 0 failures

### Task 2: Build `helpers/skill_match.py` ✅
- [x] Add target-tool detection helper
- [x] Add loaded-skill lookup via `get_loaded_skill_entries(agent)`
- [x] Add `search_skills()` prefilter
- [x] Add utility-model classifier wrapper
- [x] Return explicit states:
  - [x] `no_candidate`
  - [x] `already_loaded`
  - [x] `should_correct`
  - [x] `should_not_correct`
  - [x] `classifier_unavailable`
- 26 new tests in `tests/test_skill_match.py` — all green
- Full suite: 327 passed, 42 skipped, 0 failures

### Task 3: Extend telemetry for gate decisions ✅
- [x] Add would-fire / would-correct decision logging
- [x] Add observe vs enforce distinction
- [x] Add `classifier_unavailable` event/reason
- [x] Keep existing activation logging working
- [x] Keep same JSONL file: `.a0proj/skill_activations.jsonl`
- 11 new tests in `tests/test_gate_telemetry.py` — all green
- Full suite: 338 passed, 42 skipped, 0 failures

### Phase 1 checkpoint ✅
- [x] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_skill_match.py -v`
- [x] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_outcome_telemetry.py -v`
- [x] Existing telemetry tests remain green
- [x] No execution behavior changed yet

---

## Phase 2: Observe-mode gate

### Task 4: Implement `_10_skill_enforcer.py` in observe mode ✅
- [x] Create `extensions/python/tool_execute_before/_10_skill_enforcer.py`
- [x] Restrict to `code_execution_tool` and `text_editor`
- [x] Evaluate gate predicate
- [x] Log would-fire decisions only
- [x] Do **not** mutate `tool_args`
- [x] Do **not** change execution flow
- [x] Wrap body in fail-safe `try/except`
- [x] Observe mode: NO classifier calls
- 13 new tests in `tests/test_skill_enforcer.py` — all green
- Full suite: 351 passed, 42 skipped, 0 failures

### Task 5: Document observe mode ✅
- [x] Update README with `observe` vs `enforce`
- [x] Explain would-fire-rate
- [x] Explain `classifier_unavailable`
- [x] Make it explicit that enforcement is **not** enabled by default

### Phase 2 checkpoint ✅
- [x] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py -v`
- [x] Observe mode shows zero behavior change
- [x] README matches config defaults and spec wording

---

## Phase 3: Enforce-mode self-correction

### Task 6: Add enforce-mode corrective warning ✅
- [x] Run utility-model classifier only in `enforce`
- [x] Append in-band corrective warning when classifier says yes
- [x] Skip correction and log `classifier_unavailable` when utility model is unavailable
- [x] Do **not** use `nudge()`
- [x] Do **not** force a `skills_tool` rewrite
- [x] Do **not** fall back silently to the main chat model
- 11 new tests in `tests/test_skill_enforcer.py` (3 verification + 8 enforce-mode) — all green
- Full suite: 362 passed, 42 skipped, 0 failures

### Task 7: Add guardrail regression tests ✅
- [x] Test that `nudge()` is never used (3 behavioural + 1 source-level)
- [x] Test that tool_args are never mutated in either mode (3 tests)
- [x] Test no forced `skills_tool` rewrite in tool_args (2 behavioural + 1 AST-level)
- [x] Test enforce mode does not hard-pause / raise InterventionException (3 tests)
- [x] Test classifier unavailable degrades gracefully (3 tests)
- [x] Test no silent chat-model fallback (2 tests: behavioural + source)
- [x] Test already-loaded skill produces clean no-op (1 test)
- [x] Test non-target-tool no-op (6 parametrized tools)
- [x] Test corrective warning uses only `hist_add_message` (2 tests)
- 27 new tests in `tests/test_enforcement_guardrails.py` — all green
- Full suite: 389 passed, 42 skipped, 0 failures

### Phase 3 checkpoint ✅
- [x] Enforce mode emits corrective warning only when classifier says yes
- [x] Guardrail regressions are covered
- [x] No forbidden primitives have crept in

---

## Phase 4: Thin eval harness

### Task 8: Add activation eval fixtures ✅
- [x] Fixture for `spec-driven-development` (8 trigger + 8 no-trigger)
- [x] Fixture for `test-driven-development` (8 trigger + 8 no-trigger)
- [x] Fixture for `debugging-and-error-recovery` (8 trigger + 8 no-trigger)
- [x] Fixture for `code-review-and-quality` (8 trigger + 8 no-trigger)
- [x] Fixture format: JSON, simple and extensible
- Files: `tests/eval_fixtures/*.json`

### Task 9: Build eval runner ✅
- [x] `tests/run_enforcement_evals.py` — pytest module + standalone runner
- [x] Simulated keyword-based search_skills for test environments
- [x] Runs prefilter_match for should_trigger → asserts candidate found
- [x] Runs prefilter_match for should_not_trigger → asserts no candidate
- [x] Reports pass/fail per fixture
- [x] Can be run via `python -m pytest tests/run_enforcement_evals.py -v`
- [x] Can be run standalone via `python tests/run_enforcement_evals.py`
- 8 eval tests — all green

### Phase 4 checkpoint ✅
- [x] All four representative skills have fixtures
- [x] Eval runner executes successfully
- [x] Operator can use results to judge gate noise before wider rollout

---

## Phase 5: Final verification and rollout guidance

### Task 10: Final verification pass ✅
- [x] Run focused gate tests — all green
- [x] Run full plugin suite — **389 passed, 42 skipped, 0 failures**
- [x] Run eval runner — **8 passed, 0 failures**
- [x] Verify README rollout guidance says observe-first
- [x] Re-read spec, plan, config, tests, and docs for contradictions
- [x] Update todo marking all tasks complete

### Final release gate ✅
- [x] `python -m pytest tests/ --tb=short` — 389 passed, 42 skipped
- [x] `python -m pytest tests/run_enforcement_evals.py -v` — 8 passed
- [x] Observe-first rollout guidance is documented
- [x] No contradiction remains across spec, plan, config, tests, and docs
- [x] Ready for observe-mode production use

---

## Rollout Summary

### What was built

1. **Config surface** (`default_config.yaml`): `enforcement_mode: observe`, classifier policy, shadow sample rate (disabled)
2. **Skill-match helper** (`helpers/skill_match.py`): prefilter via `search_skills()`, utility-model classifier, explicit result states
3. **Gate telemetry** (`_05_skill_telemetry.py`): would-fire decisions, observe/enforce distinction, classifier_unavailable events
4. **Observe-mode enforcer** (`_10_skill_enforcer.py`): logs decisions without mutating tool_args or changing execution
5. **Enforce-mode correction**: appends in-band warning via `hist_add_message()`, no nudge/rewrite/exception
6. **Guardrail regression tests** (`tests/test_enforcement_guardrails.py`): 27 tests protecting against forbidden primitives
7. **Eval fixtures** (`tests/eval_fixtures/`): 4 JSON fixtures with 64 total test messages
8. **Eval runner** (`tests/run_enforcement_evals.py`): pytest + standalone, simulated search for test environments

### How to enable enforce mode

1. Run in observe mode first: default `enforcement_mode: observe`
2. Inspect `.a0proj/skill_activations.jsonl` for `should_correct` events
3. Evaluate false-positive rate
4. When satisfied, change to `enforcement_mode: enforce` in plugin config

### Known limitations

- MVP targets only `code_execution_tool` and `text_editor`
- Classifier depends on utility model availability
- Shadow sampling disabled (placeholder for future)
- Eval runner uses simulated search in test env (real search needs live A0)
- No outcome eval (measuring whether correction improves results) — future work

---

## Notes

- Keep implementation in **`/a0/usr/plugins/a0_agent_skills`**
- Keep planning/spec/docs in **`/a0/usr/projects/a0_agent_skills`**
- Keep tasks small, explicit, and verifiable
- Do not broaden scope into `_permissions` or `_tracing`
