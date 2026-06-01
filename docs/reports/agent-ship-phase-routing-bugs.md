# Bug Report: Agent SHIP Phase Routing Errors

**Date:** 2026-06-01
**Component:** Agent Zero — Main Agent (agent0) Skill Routing
**Severity:** Medium (process violation, not runtime bug)

---

## Summary

During the artifact-path-wiring-fix implementation, the main agent (agent0) made two routing errors in the SHIP phase that had to be corrected by the user.

## Bug 1: Wrong Skill Assigned to test-engineer in SHIP Phase

**What happened:** The agent proposed assigning `test-driven-development` skill to the `test-engineer` subordinate during the SHIP phase.

**Correct behavior:** In the SHIP phase, `test-engineer` uses `debugging-and-error-recovery`, NOT `test-driven-development`.

**Reason:**
- `test-driven-development` is for the BUILD phase — write tests first, then implement
- `debugging-and-error-recovery` is for VERIFY/SHIP phase — systematically verify working code, diagnose failures, identify edge cases
- TDD drives implementation; the test-engineer in SHIP verifies what was built

## Bug 2: Skipped Parallel Fan-Out in SHIP Phase

**What happened:** The agent proposed admin-only SHIP steps (update spec, check off todos, git commit) without running the 3-agent parallel fan-out gate.

**Correct behavior:** In the SHIP phase, ALWAYS run all 3 specialist personas in parallel fan-out:

```
call_subordinate_parallel
  ├── code-reviewer     (skill: code-review-and-quality)
  ├── security-auditor  (skill: security-and-hardening)
  └── test-engineer     (skill: debugging-and-error-recovery)
```

**The agent should NEVER:**
- Skip the parallel fan-out
- Propose doing it sequentially
- Only run one or two of the three agents
- Propose admin-only SHIP steps without the 3-agent gate first

## Root Cause

The agent confused BUILD-phase skill assignments with SHIP-phase skill assignments. The mandatory routing rules clearly specify which skills belong to which phase, but the agent failed to apply them correctly when transitioning from REVIEW to SHIP.

## Corrected Skill-to-Phase Mapping

| Phase | Agent | Skill |
|-------|-------|-------|
| BUILD | developer | `test-driven-development` |
| VERIFY | test-engineer | `debugging-and-error-recovery` |
| SHIP | code-reviewer | `code-review-and-quality` |
| SHIP | security-auditor | `security-and-hardening` |
| SHIP | test-engineer | `debugging-and-error-recovery` |

## Bug 3: Loaded shipping-and-launch Skill But Ignored Its Cross-References

**What happened:** The agent loaded the `shipping-and-launch` skill and read its content, which explicitly references companion skills and their checklists:

- `security-and-hardening` → `security-checklist.md` for security pre-launch checks
- `performance-optimization` → `performance-checklist.md` for performance pre-launch checks
- `frontend-ui-engineering` → `accessibility-checklist.md` for accessibility verification
- `git-workflow-and-versioning` → for proper git commit workflow (never done!)
- `documentation-and-adrs` → for changelog updates (never done!)

The agent treated the skill as a standalone document instead of a hub that routes to other skills. It ran the 3-agent fan-out and admin tasks but never loaded the companion skills or their checklists.

**Consequence:**
- No performance pre-launch checks were done
- No git commit was made (changes are uncommitted)
- No changelog was updated
- The security-auditor ran ad-hoc instead of using the structured security-checklist.md

**Correct behavior:** When loading a skill that references other skills, follow those cross-references. The `shipping-and-launch` SKILL.md explicitly says:

> For security pre-launch checks, load `security-and-hardening` and read `security-checklist.md`
> For performance pre-launch checks, load `performance-optimization` and read `performance-checklist.md`

The agent should have:
1. Loaded `shipping-and-launch` (done ✅)
2. Loaded `security-and-hardening` and read `security-checklist.md` (missed ❌)
3. Loaded `performance-optimization` and read `performance-checklist.md` (missed ❌)
4. Loaded `git-workflow-and-versioning` for proper commit (missed ❌)
5. Loaded `documentation-and-adrs` for changelog (missed ❌)

## Bug 4: Proposed Already-Shipped Specs as New Work

**What happened:** When presenting next steps after shipping, the agent listed specs from the file tree as "Option C: Move to Another Feature":

- `skill-enforcement-gate` (spec + plan + todo exist)
- `phase-aware-governance` (spec + plan + todo exist)
- `skill-registry-strengthening` (spec + plan + todo exist)
- `durable-workflow-state` (spec + plan + todo exist)

These are **completed work from previous sprints**, not new features. The agent has no sprint history awareness and cannot distinguish between shipped, in-progress, and not-started work.

**Root cause:** The agent only looked at file existence (does a spec/plan/todo file exist?) without checking:
1. Spec status field (`SHIPPED`, `In Progress`, `Draft`)
2. Todo completion state (all items checked vs unchecked)
3. Any sprint/release history or changelog

**Impact:**
- Proposing already-shipped work wastes time and confuses the user
- Shows lack of project awareness — the user expects the agent to know what's been done
- Could lead to duplicate implementation attempts

