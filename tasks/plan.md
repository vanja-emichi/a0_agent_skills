# Implementation Plan: Karpathy Coding Guidelines — Option B Integration

## Overview

Patch 7 existing skill files with the unique, A0-specific content from `karpathy-coding-guidelines`. No new skills created. No existing sections rewritten. Each patch is self-contained and independently revertable.

## Principles

- **Patch-only** — `text_editor:patch`, never `text_editor:write` on existing files
- **Read first** — `text_editor:read` the full skill before patching
- **Verify after** — check line count doesn't exceed 500, skill loads without error
- **No duplication** — new sections add only what the karpathy SKILL.md has that the target skill doesn't

## Dependency Graph

```
SPEC.md (existing)
     │
     ├── T1: context-engineering          ─┐
     ├── T2: spec-driven-development       │
     ├── T3: incremental-implementation    │  All independent
     ├── T4: test-driven-development       │  (different files)
     ├── T5: git-workflow-and-versioning   │
     ├── T6: code-review-and-quality      ─┘
     ├── T7: using-agent-skills
     │
     └── T8: CI validation + commit
```

All T1–T7 are independent and could be parallelized. T8 is a gate that runs after all patches are applied.

---

## Tasks

### Phase 1: High-Value Unique Content

The most unique Karpathy content — not covered by any existing skill.

#### Task 1 — `skills/context-engineering/SKILL.md`

**Adds two new sections at the end of the file:**

**Section A: `## Agent Zero Discipline (Think Before Coding)`**

Content from Karpathy P1 — A0-specific `thoughts[]` pattern:
- Pre-coding `thoughts[]` checklist: restate goal, list assumptions, surface interpretations, propose simple approach, read first
- Stop-and-ask triggers: guessing file paths, ambiguous requirements, code not understood, public interface change
- Example `thoughts[]` pattern with inline comments
- Complete A0 coding workflow diagram (from karpathy SKILL.md)

**Section B: `## Safe Operations Protocol`**

Content from Karpathy P5 — fully missing from all existing skills:
- What counts as destructive (rm, DROP TABLE, git push --force, production deploys, irreversible API calls)
- 4 rules: state implication in thoughts → confirm with user → verify safety first → use notify_user
- Example thoughts pattern for destructive ops
- Example response warning template

**Acceptance criteria:**
- [ ] Section A present in context-engineering SKILL.md
- [ ] Section B present with full Safe Operations rules
- [ ] File still valid YAML frontmatter
- [ ] File under 500 lines after patch
- [ ] No content duplicated from existing sections

**Verification:**
```bash
wc -l skills/context-engineering/SKILL.md   # must be ≤ 500
grep -c 'Safe Operations' skills/context-engineering/SKILL.md   # must be ≥ 1
grep -c 'thoughts' skills/context-engineering/SKILL.md           # must be ≥ 1
python3 scripts/validate.py
```

**Files touched:** `skills/context-engineering/SKILL.md` (patch)

**Estimated scope:** M (two sections, ~40-60 lines of new content)

---

#### Task 2 — `skills/spec-driven-development/SKILL.md`

**Adds one new section: `## Agent Zero Clarification Protocol`**

Content from Karpathy P1 stop-and-ask, adapted for spec context:
- When to stop and ask vs proceed: ambiguous requirements, multiple interpretations, missing context
- Read existing code before specifying (not just ask questions)
- Example of presenting options vs picking silently

**Acceptance criteria:**
- [ ] New section present in spec-driven-development SKILL.md
- [ ] Contains stop-and-ask triggers specific to spec phase
- [ ] File under 500 lines
- [ ] No duplication with existing "Ask Clarifying Questions" section

**Verification:**
```bash
wc -l skills/spec-driven-development/SKILL.md
grep -c 'Clarification Protocol\|stop.*ask\|present.*options' skills/spec-driven-development/SKILL.md
python3 scripts/validate.py
```

