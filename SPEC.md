# SPEC: Agent Skills Flow Alignment v0.4.0

**Version**: 0.4.0
**Status**: Draft
**Date**: 2026-04-27

## Objective

Fix the command delegation pattern so every slash command delegates to the right subordinate agent, who loads and executes the skill. The orchestrator (parent) only routes — it does not execute skills directly.

## Problem

1. **5 of 9 commands have the parent agent loading and executing skills** instead of delegating to subordinates.
2. **Delegation messages only mention primary skills** — subordinates don't know about conditional skills (git, CI/CD, docs, debugging, etc.).
3. **Two meta-skills where one suffices** — `lifecycle-runtime` and `using-agent-skills` should be merged into a single orchestrator meta-skill.
4. **Orphaned skills** — git-workflow, CI/CD, documentation, deprecation, performance-optimization are never loaded by any command.

## Scope

### In Scope
1. Fix 5 command `.txt` files to delegate to subordinates with conditional skill mentions
2. Update remaining 4 command `.txt` files to include conditional skill mentions
3. Merge `lifecycle-runtime` SKILL.md into `using-agent-skills` SKILL.md
4. Delete `skills/lifecycle-runtime/` directory
5. Update `_20_agent_skills_prompt.py` delegation table
6. Update `using-agent-skills` routing table and flowchart
7. Update tests to match new patterns

### Not In Scope
- New skills, new commands, new extensions
- Architecture changes to lifecycle, gates, or state management
- Changes to agent profiles or their prompt files
- Changes to the lifecycle tool (init/status/archive)
- Simplify-ignore system changes

## Command Delegation Map

| Command | Profile | Primary Skills | Conditional Skills |
|----------|---------|---------------|-------------------|
| `/idea` | `researcher` | idea-refine | — |
| `/spec` | `developer` | spec-driven-development | context-engineering (complex domain) |
| `/plan` | `researcher` | planning-and-task-breakdown | context-engineering (complex codebase) |
| `/build` | `developer` | incremental-implementation, test-driven-development | frontend-ui-engineering (UI), api-and-interface-design (API), source-driven-development (docs), context-engineering (context), debugging-and-error-recovery (on failure), git-workflow-and-versioning (before commit), documentation-and-adrs (docs needed), deprecation-and-migration (migrating) |
| `/test` | `test-engineer` | test-driven-development | browser-testing-with-devtools (browser), debugging-and-error-recovery (on failure) |
| `/review` | `code-reviewer` | code-review-and-quality | security-and-hardening (security), performance-optimization (perf) |
| `/security` | `security-auditor` | security-and-hardening | — |
| `/code-simplify` | `developer` | code-simplification, code-review-and-quality | debugging-and-error-recovery (on failure) |
| `/ship` | (orchestrator) | shipping-and-launch | ci-cd-and-automation (CI/CD), git-workflow-and-versioning (branching) |

## Meta-Skill Merge

Merge `lifecycle-runtime` content into `using-agent-skills`:
- Manus Principles (Memory Externalized, Keep-Wrong-Stuff-In, Attention via Recitation)
- 5-Question Reboot Test
- 3-Strike Error Protocol
- Read vs Write Decision Matrix
- Lifecycle tool usage table

Delete `skills/lifecycle-runtime/` after merge.

The `using-agent-skills` routing table should list `Load skill` for itself only — all other skills use `Delegate → <profile>`.

## Acceptance Criteria

- [ ] All 9 command `.txt` files use `call_subordinate` delegation pattern (except `/ship`)
- [ ] Delegation messages include conditional skill mentions
- [ ] No orphaned skills — every skill is referenced by at least one command or specialist
- [ ] `lifecycle-runtime` directory deleted, content merged into `using-agent-skills`
- [ ] `using-agent-skills` SKILL.md has consistent `Delegate → <profile>` for all skills except meta
- [ ] `_20_agent_skills_prompt.py` delegation table maps ALL commands
- [ ] All existing tests pass (after updates)
- [ ] SPEC.md exists at project root

## Boundaries

### Always Do
- Keep command text concise — subordinates load skill details themselves
- Include lifecycle context in delegation messages when lifecycle is active
- Maintain exit criteria and anti-rationalization tables in command files

### Ask First
- Changing the `/ship` scheduler task pattern
- Adding new commands or profiles

### Never Do
- Add new skills, extensions, tools, or agent profiles
- Modify lifecycle tool (init/status/archive)
- Change simplify-ignore system
- Over-engineer — this is a text update, not an architecture change
