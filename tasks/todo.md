# Caveman Option B Integration — Task Checklist

## Phase 1: context-engineering (P1 + P2)

- [ ] P1: Append `## Output Compression` section to context-engineering/SKILL.md (after L388)
  - [ ] A0 Compression Boundaries table (4 rows: thoughts[], headline, tool_args, response.text)
  - [ ] Compression rules (drop/keep/pattern)
  - [ ] Persistence statement
  - [ ] Verify: `grep -ic 'output compression'` + `wc -l` under 500
- [ ] P2: Insert `### Communication Override` subsection in Safe Operations Protocol (after L375, before Example)
  - [ ] Full prose revert rule with 4 triggers
  - [ ] Verify: `grep -ic 'communication override'` + `wc -l` under 500
- [ ] Checkpoint 1: `python3 scripts/validate.py` + `python3 -m pytest tests/ -v`

## Phase 2: Agent Specifics (P3 + P4 + P5)

- [ ] P3: Append `## Output Compression` to code-reviewer specifics.md (after L51)
  - [ ] Boundaries (3 bullets) + Auto-clarity (3 triggers: security findings, destructive ops, ambiguous review)
  - [ ] Pattern line
  - [ ] Verify: `grep -ic 'auto-clarity'` + `wc -l` under 75
- [ ] P4: Append `## Output Compression` to test-engineer specifics.md (after L45)
  - [ ] Boundaries (3 bullets) + Auto-clarity (3 triggers: security test failures, destructive test ops, ambiguous results)
  - [ ] Pattern line
  - [ ] Verify: `grep -ic 'auto-clarity'` + `wc -l` under 75
- [ ] P5: Append `## Output Compression` to security-auditor specifics.md (after L52)
  - [ ] Boundaries (3 bullets) + Auto-clarity (4 triggers: ALL Critical/High findings, destructive ops, exploit PoC, user confusion)
  - [ ] Pattern line
  - [ ] Verify: `grep -ic 'auto-clarity'` + `grep -ic 'Critical.*High.*full prose'` + `wc -l` under 75
- [ ] Checkpoint 2: `python3 scripts/validate.py` + `python3 -m pytest tests/ -v`

## Phase 3: Meta-Skill Reference (P6)

- [ ] P6: Add caveman row to using-agent-skills External Reference Skills table (after L182)
  - [ ] New table row: `caveman | Global (/a0/usr/skills/caveman/) | For full compression reference + intensity switching`
  - [ ] Update blockquote (L184): add `Output-Compression` to discipline list
  - [ ] Verify: `grep -ic 'caveman'` + `grep -ic 'output-compression'`

## Final Verification

- [ ] `python3 scripts/validate.py` — 44/44 pass
- [ ] `python3 -m pytest tests/ -v` — 39/39 pass
- [ ] All line counts within limits (context-engineering <500, agent specifics <75, using-agent-skills <500)
- [ ] Manual grep: P1 output compression ✅, P2 communication override ✅, P3-P5 auto-clarity ✅, P6 caveman ✅

## Commit

- [ ] `git add tasks/plan.md tasks/todo.md && git commit -m 'docs: plan for caveman Option B integration'`
- [ ] Do NOT push
