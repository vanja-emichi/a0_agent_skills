# Skill Checkpoint, Gate & Approval Point Analysis

> Comprehensive extraction from all 23 SKILL.md files in `/a0/usr/plugins/a0_agent_skills/skills/`
> Purpose: Inform the design of a phase-transition approval system where certain transitions require explicit user approval.

---

## 1. Master Table: All 23 Skills

### DEFINE Phase Skills

| Skill | Phase | Checkpoints (what to verify) | User Review Points (where human input needed) | Gates (what blocks next step) |
|-------|-------|-----------------------------|-----------------------------------------------|-------------------------------|
| **interview-me** | DEFINE | - Explicit hypothesis with confidence number stated in first turn (8 checklist items total) - Every confidence below 70% has a one-line reason - Questions asked one at a time with agent's guess attached - At least one "what would you actually want?" probe ran - Concrete restate written (Outcome/User/Why now/Success/Constraint/Out of scope) - Agent can predict reactions to next 3 questions | - User must confirm restate with an explicit "yes" - "Sounds good" / "whatever you think" are NOT accepted as confirmation - Wait for user reaction before next question | - The gate is an explicit "yes" — ambiguous responses rejected - Must reach ~95% confidence before stopping - Wait for user reaction before asking next question |
| **idea-refine** | DEFINE | - Clear "How Might We" problem statement exists (10 checklist items) - Target user and success criteria defined - Multiple directions explored (not just first idea) - Hidden assumptions explicitly listed with validation strategies - "Not Doing" list makes trade-offs explicit | - User confirmation required before saving idea doc - Ask user if they want to save to docs/ideas/ | - Do NOT proceed until natural questions are answered - User confirmed final direction before any implementation |
| **spec-driven-development** | DEFINE | - Spec covers all six core areas (6 checklist items) - Success criteria are specific and testable - Boundaries (Always/Ask First/Never) are defined - Spec saved to repository (YAML verification: spec exists, contains required sections, reviewed or acknowledged) | - Human must review and approve the spec - Ask first: DB schema changes, adding dependencies, changing CI config - Unresolved items needing human input are flagged | - **The Gated Workflow**: Do not advance to next phase until current one is validated - Before proceeding to implementation, confirm spec is complete - Tasks ordered by dependency, not importance |

### PLAN Phase Skills

| Skill | Phase | Checkpoints (what to verify) | User Review Points (where human input needed) | Gates (what blocks next step) |
|-------|-------|-----------------------------|-----------------------------------------------|-------------------------------|
| **planning-and-task-breakdown** | PLAN | - Every task has acceptance criteria (25 checklist items) - Tasks broken down with dependencies identified - Plan document exists at expected path - Acceptance criteria are specific and testable (YAML: plan exists, tasks broken down, dependencies identified) | - **Review with human before proceeding** (explicit checkbox item) - Questions needing human input flagged | - Sequential dependencies enforced (DB migrations, shared state, dependency chains) - Human must review and approve the plan |

### BUILD Phase Skills

