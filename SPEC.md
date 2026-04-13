# Spec: Caveman Communication Compression Integration (Option B)

## Objective

Merge the unique, Agent Zero-specific parts of `caveman` into existing agent-skills. No new skill is created. No content is duplicated. Each target receives a targeted patch adding only the Caveman content that is NOT already covered by the global skill or existing skills.

**Key decisions (confirmed by user):**
1. Auto-compress at agent level — agents ALWAYS use compressed output, no activation needed
2. Remove wenyan levels (Chinese) — keep lite, full, ultra only
3. Global caveman skill stays at `/a0/usr/skills/caveman/` as full reference
4. Agents benefit automatically — specifics.md updated, no separate skill load

**Primary value:** All agents compress output by default (~75% token reduction). The A0 Compression Boundaries table ensures thoughts[] stay verbose (reasoning quality) while headline and response.text go terse (token efficiency). Auto-clarity rule ensures safety-critical moments revert to full prose.

**What we do NOT do:**
- Duplicate content from the global caveman skill (pattern examples, intensity examples)
- Create a new standalone skill
- Add activation instructions (auto-compress is the default)
- Include wenyan/Chinese levels (removed per user decision)
- Add general communication advice already covered by existing skills

---

## Overlap Analysis — What We Skip

| Caveman Content | Existing Coverage | Overlap | Decision |
|---|---|---|---|
| Activation instructions (behaviour_adjustment) | N/A — auto-compress, no activation | N/A | **Skip entirely.** Agents auto-compress. |
| Wenyan intensity levels (wenyan-lite/full/ultra) | N/A — removed per user | N/A | **Skip entirely.** User decided Chinese levels out of scope. |
| Pattern examples (lite/full/ultra) | Global caveman skill only | 0% in plugin | **Skip.** Stay in global skill as reference. |
| General communication advice | `using-agent-skills` Core Operating Behaviors | ~60% | **Skip.** Already covered. |
| Intensity level descriptions (lite/full/ultra) | Global caveman skill | 100% | **Skip.** Already in global skill. |
| Drop rules (articles/filler/pleasantries/hedging) | No existing coverage | 0% | **Integrate** into Output Compression section. |
| A0 Compression Boundaries table | No existing coverage | 0% | **Integrate** into Output Compression section. |
| Auto-clarity rule | `context-engineering` Safe Operations (destructive ops) | ~40% behavioral overlap | **Integrate** into Safe Operations as Communication Override. |
| Persistence model (active until off) | No existing coverage | 0% | **Integrate** into Output Compression section. |

---

## What Gets Integrated — The 6 Patches

### Patch 1 — `skills/context-engineering/SKILL.md`: Output Compression Section

**Location:** New `## Output Compression` section after the existing Safe Operations Protocol section (after line 388).

**Adds:**

1. **A0 Compression Boundaries table** — which JSON fields get compressed and which stay verbose:

| A0 JSON field | Compressed? | Reason |
|--------------|------------|--------|
| `thoughts[]` | ❌ Never | Internal reasoning — always verbose |
| `headline` | ✅ Yes | User-facing summary |
| `tool_name` / `tool_args` | ❌ Never | Literal API ids + code/paths must be exact |
| `response.text` | ✅ Yes | Primary user output |

2. **Compression rules** — what to drop and what to keep:

Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries ("sure"/"certainly"/"of course"), hedging ("it might be worth"/"you could consider").

Keep: all technical terms exact, code blocks unchanged, error messages quoted verbatim, numbers/versions/paths exact.

Pattern: `[thing] [action] [reason]. [next step].`

3. **Persistence model** — compression stays active every response until explicitly turned off. Does not revert after many turns, topic changes, or new skill loads.

**Rationale:** context-engineering is the skill for A0 behavioral patterns. It already houses Agent Zero Discipline (thoughts[] structure) and Safe Operations Protocol (destructive action handling). Output Compression is the third pillar of A0 agent behavior — how the agent communicates. All three belong together.

**Estimated addition:** ~25-30 lines. Current file: 388 lines → ~415-418 lines (under 500).

---

### Patch 2 — `skills/context-engineering/SKILL.md`: Communication Override in Safe Operations

**Location:** New `### Communication Override` subsection inside the existing `## Safe Operations Protocol` section (after line 375, after the Rules list, before the Example subsection).

**Adds:**

A subsection stating: when any Safe Operations trigger fires (destructive action, security warning, irreversible operation), the agent reverts to full prose — no compression, no fragments, complete sentences with full context. Resume compression after the clear section.

