# Implementation Plan: Caveman Communication Compression — Option B Integration

## Overview

Patch 5 files with 6 patches adding the unique, A0-specific parts of `caveman` compression into existing agent-skills. No new skills created. No existing sections rewritten. Each patch is self-contained and independently revertable.

## Principles

- **Patch-only** — `text_editor:patch`, never `text_editor:write` on existing files
- **Read first** — `text_editor:read` the full skill before patching
- **Verify after** — grep + line count after each patch
- **Checkpoint between phases** — validate.py + pytest at each checkpoint

## Source Material

- **SPEC.md** at `/a0/usr/projects/agent_skills/SPEC.md` — full specification
- **Caveman skill** at `/a0/usr/skills/caveman/SKILL.md` (161 lines) — source content

## Dependency Graph

```
Phase 1: P1 + P2  (context-engineering/SKILL.md)
    │
    │  context-engineering is the canonical home for A0 behavioral patterns.
    │  Agents reference it conceptually but are self-contained.
    │
    ▼
Checkpoint 1: validate.py + pytest
    │
    ▼
Phase 2: P3 + P4 + P5  (agent specifics — independent, parallelizable)
    │
    │
    ▼
Checkpoint 2: validate.py + pytest
    │
    ▼
Phase 3: P6  (using-agent-skills/SKILL.md)
    │
    │
    ▼
Final Checkpoint: validate.py + pytest + manual grep verification
```

## Baseline Line Counts

| File | Current Lines | Max | Headroom |
|------|--------------|-----|----------|
| `skills/context-engineering/SKILL.md` | 388 | 500 | 112 |
| `agents/code-reviewer/prompts/agent.system.main.specifics.md` | 51 | 75 | 24 |
| `agents/test-engineer/prompts/agent.system.main.specifics.md` | 45 | 75 | 30 |
| `agents/security-auditor/prompts/agent.system.main.specifics.md` | 52 | 75 | 23 |
| `skills/using-agent-skills/SKILL.md` | 184 | 500 | 316 |

---

## Phase 1: context-engineering (P1 + P2)

### Task 1.1 — P1: Output Compression Section

**Target:** `skills/context-engineering/SKILL.md`
**Location:** New `## Output Compression` section appended after line 388 (end of file)
**Estimated addition:** ~25-30 lines
**Post-patch lines:** ~413-418

**Content to add:**

```markdown

## Output Compression

Compress output by default. ~75% token reduction while preserving all technical substance.

### A0 Compression Boundaries

| A0 JSON field | Compressed? | Reason |
|--------------|------------|--------|
| `thoughts[]` | ❌ Never | Internal reasoning — always verbose |
| `headline` | ✅ Yes | User-facing summary |
| `tool_name` / `tool_args` | ❌ Never | Literal API ids + code/paths must be exact |
| `response.text` | ✅ Yes | Primary user output |

### Compression Rules

**Drop:** articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries ("sure"/"certainly"/"of course"), hedging ("it might be worth"/"you could consider").

**Keep:** all technical terms exact, code blocks unchanged, error messages quoted verbatim, numbers/versions/paths exact.

**Pattern:** `[thing] [action] [reason]. [next step].`

### Persistence

Compression stays active every response until explicitly turned off. Does not revert after many turns, topic changes, or new skill loads.
```

**Acceptance criteria:**
- [ ] `## Output Compression` heading exists after line 388
- [ ] A0 Compression Boundaries table with 4 rows present
- [ ] Compression rules (drop/keep/pattern) present
- [ ] Persistence statement present
- [ ] File under 500 lines

**Verification:**
```bash
grep -ic 'output compression' skills/context-engineering/SKILL.md
grep -ic 'compression boundaries' skills/context-engineering/SKILL.md
grep -ic 'drop.*articles.*filler' skills/context-engineering/SKILL.md
wc -l skills/context-engineering/SKILL.md
```

---

### Task 1.2 — P2: Communication Override Subsection

**Target:** `skills/context-engineering/SKILL.md`
**Location:** New `### Communication Override` subsection inside `## Safe Operations Protocol`, inserted after line 375 (after the Rules `notify_user` code block), before line 377 (`### Example`)
**Estimated addition:** ~12-15 lines
**Post-patch lines:** ~425-433

**Content to insert (before `### Example`):**

```markdown

### Communication Override

When any Safe Operations trigger fires, revert to full prose — no compression, no fragments, complete sentences with full context. Resume compression after the clear section.

**Triggers for full prose:**
- Security warnings — CVE-class bugs, credential exposure
- Irreversible actions — `rm -rf`, `DROP TABLE`, `git push --force`, prod deploy
- Multi-step sequences where fragment order risks misread
- User confusion — repeating question or asking for clarification
```

