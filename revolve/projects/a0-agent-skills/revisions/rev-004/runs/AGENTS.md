# revolve/projects/a0-agent-skills/revisions/rev-004/runs/AGENTS.md

## Purpose

Run index for revision rev-004.

## Run Index

| Run ID | Checkpoint | Suite | Score | Validity | Raw Result | Decision |
|---|---|---|---|---|---|---|
| `run-001-rev004-baseline-rubric` | `cp-000-rev004-baseline` | LLM rubric (5 pilot skills) | avg 8.4/12 | valid | subordinate report | Baseline — universal D3 gap found |
| `run-002-rev004-merged-scan` | `cp-001-merged` | content depth scan (live-overlay) | avg 7.96/8 (191/192) | valid | `runs/raw/run-002-rev004-merged-scan.json` | No regression from baseline |
| `run-002b-rev004-merged-pytest` | `cp-001-merged` | live-overlay regression guard | 161 pass, 0 fail | valid | `runs/raw/run-002b-rev004-merged-pytest.txt` | Candidate PROMOTABLE |
| `run-003-rev004-fullscale` | live plugin (all 24 skills) | content depth + regression | **avg 8.0/8 (192/192); 161 pass, 0 fail** | valid | `runs/raw/run-003-rev004-fullscale-scan.json`, `runs/raw/run-003-rev004-fullscale-pytest.txt` | **PERFECT SCORE — full-scale promotion complete** |

## Run Details

### run-003-rev004-fullscale

- **Date:** 2026-06-20
- **Content depth:** **8.0/8 (192/192)** — ALL 24 SKILLS PERFECT
- **Delta vs original rev-003 baseline:** +55 total, +2.29 average (5.71→8.0)
- **Regression guard:** 161 passed, 10 skipped, 69 deselected, 0 failed — exit 0
- **memory_save check:** Zero references found across all skills
- **Changes applied (full-scale, 24 skills):**
  - 24 A0-specific eval cases added (1 per skill)
  - JSON tool-call examples added to all skills' Parallel Work sections
  - memory_save/memory_load references fixed (7 total across code-review, context-engineering)
  - pytest alternatives added alongside npm test in all verification sections
  - Python framework examples added (Flask, Django, FastAPI, pydantic, ruff, mypy)
  - interview-me parallel scanner gap fixed