**Files touched:** `skills/spec-driven-development/SKILL.md` (patch)

**Estimated scope:** S (~15-20 lines)

---

### Phase 2: Tool Discipline

#### Task 3 — `skills/incremental-implementation/SKILL.md`

**Adds to Rule 0: `### A0 Tool Selection Guide` subsection**

Table from Karpathy P2:

| Situation | Preferred Approach |
|-----------|-------------------|
| Simple text transformation | `terminal` with `sed`, `awk`, `grep` |
| File inspection | `text_editor:read` — not a Python script |
| Targeted edit to existing file | `text_editor:patch` — not `text_editor:write` |
| Multi-step logic or computation | Python in `code_execution_tool` |
| Reusable component | Only modularize if reuse was asked for |

**Adds to Rule 0.5: `### A0 Tool Discipline` subsection**

Content from Karpathy P3:
- `text_editor:read` the file before any patch
- Use `text_editor:patch` for edits — `text_editor:write` only for new files
- `git diff --stat && git diff` audit before responding
- Collateral changes → revert, mention in response

**Acceptance criteria:**
- [ ] Tool selection table present under Rule 0
- [ ] Tool discipline rules present under Rule 0.5
- [ ] File under 500 lines
- [ ] No duplication with existing Rule 0 / Rule 0.5 content

**Verification:**
```bash
wc -l skills/incremental-implementation/SKILL.md
grep -c 'text_editor:patch\|Tool Selection' skills/incremental-implementation/SKILL.md
python3 scripts/validate.py
```

**Files touched:** `skills/incremental-implementation/SKILL.md` (patch)

**Estimated scope:** S (~25-30 lines)

---

### Phase 3: Verification & Review

#### Task 4 — `skills/test-driven-development/SKILL.md`

**Adds to Verification section: `### Goal-Driven Verification Loop`**

