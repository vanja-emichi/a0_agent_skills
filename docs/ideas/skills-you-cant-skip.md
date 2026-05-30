# Skills You Can't Skip (and Can Measure)

*idea-refine one-pager — confirmed intent. Scope: a0_agent_skills workflow-governance evolution within Direction C.*
*Date: 2026-05-30*

## Problem Statement

**How might we turn a0_agent_skills' lifecycle from prompt-only guidance the model can rationalize past into a code-level gate it can't silently skip — and prove, with a thin eval harness, that forcing the skill actually improves outcomes?**

## Recommended Direction

Build a **workflow-governance layer inside a0_agent_skills** with enforcement as the headline and a thin eval/measurement harness riding alongside. This sits within the agreed **Direction C** (three plugins: `_permissions` for safety, `_tracing` for observability, `a0_agent_skills` for workflow) but this build touches **only a0_agent_skills**.

The enforcement gate is a new `tool_execute_before` extension. Codebase research is binding here: the hook's return value is **ignored** in `process_tools()` (agent.py ~927-935), so the gate **cannot block by returning a Response**. It must either **mutate `tool_args` in place** or **raise an exception**. Because the chosen UX is auto self-correction, the gate leans on the **arg-mutation / injected-correction** path: when it detects the agent about to implement directly (`code_execution_tool` / `text_editor`) while a clearly-matching skill was never loaded, it injects a "load the skill first" correction so the agent recovers on its own — no human pause. `InterventionException` (the framework's pause-for-user substrate) stays available as a future "strict" mode.

The measurement half extends the **existing** `_05_skill_telemetry` extension from logging *activations* to logging *outcomes* (skill load → tool sequence → result), plus a small eval-fixture runner that asserts each skill triggers on should-trigger prompts and stays quiet on near-misses. Enforcement makes skills fire; evals prove the firing helped.

### Confirmed design decisions

| Decision | Choice |
|----------|--------|
| Headline vs evals | Enforcement headline; evals thin-but-real proof-harness |
| Match signal | Reuse `skills_tool:search` ranking (no second matching engine) |
| Enforce-mode UX | Auto self-correction via arg-mutation / injected correction (no hard pause in MVP) |
| Default mode | Observe-first; raising/correcting only when `enforcement_mode: enforce` |
| Scope | a0_agent_skills only; user-space; no core edits |

## Key Assumptions to Validate

- [ ] **Loaded-skill state is queryable at `tool_execute_before`** — verify how loaded skills are tracked (e.g. `agent.data`) before building the predicate.
- [ ] **The match predicate is precise enough to avoid false positives** — run telemetry-only shadow mode first; measure would-fire rate against real transcripts before enabling corrections.
- [ ] **The injected-correction path resumes cleanly** — a misfire must degrade to a harmless nudge the agent can shrug off, not a loop.
- [ ] **Forcing a skill measurably improves outcomes** — A/B a few fixtures gate-on vs gate-off; compare outcome classification.

## MVP Scope

**In:**
- One `tool_execute_before` extension (`_10_skill_enforcer.py`) running **observe-first**: logs every would-correct decision but does not act, flipped by config `enforcement_mode: observe | enforce`.
- Match signal reuses `skills_tool:search` ranking.
- Extend `_05_skill_telemetry` to capture outcome events (load → first tool → final response) alongside today's activation log.
- A minimal eval-fixture format + runner under `tests/` (should-trigger / should-not-trigger for 3-5 representative skills).
- Config + README + pytest coverage following existing plugin conventions.

**Out:**
- Any correcting/raising enabled by default (ships in `observe`).
- Hard `InterventionException` pause (deferred to a future strict mode).
- Semantic FAISS skill search, frontmatter skill contracts, dependency graph, durable plan/goal state — later slices.
- Anything in `_permissions` or `_tracing`.

## Not Doing (and Why)

- **No `return Response()` blocking** — verified non-functional under the current loop; mutate-or-raise only.
- **No core edits** to agent.py / models.py / history.py — the hook + telemetry substrate already exist; respects the user-space constraint.
- **No enforcement-on-by-default** — a gate you can't yet measure will misfire; observe-first earns the right to enforce.
- **No full eval framework** — thin proof-harness only; a standalone evals project is separate scope.
- **No hard user pause in MVP** — auto self-correction keeps misfires cheap and the human out of the loop.

## Open Questions

- None blocking. Both prior forks (match signal, enforce UX) are resolved. Next step is to hand off to `spec-driven-development` for the formal spec.
