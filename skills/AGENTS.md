# skills/

## Core Contract

- This AGENTS.md is the binding work contract for the `skills/` subtree
- All skill definitions, metadata, scripts, and reference files must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `skills/AGENTS.md` before modifying any skill
3. Identify the specific skill directory you will touch
4. Read the target `SKILL.md` and any reference files before editing
5. Do not rely on memory — re-read in the current session

## Update After Editing

Every meaningful change to a skill requires an AGENTS.md pass:

- Update this doc when: adding/removing skills, changing phase mapping, altering DAG dependencies, changing naming conventions
- Update `SKILL.md` frontmatter when: changing name, version, dependencies, triggers, tags
- Update parent root AGENTS.md when: skill catalog table changes, phase mapping changes
- Small edits that don't change behavior or contracts may leave docs unchanged, but the pass must still happen

## Purpose

The 23 production-grade engineering workflow skills that form the core of the a0_agent_skills plugin. Each skill is a self-contained directory with a SKILL.md definition, optional supporting files, and optional scripts. Skills are loaded on-demand by the agent and drive the 6-phase SDLC lifecycle.

**Owns:** Skill definitions, skill metadata (YAML frontmatter), skill dependency graph, supporting reference files, executable scripts.

**Does NOT own:** Skill enforcement logic (in `helpers/skill_match.py`), state persistence (in `helpers/workflow_state.py`), contract parsing (in `helpers/skill_contracts.py`).

## Entry Points

Each skill directory must contain:

```
skills/<skill-name>/
├── SKILL.md              # Required: skill definition with YAML frontmatter
├── <reference>.md        # Optional: supporting reference files
└── scripts/              # Optional: executable helper scripts
    └── <script>.sh
```

Skills are discovered via `skills_tool:search` and loaded via `skills_tool:load`.

## Directory Layout

```
skills/
├── api-and-interface-design/SKILL.md
├── browser-testing-with-devtools/SKILL.md
├── ci-cd-and-automation/SKILL.md
├── code-review-and-quality/SKILL.md
├── code-simplification/SKILL.md
├── context-engineering/SKILL.md
├── debugging-and-error-recovery/SKILL.md
├── deprecation-and-migration/SKILL.md
├── documentation-and-adrs/SKILL.md
├── doubt-driven-development/SKILL.md
├── frontend-ui-engineering/SKILL.md
│   └── accessibility-checklist.md     # Reference file
├── git-workflow-and-versioning/SKILL.md
├── idea-refine/
│   ├── SKILL.md
│   ├── frameworks.md                  # Reference file
│   ├── refinement-criteria.md         # Reference file
│   ├── examples.md                    # Reference file
│   └── scripts/idea-refine.sh         # Executable script
├── incremental-implementation/SKILL.md
├── interview-me/SKILL.md
├── performance-optimization/
│   ├── SKILL.md
│   └── performance-checklist.md       # Reference file
├── planning-and-task-breakdown/SKILL.md
├── security-and-hardening/
│   ├── SKILL.md
│   └── security-checklist.md          # Reference file
├── shipping-and-launch/SKILL.md
├── source-driven-development/SKILL.md
├── spec-driven-development/SKILL.md
├── test-driven-development/
│   ├── SKILL.md
│   └── testing-patterns.md            # Reference file
└── using-agent-skills/
    ├── SKILL.md
    └── orchestration-patterns.md      # Reference file
```

## Contracts & Invariants

### SKILL.md Format

Every SKILL.md MUST have YAML frontmatter followed by Markdown body:

```markdown
---
name: <skill-name>
version: 1.0.0
author: Author Name
description: >
  One sentence describing what the skill does, followed by one or more
  "Use when" trigger conditions.
tags: [tag1, tag2, tag3]
trigger_patterns: trigger-phrase-1, trigger-phrase-2, ...
depends_on: []  # Optional: auto-loaded prerequisite skills
---

# Skill Title

[Skill body — workflow, steps, examples, verification checklist]
```

### Required Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Matches directory name (kebab-case) |
| `version` | Yes | Semantic version (e.g. `1.0.0`) |
| `author` | Yes | Author attribution |
| `description` | Yes | One-liner + "Use when" triggers |
| `tags` | Yes | Array of searchable keywords |
| `trigger_patterns` | Yes | Phrases the agent matches against |
| `depends_on` | No | List of skill names this skill requires (auto-loaded when skill is loaded) |

### Naming Conventions

- **Directory name**: kebab-case (e.g. `code-review-and-quality`)
- **SKILL.md**: Always uppercase, always this exact filename
- **Reference files**: kebab-case.md (e.g. `security-checklist.md`)
- **Scripts**: kebab-case.sh (e.g. `idea-refine.sh`)

### Context Efficiency

Skills are loaded on-demand — only the skill name and description are loaded at startup. The full SKILL.md loads into context only when the agent decides the skill is relevant.

- **Keep SKILL.md under 500 lines** — put detailed reference material in separate files
- **Write specific descriptions** — helps the agent know exactly when to activate the skill
- **Use progressive disclosure** — reference supporting files that get read only when needed
- **Prefer scripts over inline code** — script execution doesn't consume context
- **File references work one level deep** — link directly from SKILL.md to supporting files

