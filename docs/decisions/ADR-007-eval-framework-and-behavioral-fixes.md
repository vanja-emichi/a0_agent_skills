# ADR-007: Eval Framework Integration and Behavioral Fixes (Fix 1-5)

## Status
Accepted

## Date
2026-06-06

## Context

The a0_agent_skills plugin had 24 skills with no evidence they actually improve agent behavior. Skills were text documents that agents could ignore. An investigation revealed five root causes for DOX non-compliance:

1. DOX skill not auto-loaded at session start
2. Subordinate agents receive no DOX context
3. No programmatic gate before file edits
4. Core behavioral rules buried in long context
5. No compliance feedback mechanism

Additionally, there was no measurement framework to determine whether skills provide measurable lift.

## Decision

### Eval Framework

Integrate `agent-skills-eval` (TypeScript CLI) for single-turn behavioral evaluation:

- Each skill has `evals/evals.json` with prompts and assertions
- Framework runs with_skill vs without_skill (A/B comparison)
- LLM judge grades outputs against assertions
- Delta pass rate measures behavioral lift

### Fix 1-5 Extensions

Implement five Python extensions addressing root causes:

| Fix | Extension | Root Cause | Solution |
|---|---|---|---|
| 1 | `agent_init/_00_inject_meta_skill.py` | DOX not auto-loaded | Auto-inject using-agent-skills + dox-project-context |
| 2 | `tool_execute_before/_30_dox_subordinate_handoff.py` | Subordinates DOX-blind | Inject [DOX HANDOFF] in call_subordinate messages |
| 3 | `text_editor_write_before/_10_dox_preflight_check.py` + patch variant | No edit gate | Warn if DOX not loaded before write/patch |
| 4 | `core-behaviors.promptinclude.md` | Context noise | 30-line condensed rules auto-injected |
| 5 | `monologue_end/_20_dox_compliance_check.py` | No feedback | Remind if files edited without reading AGENTS.md |

## Alternatives Considered

### No eval framework (status quo)
- Rejected: No way to prove skills improve behavior
- Risk of shipping skills that actively hurt performance (ci-cd was -10pp)

### Fork agent-skills-eval and customize
- Rejected: Framework tests single-turn completions, not multi-turn Agent Zero sessions
- Custom harness on top of existing A0E2EClient is more appropriate for multi-turn testing

### Blocking extensions (prevent edits without DOX)
- Rejected: Too aggressive — would break legitimate workflows
- Advisory warnings (log only) are safer and still provide feedback

## Consequences

### Positive

- 24/24 skills have evals (55 cases, 247 assertions)
- 21/24 skills show positive lift (average +34.4pp after fixes)
- ci-cd-and-automation fixed from -10pp to +12pp
- security-and-hardening rewritten from 0pp to +6.7pp
- idea-refine improved from 42% to 100% absolute
- Fix 1 verified in live session (both skills auto-loaded)
- test_eval_report.py provides ongoing quality monitoring

### Negative

- Eval framework tests single-turn only (can't measure multi-turn DOX compliance)
- LLM variance is ±10-20pp between iterations
- code-review-and-quality shows floor effect (model already 100% without skill)
- Fix 2-5 can't be measured by eval framework (they target multi-turn behavior)

### Risks

- Model-dependent results (glm-5.1 baselines)
- Evals may need updating when skills change
- Extensions are advisory, not blocking — agents can still ignore warnings

## Verification

- Iteration-7 baseline: 21/24 positive, +34.4pp average
- After skill fixes: ci-cd +12pp, security +6.7pp, idea-refine 100%, planning +38pp
- 182 structural tests + 41 e2e tests all pass
- CI/CD green on GitHub
