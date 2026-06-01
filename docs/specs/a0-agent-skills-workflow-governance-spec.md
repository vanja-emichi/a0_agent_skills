# Spec: a0_agent_skills Workflow Governance + Durability

*Umbrella spec for the broader `a0_agent_skills` roadmap. This supersedes the narrow skill-enforcement-gate documents as the primary planning reference while keeping them as Phase-1 slice docs.*
*Date: 2026-05-30*

## Assumptions

1. This roadmap remains entirely within **`a0_agent_skills`** and other user-space project/plugin files.
2. The plugin can own **workflow governance** and **workflow durability**, but not full cross-harness safety governance.
3. Safety/risk/approval policy remains the responsibility of **`_permissions`**.
4. Cross-harness typed traces and replay remain the responsibility of **`_tracing`**.
5. No core-framework edits are required for the roadmap baseline; if later justified, they must be explicitly approved.
6. Existing skill-enforcement-gate docs remain valid as the first implementation slice under this umbrella roadmap.

## Objective

Evolve `a0_agent_skills` from a prompt-driven workflow pack into a **workflow-governance and workflow-durability layer** for Agent Zero's engineering lifecycle.

That means the plugin should not only describe the six-phase SDLC workflow, but also:

- make it harder to skip,
- remember the active workflow state across sessions and compaction,
- guide what phase comes next,
- log what happened and whether it helped,
- and support resumable, long-running engineering work.

**Users:**
- maintainers running their own Agent Zero instance,
- community users installing the distributable plugin,
- future agents resuming long-running project work.

## Scope

### In scope

1. **Skill enforcement and routing hardening**
   - observe-mode gate
   - enforce-mode in-band self-correction
   - utility-model classifier for ambiguous cases
   - stronger workflow routing inside the plugin

2. **Workflow durability**
   - active plan persistence
   - goal state persistence
   - progress log
   - loaded-skill persistence and rehydration
   - phase state persistence
   - checkpoint and handoff artifacts

3. **Phase-aware workflow governance**
   - awareness of DEFINE / PLAN / BUILD / VERIFY / REVIEW / SHIP state
   - phase-sensitive enforcement rules
   - checkpoint-aware next-step guidance

4. **Skill-registry strengthening inside the plugin**
   - outcome telemetry
   - activation eval fixtures
   - thin eval runner
   - stronger skill contracts for core engineering skills
   - dependency / next-skill relationships

5. **Operator guidance and rollout**
   - observe-first rollout
   - explicit docs for utility-model dependency and failure behavior
   - docs for resumable workflow state files

### Out of scope

- `_permissions` safety governance
- `_tracing` cross-harness typed event infrastructure
- full core compaction rewrite
- universal long-running goal-worker runtime for all Agent Zero plugins/tools
- core model-adapter redesign or native tool-calling adoption

## Tech Stack

- Python 3.11+
- Agent Zero plugin extension system
- Existing `helpers.skills` APIs
- Existing utility-model path via `agent.call_utility_model(...)`
- Project-scoped persistence in `.a0proj/`
- JSON / JSONL / Markdown artifacts for workflow state
- pytest for verification

## Commands

```text
Plugin tests:   cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ --tb=short
One test:       python -m pytest tests/test_skill_enforcer.py -v
Parity report:  python scripts/parity_report.py
```

## Project Structure

### Planning artifacts

```text
/a0/usr/projects/a0_agent_skills/
├── docs/specs/
├── docs/plans/
└── tasks/
```

### Implementation targets

```text
/a0/usr/plugins/a0_agent_skills/
├── extensions/python/tool_execute_before/
├── extensions/python/tool_execute_after/
├── extensions/python/message_loop_prompts_after/
├── extensions/python/message_loop_start/
├── helpers/
├── tests/
├── evals/
└── default_config.yaml
```

### Expected new workflow-state artifacts

```text
.a0proj/state/
├── active_plan.json
├── active_goal.json
├── current_phase.json
├── loaded_skills.json
├── checkpoints.json
├── progress_log.jsonl
└── handoff.md
```

## Code Style

Follow existing plugin patterns:

- top-level fail-safe `try/except` in extensions
- config access via plugin config helpers
- lazy imports where it reduces unnecessary coupling
- explicit JSONL logging, no silent schema drift
- helper modules for shared logic rather than embedding policy in extension bodies

## Testing Strategy

- **Unit tests** for helpers, config parsing, classifier result handling, contract parsing
- **Behavioral tests** for observe-mode and enforce-mode gate behavior
- **State tests** for persistence, rehydration, and progress logging
- **Eval tests** for skill activation matching and near-miss rejection
- **Regression tests** to prevent `nudge()`, forced tool rewrites, or silent chat-model fallback
- **Documentation consistency checks** where public contract and defaults matter

## Boundaries