### DAG Dependency Validation

Skills declare dependencies via the `depends_on` frontmatter field. These form a directed acyclic graph (DAG) validated at build time by `helpers/skill_contracts.py`.

- Dependencies must reference existing skill directory names
- Cycles are detected and rejected
- Next-skill hints are generated from the DAG for workflow state rehydration

### Active Dependencies

These skills currently declare `depends_on` prerequisites (auto-loaded):

| Skill | Dependencies |
|-------|-------------|
| `spec-driven-development` | `markdown-documents`, `architecture`, `design` |
| `planning-and-task-breakdown` | `markdown-documents` |

### Phase Mapping

Each skill belongs to a lifecycle phase. This mapping is maintained in:
1. `helpers/phase_governance.py` (PHASE_SKILL_MAP)
2. `prompts/agent.skills.routing.md` (routing rules)
3. This doc's skill catalog table below

All three must be kept in sync when adding new skills.

## The 23 Skills by Phase

| Phase | Skills | Description Focus |
|-------|--------|------------------|
| **DEFINE** | `spec-driven-development`, `interview-me`, `idea-refine` | Requirements extraction, spec writing, idea refinement |
| **PLAN** | `planning-and-task-breakdown`, `context-engineering` | Task decomposition, context management |
| **BUILD** | `incremental-implementation`, `test-driven-development`, `source-driven-development`, `doubt-driven-development`, `frontend-ui-engineering`, `api-and-interface-design` | Implementation, testing, verification, UI, API design |
| **VERIFY** | `browser-testing-with-devtools`, `debugging-and-error-recovery` | Runtime verification, systematic debugging |
| **REVIEW** | `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization` | Multi-axis review, simplification, security audit, perf checks |
| **SHIP** | `shipping-and-launch`, `ci-cd-and-automation`, `git-workflow-and-versioning`, `documentation-and-adrs`, `deprecation-and-migration` | Deployment, CI/CD, versioning, docs, migration |
| **META** | `using-agent-skills` | Meta-skill for skill selection guidance |

## Style

- Keep SKILL.md concise and operational — under 500 lines
- Document workflows and exit criteria, not diary entries
- Put detailed reference material in sibling files, not in SKILL.md itself
- Prefer direct bullets and numbered steps
- Delete stale content immediately

## Closeout Protocol

After modifying any skill:

1. Re-check the skill's frontmatter matches directory name and phase
2. Update this doc's directory layout and skill catalog if structure changed
3. Update parent root AGENTS.md skill catalog if phase mapping changed
4. Update `helpers/phase_governance.py` PHASE_SKILL_MAP if phase changed
5. Update `prompts/agent.skills.routing.md` if triggers changed
6. Run `python -m pytest tests/test_skill_contracts.py tests/test_skill_graph.py -v`
7. Report docs intentionally left unchanged and why

## Patterns

### To create a new skill:
1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter
2. Set `name`, `version`, `author`, `description`, `tags`, `trigger_patterns` (required fields)
3. Set `depends_on` if the skill has prerequisites in the DAG
4. Add supporting reference files as siblings to SKILL.md
5. Add executable scripts in `scripts/` subdirectory if needed
6. Update phase mapping in `helpers/phase_governance.py` (PHASE_SKILL_MAP)
7. Update routing rules in `prompts/agent.skills.routing.md`
8. Add tests in `tests/test_skill_*.py`
9. Update root README skill catalog table
10. Run closeout protocol

### To add a reference file to an existing skill:
1. Create `<skill-name>/<filename>.md` as a sibling to SKILL.md
2. Reference it from SKILL.md body: "Load with `text_editor:read` on `<filename>`"
3. Reference files are NOT auto-loaded — they're read on-demand

### To add a script to an existing skill:
1. Create `skills/<skill-name>/scripts/<name>.sh`
2. Use `#!/bin/bash` shebang and `set -e`
3. Write status to stderr, machine-readable output (JSON) to stdout
4. Reference in SKILL.md Usage section

## Anti-patterns

- **Do NOT** skip YAML frontmatter — skill contracts and DAG validation depend on it
- **Do NOT** exceed 500 lines in SKILL.md — move detailed content to reference files
- **Do NOT** create circular dependencies in `depends_on` — the DAG validator will reject them
- **Do NOT** hardcode phase assignments only in SKILL.md — must also update `phase_governance.py` and routing rules
- **Do NOT** auto-load reference files from SKILL.md — they consume context; reference them for on-demand loading
- **Do NOT** use skills for trivial tasks that don't match the lifecycle phases
- **Do NOT** duplicate content across skill SKILL.md files — reference shared resources instead
- **Do NOT** skip the Read Before Editing protocol — re-read this doc and the target SKILL.md before changes
- **Do NOT** skip the AGENTS.md pass after editing

## Related Context

- Parent: `AGENTS.md` (plugin root)
- Helpers: `helpers/AGENTS.md` (skill_match, skill_contracts, phase_governance)
- Routing: `prompts/agent.skills.routing.md` (intent → skill mapping)
- Tests: `tests/test_skill_*.py` (skill-specific tests)
