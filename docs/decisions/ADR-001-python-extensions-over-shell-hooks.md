# ADR-001: Python Extensions and YAML Commands Over Shell Hooks

## Status

Accepted

## Date

2026-06-05

## Context

The source project (`addyosmani/agent-skills`) was originally designed for Claude Code and Gemini CLI. It used:

- **Shell hooks** (`.sh` scripts) for tool interceptors like `sdd-cache` and `simplify-ignore`
- **Markdown agent profiles** (`.md` files) for subordinate personas
- **Platform-specific command files** — `.claude/commands/*.md` for Claude Code, `.gemini/commands/*.toml` for Gemini CLI
- **No plugin manifest** — discovery relied on platform conventions

When converting to an Agent Zero plugin (`vanja-emichi/a0_agent_skills`), we needed formats that integrate with Agent Zero's discovery mechanisms:

- `skills_tool` auto-discovery via `skills/*/SKILL.md`
- Agent profile discovery via `agents/<profile>/agent.yaml`
- Extension discovery via `extensions/python/<extension_point>/_NN_name.py`
- Command discovery via `commands/*.command.yaml`
- Plugin lifecycle via `hooks.py` (`install()`/`uninstall()`)

Agent Zero's plugin system is Python-native. The framework discovers extensions by importing Python classes, resolves agent profiles from YAML, and discovers commands from YAML metadata files.

## Decision

Convert all source artifacts to Agent Zero's native formats:

| Source Format | Plugin Format | Integration Point |
|---|---|---|
| Shell hooks (`.sh`) | Python extensions (`extensions/python/`) | `agent_init`, `call_tool` extension points |
| Markdown agents (`.md`) | YAML profiles (`agent.yaml` + `prompts/*.md`) | `get_agents_dict()` discovery |
| Claude `.md` commands | YAML text commands (`*.command.yaml` + `*.txt`) | Commands plugin discovery |
| Gemini `.toml` commands | Same YAML commands (unified) | Commands plugin discovery |
| No manifest | `plugin.yaml` | Plugin discovery |
| No lifecycle | `hooks.py` | `call_plugin_hook()` |

This gives us 7 verified integration points traced to framework code (`/a0/helpers/skills.py`, `/a0/helpers/subagents.py`, `/a0/helpers/extension.py`, `/a0/usr/plugins/commands/helpers/commands.py`).

## Alternatives Considered

### Keep Shell Hooks

- **Pros:** Proven in Claude Code, no conversion effort
- **Cons:** Agent Zero has no shell hook mechanism; hooks are Python extension classes. Shell scripts would be invisible to the framework
- **Rejected:** Fundamentally incompatible with Agent Zero's plugin architecture

### JavaScript Extensions

- **Pros:** Familiar to frontend developers, async-native
- **Cons:** Agent Zero extension points require Python classes inheriting `helpers.extension.Extension`. No JavaScript runtime in the extension pipeline
- **Rejected:** Framework only supports Python extensions

### JSON Configuration Files

- **Pros:** Universal, easy to generate and validate
- **Cons:** Agent profiles use `agent.yaml`, commands use `.command.yaml`. The framework parses these specific formats. JSON would require custom parsers
- **Rejected:** Framework expects YAML for these integration points

### TOML Configuration

- **Pros:** Used by Gemini CLI, simpler than YAML for flat configs
- **Cons:** Agent Zero does not parse TOML for any plugin integration point. Would need a custom loader
- **Rejected:** Not a supported format in the framework

## Consequences

### Positive

- **Full framework integration** — all 7 integration points work through native discovery mechanisms
- **Single source of truth** — one command format (YAML) replaces two platform-specific formats
- **Extension access to agent context** — Python extensions receive `self.agent` with full access to properties, memory, and tools
- **Testable** — extensions can be unit-tested as Python classes, shell hooks could only be integration-tested
- **Maintainable** — YAML is human-readable and editable, Python is debuggable with standard tooling

### Negative

- **Conversion effort** — every shell hook, markdown agent, and platform command needs manual conversion
- **Source-plugin divergence** — source project retains original formats for its target platforms; plugin uses Agent Zero formats. Changes must be applied separately
- **Python dependency** — extensions require understanding of Agent Zero's `Extension` base class and async patterns
- **Skill authors must know two formats** — if contributing to both source and plugin

### Risks Mitigated

- **Framework API stability** — integration points are traced to specific code locations, making breaking changes detectable
- **Profile merging** — framework merges default → plugin → user agents with clear precedence (`_merge_agent_dicts`)
