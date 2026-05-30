# Spec: Skill Enforcement Gate + Outcome Eval Harness

*Phase 1 (Specify) artifact of spec-driven-development. Status: awaiting review before PLAN.*
*Source idea: docs/ideas/skills-you-cant-skip.md · Date: 2026-05-30*

> **Status in broader roadmap:** This document defines **Phase 1 / Slice 1** of the larger `a0_agent_skills` workflow-governance roadmap.
> The primary long-range roadmap documents are:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

## Assumptions (correct before PLAN)

1. Spec + feature live entirely in `a0_agent_skills` (user-space); no edits to `/a0/agent.py`, `models.py`, `history.py`.
2. One feature, two halves: the **enforcement gate** and the **outcome/eval harness**, shipped together.
3. Gate is a new `tool_execute_before` extension; it enforces by **mutating `tool_args` in place** or **raising** — never by return value (verified ignored in `agent.py` ~927-935).
4. Loaded-skill state read via `helpers.skills.get_loaded_skill_entries(agent)` → `agent.data['loaded_skills']` (verified).
5. `helpers.skills.search_skills()` returns `List[Skill]` with the internal score stripped (verified) — usable as a **prefilter** only, not a tunable threshold.
6. Outcome telemetry **extends** the existing `_05_skill_telemetry.py` and the existing `.a0proj/skill_activations.jsonl` — no new log file, no new plugin.
7. The classifier uses Agent Zero's first-class utility-model path via `agent.call_utility_model(...)` (verified). If the utility model is unavailable or misconfigured, the gate logs `classifier_unavailable` and skips correction.
8. Tests follow the plugin's existing pytest conventions in `tests/`.

## Objective

Turn a0_agent_skills' lifecycle from prompt-only guidance the model can rationalize past into a **code-level gate it cannot silently skip**, and prove with a thin eval harness that forcing a skill improves outcomes.

**Users:** (a) the maintainer running their own A0 instance; (b) the community installing the distributable plugin.

**Success looks like:** when the agent is about to implement directly while a clearly-applicable skill was never loaded, the harness notices — logging it in `observe` mode, auto-correcting it in `enforce` mode — and the maintainer can measure activation accuracy and outcome lift from telemetry.

## Tech Stack

- Python 3.11+, Agent Zero plugin/extension API (`helpers.extension.Extension`)
- Existing `helpers.skills` (`search_skills`, `get_loaded_skill_entries`, `AGENT_DATA_NAME_LOADED_SKILLS`)
- Agent Zero utility-model path via `agent.call_utility_model(...)` for the lightweight classifier side-query
- pytest for tests; JSONL for telemetry

## Commands

```
Test:        cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ --tb=short
Test (one):  python -m pytest tests/test_skill_enforcer.py -v
Parity:      python scripts/parity_report.py
```

## Project Structure

```
extensions/python/tool_execute_before/_10_skill_enforcer.py   ← NEW: the gate
extensions/python/tool_execute_after/_05_skill_telemetry.py   ← EXTEND: outcome events
helpers/skill_match.py                                        ← NEW: prefilter + utility-model classifier helper
default_config.yaml                                           ← EXTEND: enforcement_* keys
evals/fixtures/*.yaml                                         ← NEW: activation eval fixtures
evals/run_skill_evals.py                                      ← NEW: thin eval runner
tests/test_skill_enforcer.py                                  ← NEW
tests/test_skill_match.py                                     ← NEW
tests/test_outcome_telemetry.py                               ← NEW
```

## Code Style

Match the existing telemetry extension exactly: top-level try/except so the extension can **never** break the agent loop; lazy imports of plugin helpers; config read via `helpers.plugins.get_plugin_config("a0_agent_skills", agent=agent)`.

```python
class SkillEnforcer(Extension):
    async def execute(self, tool_args=None, tool_name=None, **kwargs):
        try:
            if tool_name not in ("code_execution_tool", "text_editor"):
                return
            cfg = _get_plugin_config(self.agent)
            mode = cfg.get("enforcement_mode", "observe")
            candidate = _prefilter(self.agent)          # search_skills, cheap
            if not candidate:
                return
            if mode == "enforce":
                verdict = await _classify(self.agent, candidate)  # utility-model side-query
                if verdict.classifier_unavailable:
                    _log_classifier_unavailable(self.agent, tool_name, candidate)
                    return
                if verdict.should_have_loaded:
                    _append_corrective_warning(self.agent, candidate)
            _log_decision(self.agent, tool_name, candidate, mode)  # always log
        except Exception:
            pass  # never break the loop
```

## Testing Strategy

- **Unit:** prefilter matches/skips correctly; classifier verdict parsing; corrective warning emission is appended as expected; observe-mode asserts **zero** mutation and **zero** classifier calls.
- **Behavioral:** gate ignores non-target tools; gate no-ops when a matching skill is already loaded.
- **Eval harness:** `run_skill_evals.py` asserts should-trigger prompts flag a candidate and near-misses don't, for `spec-driven-development`, `test-driven-development`, `debugging-and-error-recovery`, `code-review-and-quality`.
- Coverage expectation: parity with current suite discipline (all pass / skips intentional).

## Boundaries

- **Always:** wrap extension body in try/except; default `enforcement_mode: observe`; keep classifier off in observe mode; set `enforcement_shadow_sample_rate: 0.0` in MVP.
- **Ask first:** adding any new dependency; raising `InterventionException` (hard pause) instead of auto-correction; expanding target tools beyond `code_execution_tool`/`text_editor`.
- **Never:** edit core framework files; block by extension return value; use `context.nudge()` / `agent.nudge()` as the correction primitive; rewrite target tool calls into forced `skills_tool` calls; enable enforce-by-default in the shipped config; let telemetry or the gate raise into the loop in MVP.

## Success Criteria (testable)

1. In `observe` mode, a target tool call with an unloaded matching skill produces one telemetry decision record and **zero** change to `tool_args` (asserted).
2. In `enforce` mode, the same situation appends an in-band corrective observation/warning such as "load the skill first"; the utility-model classifier fires only here.
3. Gate no-ops (no log, no mutation) when the matching skill is already in `agent.data['loaded_skills']`.
4. would-fire-rate (would-correct count / target-tool calls) is computable from telemetry.
5. Eval runner passes for the 4 fixture skills: should-trigger flags, near-miss stays quiet.
6. If the utility model is unavailable, the gate logs `classifier_unavailable` and skips correction rather than silently falling back to the main chat model.
7. In MVP, `observe` mode performs no classifier calls; `enforcement_shadow_sample_rate` defaults to `0.0`.
8. Full pytest suite green.

## Open Questions

1. Classifier model policy: use the configured utility model via `agent.call_utility_model(...)`; do not silently fall back to the main chat model. Optional future config: `enforcement_classifier_model` if a plugin-specific override is needed.
2. Correction shape: append an in-band corrective observation/warning; do not use `nudge()` and do not rewrite the attempted tool call into a forced `skills_tool` invocation.
3. Shadow sampling: out of MVP. Add optional config placeholder `enforcement_shadow_sample_rate: 0.0`, default disabled.
