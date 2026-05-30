# Implementation Plan: a0_agent_skills Managed Fork Alignment

> Generated from spec `docs/specs/managed-fork-alignment-spec.md`.

## Overview

This plan brings `/a0/usr/plugins/a0_agent_skills` to a safe-to-ship state while reducing unmanaged drift from `/a0/usr/projects/a0_agent_skills/comparison/official_agent_skills`.

The plan follows four principles:

1. **Ship safety first** — correctness and contract mismatches get fixed before broader alignment work.
2. **Managed fork, not mirror** — upstream remains the semantic reference, while Agent Zero remains the runtime surface.
3. **Parity tooling before broad rewrites** — measure drift before aggressively reducing it.
4. **Selective hook alignment** — port or replace upstream hook behavior only where it still makes sense in Agent Zero.

## Architecture Decisions

- `/ship` is canonically a **parallel fan-out** workflow.
- Telemetry remains **enabled by default**.
- Parity tooling begins as **report-only**, then becomes enforceable once the fork policy stabilizes.
- Shared skills should move closer to upstream wording/behavior where practical, but retain explicit A0 metadata and tool guidance.
- Upstream `hooks/` will be handled via **selective porting + documented omission**, not blind one-to-one copying.

## Task List

### Phase 1: Ship Safety and Public Contract

## Task 1: Correct product truth in manifest and README

**Description:**
Update top-level plugin metadata and public-facing documentation so the repository accurately describes the current plugin: skill count, managed-fork status, telemetry default, and the high-level A0-native positioning.

**Acceptance criteria:**
- [ ] `plugin.yaml` no longer claims 21 skills if the repo contains 23 skill directories
- [ ] `README.md` describes the plugin as an Agent Zero-native managed fork/port
- [ ] README top-level product description matches actual telemetry default and A0 scope

**Verification:**
- [ ] Read `plugin.yaml` and confirm the skill count/product description is correct
- [ ] Read `README.md` and confirm the opening sections match actual repo behavior
- [ ] Shell check: count skill directories and confirm docs match

**Dependencies:** None

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/plugin.yaml`
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Small

## Task 2: Fix `/ship` sanitization bug with focused regression tests

**Description:**
Patch `commands/ship.py` so sanitization removes actual control characters instead of stripping literal hyphens. Add focused tests proving valid text is preserved and unsafe control characters are removed.

**Acceptance criteria:**
- [ ] `_sanitize_spec_text()` removes real control characters
- [ ] `_sanitize_scope()` removes real control characters without damaging normal hyphenated text
- [ ] Regression tests cover hyphen preservation and control-character removal

**Verification:**
- [ ] New focused test file passes
- [ ] Read `commands/ship.py` and confirm regex behavior matches comments/docstrings
- [ ] Manual spot-check with representative input strings

**Dependencies:** Task 1

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/commands/ship.py`
- `/a0/usr/plugins/a0_agent_skills/tests/test_ship_sanitization.py` (new)

**Estimated scope:** Small

## Task 3: Align `/ship` contract across command config, implementation, and docs

**Description:**
Make the `/ship` contract consistently describe and implement parallel fan-out. Remove contradictory sequential wording from command metadata and README, and ensure command-facing docs align with the actual A0 orchestration behavior.

**Acceptance criteria:**
- [ ] `commands/ship.command.yaml` describes parallel fan-out, not sequential review
- [ ] `README.md` `/ship` description matches the implemented behavior
- [ ] No surviving contradictory sequential wording remains in the primary public contract

**Verification:**
- [ ] Grep for `sequential` and `parallel` across `/ship` surfaces and review results
- [ ] Read generated `/ship` prompt text in `commands/ship.py`
- [ ] Re-read `ship.command.yaml` and the `/ship` section in `README.md`

