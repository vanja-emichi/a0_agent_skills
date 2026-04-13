# Todo: GitHub Actions CI Validation

## Phase 1: Validation Script
- [x] T1: Write `scripts/validate.py` — pure Python, validates plugin.yaml, skills, agents, commands, extensions, references

**Checkpoint:** ✅ `python3 scripts/validate.py` exits 0; 37/37 tests pass

## Phase 2: CI Workflow
- [x] T2: Write `.github/workflows/ci.yml` — push + PR triggers, ubuntu-latest, calls validate.py

**Checkpoint:** Push to GitHub and verify Actions tab green

## Phase 3: Documentation
- [x] T3: Add CI badge to README.md

**Checkpoint: Complete**
- [ ] Local validate passes ✅
- [ ] GitHub Actions green (verify after push)
- [ ] README badge visible