Content from Karpathy P4:
- Weak→strong task transformation table
- Never-report-success-without-output mandate
- Re-verify loop — diagnose → fix → re-verify (don't give up)
- Verification commands cheatsheet (pytest, npm test, smoke test)

**Acceptance criteria:**
- [ ] Goal-driven table present
- [ ] "never report success without verification output" rule present
- [ ] File under 500 lines
- [ ] No duplication with existing Verification section checklist

**Verification:**
```bash
wc -l skills/test-driven-development/SKILL.md
grep -c 'Goal-Driven\|never report' skills/test-driven-development/SKILL.md
python3 scripts/validate.py
```

**Files touched:** `skills/test-driven-development/SKILL.md` (patch)

**Estimated scope:** S (~25-30 lines)

---

#### Task 5 — `skills/git-workflow-and-versioning/SKILL.md`

**Adds to Section 3 (Descriptive Messages): `### A0 Commit Strictness`**

Content from Karpathy P6 — stricter than existing rules:
- Subject ≤50 chars rule (count characters, not words)
- Imperative mood only: `add`, `fix`, `remove` — not `added`, `fixes`, `fixing`
- No trailing period on subject line
- Never include AI attribution (`Co-authored-by: Claude`, `Generated by AI`, etc.)
- Body only when the *why* is not obvious — not a summary of the diff

**Acceptance criteria:**
- [ ] ≤50 chars rule present
- [ ] No AI attribution rule present
- [ ] File under 500 lines
- [ ] No duplication with existing "Descriptive Messages" section

**Verification:**
```bash
wc -l skills/git-workflow-and-versioning/SKILL.md
grep -c 'AI attribution\|50 char' skills/git-workflow-and-versioning/SKILL.md
python3 scripts/validate.py
```

**Files touched:** `skills/git-workflow-and-versioning/SKILL.md` (patch)

**Estimated scope:** S (~20 lines)

---

#### Task 6 — `skills/code-review-and-quality/SKILL.md`

**Adds to Step 4 (Categorize Findings): `### Per-Line Notation (Compact Format)`**

Content from Karpathy P7 — complement to existing 5-axis severity labels:
- Format: `L<line>: <severity> <problem>. <fix>.`
- Severity labels: 🔴 bug, 🟡 risk, 🔵 nit, ❓ q
- 3 examples showing the format in use
- What to drop (hedging, "I noticed that...", restating what the line does)
- Auto-clarity exception (write full paragraph for CVE-class bugs)

**Acceptance criteria:**
- [ ] Per-line notation section present under Step 4
- [ ] All 4 severity emoji labels documented
- [ ] 3 examples present
- [ ] File under 500 lines
- [ ] Does not replace existing Critical/Nit/Optional/FYI labels — complements them

**Verification:**
```bash
wc -l skills/code-review-and-quality/SKILL.md
grep -c 'Per-Line Notation\|L<line>' skills/code-review-and-quality/SKILL.md
python3 scripts/validate.py
```

**Files touched:** `skills/code-review-and-quality/SKILL.md` (patch)

**Estimated scope:** S (~25-30 lines)

---

### Phase 4: Meta-Skill Update

#### Task 7 — `skills/using-agent-skills/SKILL.md`

**Adds reference to karpathy-coding-guidelines in skill discovery section**

Content:
- `karpathy-coding-guidelines` entry in the skill reference table/list
- Note: Karpathy principles are now embedded in individual skills — this is the full reference
- When to load it directly: before any non-trivial coding task as full principles reference

**Acceptance criteria:**
- [ ] `karpathy-coding-guidelines` referenced in using-agent-skills
- [ ] Correct description of relationship (embedded vs full reference)
- [ ] File under 500 lines

**Verification:**
```bash
wc -l skills/using-agent-skills/SKILL.md
grep -c 'karpathy' skills/using-agent-skills/SKILL.md
python3 scripts/validate.py
```

**Files touched:** `skills/using-agent-skills/SKILL.md` (patch)

**Estimated scope:** XS (~10 lines)

---

### Phase 5: Validation & Commit

#### Task 8 — CI validation + single commit

**After all 7 patches are applied:**

1. Run `python3 scripts/validate.py` — must exit 0 (44 checks, all PASS)
2. Run `python3 -m pytest tests/ -v` — 39/39 must pass (no test changes needed)
3. Check each patched skill line count ≤ 500
4. Single commit: `feat: integrate karpathy A0-specific discipline into skills (Option B)`
5. Push to GitHub, verify CI green

**Acceptance criteria:**
- [ ] All 7 patches applied
- [ ] `python3 scripts/validate.py` exits 0
- [ ] `python3 -m pytest tests/ -v` → 39 passed
- [ ] No SKILL.md exceeds 500 lines
- [ ] CI green on GitHub Actions

**Verification:**
```bash
python3 scripts/validate.py
python3 -m pytest tests/ -v
for f in skills/*/SKILL.md; do lines=$(wc -l < $f); echo "$lines $f"; done | sort -rn | head -5
git log --oneline -1
```

---

## Checkpoints

**After Phase 1 (T1+T2):** context-engineering has both unique sections, spec-driven-development has clarification protocol. Both validate OK.

**After Phase 2 (T3):** incremental-implementation has A0 tool discipline embedded. Validate OK.

**After Phase 3 (T4+T5+T6):** TDD, git, and code review skills all enriched. Validate OK.

**After Phase 4 (T7):** Meta-skill links to karpathy reference. Validate OK.

**Final (T8):** Full validation suite passes. CI green. Single commit.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Patch pushes a skill over 500 lines | Medium | Check `wc -l` after each patch; split into smaller additions if needed |
| Content accidentally duplicates existing section | Medium | Read full skill before patching; compare with karpathy content |
| Patch applies to wrong line numbers (file drifts) | Low | Always `text_editor:read` immediately before `text_editor:patch` |
| CI fails due to frontmatter issue | Low | `python3 scripts/validate.py` catches this before push |
