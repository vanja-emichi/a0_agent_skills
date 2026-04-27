# Spec: 3-Tier Routing Upgrade

**Status:** Completed

## Objective

Upgrade the agent-skills plugin from a flat skill-loading model to a 3-tier routing architecture where specialist tasks (code review, testing, security) are delegated to dedicated sub-agent personas, while general tasks load skills directly. This eliminates ambiguity in skill dispatch and ensures the right agent with the right context handles each task.

## Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Add specialist sub-agent personas (code-reviewer, test-engineer, security-auditor) | Done |
| 2 | Create slash commands that delegate to specialists (/review, /test, /security) | Done |
| 3 | Build routing-table extension that injects specialist vs. general dispatch rules into system prompt | Done |
| 4 | Update using-agent-skills SKILL.md with flowchart, quick reference, and lifecycle delegation markers | Done |
| 5 | Add comprehensive tests for routing table, command templates, skill anatomy, and delegation markers | Done |

## Doc Path Convention

- **Canonical location:** `SPEC.md` in repo root — committed to git, tracks completed work
- **Working docs:** `.a0proj/specs/`, `.a0proj/tasks/`, `.a0proj/ideas/` — gitignored, used during planning

## Success Criteria

- 48 validation checks passing (`python scripts/validate.py`)
- 335 tests passing (`pytest tests/ -q`)
- 3 specialist agents with correct skill mappings
- 18 general skills routed via `skills_tool:load`
- Routing table injected into system prompt at agent startup
- All skills under 500 lines

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Specialist dispatch method | `call_subordinate profile=<agent>` | Sub-agents have isolated context and persona-specific system prompts |
| General dispatch method | `skills_tool:load <skill>` | No persona needed — skill instructions load into current agent context |
| Specialist skills set | code-review-and-quality, test-driven-development, security-and-hardening | Three skills where independent agent persona adds clear value |
| Routing table injection | System prompt extension (`_20_agent_skills_prompt.py`) | Available to agent on every turn without re-loading |
| Command templates | `.txt` files with `call_subordinate` / `skills_tool:load` | Consistent UX via slash commands |
| /code-simplify final step | Delegates to code-reviewer for quality check | Ensues simplified code still passes review |

## Boundaries

- **Always:** Run `python scripts/validate.py` and `pytest tests/` before committing
- **Always:** Keep specialist set at exactly 3 unless adding a new sub-agent persona with its own prompt file
- **Always:** New skills default to general tier (skills_tool:load) unless a dedicated agent persona is created
- **Never:** Mix dispatch methods — a skill is either specialist (delegate) or general (load), never both
- **Never:** Add skills that are vague advice instead of actionable processes

---

# Spec: Planning-with-Files Runtime Layer

**Status:** Completed

## Objective

Ship a runtime-enforced planning layer inside the `a0_agent_skills` plugin: one structured `plan` tool with 9 methods (`init`, `status`, `phase_start`, `phase_complete`, `extend`, `log_finding`, `log_progress`, `log_error`, `archive`), one `PlanState` library with disk persistence and in-memory cache, one EXTRAS extension injecting plan state every turn, three enforcement gates (no-plan gate, response gate, auto-progress), three lifecycle extensions (resume, verifier, auto-progress), two plan templates (default + analytics), one discipline skill (`planning-with-files`), and one `/plan-status` slash command. All additive — no existing files reshaped.

## Tasks

| # | Task | Status |
|---|------|--------|
| T01–T06 | Probes + Foundation (PlanState, tool, EXTRAS, gates) | Done |
| T07–T09 | First slice: init → status → EXTRAS-in-every-turn | Done |
| T10–T12 | Phase lifecycle + logging (findings, progress, errors) | Done |
| T13–T15 | Enforcement gates (no-plan, response, auto-progress) | Done |
| T16–T19 | Lifecycle extensions (resume, verifier) + templates | Done |
| T20 | `plan:archive` (completed + abandoned + SPEC.md emission) | Done |
| T21 | `skills/planning-with-files/SKILL.md` discipline skill | Done |
| T22 | `scripts/validate.py` extensions for v0.2.0 artifacts | Done |
| T24 | Command + skill integration with runtime layer | Done |
| T25 | Documentation update (SPEC.md, CHANGELOG.md, README.md) | Done |
| T23 | End-to-end lifecycle test + full regression | Done |

## Doc Path Convention

- **Canonical location:** `SPEC.md` in repo root — committed to git, tracks completed work
- **Working docs:** `.a0proj/specs/`, `.a0proj/tasks/`, `docs/ideas/` — gitignored, used during planning
- **Plan runtime state:** `.a0proj/run/current/` — gitignored, auto-managed by the plan tool

## Success Criteria

- 91 validation checks passing (`python scripts/validate.py`)
- 714 tests passing (`pytest tests/ -q`)
- Plan tool with 9 methods all functional
- EXTRAS block injected every turn with plan state when active
- 3-strike error protocol enforced by response gate
- `/plan-status` slash command registered and working
- `planning-with-files` skill with Manus principles, 5-Question Reboot, Read/Write matrix
- Commands (`/plan`, `/build`, `/ship`) integrated with plan tool methods
- Full lifecycle test covering init → phases → archive

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State persistence | Disk at `.a0proj/run/current/` with in-memory cache | Survives context compaction, subordinate delegation, and conversation restarts |
| Cache invalidation | mtime-based with content-hash fallback | Efficient cache hits for unchanged state |
| Tool architecture | Single tool with 9 sub-methods | Cohesive API surface, one tool prompt |
| Findings model | Append-only with trusted/untrusted tags | Audit trail + prompt injection defense |
| Error tracking | 3-strike protocol with signature hashing | Breaks retry loops automatically |
| Gate enforcement | `tool_execute_before` + `tool_execute_after` extensions | Hooks into existing framework lifecycle |
| SPEC emission on archive | Optional `emit_spec` flag | Completed plans can write findings to SPEC.md |
| Archive for abandoned | Write to `docs/ideas/<slug>-abandoned.md` | Preserves institutional knowledge |

## Boundaries

- **Always:** Use plan tool for state mutations — never edit `.a0proj/run/current/` files directly
- **Always:** Tag findings from external sources as `untrusted`
- **Always:** Run `plan:status` after context compaction or conversation resume
- **Never:** Delete or edit findings — append superseding ones instead
- **Never:** Proceed past 3-strike block without user escalation
- **Never:** Mix plan state with project state — plan state is ephemeral and cleaned up on archive
- **Never:** Duplicate content between skills — reference other skills instead
