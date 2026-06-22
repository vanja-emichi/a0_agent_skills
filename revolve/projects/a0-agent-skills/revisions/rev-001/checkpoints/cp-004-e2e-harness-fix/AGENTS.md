# checkpoints/cp-004-e2e-harness-fix/AGENTS.md

## Checkpoint ID

`cp-004-e2e-harness-fix`

## Parent

`cp-003-scaled` (all 24 skills scaled + observability ported)

## Branch

Evaluation environment (State 3 — harness repair)

## Storage

Live plugin at: `/a0/usr/plugins/a0_agent_skills/tests/e2e/` (6 files modified)

## Restore Method

Rollback to baseline: `cp -r checkpoints/cp-000-baseline/plugin/* /a0/usr/plugins/a0_agent_skills/`

## Changes

### 5 Critical Fixes
1. `_extract_response_text` moved to shared utility in `_a0_e2e_client.py`
2. Wrong log API endpoint fixed: `log_get` → `api_log_get`
3. API key header added to `get_logs()` via `_get_api_key()` helper
4. Missing override file tests rewritten to test absence (ADR-008)
5. Stale DOX propagation test class removed (markers no longer match)

### 7 Important Fixes
6. Task leak fixed in `test_e2e_extension_behavior.py` (2 tests)
7. Task leak fixed in `test_e2e_reference_access.py`
8. Port priority reordered: `[80, 8089, 85, 8000]`
9. Fragile exception handling replaced with HTTP 200-only checks
10. Dead `DOX_MARKER` constant removed
11. Missing extensions added to `EXPECTED_EXTENSIONS`
12. Error checking added to `list_effective_commands()`

## Rationale

The e2e audit revealed the harness had critical bugs making dimension 6 (behavioral) effectively non-functional. Most critically, wrong API endpoint (C2) meant log error checking never worked — every test passed vacuously.

## Results

**Run:** `run-006-e2e-harness-fix` (2026-06-19)
- Structural + Runtime tests: 161 passed, 10 skipped, 39 deselected, 0 failed
- E2e structural tests: 7 passed
- Files modified: 6 (`_a0_e2e_client.py`, `test_e2e_prompt_override.py`, `test_e2e_agent_profiles.py`, `test_e2e_extensions.py`, `test_e2e_extension_behavior.py`, `test_e2e_reference_access.py`)

## Status

`promoted` — externally applied to live plugin. E2e harness now trustworthy for dimension 6.
