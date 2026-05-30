# Managed Fork Surface Mapping

> Maps upstream `addyosmani/agent-skills` assets to their Agent Zero-native
> equivalents in the `a0_agent_skills` plugin.

## Legend

| Status | Meaning |
|---|---|
| **ported** | Content carried over with A0-specific adaptations |
| **replaced** | Upstream concept replaced by a different A0-native surface |
| **omitted** | Intentionally not included; not applicable to Agent Zero |

---

## Skills (23 shared)

All 23 upstream skills are **ported** as `skills/<name>/SKILL.md`.

| Upstream path | Plugin path | Status | Notes |
|---|---|---|---|
| `skills/api-and-interface-design/SKILL.md` | `skills/api-and-interface-design/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/browser-testing-with-devtools/SKILL.md` | `skills/browser-testing-with-devtools/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/ci-cd-and-automation/SKILL.md` | `skills/ci-cd-and-automation/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/code-review-and-quality/SKILL.md` | `skills/code-review-and-quality/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/code-simplification/SKILL.md` | `skills/code-simplification/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/context-engineering/SKILL.md` | `skills/context-engineering/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/debugging-and-error-recovery/SKILL.md` | `skills/debugging-and-error-recovery/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/deprecation-and-migration/SKILL.md` | `skills/deprecation-and-migration/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/documentation-and-adrs/SKILL.md` | `skills/documentation-and-adrs/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/doubt-driven-development/SKILL.md` | `skills/doubt-driven-development/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/frontend-ui-engineering/SKILL.md` | `skills/frontend-ui-engineering/SKILL.md` | ported | A0 metadata + sibling checklist wiring |
| `skills/git-workflow-and-versioning/SKILL.md` | `skills/git-workflow-and-versioning/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/idea-refine/SKILL.md` | `skills/idea-refine/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/incremental-implementation/SKILL.md` | `skills/incremental-implementation/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/interview-me/SKILL.md` | `skills/interview-me/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/performance-optimization/SKILL.md` | `skills/performance-optimization/SKILL.md` | ported | A0 metadata + sibling checklist wiring |
| `skills/planning-and-task-breakdown/SKILL.md` | `skills/planning-and-task-breakdown/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/security-and-hardening/SKILL.md` | `skills/security-and-hardening/SKILL.md` | ported | A0 metadata + sibling checklist wiring |
| `skills/shipping-and-launch/SKILL.md` | `skills/shipping-and-launch/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/source-driven-development/SKILL.md` | `skills/source-driven-development/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/spec-driven-development/SKILL.md` | `skills/spec-driven-development/SKILL.md` | ported | A0 metadata + A0 tool phrasing added |
| `skills/test-driven-development/SKILL.md` | `skills/test-driven-development/SKILL.md` | ported | A0 metadata + sibling checklist wiring |
| `skills/using-agent-skills/SKILL.md` | `skills/using-agent-skills/SKILL.md` | ported | Major A0-specific orchestration rewrite |

### Typical porting changes per skill

- Added frontmatter metadata: `version`, `author`, `tags`, `trigger_patterns`
- Replaced upstream tool references with Agent Zero tool names
- Repointed reference docs from central `references/` to sibling files
- Minor prose adjustments for A0 context

---

## Commands (7)

Upstream editor command packs are **replaced** by Agent Zero command surfaces.

| Upstream concept | Plugin surface | Status | Notes |
|---|---|---|---|
| `.claude/commands/build.md` | `commands/build.command.yaml` + `commands/build.txt` | replaced | A0 command YAML + prompt template |
| `.claude/commands/code-simplify.md` | `commands/code-simplify.command.yaml` + `commands/code-simplify.txt` | replaced | A0 command YAML + prompt template |
| `.claude/commands/plan.md` | `commands/plan.command.yaml` + `commands/plan.txt` | replaced | A0 command YAML + prompt template |
| `.claude/commands/review.md` | `commands/review.command.yaml` + `commands/review.txt` | replaced | A0 command YAML + prompt template |
| `.claude/commands/ship.md` | `commands/ship.command.yaml` + `commands/ship.py` | replaced | A0 command YAML + Python script (parallel fan-out) |
| `.claude/commands/spec.md` | `commands/spec.command.yaml` + `commands/spec.txt` | replaced | A0 command YAML + prompt template |
| `.claude/commands/test.md` | `commands/test.command.yaml` + `commands/test.txt` | replaced | A0 command YAML + prompt template |

### Gemini equivalents

All `.gemini/commands/*.toml` files are **omitted** — the A0 command YAML surfaces replace both the Claude and Gemini command packs.

---

## Agents / Personas (3)

Upstream markdown persona docs are **replaced** by executable Agent Zero agent profiles.

| Upstream | Plugin | Status | Notes |
|---|---|---|---|
| `agents/code-reviewer.md` | `agents/code-reviewer/agent.yaml` + `agents/code-reviewer/prompts/agent.system.main.specifics.md` | replaced | Runnable A0 agent profile |
| `agents/security-auditor.md` | `agents/security-auditor/agent.yaml` + `agents/security-auditor/prompts/agent.system.main.specifics.md` | replaced | Runnable A0 agent profile |
| `agents/test-engineer.md` | `agents/test-engineer/agent.yaml` + `agents/test-engineer/prompts/agent.system.main.specifics.md` | replaced | Runnable A0 agent profile |
| `agents/README.md` | — | omitted | Upstream index doc; not needed as A0 runtime surface |

