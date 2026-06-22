# revolve/projects/a0-agent-skills/revisions/rev-002/AGENTS.md

## Reason

Content depth focus. rev-001 achieved all-green on structural integration. rev-002 shifted to content quality: how well do the skills leverage A0-native concepts, and how deeply are Claude/Codex assumptions removed?

## Parent

`rev-001` — structural integration complete (24 skills, all 6 dimensions green)

## Subject

Live plugin: `/a0/usr/plugins/a0_agent_skills/` (24 skills, all structurally integrated)

## Incumbent

Checkpoint: `checkpoints/cp-000-rev002-baseline`
Status: Incumbent preserved — rev-002 pilot candidates were not promotable within this revision due to a harness comparability issue.

## Evaluation

Contract: `eval/AGENTS.md`

rev-002 eval dimensions focused on **content depth**:
1. **A0-native concept coverage**
2. **Content adaptation depth**
3. **Eval alignment**
4. **Workflow A0-context**

## Acceptance Gates

- **Candidate promotion gate:** Candidate must not regress rev-001 dimensions, and must improve at least one rev-002 dimension.

## Suite Identity

- 24 skills × 4 content depth dimensions = 96 rubric checks
- Plus rev-001 regression check (161 structural + 30 e2e tests)

## Stop Directive

**Runtime stop (user-specified):** Stop after first content depth audit batch (pilot 3-5 skills). User reviews before scaling.

## Branches

| Branch ID | Hypothesis | Status | Best Result | Detail |
|---|---|---|---|---|
| `branch-e-project-context` | Add explicit project-context awareness | promising (carried to rev-003) | `cp-001e`: 5.88/8 avg, +4 total | `branches/branch-e-project-context/AGENTS.md` |
| `branch-f-parallel-delegation` | Add explicit parallel + subordinate guidance | promising (carried to rev-003) | `cp-001f`: 6.08/8 avg, +9 total | `branches/branch-f-parallel-delegation/AGENTS.md` |

## Current Best

Strongest candidate inside rev-002: `cp-001f` — Average 6.08/8 content depth on checkpoint-clone evaluation.

Incumbent remained `cp-000-rev002-baseline` because promotion was blocked by a regression-harness comparability issue.

## Blocker

Checkpoint-clone regression verification was not fully comparable: `test_plugin_helpers_resolve_plugin_and_route_lifecycle_hooks` asserted that plugin resolution equals the live path `/a0/usr/plugins/a0_agent_skills`, so even unchanged checkpoint clones failed one path-bound harness assertion.

## Analysis

Baseline revealed three systematic gaps:
1. **Project context awareness** (20/24 missing)
2. **Parallel tool** (14/24 missing)
3. **Call subordinate** (13/24 missing)

Pilot batch results:
- **Branch E / `cp-001e`:** improved project-context coverage on 4 pilot skills with natural, additive sections.
- **Branch F / `cp-001f`:** produced the strongest automated lift by adding domain-specific `parallel` and `call_subordinate` guidance across all 5 pilot skills.
- Both branches survived content review; neither showed evidence of subject regressions.
- Both branches hit the same remaining regression failure, classified as a **harness/comparability issue**, not a content failure.

This evaluation-context change required a new revision.

## Supersession

`rev-002` is **superseded by `rev-003`** for comparable regression verification. Promising seeds carried forward:
- `branch-f-parallel-delegation` → `cp-001f` (strongest)
- `branch-e-project-context` → `cp-001e` (complementary)

## Next Action

`rev-002` is closed. Resume work in `revisions/rev-003/AGENTS.md`.