Triggers for reverting to full prose:
- Security warnings — CVE-class bugs, credential exposure
- Irreversible actions — `rm -rf`, `DROP TABLE`, `git push --force`, prod deploy
- Multi-step sequences where fragment order risks misread
- User confusion — repeating question or asking for clarification

**Rationale:** Safe Operations already defines WHAT counts as destructive and HOW to handle it (confirm, verify, notify). The Communication Override defines HOW TO COMMUNICATE during those moments — switch from compressed to full prose. One place for all safety-related behavior (both action and communication) is cleaner than splitting across sections.

**Estimated addition:** ~12-15 lines. Combined with Patch 1, context-engineering goes to ~430-433 lines (under 500).

---

### Patch 3 — `agents/code-reviewer/prompts/agent.system.main.specifics.md`

**Location:** New `## Output Compression` section at end of file (after line 51).

**Adds:**

```
## Output Compression

Compress all output by default. No activation needed — this is your standard communication mode.

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

**Rationale:** Code reviewers produce structured reports. Compression makes reports denser and faster to read. But security findings and destructive-operation warnings must never be compressed — a terse "bug in auth" could be missed when it's actually a credential leak. The auto-clarity rule ensures critical findings get full prose.

**Estimated addition:** ~15-18 lines. Current file: 51 lines → ~66-69 lines.

---

### Patch 4 — `agents/test-engineer/prompts/agent.system.main.specifics.md`

**Location:** New `## Output Compression` section at end of file (after line 45).

**Adds:**

```
## Output Compression

Compress all output by default. No activation needed — this is your standard communication mode.

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

**Rationale:** Test engineers report results frequently. Compression reduces noise in pass/fail reports. But security-relevant test failures and destructive test setup must use full prose for clarity.

**Estimated addition:** ~15-18 lines. Current file: 45 lines → ~60-63 lines.

---

### Patch 5 — `agents/security-auditor/prompts/agent.system.main.specifics.md`

**Location:** New `## Output Compression` section at end of file (after line 52).

**Adds:**

```
## Output Compression

Compress all output by default. No activation needed — this is your standard communication mode.

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

**Rationale:** Security auditors handle the most sensitive findings. While general audit prose can be compressed, ALL Critical/High findings must use full prose — terse "SQL injection in login" could be missed when it's actually exploitable. This agent has the most aggressive auto-clarity triggers.

**Estimated addition:** ~17-20 lines. Current file: 52 lines → ~69-72 lines.

---

### Patch 6 — `skills/using-agent-skills/SKILL.md`: External Reference

**Location:** Add row to the `## External Reference Skills` table (line 180-184).

**Adds:**

| `caveman` | Global (`/a0/usr/skills/caveman/`) | For full compression reference + intensity switching |

Update the note below the table:

> Full A0 behavioral discipline: Think-Before-Coding, Surgical-Changes, Safe-Operations, Terse-Commits, Structured-Review, Output-Compression. Principles are embedded into individual plugin skills above; these are the canonical references.

**Rationale:** The meta-skill governs discovery. Users who want the full caveman reference (intensity switching, pattern examples, wenyan levels) should know it exists as a global skill. The embedded version is the auto-compress default.

**Estimated addition:** ~3-4 lines. Current file: 184 lines → ~187-188 lines.

---

## Project Structure (Files Modified)

```
skills/context-engineering/SKILL.md        ← Patch 1 + 2 (Output Compression + Communication Override)
agents/code-reviewer/prompts/agent.system.main.specifics.md  ← Patch 3
agents/test-engineer/prompts/agent.system.main.specifics.md   ← Patch 4
agents/security-auditor/prompts/agent.system.main.specifics.md ← Patch 5
skills/using-agent-skills/SKILL.md         ← Patch 6
```

**Files NOT modified:**
- All other 19 skills (no relevant overlap)
- Global caveman skill (`/a0/usr/skills/caveman/`) — stays as-is, full reference
- No new files created

---

## Commands

N/A — This integration is pure Markdown patches. No code, scripts, or commands added.

---

## Code Style

- New sections use `##` or `###` headings consistent with the file's existing heading depth
- Tables, code blocks, and bullet lists — match the skill's existing formatting style
- A0-specific content labeled clearly ("Agent Zero", "A0", or section title contains "Output Compression")
- Every patch is self-contained — can be reverted without affecting surrounding content
- Agent specifics patches use identical structure for consistency across the 3 agents
- Patch-only approach: add clearly-labeled sections, never rewrite existing content

---

## Testing Strategy

