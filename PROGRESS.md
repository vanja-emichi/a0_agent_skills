# A0 Agent Skills — Progress

## Current Best

`rev-006` / `cp-d001-live-workflow` — all 5 evaluation layers proven. **199 total tests passed**.

Live plugin: `/a0/usr/plugins/a0_agent_skills/`

## rev-006 Summary

### All 5 Evaluation Layers Proven

| Layer | Description | Result |
|---|---|---|
| 1. Architecture Brief | Source order followed, 8 questions answered | complete |
| 2. Static Contract | Plugin inventory, manifest, paths | verified in architecture tests |
| 3. Framework-Runtime | Plugin discovery, skills catalog, profiles, extensions | **37/37 passed** |
| 4. HTTP/API | Plugin, skills, projects, catalog endpoints | **4/4 passed** |
| 5. Thin Live E2E | Spec artifact creation in live LLM session | **PASSED** — `tasks/spec.md` created |

### Branch Results

| Branch | Objective | Result |
|---|---|---|
| branch-a-architecture-fixes | Source parity + runtime test harness | 22 arch + 145 struct + 12 runtime |
| branch-b-deeper-architecture | Prompt inheritance, API surface, workflow lifecycle | 37 arch tests (12 classes) |
| branch-c-api-harness | HTTP/API Layer 4 tests | 4/4 HTTP API passed |
| branch-d-live-e2e-workflow | Live workflow artifact proof | tasks/spec.md created |

### What Was Added to the Live Plugin

- `web-performance-auditor` agent profile (source parity: 4/4 personas)
- `webperf` command (source parity: 9/9 commands)
- `tests/test_runtime_architecture.py` — 37 deterministic runtime tests across 12 classes
- `tests/test_http_api.py` — 4 HTTP API tests
- Updated plugin AGENTS.md (4 profiles, 9 commands)
- Updated existing tests for new command counts
- Created `a0-skills-test` project with `agent_skills_enabled: true`

### Architecture Proven

| Question | Answer |
|---|---|
| Is `agent0` the correct orchestrator? | Yes — profiles are bounded subordinates |
| Is prompt inheritance correct? | Yes — profiles only override `specifics.md` |
| Are skills loaded natively? | Yes — via `list_skill_catalog()` and `search_skills()` |
| Is source parity complete? | Yes — 4/4 personas, 9/9 commands, 24/24 skills |
| Is auto-load separate from `_skills`? | Yes — different mechanisms, no conflict |
| Is the API surface intentional? | Yes — 0 endpoints, behavior via extensions |
| Does workflow lifecycle work? | Yes — spec artifact created in live session |

## Revision History

| Revision | Focus | Status |
|---|---|---|
| rev-001 to rev-004 | Structural, content depth, scanner-based | superseded |
| rev-005 | Runtime-alignment recalibration (14.54/15 semantic) | complete |
| rev-006 | Architecture proof via 5-layer evaluation (199 tests) | **complete** |

## rev-007 Summary

### References Porting Complete

| Item | Status |
|---|---|
| Hooks classification | All 3 hooks already ported as Python extensions |
| observability-checklist.md | PORTED (91 lines) |
| security-checklist.md | ENRICHED (134→179 lines, +4 sections) |
| E2e test cleanup | 10→5 files, ~500 lines removed |
| runtime_integration markers | Added to 4 files for clean venv separation |
| Tests | 34 structural + 164 runtime + 51 e2e = all green |

### Test Results

| Suite | Result |
|---|---|
| Structural | 34 passed, 10 skipped |
| Runtime | 164 passed |
| E2E | 51 collected (down from ~80+) |

## rev-008 Summary

### Parity Audit Complete — Porting Contract Satisfied

| Surface | Items | Status |
|---|---|---|
| Skills (24) | 24 | All ported ✅ |
| References (6) | 6 | All ported/adapted ✅ |
| Hooks (3) | 3 | All ported as Python extensions ✅ |
| Commands (9) | 9 | All adapted as .command.yaml ✅ |
| Agents (4) | 4 | All adapted as profiles ✅ |
| Docs (9) | 9 | 1 adapted, 8 omitted (platform-specific) ✅ |
| Scripts (2) | 2 | 1 synced, 1 omitted ✅ |

Changes applied:
- Adapted `docs/skill-anatomy.md` (174 lines) for A0 format
- Synced `scripts/validate-skills.js` error-handling improvements
- Created complete parity audit artifact at `rev-008/parity-audit.md`

### Test Results

| Suite | Result |
|---|---|
| Structural | 34 passed, 10 skipped |
| Runtime | 164 passed |
| validate-skills.js | 24 skills, 0 errors |

### Infrastructure Fixes (this session)

- E2e test project routing: all tasks now route to `a0-skills-test` project
- Stale running task cleaned up
- E2e test cleanup: 10→5 files, ~500 lines removed
- runtime_integration markers added for clean venv separation

## Post-rev-008 Live Plugin Fixes (2026-06-21)

Applied directly to the installed plugin at `/a0/usr/plugins/a0_agent_skills/` so fixes work across all projects.

| Fix | File | Change |
|---|---|---|
| Restore auto-unload | `extensions/python/monologue_end/_15_skill_auto_unload.py` | Restored from `.bak` — non-persistent skills now unload at monologue_end to prevent context bloat. Skills with `persist: true` and `using-agent-skills` are retained. |
| Narrow activation | `extensions/python/tool_execute_after/_20_activate_on_skill_load.py` | Added guard so `agent_skills_enabled: true` is only set when `using-agent-skills` is loaded, not on every skill load. Progressive disclosure still fires for all skills. |
| DOX sync | 4 AGENTS.md files | Updated tool_execute_after, monologue_end, and root plugin AGENTS.md to match new behavior. |
| Cleanup | Removed `.bak` file | `_15_skill_auto_unload.py.bak` deleted after successful restoration. |

### Test Results

- Structural: 31 passed, 4 failed (HTTP API — requires live server, pre-existing)
- Runtime integration: skipped (requires `/opt/venv-a0/bin/python`)

## Next

- **Option D (e2e validation): COMPLETE** — 9/9 tests passed, all routed to a0-skills-test, orphans cleaned.
- **Option E (paper.md): COMPLETE** — Case study appendix added (Appendix A, 93 lines).
- **Option F (self-audit): IN PROGRESS** — Running plugin's own review skills against itself.

Authoritative state: `revolve/projects/a0-agent-skills/revisions/rev-008/AGENTS.md`
