# Implementation Plan: GitHub Actions CI Validation

## Overview

Add a GitHub Actions CI pipeline that validates the plugin structure on every push and pull request. The pipeline runs a pure-Python validation script that checks all plugin components — no external tools or Claude Code CLI required. The script is also runnable locally for pre-commit validation.

## Architecture Decisions

- **Pure Python script, no external deps** — Upstream used `claude plugin validate .` (Claude Code CLI). We write our own validator using only Python stdlib (yaml via `python3-yaml`, pathlib, sys). No npm install, no Claude CLI. Runs anywhere Python 3.8+ is available.
- **Script-first, CI-second** — The validation script is the primary artifact. CI just calls it. This makes local validation identical to CI validation.
- **Exit code contract** — Script exits 0 on full pass, 1 on any failure. CI fails the workflow on non-zero exit.
- **Clear per-check output** — Each check prints PASS/FAIL with the file path and reason. Human-readable and machine-parseable.

## Dependency Graph

```
SPEC.md (existing)
    │
    ├── scripts/validate.py          ← T1: validation logic
    │       │
    │       └── .github/workflows/ci.yml  ← T2: calls script in CI
    │               │
    │               └── README.md update  ← T3: CI badge
```

Implementation order: T1 → T2 → T3 (each depends on prior).

---

## Tasks

### Phase 1: Validation Script

#### Task 1: Python validation script

**Description:** Write `scripts/validate.py` — a standalone Python 3 script that validates the plugin structure. Covers all components defined in SPEC.md. Runs locally and in CI. Produces clear per-check output.

**What it validates:**

| Check | Rule |
|-------|------|
| `plugin.yaml` | Must exist; must have `name`, `title`, `version`, `description` fields |
| `skills/*/SKILL.md` | Each skill dir must have SKILL.md; must have YAML frontmatter with `name` and `description` |
| `agents/*/agent.yaml` | Each agent dir must have agent.yaml; must have `title`, `description`, `context` |
| `agents/*/prompts/agent.system.main.specifics.md` | Must exist for each agent |
| `commands/*.command.yaml` | Must have `name`, `description`, `type`, `template_path`; paired `.txt` must exist |
| `extensions/**/*.py` | Files named `_NN_*.py` — valid Python syntax (`py_compile`) |
| `references/*.md` | Must be non-empty |

**Acceptance criteria:**
- [ ] Script exits 0 on this repo (all checks currently pass)
- [ ] Script exits 1 if any check fails
- [ ] Each check prints `PASS` or `FAIL [reason] [path]`
- [ ] Summary at end: `N checks passed, M failed`
- [ ] Runs with `python3 scripts/validate.py` from repo root
- [ ] No external pip dependencies (only stdlib + PyYAML which is always available)

**Verification:**
```bash
cd /a0/usr/projects/agent_skills
python3 scripts/validate.py
echo "Exit: $?"
```

**Dependencies:** None (first task)

**Files touched:**
- `scripts/validate.py` (new)

**Estimated scope:** S (1 file, ~80-100 lines)

---

### Checkpoint: After Task 1

- [ ] `python3 scripts/validate.py` runs and exits 0
- [ ] All 7 check categories produce PASS output
- [ ] Intentionally breaking a check (e.g., removing a required field) produces FAIL + exits 1

---

### Phase 2: CI Workflow

#### Task 2: GitHub Actions workflow

**Description:** Write `.github/workflows/ci.yml` that runs the validation script on every push and pull request. No external tools needed — just Python 3 (pre-installed on all GitHub runners).

**Acceptance criteria:**
- [ ] Workflow triggers on `push` and `pull_request` to `main`
- [ ] Uses `ubuntu-latest` runner
- [ ] Steps: checkout → run `python3 scripts/validate.py`
- [ ] Workflow YAML is valid
- [ ] CI passes on first push after this task
- [ ] Workflow name and job name are human-readable in GitHub UI

**Verification:**
```bash
# Local YAML syntax check
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
echo "YAML valid: $?"
# Then: push to GitHub and verify Actions tab shows green
```

**Dependencies:** Task 1 (script must exist)

**Files touched:**
- `.github/workflows/ci.yml` (new)
- `.github/` directory (new)

**Estimated scope:** XS (~25 lines YAML)

---

### Checkpoint: After Task 2

- [ ] GitHub Actions run visible at `https://github.com/vanja-emichi/a0_agent_skills/actions`
- [ ] Most recent run shows green checkmark
- [ ] All 7 check categories pass in CI log

---

### Phase 3: Documentation

#### Task 3: README CI badge

**Description:** Add GitHub Actions CI badge to README.md so plugin users can see build status at a glance.

**Acceptance criteria:**
- [ ] Badge at top of README, below the title
- [ ] Badge links to the Actions workflow runs page
- [ ] Badge shows current status (green after Task 2 CI passes)

**Verification:**
```bash
# Check badge markdown is correct
head -10 README.md | grep actions
```

**Dependencies:** Task 2 (CI must exist to have a badge URL)

**Files touched:**
- `README.md` (patch — add 1 line)

**Estimated scope:** XS (1 line)

---

### Checkpoint: Complete

- [ ] `python3 scripts/validate.py` passes locally
- [ ] GitHub Actions shows green on latest commit
- [ ] README badge visible and green
- [ ] All success criteria from SPEC.md CI section met

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PyYAML not available on runner | Medium | GitHub ubuntu-latest has python3-yaml pre-installed; add `pip install pyyaml` step as fallback |
| Validation too strict, breaks on edge cases | Low | Test locally first on real repo before pushing CI |
| Symlinks in .a0proj not committed | None | .a0proj is gitignored; validation script only checks tracked files |

## Open Questions

- Should CI also validate Python extension syntax beyond `py_compile` (e.g., import check)? Currently: no, too risky without A0 framework available in CI.
- Should we add a `workflow_dispatch` trigger for manual runs? Nice to have — easy to add.
