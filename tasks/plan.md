# Plan: Agent Skills Flow Alignment v0.4.0

## Dependency Graph

```
Task 1: Command files (9 files)
  ├── 1.1 idea.txt (delegate + conditional skills)
  ├── 1.2 spec.txt (delegate + conditional skills)
  ├── 1.3 plan.txt (delegate + conditional skills)
  ├── 1.4 build.txt (delegate + conditional skills)
  ├── 1.5 code-simplify.txt (delegate + conditional skills)
  ├── 1.6 test.txt (add conditional skills)
  ├── 1.7 review.txt (add conditional skills)
  ├── 1.8 security.txt (add conditional skills)
  └── 1.9 ship.txt (add conditional skills)

Task 2: Merge lifecycle-runtime into using-agent-skills
  └── Depends on nothing, but must happen before Task 4

Task 3: _20_agent_skills_prompt.py delegation table
  └── Independent of Tasks 1 & 2

Task 4: Update tests
  └── DEPENDS ON Tasks 1, 2, 3
```

## Test Impact Analysis

### Tests That Will Break (must be updated in Task 4)

1. **test_three_tier_routing.py → TestDirectLoadCommands**
   - Currently asserts: /spec, /plan, /build do NOT contain `call_subordinate`
   - Must change: These commands WILL now contain `call_subordinate`

2. **test_three_tier_routing.py → TestCodeSimplifyCommand**
   - Currently asserts: loads code-simplification first, then delegates to code-reviewer
   - Must change: Full delegation to `developer` profile

3. **test_clean_orchestrator.py → TestDelegationTableContent**
   - Must verify: expanded table includes all command→profile mappings

4. **test_system_prompt_routing.py → TestDelegationTable**
   - Must verify: Updated table still fits under 1000 chars

5. **Tests referencing lifecycle-runtime skill**
   - Must verify: lifecycle-runtime directory deleted, references removed

### Tests That Should NOT Break
- test_lifecycle_tool.py, test_lifecycle_state.py
- test_validate_skills.py (skill anatomy unchanged)
- test_ship_parallel.py (/ship unchanged)
- All simplify-ignore tests

## Execution Order

Tasks 1-3 can be done in parallel. Task 4 must come after all of them.
