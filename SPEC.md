# Spec: Karpathy Coding Guidelines Integration (Option B)

## Objective

Merge the unique, Agent Zero-specific parts of `karpathy-coding-guidelines` into existing agent-skills. No new skill is created. No content is duplicated. Each skill receives a targeted patch adding only the Karpathy content that is NOT already covered.

**Target users:** Agent Zero developers using the plugin — all 20 skills become richer without needing to explicitly load a separate karpathy skill.

**Primary value:** The A0-specific behavioral patterns (tool discipline, safe operations, thoughts[] structure, verification loop, per-line review notation) are embedded into the skills where they're most relevant. A developer following any skill automatically gets Karpathy-quality discipline.

**What we do NOT do:**
- Duplicate content that already exists in the skill
- Rewrite existing sections
- Add Karpathy content that has >80% overlap with existing content (see Overlap Analysis below)
- Create a new standalone skill

---

## Overlap Analysis — What We Skip

| Karpathy Principle | Existing Skill | Overlap | Decision |
|---|---|---|---|
| P2 Simplicity First (general) | `incremental-implementation` Rule 0 | ~85% | Skip rewrite. Add A0 tool selection table only. |
| P3 Surgical Changes (general) | `incremental-implementation` Rule 0.5 | ~80% | Skip rewrite. Add A0 tool discipline commands only. |
| P6 Terse Commits (general) | `git-workflow-and-versioning` Descriptive Messages | ~70% | Add ≤50 chars rule + no-AI-attribution rule only. |
| P7 Structured Review (general 5-axis) | `code-review-and-quality` Step 4 | ~60% | Add per-line L<line> notation as complement to 5-axis. |

---

## What Gets Integrated — The 7 Patches

### Patch 1 — `skills/context-engineering/SKILL.md`

**Adds two new sections:**

**Section A: A0 Agent Discipline (from P1 Think Before Coding)**

