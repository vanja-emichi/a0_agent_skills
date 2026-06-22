# revolve/projects/a0-agent-skills/AGENTS.md

## Objective

Improve the native Agent Zero integration quality of the `a0_agent_skills` plugin. The plugin was adapted from the Claude/Codex-oriented `addyosmani/agent-skills` repo. This project systematically audits each skill for integration issues, fixes them under `revolve/`, and promotes validated improvements to the live plugin.

## Subject

Live plugin: `/a0/usr/plugins/a0_agent_skills/`
- 24 skills under `skills/<skill-name>/SKILL.md`
- 3 subordinate agent profiles (code-reviewer, security-auditor, test-engineer)
- 8 slash commands
- 5 reference checklists
- Python extensions for skill activation, file protection, documentation caching
- Per-skill evals under `skills/<skill-name>/evals/evals.json`

## Source Reference

Original repo cloned at: `/a0/usr/projects/a0_agent_skills/references/agent-skills/`

## DOX And Architecture-First Mandate

This project uses the DOX framework (AGENTS.md hierarchy) as the primary context-discovery mechanism. Architecture research is a blocking gate before any new candidate generation, harness edits, content expansion, or live promotion.

Before any analysis or change work, always:
1. Read the applicable project/Revolve `AGENTS.md` chain from root to target path.
2. Understand `/a0` via `/a0/AGENTS.md` and child DOX for `agents/`, `prompts/`, `tools/`, `helpers/`, `api/`, `extensions/`, `plugins/`, `plugins/_skills/`, `plugins/_a0_connector/`, and `skills/`.
3. Understand the live plugin via `/a0/usr/plugins/a0_agent_skills/AGENTS.md` and its child DOX index.
4. Understand the reference repo via `references/agent-skills/AGENTS.md` and its child DOX index.
5. Query external repository context with `deep_wiki` or equivalent for both `agent0ai/agent-zero` and `addyosmani/agent-skills`; record what came from upstream, what came from local DOX, and what was verified locally.
6. Inspect runtime evidence: active project `.a0proj/` metadata, installed plugin inventory, tool schemas, skill catalog behavior, profile inventory, API endpoints, extension hooks, scheduler/chat persistence, and test harness behavior.

The active revision must include a compact architecture brief before subject changes. It must answer:

- why `agent0` remains the main user-facing orchestrator unless a new architecture decision proves otherwise;
- which responsibilities belong to skills, commands, specialist profiles, prompts, plugins, hooks, tools, APIs, and projects;
- how prompt inheritance, prompt injection, `AGENTS.md`, `promptinclude`, loaded skills, and behavior persistence actually work in Agent Zero;
- how Agent Zero projects affect context, metadata, files, skills, agents, settings, and instructions;
- which `addyosmani/agent-skills` concepts are portable and which are platform-specific;
- how spec → plan → todo → build workflows are represented as real Agent Zero project artifacts;
- which checks should be deterministic runtime/API tests and which truly require live LLM e2e.

Do not rely on keyword scanners, content length, or upstream docs alone for architecture claims. If DOX, upstream docs, source code, and live runtime evidence disagree, classify the disagreement as an architecture question and resolve it before implementation.

## Workspace Complexity Finding

A 2026-06-20 audit found that the existing Revolve setup is valid but too copy-heavy: `revolve/` contained 2,198 files before cache cleanup, with `rev-005` alone containing 1,646 files, repeated full plugin checkpoint copies, repeated live-overlay backups, copied test trees, and pytest caches. Non-durable caches were removed, reducing the workspace to 2,167 files and `rev-005` to 1,617 files, but the structure remains harder to navigate than necessary.

Future revisions must apply the Lean Workspace Policy from the root protocol: prefer manifests, hashes, diffs, selective copies, tarballs, or restore recipes before adding another full plugin copy. Full copies are allowed only when they are the cheapest reliable restore method, and repeated live-overlay backups must be compressed or selectively retained when possible.

## Constraints