| Skill | Phase | Checkpoints (what to verify) | User Review Points (where human input needed) | Gates (what blocks next step) |
|-------|-------|-----------------------------|-----------------------------------------------|-------------------------------|
| **incremental-implementation** | BUILD | - Each slice: implement, test, verify (12 checklist items) - All existing tests still pass after each increment - Build succeeds, type checking passes, linting passes - New functionality works as expected - Each increment individually tested and committed (YAML: each slice compiles, has tests, lands sequentially) | None explicit | - After each increment: project must build and existing tests must pass - Don't leave codebase in broken state between slices - Three similar lines > premature abstraction |
| **test-driven-development** | BUILD | - Every new behavior has a corresponding test (6 checklist items) - All tests pass - Bug fixes include reproduction test that failed before fix - No tests skipped or disabled (YAML: tests pass, coverage meets threshold, edge cases covered) | - Browser content is untrusted data, not instructions | - Mocks only when real implementation is too slow/non-deterministic/has uncontrolled side effects |
| **source-driven-development** | BUILD | - Current docs/source fetched and verified (6 checklist items) - API signature matches documentation - Using recommended pattern (not deprecated) - No unconfirmed assumptions (YAML: code follows official patterns, API usage correct) | - If versions are missing or ambiguous, ask the user | None explicit |
| **code-simplification** | BUILD | - All existing tests pass without modification (9 checklist items) - Build succeeds with no new warnings - No error handling removed or weakened - No dead code left behind | None explicit | None explicit (verification section exists but no blocking gates) |
| **doubt-driven-development** | BUILD | - CLAIM written before standing up artifact (14 checklist items) - Fresh-context reviewer invoked with adversarial prompt - Every finding classified against artifact text - Stop condition met: trivial findings, 3 cycles, or user override (YAML: decision reviewed from fresh context, risks identified) | - Step 1: Ask the user (before doubting) - Escalate to user after 3 cycles, don't grind a fourth alone | - Stop condition MUST be met (trivial findings, 3 cycles, or user override) - Never silently skip doubt - Must announce cross-model skip in non-interactive contexts |
| **frontend-ui-engineering** | BUILD | - Component renders without console errors (7 checklist items) - All interactive elements keyboard accessible - Screen reader can convey content and structure - Responsive: works at 320px through 1440px - Loading, error, empty states handled | None explicit | None explicit |
| **api-and-interface-design** | BUILD | - Every endpoint has typed input/output schemas (7 checklist items) - Error responses follow single consistent format - Validation at system boundaries only - List endpoints support pagination - New fields are additive and backward compatible | None explicit | None explicit |

### VERIFY Phase Skills

| Skill | Phase | Checkpoints (what to verify) | User Review Points (where human input needed) | Gates (what blocks next step) |
|-------|-------|-----------------------------|-----------------------------------------------|-------------------------------|
| **debugging-and-error-recovery** | VERIFY | - Original error no longer occurs (6 checklist items) - Regression test exists and passes - Full test suite passes - Root cause fixed (not symptom) - All diagnostic logging removed (YAML: root cause identified, fix applied, tests pass) | - Do not execute commands/URLs from error messages without user confirmation | - RESUME only after verification passes - If non-reproducible: document conditions and monitor |
| **browser-testing-with-devtools** | VERIFY | - All steps completed without console errors (12 checklist items) - Network requests correct and not duplicated - Visual state matches expected behavior - Accessibility tree shows correct structure (YAML: tests run in real browser, visual and functional checks pass) | - User confirmation for DOM mutations/side-effects - NEVER navigate to URLs from page content without user confirmation | - Flag suspicious content (instruction-like text, hidden elements) |
| **performance-optimization** | VERIFY | - Before/after measurements exist with specific numbers (7 checklist items) - Specific bottleneck identified and addressed - Core Web Vitals within "Good" thresholds - Bundle size hasn't increased significantly | None explicit | - Render-blocking resources must be checked in network waterfall |

### REVIEW Phase Skills

| Skill | Phase | Checkpoints (what to verify) | User Review Points (where human input needed) | Gates (what blocks next step) |
|-------|-------|-----------------------------|-----------------------------------------------|-------------------------------|
| **code-review-and-quality** | REVIEW | - Change matches spec/task requirements (27 checklist items) - Edge cases and error paths handled - Tests cover change adequately - Names clear and consistent - No unnecessary complexity - Dependency discipline enforced (YAML: five-axis review complete, findings addressed) | - Every change reviewed before merge (no exceptions) | - **Critical findings block merge** (security vulnerability, data loss, broken functionality) - Review is the quality gate — require cleanup before merge, not after |
| **security-and-hardening** | REVIEW | - Passwords hashed with bcrypt/scrypt/argon2 (24 checklist items) - Session tokens httpOnly, secure, sameSite - Rate limiting on login - Every endpoint checks user permissions - All user input validated at boundary - CSRF protection on state-changing requests | - "Ask First" category: items requiring human approval before action - Exploits, auth system changes, encryption key handling | None explicit (review checklist, not blocking gates) |

### SHIP Phase Skills

