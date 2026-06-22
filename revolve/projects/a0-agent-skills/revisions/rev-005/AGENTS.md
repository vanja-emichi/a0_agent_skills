# revolve/projects/a0-agent-skills/revisions/rev-005/AGENTS.md — Runtime Alignment Revision

## Reason

rev-004 optimized automated content-depth presence checks and reached 8.0/8, but review found that the score over-weighted expansion and under-weighted real Agent Zero runtime alignment. rev-005 recalibrates the evaluation harness before further content optimization.

## Parent

`rev-004` — full-scale content-depth promotion complete, but quality proof limited by scanner-driven scoring and pilot-only LLM rubric.

## Subject

Installed plugin subject, evaluated through checkpointed local research copies:

- Live plugin source: `/a0/usr/plugins/a0_agent_skills/`
- Baseline checkpoint: `checkpoints/cp-live-20260620-0129/subject/a0_agent_skills/`
- Current best checkpoint: `checkpoints/cp-a001-harness-truth/subject/a0_agent_skills/`

Live plugin has been externally promoted to `cp-a001-harness-truth` via `external-promotion-001-cp-a001` and verified.

## Incumbent

`cp-d001-d4-d5-e2e-evalrunner` — externally promoted current best for rev-005. Semantic depth 14.54/15 (96.9%). Live plugin verified.

## Evaluation

Contract: `eval/AGENTS.md`.

Primary harness: `eval/check_a0_runtime_alignment.py`.

## Acceptance Gates

A candidate may not be internally promoted unless all gate checks pass under `a0_runtime_alignment_static_v1` and no new non-e2e regression is introduced.

`cp-a001-harness-truth` satisfies the active gates:

1. Static runtime-alignment: passed (`run-002`).
2. Structural/non-runtime regression: passed (`run-004`).
3. Runtime-integration regression through live-overlay: passed (`run-003`).
4. Live restore after overlay: verified byte-for-byte (`run-003`).

## Stop Directive

Initial requested corrective action complete: rev-005 now evaluates A0 runtime/project/subordinate/harness truth and has an internally promoted candidate. COMPLETE — all branches resolved, all remaining items addressed, rev-005 closed.

## Branches

| Branch ID | Hypothesis | Status | Best Result | Detail |
|---|---|---|---|---|
| `branch-d-d4-d5-e2e-evalrunner` | D4/D5/e2e/eval-runner refinement | promoted externally | semantic 14.54/15; all checks pass | `branches/branch-d-d4-d5-e2e-evalrunner/AGENTS.md` |
| `branch-a-harness-truth` | Fix concrete harness-truth failures from baseline | promoted externally | `cp-a001-harness-truth` live-promoted; post-static/structural/runtime all exit 0 | `branches/branch-a-harness-truth/AGENTS.md` |

## Current Best

`cp-a001-harness-truth` — static 0 gate failures / 0 advisory failures; structural 145 passed; runtime-integration 16 passed; live restore verified.

## Blocker

No blocking issue. Full live e2e suite not run for `cp-a001-harness-truth`; optional future validation if stronger behavioral proof is desired.

## Promising Branch Queue

| Rank | Branch | Selection reason | Status |
|---|---|---|---|
| 1 | full live e2e verification | Stronger behavioral proof after external promotion | done (68/69 pass) |
| 2 | `branch-b-runtime-contract-depth` | Deeper semantic audit — D1 runtime model deepened | **promoted externally** — semantic avg 13.29/15; D1 2.79/3; live all checks pass |
| 3 | `branch-c-eval-runner-integration` | Connect or replace behavioral eval runner claims | done — formalized as fixture-only in `cp-d001-d4-d5-e2e-evalrunner` |

## Analysis

rev-005 baseline confirmed the user's concern: the previous “perfect” score hid five gate failures and one advisory failure under a stricter A0 runtime-alignment lens. The first candidate fixed those concrete failures without broad skill expansion and passed the revised gates.

## Next Action

External promotion complete. `branch-b-runtime-contract-depth` candidate `cp-b001-runtime-contract-depth` is externally promoted. Live plugin has domain-specific A0 Runtime Model sections in all 24 skills.

## External Promotion Result

`external-promotion-001-cp-a001` applied `cp-a001-harness-truth` to `/a0/usr/plugins/a0_agent_skills/`.

Post-promotion verification:

- static runtime-alignment: exit 0
- structural/non-runtime pytest: 145 passed, 10 skipped, 85 deselected
- runtime-integration pytest: 16 passed, 224 deselected
- final live state matches candidate: true
- rollback backup: `/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-001-cp-a001/pre-promotion-live-backup-a0_agent_skills`

## E2E Follow-up Run State

`run-005-post-promotion-full-live-e2e` is invalid infrastructure/procedure evidence: pytest exited 4 because the local test environment does not have pytest-xdist and rejected `-n`. The next action is to rerun the full live e2e suite sequentially without `-n` as `run-006-post-promotion-full-live-e2e-sequential`.


