# revolve/projects/a0-agent-skills/revisions/rev-003/AGENTS.md

## Reason

Comparable regression verification. rev-002 proved two promising content-depth candidates, but checkpoint-clone regression was not comparable. rev-003 solved this with a live-overlay procedure and scaled content-depth improvements to all 24 skills.

## Parent

`rev-002` — content-depth pilot batch completed; strongest candidates identified but promotion blocked by harness comparability.

## Subject

Live plugin: `/a0/usr/plugins/a0_agent_skills/` (24 skills, all externally promoted with content-depth improvements)

## Incumbent

Live plugin with all 24 skills externally promoted (post cleanup — scanner fix + Files sections).

## Evaluation

Contract: `eval/AGENTS.md` — live-overlay procedure.

## Acceptance Gates

- ✅ Candidate improves content-depth dimensions
- ✅ Candidate passes live-overlay regression guard
- ✅ Full-scale promotion verified: 161/161 pass
- ✅ E2e: 67/69 pass (2 pre-existing behavioral failures, not content regressions)
- ✅ Content depth: 7.96/8 (191/192)

## Stop Directive

**Status:** ✅ COMPLETE — superseded by `rev-004`.

## Supersession

`rev-003` is **superseded by `rev-004`** for deeper content quality audit. The live plugin (7.96/8 content depth, 161/161 regression) becomes the rev-004 baseline.

## Branches

| Branch ID | Hypothesis | Status | Best Result | Detail |
|---|---|---|---|---|
| `branch-g-merged` | Combined parallel/delegation + project-context, scaled to 24 | promoted (full-scale + cleanup) | 7.96/8 avg, +54 total, 161/161 regression | `branches/branch-g-merged/AGENTS.md` |
| `branch-f-parallel-delegation` | Historical seed from rev-002 | superseded by merged | rev-002 seed: 6.08/8 avg | `branches/branch-f-parallel-delegation/AGENTS.md` |
| `branch-e-project-context` | Historical seed from rev-002 | superseded by merged | rev-002 seed: 5.88/8 avg | `branches/branch-e-project-context/AGENTS.md` |

## Current Best

Full-scale live plugin: Average **7.96/8** content depth (up from 5.71/8 baseline). Regression guard: 161/161 pass. E2e: 67/69 pass.

## Blocker

✅ RESOLVED.

## Analysis

rev-003 achieved:
1. Solved the rev-002 harness-comparability blocker with live-overlay procedure
2. Created merged candidate from two complementary seeds
3. Scaled to all 24 skills with parallel subordinates
4. Fixed scanner regex (6 fewer false negatives)
5. Added missing `## Files` sections (4 skills)
6. Final content depth: 5.71→7.96 (+2.25 avg, +54 total)

Remaining gap: only `interview-me` at 7/8 due to scanner regex still not matching 'in parallel' phrasing (content IS present).

## Next Action

1. Fix the 2 pre-existing e2e behavioral test failures (future work — not content related)
2. Consider rev-004 for deeper content quality audit (Claude assumption removal, eval framework)
3. Or close rev-003 as complete
