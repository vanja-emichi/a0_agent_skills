# Todo: GitHub Actions CI Validation

## Phase 1: Validation Script
- [ ] T1: Write `scripts/validate.py` — pure Python, validates plugin.yaml, skills, agents, commands, extensions, references

**Checkpoint:** `python3 scripts/validate.py` exits 0; intentional break exits 1

## Phase 2: CI Workflow
- [ ] T2: Write `.github/workflows/ci.yml` — push + PR triggers, ubuntu-latest, calls validate.py

**Checkpoint:** GitHub Actions green on first push

## Phase 3: Documentation
- [ ] T3: Add CI badge to README.md

**Checkpoint: Complete**
- [ ] Local validate passes
- [ ] GitHub Actions green
- [ ] README badge visible
