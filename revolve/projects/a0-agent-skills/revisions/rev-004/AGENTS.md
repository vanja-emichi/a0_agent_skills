# revolve/projects/a0-agent-skills/revisions/rev-004/AGENTS.md

## Reason

Deeper content quality audit. rev-003 achieved 7.96/8 automated. rev-004 assessed quality depth via LLM rubric and improved all four dimensions.

## Parent

`rev-003` — full-scale content-depth promotion complete (7.96/8 automated, 161/161 regression).

## Subject

Live plugin: `/a0/usr/plugins/a0_agent_skills/` (24 skills, **all at 8.0/8** automated content depth)

## Incumbent

Live plugin with all 24 skills externally promoted (post full-scale rev-004 scaling).

## Evaluation

Contract: `eval/AGENTS.md` — LLM rubric + automated regression guard.

## Acceptance Gates

- ✅ Automated score did not regress — improved from 7.96 to **8.0/8**
- ✅ Structural regression: 161/161 pass
- ✅ Rubric improvements: D1 (memory_save fixed), D2 (JSON examples), D3 (A0-specific evals), D4 (pytest/Python alternatives)

## Stop Directive

**Status:** superseded by rev-005 — full-scale content promotion verified, but runtime-alignment proof incomplete.

## Branches

| Branch ID | Hypothesis | Status | Best Result | Detail |
|---|---|---|---|---|
| `branch-k-merged` | Combined A0-evals + JSON examples + correctness fixes, scaled to 24 | promoted (full-scale) | **8.0/8 avg, 192/192, 161/161 regression** | `branches/branch-k-merged/AGENTS.md` |
| `branch-h-a0-evals` | Add A0-specific evals (D3 gap) | superseded by merged | pilot: 7 new evals | `branches/branch-h-a0-evals/AGENTS.md` |
| `branch-i-json-examples` | Add JSON tool-call examples (D2 gap) | superseded by merged | pilot: 4 skills enhanced | `branches/branch-i-json-examples/AGENTS.md` |
| `branch-j-correctness` | Fix memory_save + add Python examples (D1/D4 gap) | superseded by merged | pilot: 5 skills fixed | `branches/branch-j-correctness/AGENTS.md` |

## Current Best

**Full-scale live plugin: 8.0/8 content depth (192/192). Regression: 161/161 pass.**

## Blocker

✅ RESOLVED.

## Analysis

rev-004 achieved:
1. LLM rubric baseline revealed universal D3 gap (no A0-specific evals) and D2 gap (no JSON examples)
2. Three complementary branches created addressing each gap
3. Merged candidate passed live-overlay regression (pilot)
4. Scaled to all 24 skills with parallel subordinates
5. Final: 8.0/8 perfect automated score, 7 memory_save references fixed, 24 A0-specific evals added, 24 JSON examples added

## Next Action

1. Close rev-004 as complete
2. Consider rev-005 for deeper LLM rubric scaling (only 5 pilot skills have rubric scores)
3. Fix 2 pre-existing e2e behavioral test failures (not content related)

## Supersession Note

Superseded by `rev-005` for harness recalibration. rev-004 remains valid as a content-depth/scanner result, but its "perfect" score is not treated as proof of full Agent Zero runtime alignment.