**Acceptance criteria:**
- [ ] `### Communication Override` exists inside `## Safe Operations Protocol`
- [ ] Positioned after Rules, before Example
- [ ] 4 trigger types listed
- [ ] File under 500 lines

**Verification:**
```bash
grep -ic 'communication override' skills/context-engineering/SKILL.md
grep -ic 'triggers for full prose' skills/context-engineering/SKILL.md
wc -l skills/context-engineering/SKILL.md
```

### Checkpoint 1

```bash
cd /a0/usr/projects/agent_skills
python3 scripts/validate.py   # 44/44 pass
python3 -m pytest tests/ -v   # 39/39 pass
wc -l skills/context-engineering/SKILL.md  # under 500
```

---

## Phase 2: Agent Specifics (P3 + P4 + P5)

These 3 patches are independent — can be applied in any order. Each adds a self-contained `## Output Compression` section at the end of the file.

### Task 2.1 — P3: code-reviewer Output Compression

**Target:** `agents/code-reviewer/prompts/agent.system.main.specifics.md`
**Location:** New `## Output Compression` section appended after line 51
**Estimated addition:** ~15-18 lines
**Post-patch lines:** ~66-69

**Content to add:**

```markdown

## Output Compression

Compress all output by default. No activation needed — standard communication mode.

**Boundaries:**
- `thoughts[]`: always verbose — full reasoning, no compression
- `headline` and `response.text`: compressed — drop filler/articles/pleasantries/hedging
- `tool_args`: never compressed — exact code/paths required

**Auto-clarity:** Revert to full prose for:
- Security findings (CVE-class bugs, credential exposure)
- Destructive operation warnings (force pushes, table drops)
- Ambiguous review findings where terse phrasing risks misinterpretation
Resume compression after clear section.

Pattern: `[thing] [action] [reason]. [next step].`
```

**Acceptance criteria:**
- [ ] `## Output Compression` heading at end of file
- [ ] Boundaries (3 bullet points) present
- [ ] Auto-clarity with 3 agent-specific triggers present
- [ ] Pattern line present
- [ ] File under 75 lines

**Verification:**
```bash
grep -ic 'output compression' agents/code-reviewer/prompts/agent.system.main.specifics.md
grep -ic 'auto-clarity' agents/code-reviewer/prompts/agent.system.main.specifics.md
wc -l agents/code-reviewer/prompts/agent.system.main.specifics.md
```

---

### Task 2.2 — P4: test-engineer Output Compression

**Target:** `agents/test-engineer/prompts/agent.system.main.specifics.md`
**Location:** New `## Output Compression` section appended after line 45
**Estimated addition:** ~15-18 lines
**Post-patch lines:** ~60-63

**Content to add:**

```markdown

## Output Compression

Compress all output by default. No activation needed — standard communication mode.

**Boundaries:**
- `thoughts[]`: always verbose — full reasoning, no compression
- `headline` and `response.text`: compressed — drop filler/articles/pleasantries/hedging
- `tool_args`: never compressed — exact code/paths required

**Auto-clarity:** Revert to full prose for:
- Test failures indicating security vulnerabilities
- Destructive test operations (dropping test DB, wiping fixtures)
- Ambiguous test results where terse phrasing could mislead
Resume compression after clear section.

Pattern: `[thing] [action] [reason]. [next step].`
```

**Acceptance criteria:**
- [ ] `## Output Compression` heading at end of file
- [ ] Boundaries (3 bullet points) present
- [ ] Auto-clarity with 3 agent-specific triggers present
- [ ] Pattern line present
- [ ] File under 75 lines

**Verification:**
```bash
grep -ic 'output compression' agents/test-engineer/prompts/agent.system.main.specifics.md
grep -ic 'auto-clarity' agents/test-engineer/prompts/agent.system.main.specifics.md
wc -l agents/test-engineer/prompts/agent.system.main.specifics.md
```

---

### Task 2.3 — P5: security-auditor Output Compression

**Target:** `agents/security-auditor/prompts/agent.system.main.specifics.md`
**Location:** New `## Output Compression` section appended after line 52
**Estimated addition:** ~17-20 lines
**Post-patch lines:** ~69-72

**Content to add:**

