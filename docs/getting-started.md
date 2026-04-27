# Getting Started with agent-skills (Agent Zero)

This guide covers using the agent-skills plugin with **Agent Zero**. For other agents (Claude Code, Cursor, Copilot), see [the upstream README](https://github.com/addyosmani/agent-skills).

## How It Works in Agent Zero

Once installed, the plugin works automatically:

1. **Routing table auto-injects** — every turn, an intent→skill routing table is added to the agent's context via the `message_loop_prompts_after` extension. No manual setup needed.
2. **Skills load on demand** — the agent calls `skills_tool:load <skill-name>` when a task matches a skill trigger.
3. **Commands auto-register** — 7 slash commands (`/spec`, `/plan`, `/build`, `/test`, `/review`, `/code-simplify`, `/ship`) become available in the chat UI immediately.
4. **Agent personas available** — 3 specialist profiles (`code-reviewer`, `test-engineer`, `security-auditor`) can be delegated to via `call_subordinate`.

## Installation

### Option A — Plugin Index (recommended)

In the Agent Zero chat UI, run:

```
/plugin install vanja-emichi/a0_agent_skills
```

Then restart Agent Zero. Skills, commands, and hooks activate automatically.

### Option B — Manual (for development)

```bash
git clone https://github.com/vanja-emichi/a0_agent_skills.git \
  /path/to/agent-zero/usr/plugins/agent_skills
```

Then restart Agent Zero.

## Using Skills

Skills activate automatically via the routing table injected each turn. When the agent identifies a matching intent, it loads the skill:

```json
{ "tool_name": "skills_tool:load", "tool_args": { "skill_name": "spec-driven-development" } }
```

You can also trigger skills explicitly in chat:

- *"Let's spec this out"* → agent loads `spec-driven-development`
- *"Something's broken"* → agent loads `debugging-and-error-recovery`
- *"Review this code"* → agent loads `code-review-and-quality`

### Skill Discovery

The routing table (auto-injected every turn) maps intent to skill:

| Intent | Skill |
|--------|-------|
| Vague idea / needs refinement | `idea-refine` |
| New feature / project / change | `spec-driven-development` |
| Have spec, need tasks | `planning-and-task-breakdown` |
| Implementing code | `incremental-implementation` |
| UI / frontend work | `frontend-ui-engineering` |
| API or interface design | `api-and-interface-design` |
| Need doc-verified code | `source-driven-development` |
| Managing agent context | `context-engineering` |
| Writing or running tests | `test-driven-development` |
| Browser-based verification | `browser-testing-with-devtools` |
| Something broke | `debugging-and-error-recovery` |
| Reviewing code | `code-review-and-quality` |
| Security concerns | `security-and-hardening` |
| Performance concerns | `performance-optimization` |
| Simplifying code | `code-simplification` |
| Committing / branching | `git-workflow-and-versioning` |
| CI/CD pipeline work | `ci-cd-and-automation` |
| Writing docs / ADRs | `documentation-and-adrs` |
| Removing old systems | `deprecation-and-migration` |
| Deploying / launching | `shipping-and-launch` |

To list all available skills manually:

```json
{ "tool_name": "skills_tool:list", "tool_args": {} }
```

## Using Slash Commands

7 slash commands are auto-registered in the Agent Zero chat UI:

| Command | Skill activated |
|---------|----------------|
| `/spec` | `spec-driven-development` |
| `/plan` | `planning-and-task-breakdown` |
| `/build` | `incremental-implementation` + `test-driven-development` |
| `/test` | `test-driven-development` |
| `/review` | `code-review-and-quality` |
| `/code-simplify` | `code-simplification` |
| `/ship` | `shipping-and-launch` |

Command definitions live in the `commands/` directory as `.command.yaml` + `.txt` pairs, symlinked to both global and project scope on plugin init.

## Using Agent Personas

3 specialist agent profiles are available for delegation:

| Profile | Purpose | Delegate via |
|---------|---------|-------------|
| `code-reviewer` | Five-axis code review | `call_subordinate` with `profile: code-reviewer` |
| `test-engineer` | Test strategy and writing | `call_subordinate` with `profile: test-engineer` |
| `security-auditor` | Vulnerability detection | `call_subordinate` with `profile: security-auditor` |

Example: *"Review this change"* → agent delegates to `code-reviewer` persona.

## Using References

The `references/` directory contains detailed checklists loaded on demand:

| Reference | Used with |
|-----------|----------|
| `testing-patterns.md` | `test-driven-development` |
| `performance-checklist.md` | `performance-optimization` |
| `security-checklist.md` | `security-and-hardening` |
| `accessibility-checklist.md` | `frontend-ui-engineering` |

## Spec and Task Artifacts

The `/spec` and `/plan` commands create working artifacts (`SPEC.md`, `tasks/plan.md`, `tasks/todo.md`). In Agent Zero projects these are stored under `.a0proj/` (gitignored) to keep the repo root clean.

## Skill Anatomy

Every skill follows the same structure:

```
YAML frontmatter (name, description)
├── Overview — What this skill does and why
├── When to Use — Triggers and exclusions
├── Core Process — Step-by-step workflow
├── Common Rationalizations — Excuses and rebuttals
├── Red Flags — Signs the skill is being violated
└── Verification — Exit criteria checklist
```

See [skill-anatomy.md](skill-anatomy.md) for the full specification.

## Architecture Note

The original `addyosmani/agent-skills` used a `SessionStart` hook that injected the full `using-agent-skills` SKILL.md (~195 lines) once per session. The A0 adaptation uses a compact routing table (~40 lines) injected into `extras_persistent` every turn via `message_loop_prompts_after`. This is more token-efficient and ensures the routing context is always fresh regardless of context window pressure.