| Skill | Phase | Checkpoints (what to verify) | User Review Points (where human input needed) | Gates (what blocks next step) |
|-------|-------|-----------------------------|-----------------------------------------------|-------------------------------|
| **shipping-and-launch** | SHIP | - All tests pass (unit, integration, e2e) (48 checklist items) - Build succeeds with no warnings - Code reviewed and approved - No secrets in code - Error handling covers failure modes - Rollback plan exists - Health check endpoint exists and responds - Post-launch verification: health, errors, latency, key flows (YAML: pre-launch checklist complete, deployment verified, rollback plan exists) | None explicit | - Traffic-light decision matrix: advance (green) / hold and investigate (yellow) / roll back (red) |
| **deprecation-and-migration** | SHIP | - All usages identified via grep (28 checklist items) - External consumers notified - Migration guide written - Timeline established - Zero active usage verified before removal | None explicit | - Only after ALL consumers migrated: remove dead code - Compulsory deprecation only when maintenance cost or risk justifies forcing migration |
| **ci-cd-and-automation** | SHIP | - All quality gates present: lint, types, tests, build, audit (10 checklist items) - Pipeline runs on every PR and push to main - Secrets in secrets manager, not code - Deployment has rollback mechanism | None explicit | - **No gate can be skipped** — fix the issue, don't disable the rule - CI MUST pass before merge |
| **git-workflow-and-versioning** | SHIP | - Unit tests for the feature (17 checklist items) - API tests for request/response - Manual: create/filter tasks - No console errors - Commit does one logical thing - Conventional Commits format | None explicit | - Test fails → revert to last commit → investigate |
| **documentation-and-adrs** | SHIP | - ADRs exist for significant decisions (10 checklist items) - README covers quick start, commands, architecture - API functions have parameter/return docs - Code examples are syntactically correct | None explicit | None explicit |

### META Phase Skills

| Skill | Phase | Checkpoints (what to verify) | User Review Points (where human input needed) | Gates (what blocks next step) |
|-------|-------|-----------------------------|-----------------------------------------------|-------------------------------|
| **using-agent-skills** | META | - Right skills loaded for task type (5 checklist items) - Core Operating Behaviors active - Loaded skills' Red Flags checked - Loaded skills' Verification checklists will be completed | None explicit | - **STOP. Do not proceed with a guess.** - Wait for resolution before continuing |
| **context-engineering** | META | - Project guidance file exists covering tech stack, commands, conventions (12 checklist items) - Complex tasks have explicit acceptance criteria - Example tasks annotated with pointers to existing code (YAML: context files created, index is queryable) | None explicit | - You MUST NOT: skip context setup, ignore .cursorignore, guess at import paths |

---

## 2. Phase-Level Summary

| Phase | Skills | Checklist Items | MUST/NEVER Rules | Verify Steps | Gates | User Interaction Points | **Total Controls** |
|-------|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| **DEFINE** | 3 | 24 | 14 | 13 | 7 | 6 | **64** |
| **PLAN** | 1 | 25 | 1 | 6 | 1 | 2 | **35** |
| **BUILD** | 7 | 61 | 18 | 24 | 6 | 6 | **115** |
| **VERIFY** | 3 | 25 | 8 | 15 | 5 | 4 | **57** |
| **REVIEW** | 2 | 51 | 15 | 11 | 1 | 10 | **88** |
| **SHIP** | 5 | 113 | 11 | 16 | 3 | 0 | **143** |
| **META** | 2 | 17 | 6 | 9 | 2 | 0 | **34** |

### Key Observations

- **SHIP has the most controls (143)** — dominated by shipping-and-launch's 48 checklist items and deprecation-and-migration's 28. This phase is checklist-heavy but has zero explicit user interaction points.
- **BUILD has the most verify steps (24)** — every build skill has a "verify" step, reflecting the implement-test-verify cycle.
- **REVIEW has the most MUST/NEVER rules (15)** and the highest user interaction density (10 points across only 2 skills) — reflecting its role as the quality gate.
- **DEFINE has the most gates (7)** relative to its skill count — confirming it as the phase where wrong decisions are most costly.
- **PLAN has a critical human gate** — "Review with human before proceeding" is an explicit checkbox item.

---

## 3. Natural Approval Gates in the Lifecycle

