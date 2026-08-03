# AGENTS.md — a0_agent_skills

## Purpose

Agent Zero plugin that ports the [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) development-workflow toolkit into the Agent Zero plugin system. Gives any Agent Zero agent a production-grade software-engineering lifecycle: **spec → plan → build → verify → review → ship**.

Ships:
- **21 skills** (`skills/`), each a `SKILL.md`, organized across the 6-phase lifecycle.
- **3 specialist agent profiles** (`agents/`): `code-reviewer`, `security-auditor`, `test-engineer` — invoked via `call_subordinate`.
- **7 slash commands** (`commands/`): `/spec`, `/plan`, `/build`, `/test`, `/review`, `/code-simplify`, `/ship` — require the `commands` plugin.
- **Declarative routing** injected into every session via a `system_prompt` extension (works regardless of whether a project is active).
- **Telemetry** — opt-in JSONL logging of every `skills_tool` activation for workflow validation.

## Knowledge

- **Owning KB:** none dedicated — catalog entry in `~/knowledge/agent_zero_plugins` (② Tool). Promote to a dedicated KB if this plugin grows substantial durable knowledge (Hub placement rule #7).
- **Access:** OpenKnowledge MCP only — `cwd: ~/knowledge/agent_zero_plugins`. Tools: `exec`, `search`, `write`, `edit`, `audit`, `lint`. Never `lsp` on KB markdown.
- **Fleet index:** `vanja-emichi/vbunjevac` → `registry/repos.md`.

## Ownership

- **Repo:** `vanja-emichi/a0_agent_skills` (Vanja's fleet, account `vanja-emichi` / git identity `vbunjevac`).
- **Provenance:** Ported from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) by Addy Osmani, adapted to the Agent Zero plugin system.
- **Current version:** `0.4.0` (see `plugin.yaml`, `CHANGELOG.md`).

## Local Contracts

- `plugin.yaml` — plugin manifest (name, title, description, version, `settings_sections: [agent]`, `per_project_config: true`).
- `skills/<name>/SKILL.md` — one self-contained skill per directory; the 21 skills are the core deliverable. `using-agent-skills` is a meta-skill loaded on demand (never pinned).
- `commands/<name>.command.yaml` + `<name>.txt|py` — slash-command definitions; `/ship` is implemented in Python (`ship.py`), the rest are text prompts. **Depends on the `commands` plugin** for dispatch.
- `agents/<profile>/` — specialist subordinate profiles; invoked only by the orchestrator (profiles never call each other).
- `extensions/python/system_prompt/_15_agent_skills_routing.py` — **the routing entry point.** Reads `prompts/agent.skills.routing.md` at runtime and appends routing rules to the system prompt during assembly (universal, project-active or not).
- `extensions/python/tool_execute_after/_05_skill_telemetry.py` — appends one JSON line per `skills_tool` activation when telemetry is enabled; failures never interrupt the agent.
- `hooks.py` — intentionally empty lifecycle stubs (`install`/`uninstall`/`pre_update`). Routing is handled by the extension above, NOT here.
- `default_config.yaml` — telemetry defaults (`telemetry_enabled`, `telemetry_log_path`, `telemetry_max_lines`).
- `tests/` — pytest suite covering telemetry defaults/hooks, enforcement language, and skill telemetry.

## Work Guidance

- **Skill content is markdown.** Edit `SKILL.md` files directly; keep each skill self-contained and on-demand-loadable.
- **Respect the 20-skill context budget.** When pinning skills for a project, prioritize the 7 lifecycle skills. `using-agent-skills` is meta — load on demand, never pin.
- **Routing changes go in `prompts/agent.skills.routing.md`**, consumed by the `system_prompt` extension — do not reintroduce workdir promptinclude writing (it is invisible when a project is active; that was the original flaw documented in `hooks.py`).
- **Project-scope overrides:** copy a skill's `SKILL.md` into a project's `.a0proj/skills/<name>/` to override without touching the plugin; project scope wins.
- **Per-profile model override:** Agent Zero has no `model` field in `agent.yaml`; use a `_model_config/config.json` alongside the profile (see README).

## Verification

- **Test suite:** `pytest` from the repo root (`tests/conftest.py`, `tests/test_telemetry_default_and_hooks.py`, `tests/test_enforcement_language.py`, `tests/test_skill_telemetry.py`).
- **Smoke check:** install into `/a0/usr/plugins/a0_agent_skills`, ensure the `commands` plugin is active, restart Agent Zero, then exercise the lifecycle: `/spec` → `/plan` → `/build` → `/test` → `/review` → `/ship`.
- **Telemetry check:** with `telemetry_enabled: true`, confirm `.a0proj/skill_activations.jsonl` receives one JSON line per `skills_tool` call.

## Child DOX Index

None — no nested `AGENTS.md` files exist in `skills/`, `commands/`, `agents/`, `extensions/`, or `tests/`. Add per-directory DOX only if a subsystem grows substantial durable knowledge.