- **Local research first:** all candidate changes are made on checkpointed copies under `revolve/`. The live plugin stays read-only unless external promotion is explicit.
- **External promotion boundary:** internal promotion is the research default; applying changes to the live plugin is a separate decision requiring user intent.
- **No overfitting:** improvements must generalize, not hack specific eval cases.
- **DOX-first:** all analysis and candidate work must be grounded in the applicable AGENTS.md chains.

## Active Revision

`rev-006` — Agent Zero architecture and runtime integration proof.

## Revision Index

| Revision | Reason | Status | Detail |
|---|---|---|---|
| `rev-001` | Structural integration (tool names, triggers, frontmatter, e2e loading) | superseded — all 6 dimensions green | `revisions/rev-001/AGENTS.md` |
| `rev-002` | Content depth pilot batch (A0-native concepts, adaptation depth) | superseded — promising seeds, comparability blocker discovered | `revisions/rev-002/AGENTS.md` |
| `rev-003` | Comparable regression verification + full-scale content-depth promotion | superseded — 7.96/8, 161/161, all green | `revisions/rev-003/AGENTS.md` |
| `rev-004` | Deeper content quality audit (LLM rubric: Claude removal, guidance quality, eval alignment, naturalness) | superseded — scanner-perfect but runtime-alignment proof incomplete | `revisions/rev-004/AGENTS.md` |
| `rev-005` | Recalibrate evaluation to Agent Zero runtime/project/subordinate/harness truth | **complete** — semantic 14.54/15 (96.9%); all branches promoted | `revisions/rev-005/AGENTS.md` |
| `rev-006` | Prove native Agent Zero integration architecture via 5-layer evaluation | **complete** — 199 tests passed across all 5 layers; 4 branches promoted |
| `rev-007` | Hooks/references porting classification + e2e test cleanup | **complete** — observability ported, security enriched, e2e cleaned, all tests green | `revisions/rev-007/AGENTS.md` |
| `rev-008` | Complete porting parity audit (docs, scripts, platform formats) | **complete** — porting contract fully satisfied; skill-anatomy adapted, validate-skills synced | `revisions/rev-008/AGENTS.md` |

## Branch Memory (Cross-Revision Ledger)

| Branch ID | Revision | Hypothesis | Best Result | Status | Detail |
|---|---|---|---|---|---|
| branch-a-correctness | rev-001 | Fix introduced correctness errors | 161/161, 0 regressions | promoted | `revisions/rev-001/branches/branch-a-correctness/AGENTS.md` |
| branch-b-structural | rev-001 | Add missing structural elements | 161/161, 0 regressions | promoted | `revisions/rev-001/branches/branch-b-structural/AGENTS.md` |
| branch-c-a0native | rev-001 | Add A0-native concept references | 161/161, 0 regressions | promoted | `revisions/rev-001/branches/branch-c-a0native/AGENTS.md` |
| branch-d-e2e-coverage | rev-001 | Add parametrized e2e tests for all 24 skills | 30/30 e2e pass | promoted | `revisions/rev-001/branches/branch-d-e2e-coverage/AGENTS.md` |
| branch-e-project-context | rev-002 | Add project-context awareness | +4 total / +0.17 avg | superseded (absorbed into merged) | `revisions/rev-002/branches/branch-e-project-context/AGENTS.md` |
| branch-f-parallel-delegation | rev-002 | Add explicit `parallel` + `call_subordinate` guidance | +9 total / +0.37 avg | superseded (absorbed into merged) | `revisions/rev-002/branches/branch-f-parallel-delegation/AGENTS.md` |
| branch-g-merged | rev-003 | Combined parallel/delegation + project-context, scaled to 24 | 7.96/8 avg, +54 total, 161/161 regression | promoted (full-scale) | `revisions/rev-003/branches/branch-g-merged/AGENTS.md` |
| branch-h-a0-evals | rev-004 | Add A0-specific evals (D3 gap) | pilot: 7 new evals | superseded (absorbed into k-merged) | `revisions/rev-004/branches/branch-h-a0-evals/AGENTS.md` |
| branch-i-json-examples | rev-004 | Add JSON tool-call examples (D2 gap) | pilot: 4 skills enhanced | superseded (absorbed into k-merged) | `revisions/rev-004/branches/branch-i-json-examples/AGENTS.md` |
| branch-j-correctness | rev-004 | Fix memory_save + add Python examples (D1/D4 gap) | pilot: 5 skills fixed | superseded (absorbed into k-merged) | `revisions/rev-004/branches/branch-j-correctness/AGENTS.md` |
| branch-k-merged | rev-004 | Combined A0-evals + JSON examples + correctness, scaled to 24 | **8.0/8 avg, 192/192, 161/161 regression** | promoted (full-scale) | `revisions/rev-004/branches/branch-k-merged/AGENTS.md` |
| branch-d-d4-d5-e2e-evalrunner | rev-005 | D4/D5 refinement + e2e fix + eval-runner formalization | `cp-d001-d4-d5-e2e-evalrunner`: semantic 14.54/15; all checks pass | promoted externally | `revisions/rev-005/branches/branch-d-d4-d5-e2e-evalrunner/AGENTS.md` |
| branch-b-runtime-contract-depth | rev-005 | Deepen D1 A0 Runtime Model awareness across all 24 skills | `cp-b001-runtime-contract-depth`: semantic 13.29/15; D1 2.79/3; live-promoted | promoted externally | `revisions/rev-005/branches/branch-b-runtime-contract-depth/AGENTS.md` |
| branch-a-harness-truth | rev-005 | Fix runtime/harness-truth failures hidden by scanner-perfect rev-004 | `cp-a001-harness-truth`: live-promoted; post-static/structural/runtime all exit 0 | promoted externally | `revisions/rev-005/branches/branch-a-harness-truth/AGENTS.md` |