Based on the skill analysis, these are the natural points where user approval should be required before the agent can advance:

### Gate 1: DEFINE → PLAN ("What are we building?")

**Blocking skill:** `spec-driven-development`

- **The Gated Workflow**: "Do not advance to the next phase until the current one is validated"
- **Spec approval**: "The human has reviewed and approved the spec" (explicit checkbox)
- **Boundaries**: "Ask first" items defined (DB changes, new dependencies, CI changes)
- **Interview gate**: "The gate is an explicit yes" — ambiguous confirmation rejected
- **Idea refinement**: "User confirmed the final direction before any implementation work"

**Recommendation**: Require explicit user approval of the spec before proceeding to planning.

### Gate 2: PLAN → BUILD ("How are we building it?")

**Blocking skill:** `planning-and-task-breakdown`

- **Human review**: "Review with human before proceeding" (explicit checkbox)
- **Plan approval**: "The human has reviewed and approved the plan" (explicit checkbox)
- **Acceptance criteria**: "Every task has acceptance criteria" verified before proceeding

**Recommendation**: Require explicit user approval of the plan (tasks, dependencies, acceptance criteria) before any code is written.

### Gate 3: BUILD → VERIFY ("Does it work?")

**Blocking skills:** `incremental-implementation`, `test-driven-development`

- **Each slice verified**: tests pass, build succeeds, manual check done
- **No broken state**: "After each increment, the project must build and existing tests must pass"
- **Doubt cycles**: stop condition must be met (trivial findings, 3 cycles, or user override)

**Recommendation**: This is primarily an internal verification gate. The exit criteria are mechanical (tests pass, build succeeds). No explicit human approval required unless doubt-driven-development surfaces substantive findings that need user resolution.

### Gate 4: VERIFY → REVIEW ("Is it correct?")

**Blocking skills:** `debugging-and-error-recovery`, `browser-testing-with-devtools`

- **RESUME only after verification passes** (debugging)
- **All diagnostic logging removed** (debugging)
- **Visual and functional checks pass** (browser testing)
- **No new failures introduced** (debugging)

**Recommendation**: Mechanical gate — all verification checks must pass. Human approval only for non-reproducible bugs ("document conditions and monitor").

### Gate 5: REVIEW → SHIP ("Is it ready to ship?")

**Blocking skills:** `code-review-and-quality`, `security-and-hardening`

- **Critical findings block merge** (code-review: security vulnerability, data loss, broken functionality)
- **Every change reviewed before merge — no exceptions**
- **Five-axis review complete, findings addressed** (YAML verification)
- **Security: "Ask First" items require human approval**

**Recommendation**: Require explicit user approval after code review. Critical findings must be resolved. Security-sensitive changes require separate human sign-off.

### Gate 6: SHIP → DONE ("Did it ship safely?")

**Blocking skill:** `shipping-and-launch`

- **Pre-launch checklist complete** (YAML verification)
- **Deployment verified, rollback plan exists** (YAML verification)
- **No gate can be skipped** (CI/CD)
- **Post-launch verification**: health check, errors, latency, key flows

**Recommendation**: Require explicit user approval before launch. Post-launch health checks are mechanical but results should be reported.

---

## 4. Skills Ranked by Control Density

