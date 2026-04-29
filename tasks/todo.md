# TODO: Agent Skills Flow Alignment v0.4.0

## Task 1.1: Update /idea command ✅
- [x] Delegate to `researcher` with `call_subordinate`
- [x] Subordinate loads `idea-refine`
- [x] Exit criteria, anti-rationalization, red flags preserved

## Task 1.2: Update /spec command ✅
- [x] Delegate to `developer` with `call_subordinate`
- [x] Subordinate loads `spec-driven-development`
- [x] Add conditional skill: `context-engineering` (complex domain)
- [x] Exit criteria, anti-rationalization, red flags preserved

## Task 1.3: Update /plan command ✅
- [x] Delegate to `researcher` with `call_subordinate`
- [x] Subordinate loads `planning-and-task-breakdown`
- [x] Add conditional skill: `context-engineering` (complex codebase)
- [x] Exit criteria, anti-rationalization, red flags preserved

## Task 1.4: Update /build command ✅
- [x] Delegate to `developer` with `call_subordinate`
- [x] Subordinate loads `incremental-implementation` + `test-driven-development`
- [ ] Add conditional skills: `frontend-ui-engineering`, `api-and-interface-design`, `source-driven-development`, `context-engineering`, `debugging-and-error-recovery`, `git-workflow-and-versioning`, `documentation-and-adrs`, `deprecation-and-migration`
- [x] Exit criteria, anti-rationalization, red flags preserved

## Task 1.5: Update /code-simplify command ✅
- [x] Delegate to `developer` with `call_subordinate`
- [x] Subordinate loads `code-simplification` + `code-review-and-quality`
- [ ] Add conditional skill: `debugging-and-error-recovery` (on failure)

## Task 1.6: Update /test command
- [ ] Add conditional skills: `browser-testing-with-devtools` (browser), `debugging-and-error-recovery` (on failure)
- **Verify**: File contains both conditional skill mentions

## Task 1.7: Update /review command
- [ ] Add conditional skills: `security-and-hardening` (security), `performance-optimization` (perf)
- **Verify**: File contains both conditional skill mentions

## Task 1.8: Update /security command
- [ ] Verify no conditional skills needed (already correct)
- **Verify**: File unchanged

## Task 1.9: Update /ship command
- [ ] Add conditional skills: `ci-cd-and-automation` (CI/CD), `git-workflow-and-versioning` (branching)
- **Verify**: File contains conditional skill mentions

## Task 2: Merge lifecycle-runtime into using-agent-skills
- [ ] Copy Manus Principles, 5-Question Reboot, Read/Write Matrix from lifecycle-runtime
- [ ] Insert into using-agent-skills SKILL.md (after Quick Reference section)
- [ ] Update lifecycle tool usage table references
- [ ] Remove lifecycle-runtime from routing table (replaced by merged content)
- [ ] Delete `skills/lifecycle-runtime/` directory
- **Verify**: `skills/lifecycle-runtime/` does not exist, content exists in `skills/using-agent-skills/SKILL.md`

## Task 3: Update _20_agent_skills_prompt.py delegation table
- [ ] Expand DELEGATION_TABLE to map ALL commands (not just /build)
- [ ] Keep table under 1000 chars
- [ ] List all 6 agents
- [ ] Update lifecycle line: all phases delegate
- **Verify**: `get_delegation_table()` returns table with all mappings, under 1000 chars

## Task 4: Update tests
- [ ] Fix `TestDirectLoadCommands`: /spec, /plan, /build now SHOULD contain `call_subordinate`
- [ ] Fix `TestCodeSimplifyCommand`: now delegates to `developer`, not hybrid
- [ ] Fix `TestDelegationTableContent`: expanded table includes all command→profile mappings
- [ ] Fix any tests referencing `lifecycle-runtime` as separate skill
- [ ] Run full test suite: `cd /a0/usr/projects/a0_agent_skills && python -m pytest tests/ -x`
- [ ] All tests pass
- **Verify**: `python -m pytest tests/ -x` exits 0