**Correct behavior:** Before proposing next steps, the agent should:
1. Read the status field from each spec file
2. Filter to only `Draft` or `In Progress` specs
3. Never propose specs with status `SHIPPED`
4. Maintain or reference a sprint history / changelog for cross-session awareness

## Bug 5: Never Loaded `using-agent-skills` Meta-Skill for Routing Guidance

**What happened:** Throughout the entire session (DEFINE → PLAN → BUILD → REVIEW → SHIP), the agent never loaded the `using-agent-skills` meta-skill. This skill is explicitly designed as the routing hub:

> "Meta-skill for selecting and applying the right skill for any task. Use when starting a task and unsure which skill to apply."

It contains detailed flowcharts for phase-to-skill routing, multi-skill combinations, and the complete skill taxonomy.

**Root cause:** The agent treated the mandatory routing rules in the system prompt as sufficient guidance. While those rules list the six phases and required skills, they don't include the detailed flowcharts, conditional branches, and cross-reference chains that `using-agent-skills` provides.

**Impact:** Without the meta-skill's routing guidance:
- Bug 1 (wrong skill for test-engineer) could have been prevented — the flowchart clearly shows `debugging-and-error-recovery` in SHIP
- Bug 2 (skipped fan-out) could have been prevented — the skill taxonomy shows SHIP requires all 3 agents
- Bug 3 (ignored cross-references) could have been prevented — the meta-skill maps skill dependencies
- Bug 4 (proposed shipped work) could have been prevented — the meta-skill emphasizes checking existing state

**Correct behavior:**
1. Load `using-agent-skills` at the START of any task, before loading phase-specific skills
2. Follow its flowcharts for phase-to-skill routing
3. Use its taxonomy to discover skills that should be loaded but weren't
4. Re-reference it when transitioning between phases

**Additional missed skills that `using-agent-skills` would have surfaced:**

| Skill | When It Should Have Been Loaded | Phase |
|-------|--------------------------------|-------|
| `context-engineering` | When working across 10+ files with complex interdependencies | BUILD |
| `doubt-driven-development` | Before committing to the two-store model merge approach | PLAN/REVIEW |
| `git-workflow-and-versioning` | During SHIP for proper commit workflow | SHIP |
| `documentation-and-adrs` | During SHIP for changelog and ADR updates | SHIP |
| `performance-optimization` | Cross-referenced by `shipping-and-launch` checklist | SHIP |

## Bug 6: Never Applied Context-Engineering Practices During Long Session

**What happened:** Throughout a 300+ message session spanning 5 lifecycle phases, the agent never applied context-engineering practices despite loading the `context-engineering` skill.

Note: Reading AGENTS.md is NOT part of this bug — that file is the plugin's upstream documentation, not a project guidance file.

**Specific failures:**

| Context-Engineering Practice | What Should Have Happened | What Actually Happened |
|----------------------------|--------------------------|----------------------|
| Summarize decisions to file | Write decisions to a file as context grew | Never summarized — 300+ messages of growing context |
| Task tracking file | Maintain a session task tracking file updated as work progresses | Never created one |
| Subordinate delegation context | Include project context, conventions, acceptance criteria in delegations | Some delegations lacked ADR-007 context, two-store model details |
| Use `§§include()` for long outputs | Reference prior outputs instead of rewriting | Rewrote long outputs instead of using include |
| Phase transition context management | Summarize and compact before each phase transition | Each phase inherited a growing messy context |

**Impact:**
- Growing context window led to declining output quality (wrong skill assignments, missed cross-references)
- Subordinates sometimes lacked sufficient context to do their jobs well
- Long repeated outputs wasted tokens
- No durable record of decisions for future sessions

**Correct behavior:**
1. At session start, create a task tracking file and update it as work progresses
2. After each phase, summarize key decisions to a file
3. Before delegating, include project conventions and acceptance criteria
4. Use `§§include()` for long existing text instead of rewriting
5. When context is getting full, deliberately compact or summarize

## Lessons Learned

1. When transitioning between lifecycle phases, re-verify skill assignments against the six-phase model
2. SHIP always requires the 3-agent parallel fan-out — there are no exceptions
3. `test-driven-development` is NEVER used outside the BUILD phase
4. When a loaded skill cross-references other skills, ALWAYS follow those references — skills are hubs, not standalone documents
5. `git-workflow-and-versioning` must be loaded during SHIP for proper commit workflow
6. `documentation-and-adrs` must be loaded during SHIP for changelog and ADR updates
7. Before proposing next work, check spec status fields — never propose already-shipped specs as new features
8. Maintain sprint history awareness — know what was done in previous sessions
9. **Load `using-agent-skills` FIRST at the start of any task** — it is the routing hub that prevents skill-miss bugs
10. Re-reference `using-agent-skills` when transitioning between phases — its flowcharts catch routing errors
11. **Apply context-engineering practices during long sessions** — summarize decisions, track tasks, use `§§include()`, manage context deliberately
12. **Subordinate delegations must include project conventions, architectural decisions, and acceptance criteria** — not just the task name