| Rank | Skill | Phase | Checklist | MUST/NEVER | Verify | Gates | User Points | Total |
|-----:|-------|-------|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | shipping-and-launch | SHIP | 48 | 0 | 10 | 0 | 0 | **58** |
| 2 | security-and-hardening | REVIEW | 24 | 10 | 4 | 0 | 8 | **46** |
| 3 | code-review-and-quality | REVIEW | 27 | 5 | 7 | 1 | 2 | **42** |
| 4 | deprecation-and-migration | SHIP | 28 | 4 | 4 | 2 | 0 | **38** |
| 5 | doubt-driven-development | BUILD | 14 | 9 | 8 | 4 | 2 | **37** |
| 6 | planning-and-task-breakdown | PLAN | 25 | 1 | 6 | 1 | 2 | **35** |
| 7 | browser-testing-with-devtools | VERIFY | 12 | 6 | 12 | 1 | 3 | **34** |
| 8 | idea-refine | DEFINE | 10 | 9 | 2 | 1 | 2 | **24** |
| 9 | spec-driven-development | DEFINE | 6 | 5 | 4 | 3 | 4 | **22** |
| 10 | context-engineering | META | 12 | 4 | 5 | 0 | 0 | **21** |
| 11 | git-workflow-and-versioning | SHIP | 17 | 1 | 1 | 0 | 0 | **19** |
| 12 | interview-me | DEFINE | 8 | 0 | 7 | 3 | 0 | **18** |
| 13 | ci-cd-and-automation | SHIP | 10 | 4 | 1 | 1 | 0 | **16** |
| 14 | incremental-implementation | BUILD | 12 | 1 | 2 | 1 | 0 | **16** |
| 15 | source-driven-development | BUILD | 6 | 3 | 5 | 0 | 1 | **15** |
| 16 | code-simplification | BUILD | 9 | 2 | 3 | 0 | 0 | **14** |
| 17 | using-agent-skills | META | 5 | 2 | 4 | 2 | 0 | **13** |
| 18 | documentation-and-adrs | SHIP | 10 | 2 | 0 | 0 | 0 | **12** |
| 19 | frontend-ui-engineering | BUILD | 7 | 1 | 4 | 0 | 0 | **12** |
| 20 | performance-optimization | VERIFY | 7 | 1 | 2 | 2 | 0 | **12** |
| 21 | api-and-interface-design | BUILD | 7 | 1 | 1 | 0 | 2 | **11** |
| 22 | debugging-and-error-recovery | VERIFY | 6 | 1 | 1 | 2 | 1 | **11** |
| 23 | test-driven-development | BUILD | 6 | 1 | 1 | 1 | 1 | **10** |

---

## 5. Phase Handoff Chain (from YAML `next_skills`)

```
interview-me
  └→ spec-driven-development
       └→ planning-and-task-breakdown
            ├→ incremental-implementation
            │    ├→ test-driven-development
            │    │    └→ debugging-and-error-recovery
            │    │         └→ code-review-and-quality
            │    │              └→ shipping-and-launch
            │    └→ debugging-and-error-recovery
            └→ test-driven-development

doubt-driven-development
  ├→ incremental-implementation
  └→ test-driven-development

context-engineering
  └→ incremental-implementation

source-driven-development
  ├→ incremental-implementation
  └→ test-driven-development

browser-testing-with-devtools
  └→ code-review-and-quality
```

---

## 6. Design Recommendations for the Approval System

### 6.1 Mandatory Human Approval Gates (Must Block)

These gates already exist in skills as explicit blocking conditions with user interaction:

| Gate | Transition | Trigger | What Skills Already Define |
|------|-----------|---------|---------------------------|
| **G1** | DEFINE → PLAN | Spec approval | spec-driven-development: "human has reviewed and approved the spec" + "do not advance to next phase until current one is validated" |
| **G2** | PLAN → BUILD | Plan approval | planning-and-task-breakdown: "review with human before proceeding" + "human has reviewed and approved the plan" |
| **G3** | BUILD → REVIEW | Code review | code-review-and-quality: "every change gets reviewed before merge — no exceptions" + "critical findings block merge" |
| **G4** | REVIEW → SHIP | Ship approval | shipping-and-launch: "pre-launch checklist complete" + "deployment verified" + "rollback plan exists" |

### 6.2 Conditional Human Approval Gates (Block on Trigger)

These gates require human input only when specific conditions are met:

| Gate | Condition | Source Skill | Trigger |
|------|-----------|-------------|---------|
| **C1** | Doubt findings substantive | doubt-driven-development | After 3 cycles with non-trivial findings, escalate to user |
| **C2** | Security-sensitive change | security-and-hardening | "Ask First" items: exploits, auth changes, encryption keys |
| **C3** | Non-reproducible bug | debugging-and-error-recovery | Cannot reproduce after triage — document and escalate |
| **C4** | Version ambiguity | source-driven-development | Versions missing or ambiguous — ask user before proceeding |
| **C5** | Schema/dependency change | spec-driven-development | "Ask first" items: DB schema, new dependencies, CI config |
| **C6** | Browser URL navigation | browser-testing-with-devtools | URLs from page content require user confirmation |
| **C7** | Deprecation scope | deprecation-and-migration | Compulsory vs. advisory determination affects timeline |

