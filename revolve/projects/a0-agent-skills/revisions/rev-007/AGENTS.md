# revolve/projects/a0-agent-skills/revisions/rev-007/AGENTS.md — References Porting Revision

## Reason

Classify upstream hooks/ and references/ as port/adapt/omit. Hooks already fully ported as Python extensions. Two references needed action: observability-checklist.md (missing) and security-checklist.md (enrich with adapted missing sections). Plus e2e test suite cleanup.

## Parent

`rev-006` (architecture proof, closed)

## Subject

Live plugin at `/a0/usr/plugins/a0_agent_skills/`.

## Incumbent

cp-a001-references-port (promoted)

## Evaluation

Structural + runtime + reference content checks. See `eval/AGENTS.md`.

## Acceptance Gates

All gates passed: EC-001 through EC-006.

## Stop Directive

Complete. All objectives met.

## Active Branches

| Branch | Status | Hypothesis | Best Result | Next |
|---|---|---|---|---|
| branch-a-references-porting | promoted | Port observability + enrich security | 34p struct + 164p runtime + 6 refs | none |

## Current Best

cp-a001-references-port: all gates passed, promoted.

## Blocker

None.

## Next Action

Revision complete. No further action needed.
