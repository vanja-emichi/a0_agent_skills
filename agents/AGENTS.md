# agents/

## Core Contract

- This AGENTS.md is the binding work contract for the `agents/` subtree
- All agent profiles, system prompts, and model configurations must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `agents/AGENTS.md` before modifying any profile
3. Identify the specific profile directory you will touch
4. Read the profile's `agent.yaml` and system prompt before editing
5. Do not rely on memory — re-read in the current session

## Update After Editing

Every meaningful change to a profile requires an AGENTS.md pass:

- Update this doc when: adding/removing profiles, changing orchestration rules, altering invocation patterns
- Update `agent.yaml` when: changing title, description, context
- Update system prompt when: changing output format, review focus, audit scope
- Update parent root AGENTS.md when: profile table or orchestration rules change
- Update `commands/AGENTS.md` when: profiles invoked by commands change
- Small edits that don't change behavior or contracts may leave docs unchanged, but the pass must still happen

## Purpose

Three specialist agent profiles (personas) that provide focused perspectives during the REVIEW and SHIP phases of the 6-phase lifecycle. Each profile is a subordinate agent invoked via `call_subordinate` — never by the user directly.

**Owns:** Agent profile definitions (agent.yaml), specialist system prompts, per-profile model configuration.

**Does NOT own:** Orchestration logic (belongs to commands and main agent), skill definitions, enforcement rules.

## Entry Points

```
agents/
├── code-reviewer/
│   ├── agent.yaml                              # Profile definition
│   └── prompts/
│       └── agent.system.main.specifics.md      # System prompt
├── security-auditor/
│   ├── agent.yaml
│   └── prompts/
│       └── agent.system.main.specifics.md
└── test-engineer/
    ├── agent.yaml
    └── prompts/
        └── agent.system.main.specifics.md
```

## The 3 Profiles

| Profile | Lifecycle Phase | Invoked By | Focus |
|---------|----------------|------------|-------|
| `code-reviewer` | REVIEW + SHIP | `/review`, `/ship` | Five-axis review: correctness, readability, architecture, security, performance |
| `security-auditor` | SHIP | `/ship` | OWASP vulnerability audit, threat modeling, severity-classified findings |
| `test-engineer` | VERIFY + SHIP | `/ship` | Test strategy, coverage analysis, Prove-It Pattern for bug reproduction |

## Contracts & Invariants

### Orchestration Rules (MANDATORY)

1. **The orchestrator invokes personas.** The main agent or a slash command calls `call_subordinate`.
2. **Personas do NOT invoke other personas.** No persona-on-persona calls.
3. **The ONLY multi-persona pattern** is parallel fan-out via `/ship` using `call_subordinate_parallel`.
4. **Do NOT build a "router" persona** that decides which other persona to call.
5. A persona MAY invoke skills but MUST NOT invoke other personas.

### agent.yaml Format

```yaml
title: Profile Title
description: >-
  One-paragraph description of the profile's specialization and when to use it.
  Include the invocation pattern: call_subordinate(profile="profile-name").
context: >-
  Detailed context about what the profile produces and how it should be used.
```

Required fields: `title`, `description`, `context`.

### System Prompt Location

Each profile's system prompt lives at:
```
agents/<profile-name>/prompts/agent.system.main.specifics.md
```

Agent Zero auto-discovers this file as the profile's system prompt override.

### Per-Profile Model Override

Agent Zero does not support a `model` field directly in `agent.yaml`. To assign a specific LLM model to a profile, create a `_model_config` configuration alongside the profile:

```
agents/<profile-name>/plugins/_model_config/config.json
```

This file must contain a complete effective configuration for `chat_model`, `utility_model`, and `embedding_model` (selected as a whole, not merged). See the `_model_config` plugin documentation for the schema.

### Invocation Patterns

**Single-profile delegation (sequential):**
```
call_subordinate(profile="code-reviewer", message="Review changes in src/api/tasks.py")
```

**Parallel fan-out (SHIP only):**
```
call_subordinate_parallel(
  profiles=["code-reviewer", "security-auditor", "test-engineer"],
  messages=[...]
)
```

## Style

- Keep profile system prompts focused on the profile's specific perspective
- Include output format expectations (structured reports, severity labels)
- Document stable contracts, not diary entries
- Prefer direct bullets with explicit names
- Delete stale instructions immediately

## Closeout Protocol

After modifying any profile:

1. Re-check the profile's orchestration rules are still respected
2. Update this doc's profile table if profiles were added/removed
3. Update parent root AGENTS.md profile table if invocation patterns changed
4. Update `commands/AGENTS.md` if command-profile wiring changed
5. Test the profile's output quality with representative inputs
6. Report docs intentionally left unchanged and why

## Patterns

### To add a new agent profile:
1. Create `agents/<profile-name>/agent.yaml` with title, description, context
2. Create `agents/<profile-name>/prompts/agent.system.main.specifics.md` with the specialist system prompt
3. Update routing rules in `prompts/agent.skills.routing.md` to reference the profile
4. Update the persona invocation table in the root AGENTS.md
5. For model override, create `_model_config/config.json` alongside the profile
6. Add invocation tests in `tests/`
7. Run closeout protocol

### To modify a profile's system prompt:
1. Edit `agents/<profile-name>/prompts/agent.system.main.specifics.md`
2. Keep the prompt focused on the profile's specific perspective
3. Include output format expectations (structured reports, severity labels)
4. Test the profile's output quality with representative inputs
5. Run closeout protocol

## Anti-patterns

- **Do NOT** invoke personas from other personas — orchestration belongs to the main agent or commands
- **Do NOT** use `call_subordinate_parallel` for single-profile or same-profile tasks
- **Do NOT** add a `model` field to `agent.yaml` — use `_model_config` plugin instead
- **Do NOT** create generic "router" personas that decide which specialist to call
- **Do NOT** invoke specialist profiles for tasks outside their lifecycle phase
- **Do NOT** modify system prompts without testing output quality
- **Do NOT** skip the Read Before Editing protocol — re-read this doc and the target profile before changes
- **Do NOT** skip the AGENTS.md pass after editing

## Related Context

- Parent: `AGENTS.md` (plugin root)
- Commands: `commands/AGENTS.md` (slash commands that invoke these profiles)
- Skills: `skills/code-review-and-quality/`, `skills/security-and-hardening/`, `skills/test-driven-development/` (referenced skill definitions)
- Orchestration: `skills/using-agent-skills/orchestration-patterns.md`