### Always
- Ship new workflow-governance behaviors in observe-first form where possible
- Keep state artifacts project-scoped under `.a0proj/`
- Preserve backward-safe defaults
- Verify behavior with focused tests before broad rollout

### Ask first
- Any core-framework edits
- Any expansion of target tools beyond the scoped MVP
- Any new external dependencies
- Any shift from self-correction to hard human-intervention behavior

### Never
- Put workflow durability into `_permissions`
- Use `nudge()` as the correction primitive for this roadmap
- Force target tool calls into rewritten `skills_tool` calls in MVP
- Silently fall back from the utility model to the main chat model for classifier work
- Treat this plugin as the owner of global safety governance

## Success Criteria

1. The plugin can detect and record skipped-skill situations before direct implementation.
2. The plugin can correct those situations in enforce mode using in-band warnings.
3. Active workflow state survives compaction and session resume through `.a0proj/state/` artifacts.
4. The plugin can reattach loaded skills, current phase, and active plan/goal state after context turnover.
5. Progress and checkpoints are durably recorded outside the prompt.
6. Core engineering skills have stronger contracts and explicit dependency relationships.
7. The plugin provides a lightweight eval path to measure matching quality and outcome lift.
8. All of the above remain user-space only and do not require core framework changes.

## Remediation Slice (Slice 6) — Post-Review Hardening

*Added 2026-05-30 after the parallel specialist review (`docs/reports/parallel-review-full.md`) and the `agents-best-practices` harness audit. This slice closes the gaps between the shipped plugin and the success criteria above. It remains user-space only.*

### Problem statement

The review confirmed 6 of 8 success criteria are met, but found:
- two **HIGH** security findings still open in the shipped code,
- success criterion 7 (outcome lift) only partially met — matching evals exist, but no gate-on vs gate-off measurement,
- the original "can't silently skip" headline is only partially delivered because the `tool_execute_before` return value is ignored by the framework (advisory-only),
- 825 stray `MagicMock/…` test artifacts polluting the plugin tree from tests that mocked a path object instead of using `tmp_path`.

### Remediation requirements

| ID | Requirement | Source finding | Acceptance |
|----|-------------|----------------|-----------|
| R1 | Default `telemetry_enabled: false`; redact freeform `query` to action+skill_name only; drop `result_preview`; add log path to `.gitignore` | HIGH-2 | New install logs no query text or result previews; existing tests updated; opt-in documented in README |
| R2 | Harden `_sanitize_spec_text`: NFKC-normalize first, expand injection blocklist (`forget`, `skip`, `never`, `always`, `pretend`, `act as`, `you are`, `new instruction`, `system prompt`), and wrap spec-derived text in clearly-delimited "do not follow as instructions" blocks in `ship_review.md` | HIGH-1 | Bypass-phrase fixtures (incl. zero-width / confusables) are neutralized; specialist template quotes untrusted context |
| R3 | Replace direct `AgentContext._contexts.pop()` coupling with a defensive `hasattr`/`isinstance` guard plus a logged deprecation path, and file an upstream request for a public cleanup API | MED-5 / code-review Important | Cleanup degrades safely if the private attr changes; no silent context leak path without a log |
| R4 | Build an **outcome-lift eval runner**: run representative fixtures with the gate observe vs enforce and record outcome classification, closing success criterion 7 | Criterion 7 / test-engineer | A reproducible runner emits a gate-on vs gate-off comparison report under `evals/` or `tests/` |
| R5 | Delete the 825-file `MagicMock/` tree and fix the offending tests to use `tmp_path` so mocked path objects never write real disk I/O | Repo hygiene / test quality | `MagicMock/` is gone; full suite still passes; no test writes outside `tmp_path` |
| R6 | Decide and document the deferred strict (`InterventionException`) enforcement mode — the only path to a true code-level un-skippable gate — as an explicit accept/defer ADR | Headline goal / Open Q1 | A written decision (ADR) records the choice and rationale; if deferred, the advisory limitation is stated plainly in README |

### Boundaries for this slice

- **Always:** keep changes user-space; preserve passing tests; ship security defaults backward-safe-but-private.
- **Ask first:** any move from advisory enforcement to hard `InterventionException` pausing as a *default*.
- **Never:** weaken existing path-traversal, allowlist, or recursion guards while hardening; reintroduce framework edits.

### Updated success-criteria status

- Criteria 1–6, 8: met (see review).
- Criterion 7: **closed by R4** once the outcome-lift runner lands.
- Headline "can't silently skip": **explicitly resolved by R6** (accept advisory-only or implement strict mode), not left ambiguous.

## Open Questions

1. Should strict human-gated mode (`InterventionException`) ever be added later, or should the plugin remain permanently self-correcting-only?
2. Should browser write actions join the target-tool set after observe-mode telemetry proves the current scope is stable?
3. Should utility-model override remain global, or should the plugin eventually support a plugin-specific classifier override?
