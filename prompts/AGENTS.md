# prompts/

## Core Contract

- This AGENTS.md is the binding work contract for the `prompts/` subtree
- All prompt templates must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `prompts/AGENTS.md` before modifying any template
3. Read the target template file before editing
4. Re-read every session — do not rely on memory

## Update After Editing

- Update this doc when: adding/removing templates, changing template purpose or consumers
- Update parent root AGENTS.md when: entry points table or routing contracts change
- Update consuming extension/command code when: template variable placeholders change

## Purpose

Markdown prompt templates injected into agent sessions by extensions and commands. Templates use `{variable}` placeholders resolved at injection time.

**Owns:** Prompt template content and placeholder contracts.

**Does NOT own:** Extension logic that reads/injects templates, command logic that consumes templates.

## Templates

| File | Consumer | Purpose |
|------|----------|---------|
| `agent.skills.routing.md` | `extensions/python/system_prompt/_15_agent_skills_routing.py` | Injected into every session's system prompt. Defines mandatory routing rules, 6-phase lifecycle with 4 approval gates (G1–G4), skill-driven execution model, persona invocation rules, and anti-rationalization table. |
| `ship_review.md` | `commands/ship.py` | Pre-launch review prompt for `/ship` command. Orchestrates parallel 3-agent fan-out (code-reviewer, security-auditor, test-engineer) with GO/NO-GO decision template. |

## Contracts

- Templates use `{variable}` placeholders — must match consumer's format call arguments
- `agent.skills.routing.md` is loaded with mtime-based caching by the system_prompt extension
- `ship_review.md` uses `{scope_line}`, `{project_scope}`, `{specialist_context_safe}`, `{scope_desc_review}`, `{scope_desc_audit}`, `{scope_desc_coverage}` placeholders
- Templates are pure text — no executable code, no imports

## Style

- Concise, operational — no diary entries
- Templates are version-controlled contract documents
- Changes to templates affect all agent sessions — edit with care

## Closeout Protocol

1. Verify template renders correctly with expected placeholders
2. Test consumer extension/command with modified template
3. Update this doc if template purposes or consumers change
4. Update parent AGENTS.md entry points if new templates are added

## Anti-patterns

- Do NOT add Python/Jinja logic to templates — use simple `{variable}` placeholders only
- Do NOT modify templates without checking all consumers
- Do NOT hardcode paths or secrets in templates
- Do NOT remove placeholder variables without updating consumers first

## Related Context

- **Parent:** `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
- **Consuming extensions:** `extensions/AGENTS.md`
- **Consuming commands:** `commands/AGENTS.md`
