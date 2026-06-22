# revolve/projects/a0-agent-skills/revisions/rev-006/checkpoints/cp-000-rev006-baseline/AGENTS.md — Baseline Checkpoint

## Checkpoint ID

`cp-000-rev006-baseline`

## Parent

`cp-d001-d4-d5-e2e-evalrunner` (rev-005 externally promoted incumbent)

## Branch

None — baseline for rev-006.

## Storage

Lean checkpoint: hash manifest at `manifest.sha256` (155 files) pointing to live plugin at `/a0/usr/plugins/a0_agent_skills/`.

No full plugin copy created. Restore by pointer to rev-005 checkpoint or verify live plugin against manifest.

## Restore Method

1. Verify live plugin against `manifest.sha256`
2. If mismatch: restore from `rev-005/promotion/external-promotion-003-cp-d001/pre-promotion-live-backup-a0_agent_skills`
3. Or diff against rev-005 `cp-d001-d4-d5-e2e-evalrunner/subject/a0_agent_skills/`

## Identity Verification

Manifest contains 155 file hashes. Verified against live plugin: all OK.

## Baseline Architecture/Runtime Evidence (run-001)

### Reclassified Finding: Test Infrastructure Gap (not a plugin bug)

Initially classified as critical: `agent_skills_enabled` not set in the `a0_agent_skills` development project.

**Reclassified**: The `a0_agent_skills` project is the development project, not a consumer of the plugin workflow. Not having `agent_skills_enabled` there is correct behavior.

**Resolution**: Created dedicated test project `a0-skills-test` with `agent_skills_enabled: true`. Verified via `helpers.projects.load_project_header("a0-skills-test")` — field correctly reads `True`.

This means all previous e2e tests that ran against the `a0_agent_skills` development project may not have had the auto-load extension active. Future tests must switch context to `a0-skills-test` or any project with `agent_skills_enabled: true`.

### Plugin Discovery (verified)

- Plugin roots: `/a0/usr/plugins/`, `/a0/plugins/`
- `a0_agent_skills` is discovered correctly
- 30 total plugins discovered (28 core + 2 user)

### Skills Catalog (verified)

- 46 total skills in catalog across all roots
- 24 skills from `a0_agent_skills` plugin confirmed in catalog
- Skill roots include: `/a0/skills`, `/a0/usr/skills`, project-scoped `.a0proj/skills`, plugin skill dirs
- `using-agent-skills` is discoverable via `search_skills()`

### Agent Profiles (verified)

- Core: agent0, default, developer, researcher, hacker
- Plugin: code-reviewer, security-auditor, test-engineer
- All plugin profiles have `agent.yaml` + `prompts/agent.system.main.specifics.md`

### Extension Hooks (verified)

- 10 extension files across 5 hook points

### Commands (verified)

- 8 commands confirmed: build, code-simplify, plan, review, ship, spec, test, use-agent-skills

### API Endpoints

- Plugin has 0 API files — no custom API endpoints

### Project Integration

- `include_agents_md: true` in project header
- Root `AGENTS.md` exists (41,858 bytes)
- 217 child `AGENTS.md` files exist but are NOT recursively injected by the framework

### Source Parity

| Source | Plugin | Status |
|---|---|---|
| 24 skills | 24 skills | full match |
| 4 personas | 3 profiles | web-performance-auditor missing |
| 8 commands (claude) | 8 commands | webperf missing, use-agent-skills added |

### Correct A0 Runtime APIs Discovered

| Purpose | Correct function |
|---|---|
| Plugin list | `helpers.plugins.get_plugins_list()` |
| Plugin roots | `helpers.plugins.get_plugin_roots()` |
| Skills catalog | `helpers.skills.list_skill_catalog()` |
| Skill search | `helpers.skills.search_skills(query)` |
| Skill roots | `helpers.skills.get_skill_roots()` |
| Project header | `helpers.projects.load_project_header(name)` |
| Plugin config | `helpers.plugins.get_plugin_config(name)` |

## Changes

None — baseline checkpoint.

## Status

`pending evaluation` — baseline evidence partially collected; architecture brief expansion needed.

## Rollback Note

Restore from `rev-005/promotion/external-promotion-003-cp-d001/pre-promotion-live-backup-a0_agent_skills`.
