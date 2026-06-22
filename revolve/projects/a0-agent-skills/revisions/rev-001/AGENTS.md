# revolve/projects/a0-agent-skills/revisions/rev-001/AGENTS.md

## Reason

Initial exploratory audit of the `a0_agent_skills` plugin's native Agent Zero integration quality. Establish baseline across all 23 skills, identify integration issues, and generate candidate fixes.

## Parent

Project: `a0-agent-skills`

## Subject

Live plugin: `/a0/usr/plugins/a0_agent_skills/`
All 23 skills, 3 agent profiles, 7 slash commands, and supporting infrastructure.

## Incumbent

Checkpoint: `checkpoints/cp-000-baseline` (to be created)
Status: Current live plugin state as of 2026-06-19.

## Evaluation

Contract: `eval/AGENTS.md`

Integration dimensions scored per skill:
1. **Frontmatter validity** — SKILL.md YAML frontmatter has name, description, triggers
2. **Tool name nativity** — All tool references match A0 native tools
3. **Cross-references** — Skill-to-skill references use `skills_tool` correctly
4. **Runtime loading** — Skill loads without errors via `skills_tool load`
5. **Eval schema validity** — evals.json is valid JSON with required fields
6. **Behavioral correctness** — Agent follows skill correctly in a targeted task

Scoring: binary pass/fail per dimension per skill. Overall skill score = dimensions passed / 6.

## Acceptance Gates

- **Candidate promotion gate:** Candidate must not regress any dimension vs incumbent, and must improve at least one dimension for at least one skill.
- **No regressions:** All dimensions that passed on incumbent must still pass on candidate.
- **No overfitting:** Fixes must generalize across skills, not hardcode specific eval cases.

## Suite Identity

- 23 skills × 6 integration dimensions = 138 binary checks
- Full plugin audit at baseline and after each candidate batch

## Scoring Policy

- Per-skill score: 0.0–1.0 (dimensions passed / 6)
- Overall plugin score: average of per-skill scores
- Dimension-level detail preserved for failure analysis

## Stop Directive

**Runtime stop (user-specified):** Stop after the first candidate batch evaluation (3 pilot skills: test-driven-development, debugging-and-error-recovery, git-workflow-and-versioning). User reviews the adaptation approach before scaling to all 23 skills.

## Branches

| Branch ID | Hypothesis | Status | Best Result | Detail |
|---|---|---|---|---|
| `branch-a-correctness` | Fix introduced correctness errors | promising | 161/161, 0 regressions | `branches/branch-a-correctness/AGENTS.md` |
| `branch-b-structural` | Add missing structural elements | promising | 161/161, 0 regressions | `branches/branch-b-structural/AGENTS.md` |
| `branch-c-a0native` | Add A0-native concept references | promising | 161/161, 0 regressions | `branches/branch-c-a0native/AGENTS.md` |
| `branch-d-e2e-coverage` | Add parametrized e2e tests for all 24 skills | promising | 30 tests created, collecting cleanly | `branches/branch-d-e2e-coverage/AGENTS.md` |

## Promising Branch Queue

All 3 branches are promising and complementary. Recommended merge order: A (correctness) → B (structural) → C (A0-native).

## Current Best

`cp-000-baseline` remains incumbent. All 3 candidates passed with zero regressions and are ready for internal promotion. The 3 branches are complementary (correctness + structural + A0-native) and can be merged into a single promoted checkpoint.

## Blocker

None — awaiting user review per stop directive.

## Analysis

Pilot batch complete. Deep audit found 23 issues across 3 skills (1 critical, 6 high, 10 moderate, 6 minor). All 3 candidates passed evaluation with zero regressions.

**Key findings:**
1. **Critical correctness error** introduced during adaptation ("Steps 4-10" in debugging skill)
2. **Eval mutation check copy-paste error** (debugging skill)
3. **Missing structural elements** across 2/3 skills (Related sections, file listings)
4. **Missing A0-native concepts** across all 3 skills (parallel, call_subordinate, browser tool)
5. **Cross-reference syntax gaps** (bare-text references instead of skills_tool syntax)
6. **Trigger gaps** across all 3 skills

**Cross-revision lessons (for scaling to all 23 skills):**
- Content adaptation was largely mechanical find-replace, not deep integration
- `parallel` + `call_subordinate` patterns are systematically absent
- Related sections and file listings should be standardized
- Trigger expansion is safe and low-risk
- Cross-reference syntax needs audit across all skills

## Stop Directive

**COMPLETED** — rev-001 successfully closed. All 6 dimensions green (161 structural tests + 30 e2e tests). Revision superseded by rev-002.

## Next Action

Revision superseded by rev-002 (content depth focus). Resume at `revisions/rev-002/AGENTS.md`.
