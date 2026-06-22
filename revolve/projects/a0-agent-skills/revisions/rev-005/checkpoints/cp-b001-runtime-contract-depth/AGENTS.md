# revolve/projects/a0-agent-skills/revisions/rev-005/checkpoints/cp-b001-runtime-contract-depth/AGENTS.md — Runtime Contract Depth Candidate

## Checkpoint ID

`cp-b001-runtime-contract-depth`

## Parent

`cp-a001-harness-truth`

## Branch

`branch-b-runtime-contract-depth`

## Storage

`checkpoints/cp-b001-runtime-contract-depth/subject/a0_agent_skills.tar.gz (compressed)`

## Baseline Result

`run-008-semantic-depth-baseline`: avg 11.12/15 (74.2%); D1 avg 0.75/3 (universally weakest)

## Changes

Added domain-specific `### A0 Runtime Model` sections to all 24 skills. Each section teaches how that skill's specific workflow intersects with real Agent Zero runtime behavior:

- Protocol/Extras context layering
- Two Python environments (/opt/venv-a0 vs /opt/venv)
- Lifecycle hooks (monologue_end, tool_execute_before/after, message_loop_start)
- Scheduler/chat.json runtime evidence
- promptinclude/behaviour_adjustment persistence
- Plugin discovery and extension framework
- LogItem dataclass schema
- Framework import patterns

## Post-Edit Results

- `run-009`: semantic depth avg **13.29/15 (88.6%)**; D1 avg **2.79/3** (19/24 skills at 3/3)
- `run-010`: static gates passed — gate_failures=0, advisory_failures=0
- `run-011`: structural regression passed — 145 passed, 10 skipped
- `run-012`: runtime regression passed — 16 passed; live restored byte-for-byte

## Semantic Depth Improvement

| Dimension | Baseline | After D1 Edits | Change |
|---|---:|---:|---:|
| D1 Runtime Model | 0.75/3 | 2.79/3 | **+2.04** |
| D2 Non-Boilerplate | 2.88/3 | 2.88/3 | +0.0 |
| D3 Tool Patterns | 2.96/3 | 3.0/3 | +0.04 |
| D4 Project Depth | 2.42/3 | 2.5/3 | +0.08 |
| D5 Eval Specificity | 2.12/3 | 2.12/3 | +0.0 |
| **Total** | **11.12/15** | **13.29/15** | **+2.17** |

## Decision

`internally promoted` as rev-005 current best. Eligible for external promotion.

## Status

`promoted` internally and externally.

## Rollback Note

No live rollback needed. External promotion complete via `external-promotion-002-cp-b001`.

## External Promotion

`external-promotion-002-cp-b001` applied `cp-b001-runtime-contract-depth` to `/a0/usr/plugins/a0_agent_skills/` and passed all post-promotion verification checks.