```markdown

## Output Compression

Compress all output by default. No activation needed — standard communication mode.

**Boundaries:**
- `thoughts[]`: always verbose — full reasoning, no compression
- `headline` and `response.text`: compressed — drop filler/articles/pleasantries/hedging
- `tool_args`: never compressed — exact code/paths required

**Auto-clarity:** Revert to full prose for:
- ALL security findings (Critical + High severity always full prose)
- Destructive operation warnings
- Exploit proof-of-concept descriptions
- User confusion or requests for clarification
Resume compression after clear section.

Pattern: `[thing] [action] [reason]. [next step].`
```

**Note:** Security-auditor has the most aggressive auto-clarity — ALL Critical/High findings use full prose, plus exploit PoC descriptions.

**Acceptance criteria:**
- [ ] `## Output Compression` heading at end of file
- [ ] Boundaries (3 bullet points) present
- [ ] Auto-clarity with 4 triggers (most aggressive of the 3 agents) present
- [ ] Pattern line present
- [ ] File under 75 lines

**Verification:**
```bash
grep -ic 'output compression' agents/security-auditor/prompts/agent.system.main.specifics.md
grep -ic 'auto-clarity' agents/security-auditor/prompts/agent.system.main.specifics.md
grep -ic 'Critical.*High.*full prose' agents/security-auditor/prompts/agent.system.main.specifics.md
wc -l agents/security-auditor/prompts/agent.system.main.specifics.md
```

### Checkpoint 2

```bash
cd /a0/usr/projects/agent_skills
python3 scripts/validate.py   # 44/44 pass
python3 -m pytest tests/ -v   # 39/39 pass
for f in agents/*/prompts/agent.system.main.specifics.md; do wc -l < $f; done  # all under 75
```

---

## Phase 3: Meta-Skill Reference (P6)

### Task 3.1 — P6: Caveman Reference in using-agent-skills

**Target:** `skills/using-agent-skills/SKILL.md`
**Location:** Add row to External Reference Skills table (after line 182), update blockquote (line 184)
**Estimated addition:** ~3-4 lines
**Post-patch lines:** ~187-188

**Changes:**

1. After line 182 (`| karpathy-coding-guidelines | ... |`), insert:

```markdown
| `caveman` | Global (`/a0/usr/skills/caveman/`) | For full compression reference + intensity switching |
```

2. Replace line 184 blockquote with:

```markdown
> Full A0 behavioral discipline: Think-Before-Coding, Surgical-Changes, Safe-Operations, Terse-Commits, Structured-Review, Output-Compression. Principles are embedded into individual plugin skills above; these are the canonical references.
```

**Acceptance criteria:**
- [ ] `caveman` row exists in External Reference Skills table
- [ ] Blockquote updated to include Output-Compression
- [ ] File under 500 lines

**Verification:**
```bash
grep -ic 'caveman' skills/using-agent-skills/SKILL.md
grep -ic 'output-compression' skills/using-agent-skills/SKILL.md
wc -l skills/using-agent-skills/SKILL.md
```

### Final Checkpoint

```bash
cd /a0/usr/projects/agent_skills
python3 scripts/validate.py   # 44/44 pass
python3 -m pytest tests/ -v   # 39/39 pass

# Full manual verification
grep -ic 'output compression' skills/context-engineering/SKILL.md && echo '✅ P1'
grep -ic 'communication override' skills/context-engineering/SKILL.md && echo '✅ P2'
for agent in code-reviewer test-engineer security-auditor; do
  count=$(grep -ic 'auto-clarity' agents/$agent/prompts/agent.system.main.specifics.md)
  [ "$count" -gt 0 ] && echo "✅ $agent" || echo "❌ $agent"
done
grep -ic 'caveman' skills/using-agent-skills/SKILL.md && echo '✅ P6'

# Line counts
wc -l skills/context-engineering/SKILL.md skills/using-agent-skills/SKILL.md agents/*/prompts/agent.system.main.specifics.md
```

---

## Execution Order Summary

| Step | Task | File | Lines Added | Post-Patch Lines |
|------|------|------|-------------|------------------|
| 1 | P1: Output Compression section | context-engineering/SKILL.md | ~27 | ~415 |
| 2 | P2: Communication Override | context-engineering/SKILL.md | ~14 | ~429 |
| CP1 | Validate + test | — | — | — |
| 3 | P3: Output Compression | code-reviewer specifics.md | ~16 | ~67 |
| 4 | P4: Output Compression | test-engineer specifics.md | ~16 | ~61 |
| 5 | P5: Output Compression | security-auditor specifics.md | ~18 | ~70 |
| CP2 | Validate + test | — | — | — |
| 6 | P6: Caveman reference | using-agent-skills/SKILL.md | ~3 | ~187 |
| CP3 | Final validate + test + grep | — | — | — |
| 7 | Commit | — | — | — |

**Total estimated additions:** ~94 lines across 5 files