---

## References (5)

Upstream central references are **relocated** next to the relevant skills.

| Upstream | Plugin | Status | Notes |
|---|---|---|---|
| `references/accessibility-checklist.md` | `skills/frontend-ui-engineering/accessibility-checklist.md` | ported | Moved next to relevant skill |
| `references/performance-checklist.md` | `skills/performance-optimization/performance-checklist.md` | ported | Moved next to relevant skill |
| `references/security-checklist.md` | `skills/security-and-hardening/security-checklist.md` | ported | Moved next to relevant skill |
| `references/testing-patterns.md` | `skills/test-driven-development/testing-patterns.md` | ported | Moved next to relevant skill |
| `references/orchestration-patterns.md` | `skills/using-agent-skills/orchestration-patterns.md` | ported | Moved next to relevant skill |

---

## Hooks (upstream: 9 files)

Upstream shell-based hooks are **omitted** pending selective porting in Phase 4.

| Upstream | Plugin | Status | Notes |
|---|---|---|---|
| `hooks/hooks.json` | — | omitted | Not applicable; A0 uses plugin.yaml + Python extensions |
| `hooks/session-start.sh` | — | **replaced** | A0 system_prompt extension handles session routing |
| `hooks/session-start-test.sh` | — | omitted | Node.js test; A0 uses pytest |
| `hooks/sdd-cache-pre.sh` | — | deferred | A0 uses document_query, not WebFetch; perf optimization |
| `hooks/sdd-cache-post.sh` | — | deferred | Same as sdd-cache-pre.sh |
| `hooks/SDD-CACHE.md` | — | deferred | Port when caching is implemented |
| `hooks/simplify-ignore.sh` | — | deferred | Future tool_execute_before/after extension |
| `hooks/simplify-ignore-test.sh` | — | deferred | Port with simplify-ignore |
| `hooks/SIMPLIFY-IGNORE.md` | — | deferred | Port with simplify-ignore |
| — | `hooks.py` | **A0-native** | Stub; see docs/hook-alignment.md for policy |

---

## Plugin runtime surfaces (A0-native additions)

These have no upstream equivalent — they are **new** Agent Zero-native surfaces.

| Plugin surface | Purpose |
|---|---|
| `plugin.yaml` | Plugin manifest (title, description, version) |
| `default_config.yaml` | Default settings (telemetry enabled, log path) |
| `README.md` | Plugin documentation (managed-fork positioning) |
| `extensions/python/system_prompt/_15_agent_skills_routing.py` | Injects routing rules into agent system prompt |
| `extensions/python/tool_execute_after/_05_skill_telemetry.py` | Logs skill activations to JSONL |
| `tools/call_subordinate_parallel.py` | Parallel subordinate orchestration tool |
| `prompts/agent.skills.routing.md` | Routing prompt template |
| `tests/` (6 test files) | Contract, sanitization, parity, telemetry, enforcement tests |
| `scripts/parity_report.py` | Parity report generator vs upstream snapshot |

---

## Upstream-only assets (intentionally omitted)

### Editor integrations

| Asset | Reason for omission |
|---|---|
| `.claude/` (7 command files) | Replaced by `commands/*.command.yaml` |
| `.gemini/` (7 command files) | Replaced by `commands/*.command.yaml` |
| `.claude-plugin/plugin.json` | A0 uses `plugin.yaml` instead |
| `.claude-plugin/marketplace.json` | A0 has its own plugin discovery |
| `.opencode/` | Not applicable to Agent Zero |

### Upstream documentation

| Asset | Reason for omission |
|---|---|
| `AGENTS.md` | Replaced by `agents/*/agent.yaml` profiles |
| `CLAUDE.md` | Claude-specific; not applicable to Agent Zero |
| `CONTRIBUTING.md` | Will be replaced with A0-specific contributing guide |
| `docs/getting-started.md` | Replaced by `README.md` |
| `docs/copilot-setup.md` | Editor-specific; not applicable |
| `docs/cursor-setup.md` | Editor-specific; not applicable |
| `docs/gemini-cli-setup.md` | Editor-specific; not applicable |
| `docs/opencode-setup.md` | Editor-specific; not applicable |
| `docs/windsurf-setup.md` | Editor-specific; not applicable |
| `docs/skill-anatomy.md` | May be ported in Phase 3 if useful for contributors |

### Upstream validation / CI

| Asset | Reason for omission |
|---|---|
| `scripts/validate-skills.js` | Replaced by `scripts/parity_report.py` + `tests/test_upstream_parity.py` |
| `.github/workflows/test-plugin-install.yml` | Not yet replaced; may add A0 CI equivalent later |

---

## Summary statistics

| Category | Ported | Replaced | Deferred | Omitted | A0-native |
|---|---:|---:|---:|---:|---:|
| Skills | 23 | 0 | 0 | 0 | 0 |
| Commands | 0 | 7 | 0 | 0 | 0 |
| Agents | 0 | 3 | 0 | 1 | 0 |
| References | 5 | 0 | 0 | 0 | 0 |
| Hooks | 0 | 1 | 6 | 2 | 1 (stub) |
| Editor integrations | 0 | 0 | 0 | 16 | 0 |
| Docs | 0 | 0 | 0 | 10 | 0 |
| Validation/CI | 0 | 0 | 0 | 2 | 2 |
| Runtime surfaces | 0 | 0 | 0 | 0 | 9 |
| **Total** | **28** | **11** | **6** | **31** | **12** |