## Cross-Revision Lessons

- Content adaptation was largely mechanical find-replace, not deep integration. rev-002 through rev-004 addressed this progressively.
- `parallel` + `call_subordinate` patterns are the biggest missed A0 integration across skills — now fully addressed.
- Related sections, Files sections, and trigger expansion are safe and additive.
- Cross-reference syntax needs audit — bare-text references found in multiple skills.
- E2e testing revealed that natural-language triggers matter as much as technical ones.
- Harness bugs (both structural and e2e) are a real risk — always verify the measuring stick.
- Checkpoint-clone regression can be invalidated by path-bound assertions — the live-overlay procedure solves this.
- Merging complementary branches is safe and efficient when they touch different sections.
- The live-overlay procedure (backup → overlay → test → restore → verify) produces fully comparable regression evidence.
- Scanner regex needs to handle natural-language tool references, not just exact keyword matching.
- Sub-agents correctly refuse external promotion — protocol compliance is enforced.
- `memory_save` / `memory_load` are non-existent tools in A0 — always verify tool names against `/a0/AGENTS.md`.
- LLM rubric evaluation reveals quality gaps that automated scanners cannot detect.
- TDD serves as the gold standard for skill quality — concrete JSON examples, browser action tables, subordinate templates.
- npm/Node.js centrism is a systematic bias in skills adapted from JS-oriented repos.

- Scanner-perfect content coverage is not the same as runtime-alignment proof; rev-005 treats A0 project metadata, exact tool schemas, subordinate boundaries, and live harness truth as first-class evaluation targets.

- rev-005 externally promoted `cp-a001-harness-truth` to the live plugin after proving runtime/harness-truth alignment; rollback backup is `/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-001-cp-a001/pre-promotion-live-backup-a0_agent_skills`.

## Archives

None yet.

## Parity Audit Conclusion (rev-008)

The Agent-Skills Porting Contract is **fully satisfied**. All portable concepts (skills, references, hooks, commands, agents) are ported or adapted. Platform-specific surfaces (6 setup guides, CLAUDE.md, .claude-plugin/, validate-commands.js) are documented as omitted with rationale. See `revisions/rev-008/parity-audit.md` for the complete classification table.