**Dependencies:** Task 2

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/commands/ship.command.yaml`
- `/a0/usr/plugins/a0_agent_skills/README.md`
- `/a0/usr/plugins/a0_agent_skills/commands/ship.py`

**Estimated scope:** Small

## Task 4: Add repo-contract consistency tests

**Description:**
Create tests that fail when the plugin’s public contract drifts from reality again. Cover skill count, telemetry default, and `/ship` mode consistency across config, docs, and command metadata.

**Acceptance criteria:**
- [ ] Test suite checks README vs actual skill count
- [ ] Test suite checks telemetry default against config/runtime expectation
- [ ] Test suite checks `/ship` contract consistency between README, command YAML, and implementation text cues

**Verification:**
- [ ] New contract test file passes
- [ ] Existing telemetry tests continue to pass
- [ ] Existing command-related tests remain green

**Dependencies:** Task 3

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/tests/test_plugin_contract.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_telemetry_default_and_hooks.py`

**Estimated scope:** Small

### Checkpoint: After Phase 1

- [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_ship_sanitization.py -v`
- [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_plugin_contract.py -v`
- [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_telemetry_default_and_hooks.py -v`
- [ ] `plugin.yaml`, `README.md`, and `/ship` command metadata tell the same story

### Phase 2: Parity Infrastructure and Fork Discipline

## Task 5: Add a report-only parity report tool

**Description:**
Create a script that compares the plugin tree against the upstream snapshot, classifies differences, and emits a readable parity report focused on shared files, plugin-only A0 surfaces, and upstream-only omitted assets.

**Acceptance criteria:**
- [ ] A script exists under plugin `scripts/` for parity reporting
- [ ] The script distinguishes shared-changed, plugin-only, and upstream-only assets
- [ ] The report is usable by future maintainers without rerunning a manual ad hoc comparison

**Verification:**
- [ ] Run the parity script successfully from the plugin root
- [ ] Inspect output and confirm it classifies at least skills, commands, agents, hooks, references, and docs
- [ ] Confirm no core Agent Zero files are required to run it

**Dependencies:** Task 4

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/scripts/parity_report.sh` or `.py` (new)
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Medium

## Task 6: Add report-only parity validation tests

**Description:**
Add test coverage around the parity process so shared drift is measurable in CI/local verification, but not yet release-blocking on every undocumented change.

**Acceptance criteria:**
- [ ] A parity-oriented test exists under `tests/`
- [ ] The test can validate core parity assumptions without rewriting the whole repo
- [ ] Test behavior is report-only or warning-oriented by design for this first phase

**Verification:**
- [ ] New parity test passes locally
- [ ] Test output is understandable and actionable
- [ ] Existing test suite remains green

**Dependencies:** Task 5

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/tests/test_upstream_parity.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/conftest.py`

**Estimated scope:** Medium

## Task 7: Document the managed-fork surface mapping

**Description:**
Create a durable mapping doc that explains how upstream assets correspond to Agent Zero-native surfaces. This becomes the reference for future alignment work across commands, personas, references, hooks, docs, and omitted editor integrations.

**Acceptance criteria:**
- [ ] A mapping doc exists for upstream → Agent Zero surfaces
- [ ] It covers commands, personas, references/checklists, hooks, and omitted editor/vendor assets
- [ ] It distinguishes: ported, replaced, intentionally omitted

**Verification:**
- [ ] Re-read the mapping doc and confirm all major upstream-only categories are covered
- [ ] Spot-check mappings against the parity report and repo trees

**Dependencies:** Task 6

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/docs/managed-fork-surface-mapping.md` (new)
- `/a0/usr/plugins/a0_agent_skills/README.md`

**Estimated scope:** Small

### Checkpoint: After Phase 2

- [ ] Parity script runs successfully
- [ ] Parity test passes in report-only mode
- [ ] Surface mapping doc exists and is readable
- [ ] Future drift can be measured without repeating manual repo archaeology

### Phase 3: Shared Skill Alignment Passes

## Task 8: Align planning/meta skill set

**Description:**
Review and reduce nonessential drift in the planning/meta skills while preserving A0-specific metadata and tool guidance. Prioritize shared semantics, structure, and references to upstream intent.

**Acceptance criteria:**
- [ ] The following skills are reviewed against upstream: `using-agent-skills`, `interview-me`, `idea-refine`, `spec-driven-development`, `planning-and-task-breakdown`
- [ ] Each file is classified as: aligned, intentionally divergent, or updated to reduce drift
- [ ] No unnecessary local prose divergence remains in this group where a closer upstream match is practical

**Verification:**
- [ ] Diff each touched file against upstream after edits
- [ ] Re-read changed files to confirm A0-specific instructions still make sense
- [ ] Relevant enforcement/trigger tests remain green

**Dependencies:** Task 7

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/skills/using-agent-skills/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/interview-me/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/idea-refine/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/spec-driven-development/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/planning-and-task-breakdown/SKILL.md`

**Estimated scope:** Medium

## Task 9: Align implementation-core skill set

**Description:**
Review and reduce nonessential drift in the implementation-core skills, focusing on preserving upstream behavior while keeping the necessary A0 tool references and runtime wording.

**Acceptance criteria:**
- [ ] The following skills are reviewed against upstream: `context-engineering`, `incremental-implementation`, `test-driven-development`, `source-driven-development`, `doubt-driven-development`
- [ ] A0-only instructions remain explicit and minimal
- [ ] Drift reductions do not break existing trigger/enforcement expectations

**Verification:**
- [ ] Diff touched files against upstream
- [ ] Run relevant skill-related tests
- [ ] Re-read changed files for internal consistency and tool-name accuracy

**Dependencies:** Task 8

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/skills/context-engineering/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/incremental-implementation/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/test-driven-development/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/source-driven-development/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/doubt-driven-development/SKILL.md`

**Estimated scope:** Medium

## Task 10: Align UI/API/debug skill set

**Description:**
Align the UI/API/debug cluster with upstream intent while retaining A0 browser/tool guidance and localized checklist references where they improve Agent Zero usability.

**Acceptance criteria:**
- [ ] The following skills are reviewed against upstream: `frontend-ui-engineering`, `api-and-interface-design`, `browser-testing-with-devtools`, `debugging-and-error-recovery`
- [ ] Local checklist/reference links remain correct
- [ ] A0-specific instructions are preserved only where they materially improve execution inside Agent Zero

**Verification:**
- [ ] Diff touched files against upstream
- [ ] Re-read localized checklist references for correctness
- [ ] Run any affected skill metadata/enforcement tests

**Dependencies:** Task 9

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/skills/frontend-ui-engineering/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/api-and-interface-design/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/browser-testing-with-devtools/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/debugging-and-error-recovery/SKILL.md`

**Estimated scope:** Medium

## Task 11: Align review/delivery skill sets

**Description:**
Complete the alignment pass on the review and delivery skill families, minimizing wording drift while preserving A0-specific tool instructions and managed-fork decisions.

**Acceptance criteria:**
- [ ] The following skills are reviewed against upstream: `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization`, `shipping-and-launch`
- [ ] The following skills are reviewed against upstream in a second sub-pass: `git-workflow-and-versioning`, `ci-cd-and-automation`, `documentation-and-adrs`, `deprecation-and-migration`
- [ ] Each touched file is either moved closer to upstream or explicitly classified as intentional divergence

**Verification:**
- [ ] Diff touched files against upstream in sub-passes
- [ ] Re-read changed verification sections for correctness
- [ ] Run enforcement/trigger tests after each sub-pass

**Dependencies:** Task 10

**Files likely touched (sub-pass A):**
- `/a0/usr/plugins/a0_agent_skills/skills/code-review-and-quality/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/code-simplification/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/security-and-hardening/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/performance-optimization/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/shipping-and-launch/SKILL.md`

**Files likely touched (sub-pass B):**
- `/a0/usr/plugins/a0_agent_skills/skills/git-workflow-and-versioning/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/ci-cd-and-automation/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/documentation-and-adrs/SKILL.md`
- `/a0/usr/plugins/a0_agent_skills/skills/deprecation-and-migration/SKILL.md`

**Estimated scope:** Medium

### Checkpoint: After Phase 3

- [ ] Shared skills have been reviewed in manageable domain batches
- [ ] Drift is reduced intentionally, not opportunistically
- [ ] Skill tests continue to pass
- [ ] Updated files are classified as aligned or intentionally divergent

### Phase 4: Hook Alignment, Final Docs, and Integration Verification

## Task 12: Audit upstream hooks and define A0-native hook policy

**Description:**
Inspect upstream `hooks/` assets and record which behaviors should be ported, replaced, or intentionally omitted in Agent Zero. This task is analysis + durable documentation only.

**Acceptance criteria:**
- [ ] Each upstream hook/script/doc asset is classified
- [ ] At least one clear policy exists for `session-start`, `simplify-ignore`, and `sdd-cache` families
- [ ] The classification is written in a durable doc, not left as chat-only knowledge

**Verification:**
- [ ] Re-read the hook policy doc
- [ ] Spot-check every upstream hook asset is accounted for
- [ ] Confirm classifications match the managed-fork decisions in the spec

**Dependencies:** Task 7

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/docs/hook-alignment.md` (new)

**Estimated scope:** Small

## Task 13: Implement selected hook replacements or explicit documented stubs

**Description:**
Make the minimum A0-native changes needed so useful upstream hook behavior is either represented in Agent Zero surfaces or explicitly documented as omitted. Keep this task tightly scoped to the hook policy decisions from Task 12.

**Acceptance criteria:**
- [ ] `hooks.py` and/or related docs reflect the selected policy decisions
- [ ] Any implemented replacements are clearly A0-native rather than pretending to be direct upstream clones
- [ ] Intentional omissions are documented, not silent

**Verification:**
- [ ] Re-read `hooks.py` and affected docs
- [ ] Run hook-related tests
- [ ] Confirm no unintended side effects are introduced at install/update time

**Dependencies:** Task 12

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/hooks.py`
- `/a0/usr/plugins/a0_agent_skills/docs/hook-alignment.md`
- `/a0/usr/plugins/a0_agent_skills/tests/test_telemetry_default_and_hooks.py`

**Estimated scope:** Small

## Task 14: Final verification pass and parity refresh

**Description:**
Run the focused suite, refresh the parity report, and confirm the repository is internally consistent enough to enter BUILD/IMPLEMENT work slices with confidence.

**Acceptance criteria:**
- [ ] Focused regression tests pass
- [ ] Parity report runs successfully
- [ ] Managed-fork docs and contract docs are internally consistent
- [ ] No newly introduced contradiction remains around `/ship`, telemetry, skill count, or hook policy

**Verification:**
- [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/ -v`
- [ ] Run the parity report script
- [ ] Re-read README, plugin manifest, hook policy, and key command files

**Dependencies:** Task 13

**Files likely touched:**
- All task outputs as needed for final cleanup only

**Estimated scope:** Small

## Parallelization Opportunities

- **Safe to parallelize after Phase 2:** skill-alignment domain passes (`Tasks 8–11`) if each worker owns a distinct skill group and uses the parity report as a baseline
- **Must remain sequential:** Tasks 1–7, because they establish the public contract and parity discipline that later work depends on
- **Needs coordination:** Tasks 12–13, because hook policy decisions affect both docs and runtime behavior

## Dependency Graph

```text
Task 1 (manifest + README truth)
  └→ Task 2 (/ship sanitization fix)
      └→ Task 3 (/ship contract alignment)
          └→ Task 4 (contract tests)
              └→ Task 5 (parity report script)
                  └→ Task 6 (parity test)
                      └→ Task 7 (surface mapping doc)
                          └→ Task 8 (planning/meta skills)
                              └→ Task 9 (implementation-core skills)
                                  └→ Task 10 (UI/API/debug skills)
                                      └→ Task 11 (review/delivery skills)
                          └→ Task 12 (hook audit/policy)
                              └→ Task 13 (hook replacements or documented omissions)
                                      └→ Task 14 (final verification)
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Skill alignment rewrites accidentally change behavior | High | Work in domain batches, diff against upstream after each task, keep A0-only additions minimal |
| Parity tooling becomes noisy and ignored | Medium | Start report-only, keep outputs scoped and readable, classify intentional divergences explicitly |
| Hook porting introduces runtime side effects | High | Separate audit from implementation, keep hook changes minimal, verify with focused tests |
| README and manifest drift again after fixes | Medium | Add repo-contract consistency tests early in Phase 1 |
| `/ship` fix addresses docs but not implementation edge cases | High | Add focused sanitization tests and command contract checks before broader alignment work |

## Open Questions

- None blocking for planning. The user has already approved:
  - `/ship` remains parallel fan-out
  - telemetry stays on by default
  - hooks use selective porting + documented omission
  - parity/reporting comes before broader drift reduction
  - parity enforcement starts as report-only