### Validation
- Run `python3 scripts/validate.py` — all 44 checks must pass (frontmatter, line counts, etc.)
- Run `python3 -m pytest tests/ -v` — all 39 tests must pass
- Verify line counts: `wc -l skills/context-engineering/SKILL.md skills/using-agent-skills/SKILL.md agents/*/prompts/agent.system.main.specifics.md` — all under 500 lines

### Manual Verification
- Load each patched skill via `skills_tool:load` and verify it loads without error
- Read each patched file and verify the new section is present and correct
- Verify grep for key content:

```bash
# Verify Output Compression section exists in context-engineering
grep -ic 'output compression' skills/context-engineering/SKILL.md && echo '✅'

# Verify Communication Override exists in context-engineering Safe Operations
grep -ic 'communication override' skills/context-engineering/SKILL.md && echo '✅'

# Verify A0 Compression Boundaries table exists
grep -ic 'compression boundaries' skills/context-engineering/SKILL.md && echo '✅'

# Verify auto-clarity in each agent specifics
for agent in code-reviewer test-engineer security-auditor; do
  count=$(grep -ic 'auto-clarity' agents/$agent/prompts/agent.system.main.specifics.md)
  [ "$count" -gt 0 ] && echo "✅ $agent" || echo "❌ $agent"
done

# Verify caveman reference in using-agent-skills
grep -ic 'caveman' skills/using-agent-skills/SKILL.md && echo '✅'

# Verify line counts under 500
for f in skills/context-engineering/SKILL.md skills/using-agent-skills/SKILL.md agents/*/prompts/agent.system.main.specifics.md; do
  lines=$(wc -l < $f)
  [ $lines -lt 500 ] && echo "✅ $lines $f" || echo "❌ $lines $f"
done
```

---

## Boundaries

**Always:**
- Patch only — never rewrite existing sections
- New content must be uniquely Caveman / A0-specific — no general advice
- Keep each patch focused: one concept, one section, one target
- Use identical structure for the 3 agent specifics patches (maintain consistency)
- Respect the auto-compress decision: no activation instructions, no "load caveman skill first"

**Ask first:**
- If a patch would exceed 500 lines for the target skill
- If auto-clarity triggers should differ across the 3 agents (currently differentiated)
- If the Communication Override should be a standalone section vs subsection of Safe Operations

**Never:**
- Duplicate content between skills or agent specifics
- Remove or rewrite existing skill/spec content
- Add wenyan/Chinese levels (removed per user decision)
- Add activation instructions (auto-compress is the default)
- Add caveman as a plugin skill (it's a global skill — leave it there)
- Include pattern examples from the global skill (they stay there as reference)
- Compress `thoughts[]` or `tool_args` — ever

---

## Success Criteria

- [ ] All 6 patches applied — 2 to context-engineering, 3 agent specifics, 1 using-agent-skills
- [ ] Output Compression section exists in `context-engineering` with boundaries table
- [ ] Communication Override subsection exists inside Safe Operations in `context-engineering`
- [ ] Compression rules (drop/keep/pattern) present in `context-engineering`
- [ ] Persistence model present in `context-engineering`
- [ ] All 3 agent specifics have `## Output Compression` section
- [ ] All 3 agent specifics have auto-clarity with agent-appropriate triggers
- [ ] `using-agent-skills` references caveman in External Reference Skills table
- [ ] No SKILL.md exceeds 500 lines after patches
- [ ] `python3 scripts/validate.py` exits 0 — all 44 checks pass
- [ ] `python3 -m pytest tests/ -v` exits 0 — all 39 tests pass
- [ ] Each patched skill loads correctly via `skills_tool:load`
- [ ] Commit message: `docs: spec for caveman Option B integration`

---

## Open Questions

1. **Auto-clarity trigger differentiation:** The 3 agent specifics currently have slightly different auto-clarity triggers (security-auditor has the most aggressive). Is this differentiation correct, or should all 3 use identical triggers?

2. **Output Compression in agent specifics vs context-engineering:** The 3 agent specifics each get a self-contained compression section. This is slight duplication (~15 lines × 3), but ensures each agent works standalone without needing to load context-engineering first. Acceptable trade-off?

3. **Intensity level mention:** Should the Output Compression section in context-engineering mention lite/full/ultra as available modes, or leave that entirely to the global skill?

4. **Future karpathy+caveman synergy:** The Safe Operations Protocol (from karpathy) now has Communication Override (from caveman). Should we add a cross-reference note linking Agent Zero Discipline → Output Compression → Safe Operations as a unified A0 behavior model?
