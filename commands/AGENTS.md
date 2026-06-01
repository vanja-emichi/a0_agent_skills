# commands/

## Core Contract

- This AGENTS.md is the binding work contract for the `commands/` subtree
- All slash command definitions, templates, and scripts must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `commands/AGENTS.md` before modifying any command
3. Identify the specific command file you will touch
4. Read the command's YAML config and template/script before editing
5. Do not rely on memory — re-read in the current session

## Update After Editing

Every meaningful change to a command requires an AGENTS.md pass:

- Update this doc when: adding/removing commands, changing command types, altering artifact path resolution
- Update command YAML when: changing name, description, argument_hint
- Update parent root AGENTS.md when: command table or phase mapping changes
- Update `agents/AGENTS.md` when: command-profile wiring changes
- Small edits that don't change behavior or contracts may leave docs unchanged, but the pass must still happen

## Purpose

Seven slash commands that serve as user-facing entry points to the 6-phase engineering lifecycle. Each command loads the appropriate skills or delegates to specialist agent profiles, providing a structured workflow from spec through ship.

**Owns:** Command definitions (YAML config + content files), artifact path resolution in templates, `/ship` parallel orchestration script.

**Does NOT own:** Skill logic, agent profiles, enforcement, state persistence.

## Entry Points

```
commands/
├── spec.command.yaml + spec.txt           # /spec — DEFINE phase
├── plan.command.yaml + plan.txt           # /plan — PLAN phase
├── build.command.yaml + build.txt         # /build — BUILD phase
├── test.command.yaml + test.txt           # /test — VERIFY phase
├── review.command.yaml + review.txt       # /review — REVIEW phase
├── code-simplify.command.yaml + code-simplify.txt  # /code-simplify
└── ship.command.yaml + ship.py            # /ship — SHIP phase (script)
```

**Prerequisite:** The `commands` plugin must be installed and active at `/a0/usr/plugins/commands/`.

## The 7 Commands

| Command | Phase | Type | Loads / Delegates | Output |
|---------|-------|------|-------------------|--------|
| `/spec` | DEFINE | text | `spec-driven-development` + `markdown-documents` | Feature spec at `docs/specs/<slug>-spec.md` |
| `/plan` | PLAN | text | `planning-and-task-breakdown` + `markdown-documents` | Implementation plan + task list |
| `/build` | BUILD | text | `incremental-implementation` + `test-driven-development` | Incremental code implementation |
| `/test` | VERIFY | text | `test-driven-development` | TDD cycle or bug reproduction |
| `/review` | REVIEW | text | `code-reviewer` profile via `call_subordinate` | Structured review report |
| `/code-simplify` | — | text | `code-simplification` | Simplified code preserving behavior |
| `/ship` | SHIP | script | `code-reviewer` + `security-auditor` + `test-engineer` via `call_subordinate_parallel` | GO/NO-GO decision with rollback plan |

## Contracts & Invariants

### Command Types

**Text commands** (`type: text`):
- `.command.yaml` defines config (name, description, argument_hint, type, template_path)
- `.txt` file contains the prompt template injected into the agent
- `{raw}` placeholder receives trailing user input after the command name

**Script commands** (`type: script`):
- `.command.yaml` defines config (name, description, argument_hint, type, script_path)
- `.py` file contains a `run(payload)` function returning the prompt text
- Has full Python access for complex logic (e.g., `/ship` discovers spec files)

### Command YAML Format

```yaml
name: command-name          # Must match /command-name
description: One-line description of what the command does
argument_hint: Optional description of accepted arguments
type: text | script         # text = .txt template, script = .py with run()
template_path: name.txt     # Required for type: text
script_path: name.py        # Required for type: script
```

### Text Template Patterns

All text templates follow a common structure:
1. **Skill loading instruction** — `skills_tool:load skill_name=<name>`
2. **Process directive** — "Follow the skill's complete process"
3. **`{raw}` placeholder** — User's trailing input (placed after context)
4. **Artifact path resolution** — Python snippet using `workflow_state` helpers

Example pattern from `build.txt`:
```
You MUST invoke the incremental-implementation skill AND the test-driven-development skill. Load them both:

skills_tool:load skill_name=incremental-implementation
skills_tool:load skill_name=test-driven-development

Follow both skills' process to implement the next pending task.

{raw}

Resolve the artifact paths to locate the todo list and active spec:

from helpers.workflow_state import resolve_artifact_paths, discover_feature_slug
slug = discover_feature_slug(agent)
paths = resolve_artifact_paths(agent, slug=slug)
```

### Artifact Path Resolution

Commands use `helpers/workflow_state.py` for canonical artifact paths:
- `resolve_artifact_paths(agent, slug=slug)` → dict with `spec`, `todo`, `plan` keys
- `discover_feature_slug(agent)` → finds the active feature slug from state
- Falls back gracefully when no slug/project is set

### `/ship` Script Command

`ship.py` is the only script command. It:
1. Discovers the project path and spec file (`_find_spec`)
2. Sanitizes user input for safe embedding
3. Reads the review prompt template from `prompts/ship_review.md`
4. Returns a prompt that triggers `call_subordinate_parallel` with 3 specialist profiles
5. Produces a merged GO/NO-GO decision

## Style

- Keep command templates concise and focused on their lifecycle phase
- Document stable contracts, not diary entries
- Prefer direct bullets with explicit names
- Delete stale instructions immediately

## Closeout Protocol

After modifying any command:

1. Re-check the command still loads the correct skills/profiles
2. Update this doc's command table if commands were added/removed
3. Update parent root AGENTS.md command table if phase mapping changed
4. Update `agents/AGENTS.md` if command-profile wiring changed
5. Test the command via the `/` prefix in Agent Zero
6. Report docs intentionally left unchanged and why

## Patterns

### To add a new slash command:
1. Create `commands/<name>.command.yaml` with required fields
2. For text commands: create `commands/<name>.txt` with skill loading + `{raw}` + artifact resolution
3. For script commands: create `commands/<name>.py` with `run(payload) -> str`
4. Use `{raw}` in text templates for trailing user input
5. Add skill loading: `skills_tool:load skill_name=<name>`
6. Add artifact path resolution if the command needs spec/todo/plan paths
7. Test the command via the `/` prefix in Agent Zero
8. Run closeout protocol

### To modify an existing command:
1. Edit the `.txt` template or `.py` script
2. Changes take effect immediately (no reload needed)
3. Verify the command still loads the correct skills
4. Test with representative inputs
5. Run closeout protocol

## Anti-patterns

- **Do NOT** hardcode artifact paths in templates — use `resolve_artifact_paths` and `discover_feature_slug`
- **Do NOT** skip the skill loading instruction — commands must explicitly load required skills
- **Do NOT** put `{raw}` before skill loading instructions — user input goes after context
- **Do NOT** create script commands for simple text-only workflows — prefer text commands
- **Do NOT** import from `helpers/` in `.txt` templates — use inline Python snippets in code blocks
- **Do NOT** modify `ship.py` without testing sanitization and spec discovery
- **Do NOT** skip the Read Before Editing protocol — re-read this doc and the target command before changes
- **Do NOT** skip the AGENTS.md pass after editing

## Related Context

- Parent: `AGENTS.md` (plugin root)
- Agents: `agents/AGENTS.md` (profiles invoked by /review and /ship)
- Skills: `skills/AGENTS.md` (skills loaded by each command)
- Helpers: `helpers/AGENTS.md` (workflow_state for artifact path resolution)
- Prerequisite: `/a0/usr/plugins/commands/` (commands plugin infrastructure)
