# a0_agent_skills

A plugin for [Agent Zero](https://github.com/frdel/agent-zero) that ports the [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) development workflow toolkit -- 21 curated skills, 3 specialist agent profiles, and 7 slash commands -- into the Agent Zero plugin system. It gives any Agent Zero agent access to a production-grade software engineering lifecycle: spec → plan → build → test → review → ship, with optional telemetry to track skill activations during workflow validation.

---

## Quick Start

Once the plugin is installed and enabled:

```
# 1. Discover the right skill for your task
skills_tool:search  query="write a spec for a login system"

# 2. Start the engineering lifecycle
/spec Build a user authentication system

# 3. Plan the work
/plan

# 4. Implement incrementally
/build Implement the login endpoint

# 5. Test with TDD
/test Add edge case tests for login failure

# 6. Review before merging
/review

# 7. Ship with a GO/NO-GO decision
/ship v1.0 authentication system
```

Or ask naturally -- the agent will detect the right skill:
- *"Let's write a spec before we start coding"* → `spec-driven-development`
- *"Break this feature into tasks"* → `planning-and-task-breakdown`
- *"Something is broken, help me debug it"* → `debugging-and-error-recovery`

---


## Prerequisites

The **`commands` plugin** must be installed and active. The 7 slash commands provided by this plugin (`/spec`, `/plan`, `/build`, `/review`, `/test`, `/code-simplify`, `/ship`) rely on the commands plugin's dispatch infrastructure.

Verify it is installed:
```
/a0/usr/plugins/commands/
```

If it is not present, install it via the Plugin Hub before enabling this plugin.

---

## Routing System

The plugin uses a **`system_prompt` extension** to inject mandatory routing rules into every Agent Zero session. This extension lives at:

```
/a0/usr/plugins/a0_agent_skills/extensions/python/system_prompt/_15_agent_skills_routing.py
```

It reads routing rules from:
```
/a0/usr/plugins/a0_agent_skills/prompts/agent.skills.routing.md
```

**Key advantage:** This approach works **regardless of project context**. Whether a project is active or not, the routing rules are always injected into the agent's system prompt during prompt assembly. This is the same pattern used by the built-in `_memory` and `_browser` plugins.

---

## The 6-Phase Lifecycle

Every feature or change passes through six phases in order. Each phase has a required skill:

| Phase | Required Skill(s) | Purpose |
|-------|-------------------|--------|
| **DEFINE** | `spec-driven-development` | Define what to build before building it |
| **PLAN** | `planning-and-task-breakdown` | Break work into ordered, testable increments |
| **BUILD** | `incremental-implementation` + `test-driven-development` | Implement in slices with tests first |
| **VERIFY** | `debugging-and-error-recovery` | Prove it works -- fix issues before review |
| **REVIEW** | `code-review-and-quality` | Structured quality gate before shipping |
| **SHIP** | `shipping-and-launch` | Deploy with confidence and rollback plan |

### Skills by Phase (Full Catalog)

**DEFINE:** spec-driven-development

**PLAN:** planning-and-task-breakdown, context-engineering

**BUILD:** incremental-implementation, test-driven-development, source-driven-development, frontend-ui-engineering, api-and-interface-design

**VERIFY:** browser-testing-with-devtools, debugging-and-error-recovery

**REVIEW:** code-review-and-quality, code-simplification, security-and-hardening, performance-optimization

**SHIP:** shipping-and-launch, ci-cd-and-automation, git-workflow-and-versioning, documentation-and-adrs, deprecation-and-migration

---

## The 3 Agent Profiles

Specialist subordinate agents activated via `call_subordinate`. These personas are invoked at the correct lifecycle phase:

### `code-reviewer`
Senior staff engineer conducting five-axis code review: **correctness, readability, architecture, security, performance**. Produces structured `APPROVE / REQUEST CHANGES` reports with Critical / Important / Suggestion findings and `file:line` references.

**Invoked during:** REVIEW phase (via `/review`) and SHIP phase (via `/ship`).

```
call_subordinate(profile="code-reviewer")
```

### `security-auditor`
Security engineer focused on vulnerability detection and threat modeling. Covers OWASP Top 10, input handling, authentication/authorization, data protection, infrastructure, and third-party integrations. Produces severity-classified findings (Critical / High / Medium / Low / Info) with actionable mitigations.

**Invoked during:** SHIP phase (via `/ship`).

```
call_subordinate(profile="security-auditor")
```

### `test-engineer`
QA engineer for test strategy, test writing, and coverage analysis. Implements the **Prove-It Pattern** for bug reproduction. Produces Test Coverage Analysis reports with Recommended Tests and priority classification.

**Invoked during:** VERIFY phase and SHIP phase (via `/ship`).

```
call_subordinate(profile="test-engineer")
```

> **Orchestration rule:** The main agent (or a slash command) is the orchestrator. Personas do not invoke each other. The only multi-persona pattern is parallel fan-out with a merge step, used by `/ship`.

> **Per-persona model override:** Agent Zero does not support a `model` field directly in `agent.yaml`. To assign a specific LLM model to a profile (e.g. Haiku for `test-engineer`, Opus for `security-auditor`), create a `_model_config/config.json` alongside the profile:
> ```
> /a0/usr/plugins/a0_agent_skills/agents/security-auditor/plugins/_model_config/config.json
> ```
> This file must contain a complete effective configuration for `chat_model`, `utility_model`, and `embedding_model` (selected as a whole, not merged). See the `_model_config` plugin documentation for the schema.

---

## The 7 Slash Commands

| Command | When to use |
|---|---|
| `/spec` | Start a new feature or project -- loads `spec-driven-development` and writes `SPEC.md`. Surfaces assumptions before writing any code. |
| `/plan` | Break confirmed spec into tasks -- loads `planning-and-task-breakdown` and writes `tasks/plan.md` + `tasks/todo.md`. |
| `/build` | Implement the next task -- loads `incremental-implementation` + `test-driven-development`. RED → GREEN → commit cycle. |
| `/test` | TDD workflow or bug reproduction -- loads `test-driven-development`. Write failing test first; use the Prove-It Pattern for bugs. |
| `/review` | Single-perspective code review -- delegates to the `code-reviewer` profile via `call_subordinate`. |
| `/code-simplify` | Reduce complexity without changing behavior -- loads `code-simplification`. Applies guard clauses, splits functions, removes dead code. |
| `/ship` | Pre-launch sequential review -- runs `code-reviewer` → `security-auditor` → `test-engineer` one after another, then produces a **GO / NO-GO** decision with rollback plan. |

### Example usage

```
/spec Build a REST API for task management
/plan
/build Implement POST /tasks endpoint
/test Add tests for the task creation edge cases
/review
/ship v1.0 release -- task API
```

---

## Installation

**Option A -- Copy directly:**
```bash
cp -r /path/to/a0_agent_skills /a0/usr/plugins/a0_agent_skills
```

**Option B -- Plugin Hub:**
Search for `a0_agent_skills` in the Agent Zero Plugin Hub and click Install.

After installation, restart Agent Zero (or use the UI restart button) so the plugin is picked up.

---

## Enabling Telemetry (Phase 1 Validation)

Telemetry is **off by default**. Enable it to log every `skills_tool` activation to a JSONL file for workflow analysis.

**Step 1:** Copy the plugin config to your project:
```bash
mkdir -p /a0/usr/projects/<your-project>/.a0proj/plugins/a0_agent_skills/
cp /a0/usr/plugins/a0_agent_skills/default_config.yaml \
   /a0/usr/projects/<your-project>/.a0proj/plugins/a0_agent_skills/config.yaml
```

**Step 2:** Edit the config and set `telemetry_enabled: true`:
```yaml
telemetry_enabled: true
telemetry_log_path: .a0proj/skill_activations.jsonl
```

**Step 3:** Run your workflow. Each `skills_tool:load`, `skills_tool:search`, or `skills_tool:list` call appends one JSON line to `.a0proj/skill_activations.jsonl`:
```json
{"ts": 1234567890.0, "tool": "skills_tool:load", "skill_name": "incremental-implementation", "query": null, "result_preview": "Skill loaded..."}
```

Telemetry is fully guarded -- a logging failure never interrupts agent operation.

---

## Skill Override: Customizing at Project Scope

You can override any skill for a specific project without modifying the plugin. Copy the skill's `SKILL.md` to your project's `.a0proj` directory:

```bash
mkdir -p /a0/usr/projects/<your-project>/.a0proj/skills/<skill-name>/
cp /a0/usr/plugins/a0_agent_skills/skills/<skill-name>/SKILL.md \
   /a0/usr/projects/<your-project>/.a0proj/skills/<skill-name>/SKILL.md
```

Then edit the copy. Agent Zero's skill resolution searches project scope first, so your local version takes precedence over the plugin version for that project only.

---

## The 20-Skill Cap and `using-agent-skills`

Agent Zero's skill system works best when the agent loads skills intentionally rather than pinning everything into the system prompt permanently. The `using-agent-skills` skill explains when and how to invoke other skills -- it is a **meta-skill** designed for on-demand use.

**Do not pin `using-agent-skills` as a persistent/always-loaded skill.** It should be loaded on demand only (e.g. when onboarding a new agent to the workflow).

If you are pinning skills for a project, prioritize the 7 lifecycle skills. Stay within the 20-skill context budget to maintain performance.

---

## Attribution

Skills, agent personas, and slash commands ported from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) by [Addy Osmani](https://github.com/addyosmani). Adapted for the Agent Zero plugin system.
