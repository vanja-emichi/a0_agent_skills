# ADR-003: Source-Project as Historical Reference, Plugin as Canonical

## Status

Accepted

## Date

2026-06-05

## Context

The `agent-skills` repository exists in two forms:

1. **Source project** (`addyosmani/agent-skills` at `/a0/usr/projects/a0_agent_skills/`): Original repo designed for Claude Code, Gemini CLI, Cursor, Windsurf, and Copilot. Uses shell hooks, markdown agents, `.claude/commands/*.md`, and `.gemini/commands/*.toml`.

2. **Installed plugin** (`vanja-emichi/a0_agent_skills` at `/a0/usr/plugins/a0_agent_skills/`): Agent Zero runtime plugin using Python extensions, YAML agent profiles, YAML commands, and `plugin.yaml` manifest.

Over time, the two codebases diverged significantly:

- The source project has 258 conversion issues across 36 files (documented in `a0-conversion-audit.md`)
- The plugin converted all artifacts to Agent Zero native formats
- Shared skills exist in both but are maintained independently
- Shell hooks in source (`sdd-cache`, `simplify-ignore`) became Python extensions in the plugin
- Markdown agent profiles became YAML profiles with separate prompt files
- Platform-specific commands merged into unified YAML commands

Attempts to keep both in sync created friction — every change needed dual application in different formats with different conventions.

## Decision

Establish a clear ownership boundary:

- **Source project** remains in its original format as a **historical reference**. It continues to serve Claude Code, Gemini CLI, and other platform users. It is not modified to match the plugin.
- **Installed plugin** is the **active development surface** for Agent Zero. This is what we actively develop, test, and ship.
- **Sync direction** is plugin → source for test files only. Skills, extensions, commands, and agents are maintained independently in each.

This is documented in the root `AGENTS.md` under "Source vs Plugin relationship":

> Source project: Historical reference in original format (shell hooks, markdown agents, Claude/Gemini commands). Not modified to match the plugin.
> Installed plugin: Runtime-ready Agent Zero version with Python extensions, YAML commands, agent profiles. This is what we actively develop.

## Alternatives Considered

### Keep Both in Full Sync

- **Pros:** Single source of truth for skill content, no drift risk
- **Cons:** Every change requires dual application in different formats (shell vs Python, markdown vs YAML, `.md` commands vs `.command.yaml`). The 258 conversion issues show this is unsustainable. The formats are fundamentally different
- **Rejected:** Format impedance makes full sync impractical

### Replace Source with Plugin

- **Pros:** Single repo, no sync needed
- **Cons:** Source project serves other platforms (Claude Code, Gemini CLI, Cursor, Windsurf, Copilot). Replacing it with Agent Zero format would break all non-A0 users. The source project has its own community and purpose
- **Rejected:** Would break the source project's multi-platform mission

### Stop Maintaining Plugin

- **Pros:** No divergence, no dual maintenance
- **Cons:** Agent Zero users lose all plugin functionality — skills, agents, commands, extensions, DOX integration. The plugin is the only way to deliver these features to A0 users
- **Rejected:** Plugin users are the primary development audience

## Consequences

### Positive

- **Clear ownership** — developers know where to make changes (plugin for A0, source for other platforms)
- **No false sync expectations** — explicit boundary prevents wasted effort on impossible synchronization
- **Format freedom** — plugin can use optimal A0 formats without worrying about source compatibility
- **Independent iteration** — plugin and source can evolve at different speeds
- **Historical context preserved** — source remains available as reference for understanding original design intent

### Negative

- **Skill content drift** — shared skills (e.g., `test-driven-development`) may diverge between source and plugin over time
- **Dual authoring for cross-platform skills** — contributors who want changes in both must write them twice in different formats
- **Test file sync is one-directional** — plugin → source only, which may miss source-only test scenarios
- **Discovery confusion** — new contributors may not understand which repo to modify

### Risks Mitigated

- **Documented boundary** — root `AGENTS.md` explicitly states the relationship and sync direction
- **DOX enforcement** — both repos have `AGENTS.md` contracts that define their respective conventions
- **Test parity** — plugin tests validate the installed plugin; source tests validate source-only features