### 6.3 Mechanical Gates (Auto-Pass on Criteria Met)

These gates are verification checkpoints that can pass without human input if all criteria are met:

| Gate | Criteria | Source Skills |
|------|----------|-------------|
| **M1** | Slice complete | incremental-implementation: tests pass + build succeeds + type check + lint |
| **M2** | Tests green | test-driven-development: all tests pass + coverage meets threshold |
| **M3** | Debug resolved | debugging-and-error-recovery: root cause fixed + regression test + suite green |
| **M4** | Performance validated | performance-optimization: before/after measurements + Core Web Vitals in range |
| **M5** | CI pipeline green | ci-cd-and-automation: all quality gates pass + no gate skipped |
| **M6** | Post-launch healthy | shipping-and-launch: health check 200 + no new errors + latency nominal |

### 6.4 Approval System Architecture

```
User Request
    │
    ▼
[DEFINE] ─── G1: Spec approved? ──── NO ──→ Block (revise spec)
    │                                   YES
    ▼
[PLAN]  ─── G2: Plan approved? ──── NO ──→ Block (revise plan)
    │                                   YES
    ▼
[BUILD] ─── M1: Slice green? ──── NO ──→ Block (fix slice)
    │                                 YES
    │         C1: Doubt findings? ── YES ──→ Block (escalate to user)
    │                                  NO
    ▼
[VERIFY] ── M3: Bug resolved? ──── NO ──→ Block (continue debugging)
    │                                 YES
    ▼
[REVIEW] ── G3: Review passed? ── NO ──→ Block (address findings)
    │                                 YES
    │         C2: Security items? ── YES ──→ Block (human sign-off)
    │                                  NO
    ▼
[SHIP]  ─── G4: Launch approved? ── NO ──→ Block (complete checklist)
    │                                 YES
    ▼
Done
```

### 6.5 Summary Statistics for Design

- **Total explicit user interaction points across all skills**: 32
- **Skills with zero user interaction points**: 14 of 23 (61%)
- **Skills with explicit YAML verification fields**: 12 of 23 (52%)
- **Skills with explicit next_skills (handoff points)**: 11 of 23 (48%)
- **Mandatory approval gates (G1-G4)**: 4 transitions requiring explicit human yes
- **Conditional approval gates (C1-C7)**: 7 situations requiring human input
- **Mechanical gates (M1-M6)**: 6 checkpoints that auto-pass on criteria met

### 6.6 Which Phases Have the Most Checkpoints

1. **SHIP (143 controls)** — heaviest by sheer volume, but almost all are checklist items, not gates. The phase is self-policing with clear pass/fail criteria.
2. **BUILD (115 controls)** — highest verify-step count. Controls are per-slice and per-cycle, making this the most granular phase.
3. **REVIEW (88 controls)** — highest MUST/NEVER density and user interaction density. This is the strictest quality gate.
4. **DEFINE (64 controls)** — highest gate-to-skill ratio. Wrong decisions here are most expensive, so controls are front-loaded.
5. **VERIFY (57 controls)** — focused on end-to-end validation. Mechanical rather than human-gated.
6. **PLAN (35 controls)** — single skill but heavily controlled: 25 checklist items, explicit human review gate.
7. **META (34 controls)** — cross-cutting concerns, not phase-specific.

### 6.7 Where the Natural Approval Gates Sit

The lifecycle has **four** natural approval choke points where human buy-in is already encoded:

1. **After spec, before plan** — "What are we building?" (cheapest correction point)
2. **After plan, before code** — "How will we build it?" (prevents wasted implementation)
3. **After review, before ship** — "Is it good enough?" (quality gate)
4. **After checklist, before deploy** — "Is it safe to launch?" (production gate)

Between these, the system should auto-verify mechanical criteria (tests pass, build succeeds, coverage met) and only escalate to humans on the conditional triggers (doubt findings, security items, non-reproducible bugs).
