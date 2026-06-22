# revolve/projects/a0-agent-skills/revisions/rev-008/AGENTS.md — Parity Audit Revision

## Reason

Complete the Agent-Skills Porting Contract by classifying all remaining upstream surfaces (docs/, scripts/, platform command formats) as port/adapt/omit.

## Parent

`rev-007` (references porting + e2e cleanup, closed)

## Subject

Live plugin at `/a0/usr/plugins/a0_agent_skills/`.

## Incumbent

cp-a001-parity-audit (promoted)

## Evaluation

Structural + runtime regression tests + validate-skills.js.

## Acceptance Gates

1. All structural tests pass — 34 passed ✓
2. All runtime tests pass — 164 passed ✓
3. validate-skills.js passes — 0 errors ✓
4. Parity audit artifact complete — 187 lines ✓
5. skill-anatomy.md adapted for A0 — 174 lines ✓
6. validate-skills.js error-handling synced ✓

## Post-Revision Live Fixes (2026-06-21)

Three fixes applied to the live plugin after rev-008 closure:

1. **Auto-unload restored** — `_15_skill_auto_unload.py` restored from `.bak`; non-persistent skills now unload at monologue_end across all projects.
2. **Activation narrowed** — `_20_activate_on_skill_load.py` patched so `agent_skills_enabled` flag only fires for `using-agent-skills`, not every skill load.
3. **DOX updated** — 4 AGENTS.md files synced with new behavior.

Structural tests pass (31/31 non-server). These are runtime-behavior fixes, not subject changes, so no new revision is required.

## Stop Directive

Complete. All objectives met.

## Active Branches

| Branch | Status | Best Result | Next |
|---|---|---|---|
| branch-a-parity-audit | promoted | 34p struct + 164p runtime + 0 errors | none |

## Current Best

cp-a001-parity-audit: all gates passed, promoted.

## Blocker

None.

## Next Action

Revision complete. Agent-Skills Porting Contract is now **fully satisfied**.

## Conclusion

All upstream surfaces classified:
- 24 skills: fully ported ✓
- 6 references: fully ported/adapted ✓
- 3 hooks: fully ported as Python extensions ✓
- 9 commands: fully adapted as .command.yaml ✓
- 4 agents: fully adapted as profiles ✓
- 9 docs: 1 adapted (skill-anatomy.md), 8 omitted (platform-specific) ✓
- 2 scripts: 1 synced (validate-skills.js), 1 omitted (validate-commands.js) ✓
- Platform dirs (.claude, .gemini, .opencode, .claude-plugin): all omitted ✓