## E2E Parallel Run-007 Result

Controlled manual parallel e2e verification ran 4 safe module groups concurrently with extension-behavior scheduled sequentially afterward.

**Completed groups:**

| Group | Passed | Failed | Status |
|---|---:|---:|---|
| group4 (commands/extensions) | 19 | 0 | passed |
| group3 (skill-loading/refs/init) | 12 | 0 | passed |
| group2 (skill-coverage, 24 load + 5 discovery + 1 negative) | 30 | 0 | passed |
| group1 (profiles/prompt-override) | 3 | 1 | 1 pre-existing failure |
| group5 (extension-behavior) | 3 | 0 | passed (final test completed after quota replenished) |

**Total: 68 passed, 1 failed of 69 collected.** (Final test passed after quota replenished.)

**The 1 failure (`test_subordinate_does_not_see_override`) is pre-existing** — it was failing before rev-005 and relates to the subordinate seeing framework skill-discovery content, not plugin content. This is a framework-level behavioral issue, not caused by rev-005 candidate changes.

**Group5 completion:** The final test in extension-behavior (`test_agent_respects_block_level_protection`) was initially interrupted by quota exhaustion but passed after quota replenished.

**Classification:**
- Subject failures: 0 new
- Pre-existing failures: 1 (`test_subordinate_does_not_see_override`)
- Infrastructure failures: 0
- Net new evidence: 68/69 tests pass, which is consistent with the pre-existing baseline before rev-005


## External Promotion Result (Branch B)

`external-promotion-002-cp-b001` applied `cp-b001-runtime-contract-depth` to `/a0/usr/plugins/a0_agent_skills/`.

Post-promotion verification:

- static runtime-alignment: exit 0
- semantic depth: exit 0 (avg 13.29/15)
- structural pytest: 145 passed, 10 skipped
- runtime-integration pytest: 16 passed
- final live state matches candidate: true
- rollback backup: `/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-002-cp-b001/pre-promotion-live-backup-a0_agent_skills`


## Closeout Audit

rev-005 is COMPLETE. All closeout checklist items verified:

| Closeout item | Status |
|---|---|
| State is clear | done — all branches resolved |
| Next action recorded | done — close rev-005 |
| Changed child docs updated | done — runs, checkpoints, branches, promotion |
| Parent indexes reflect child status | done — branch index, revision doc |
| Runs recorded or imported | done — run-001 through run-016 + post-promotion checks |
| Every run produced linked from evaluated checkpoint | done |
| Every evaluated checkpoint has result, validity, decision | done |
| Current best and blocker documented | done — `cp-d001-d4-d5-e2e-evalrunner`; no blocker |
| Branch statuses current | done — all promoted externally |
| No branch marked active without named next action | done |
| New revision created if evaluation changed | N/A — same revision throughout |
| Rollback path exists for promoted work | done — 3 rollback backups |
| Inactive branch summaries compacted | done |

### Final Semantic Depth Journey

| Checkpoint | Avg Score | D1 | D2 | D3 | D4 | D5 |
|---|---:|---:|---:|---:|---:|---:|
| cp-live-baseline | 11.12/15 | 0.75 | 2.88 | 2.96 | 2.42 | 2.12 |
| cp-a001 (harness truth) | 11.12/15 | 0.75 | 2.88 | 2.96 | 2.42 | 2.12 |
| cp-b001 (D1 deepening) | 13.29/15 | 2.79 | 2.88 | 3.00 | 2.50 | 2.12 |
| cp-d001 (D4/D5/e2e) | **14.54/15** | **2.79** | **2.88** | **3.0** | **2.96** | **2.92** |

### Branches Summary

| Branch | Hypothesis | Status | Key Result |
|---|---|---|---|
| `branch-a-harness-truth` | Fix hidden harness/docs/e2e bugs | promoted externally | 5 gate failures fixed; 68/69 e2e pass |
| `branch-b-runtime-contract-depth` | D1 runtime model deepening | promoted externally | D1: 0.75 -> 2.79 |
| `branch-d-d4-d5-e2e-evalrunner` | D4/D5 refinement + e2e fix + eval-runner | promoted externally | D4: 2.96; D5: 2.92; e2e expectation fixed |
| `branch-c-eval-runner-integration` | Connect eval runner | resolved (formalized as fixture-only) | No runner installed; status documented |
| e2e-failure-investigation | Investigate pre-existing e2e failure | resolved (test expectation issue) | Root cause: universal skills listing; fix applied |

### Rollback Backups

| Promotion | Backup Path |
|---|---|
| external-promotion-001-cp-a001 | `promotion/external-promotion-001-cp-a001/pre-promotion-live-backup-a0_agent_skills` |
| external-promotion-002-cp-b001 | `promotion/external-promotion-002-cp-b001/pre-promotion-live-backup-a0_agent_skills` |
| external-promotion-003-cp-d001 | `/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-003-cp-d001/pre-promotion-live-backup-a0_agent_skills` |