Before any `code_execution_tool` or `text_editor` call, `thoughts[]` must answer:
1. What is the task? (restate goal)
2. What are my assumptions? (list explicitly)
3. Are there multiple interpretations? (present — don't pick silently)
4. Is there a simpler approach? (propose before complex one)
5. What context do I need? (read existing code first)

Stop-and-ask triggers:
- About to guess a file path or function name
- Requirement has two plausible interpretations
- Don't fully understand code about to be modified
- Simplest solution would change a public interface

Example `thoughts[]` pattern (P1 format).

**Section B: Safe Operations Protocol (from P5 — UNIQUE, not in any existing skill)**

What counts as destructive: file/dir deletion, database drops, git force operations, production deploys, irreversible API calls.

Rules:
1. State full implication in `thoughts` — what data/state is permanently lost
2. Confirm with user in `response` before executing — never proceed silently
3. Verify safety first — `git status`, confirm backups, dry-run where possible
4. Use `notify_user` for high-impact mid-task warnings

Example thoughts pattern + response warning format.

**Rationale for context-engineering:** Both A0 discipline and safe operations are about HOW the agent operates — not about code quality or testing. context-engineering is the skill about agent setup and behavioral discipline. security-and-hardening is about OWASP/code vulnerabilities, not agent behavioral safety.

---

### Patch 2 — `skills/spec-driven-development/SKILL.md`

**Adds one section: A0 Clarification Protocol (from P1 — stop-and-ask)**

Before writing any spec or proceeding to implementation, surface:
- Ambiguous requirements → ask before proceeding
- Multiple plausible interpretations → present options, don't pick silently
- Missing context → read existing code before specifying

This extends the existing "Ask Clarifying Questions" section with A0-specific stop-and-ask triggers.

**Rationale:** spec-driven-development already covers clarification, but not the specific triggers for WHEN to stop and ask vs proceed. Karpathy P1's stop-and-ask list fills this gap.

---

### Patch 3 — `skills/incremental-implementation/SKILL.md`

**Adds to Rule 0 (Simplicity First): A0 Tool Selection Guide**

| Situation | Preferred Approach |
|-----------|-------------------|
| Simple text transformation | `terminal` with `sed`, `awk`, `grep` |
| File inspection | `text_editor:read` — not a Python script |
| Targeted edit to existing file | `text_editor:patch` — not `text_editor:write` |
| Multi-step logic or computation | Python in `code_execution_tool` |
| Reusable component | Only modularize if reuse was asked for |

**Adds to Rule 0.5 (Scope Discipline): A0 Tool Discipline**

Always read before editing:
- `text_editor:read` the file/section before any patch
- Use `text_editor:patch` for edits to existing files — `text_editor:write` only for new files
- Run `git diff --stat && git diff` before responding — every changed line must trace to the request
- Collateral changes seen? Revert them, mention in response instead

**Rationale:** These are pure Agent Zero tool mechanics. The existing Rule 0 and Rule 0.5 cover the principle but not the A0-specific tool commands.

---

### Patch 4 — `skills/test-driven-development/SKILL.md`

**Adds to Verification section: Goal-Driven Verification Loop (from P4)**

| Imperative (weak) | Goal-Driven (strong) |
|---|---|
| "Add validation" | "Write tests for invalid inputs → make them pass" |
| "Fix the bug" | "Write a test that reproduces it → make it pass" |
| "Refactor X" | "Tests pass before; tests pass after; diff is smaller" |

Verification mandate:
- Never report success without showing verification output
- If verification fails → diagnose root cause → fix → re-verify (loop — don't give up)
- Always run and attach output: `python -m pytest tests/ -v` or `npm test`

**Rationale:** TDD skill covers Red-Green-Refactor but not the explicit "never report success without evidence" mandate, nor the re-verify loop. This strengthens the verification story.

---

### Patch 5 — `skills/git-workflow-and-versioning/SKILL.md`

**Adds strictness to Section 3 (Descriptive Messages):**

- Subject ≤50 chars — count characters, not words
- Imperative mood only: `add`, `fix`, `remove` — not `added`, `fixes`, `fixing`
- No trailing period on subject line
- Never include AI attribution in commits (`Co-authored-by: Claude`, `Generated by AI`, etc.)
- Body only when the *why* is not obvious — not a summary of what the diff shows

**Rationale:** git-workflow-and-versioning covers format but is looser on length and doesn't address AI attribution (increasingly common issue in A0 context).

---

### Patch 6 — `skills/code-review-and-quality/SKILL.md`

**Adds to Step 4 (Categorize Findings): Per-Line Notation**

For surgical, line-level findings, use the compact format as complement to the 5-axis severity labels:

```
L<line>: <severity> <problem>. <fix>.
```

Severity labels:
- `🔴 bug:` — broken behavior, will cause incident
- `🟡 risk:` — works but fragile (null check, race, swallowed error)
- `🔵 nit:` — style/naming — author can ignore
- `❓ q:` — genuine question, not a suggestion

Examples:
```
L42: 🔴 bug: user can be null after .find(). Add guard before .email.
L88-140: 🔵 nit: 50-line fn does 4 things. Extract validate/normalize/persist.
L23: 🟡 risk: no retry on 429. Wrap in withBackoff(3).
```

Drop: "I noticed that...", "You might want to consider...", hedging, restating what the line does.

**Rationale:** The existing skill uses Critical/Nit/Optional/FYI labels which are broad and paragraph-oriented. The L<line> notation complements this for surgical, line-level findings — particularly useful in agent-to-agent reviews.

---

### Patch 7 — `skills/using-agent-skills/SKILL.md`

**Adds reference to karpathy-coding-guidelines** in the meta-skill discovery section:

- `karpathy-coding-guidelines` — load before any non-trivial coding task for A0 behavioral discipline (full principles reference)
- Note that Karpathy principles are now embedded in individual skills — the standalone skill is the full reference, the plugin skills are the embedded practice

**Rationale:** The meta-skill governs discovery. Users who want the full Karpathy reference should know it exists as a global skill.

---

## Tech Stack / Constraints

- Pure Markdown patches — no code changes
- Follow `docs/skill-anatomy.md` format for any new sections
- Keep SKILL.md files under 500 lines
- No duplication: if content is >80% same as existing, add a cross-reference instead
- Patch style: add clearly-labeled sections (e.g. `## Agent Zero Tool Discipline`), don't rewrite existing sections

---

## Code Style

- New sections use `##` or `###` headings consistent with the file's existing heading depth
- Tables, code blocks, and bullet lists — match the skill's existing formatting style
- A0-specific content labeled clearly ("Agent Zero", "A0", or "In Agent Zero Terms")
- Every patch is self-contained — can be reverted without affecting surrounding content

---

## Testing Strategy

- Manual: load each patched skill via `skills_tool:load` and verify it loads without error
- Manual: read each patched SKILL.md and verify the new section is present and correct
- CI: `scripts/validate.py` validates all SKILL.md frontmatter — run and confirm 0 failures
- No unit tests required — these are Markdown patches

---

## Boundaries

**Always:**
- Patch only — never rewrite existing sections
- New content must be uniquely Karpathy / A0-specific — no general advice
- Keep each patch focused: one concept, one section, one skill

**Ask first:**
- If a patch would exceed 500 lines for the target skill
- If a principle maps equally well to two skills

**Never:**
- Duplicate content between skills
- Remove or rewrite existing skill content
- Add general software engineering advice that has no A0-specific angle
- Add karpathy-coding-guidelines as a plugin skill (it's a global skill — leave it there)

---

## Success Criteria

- [ ] All 7 patches applied — 6 skills updated + using-agent-skills
- [ ] Each patch adds only unique, non-duplicated content
- [ ] No SKILL.md exceeds 500 lines after patches
- [ ] `python3 scripts/validate.py` exits 0 — all frontmatter valid
- [ ] Each patched skill loads correctly via `skills_tool:load`
- [ ] The A0 Safe Operations protocol is present in `context-engineering`
- [ ] The `thoughts[]` pattern is present in `context-engineering`
- [ ] Per-line L<line> notation is present in `code-review-and-quality`
- [ ] Commit message: `feat: integrate karpathy A0-specific discipline into skills (Option B)`

---

## Open Questions

- Should the `git diff --stat` audit step be added to CI as an automated check?
- Should the A0 Complete Coding Workflow diagram from karpathy-coding-guidelines be embedded in `context-engineering` as a summary diagram, or is it better left in the standalone karpathy skill?
