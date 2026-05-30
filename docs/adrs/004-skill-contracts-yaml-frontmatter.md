# ADR-004: Skill Contracts via YAML Frontmatter

**Date**: 2026-05-30
**Status**: Accepted

## Context

Skills had no structured metadata. The enforcement gate, phase governance, and telemetry systems all needed to know which phase a skill belongs to, what it depends on, and what capabilities it provides. This information was either hardcoded in helper modules or not available at all.

Without structured metadata:
- Phase mapping was maintained separately from skill definitions
- Skill dependencies were implicit and undocumented
- No way to detect circular dependencies between skills
- No way to suggest the next skill based on current context

## Decision

Add optional **YAML frontmatter** to `SKILL.md` files, enclosed between `---` delimiters at the top of the file. The contracts system:

1. **Parses** YAML frontmatter from each SKILL.md on plugin load
2. **Builds** a runtime DAG from `depends_on` fields
3. **Validates** the DAG for cycles (when `skill_graph_validate_on_build` is enabled)
4. **Provides** next-skill hints based on current phase and loaded skills

Frontmatter is optional — skills without it continue to work as before. Fields include: `name`, `version`, `phase`, `depends_on`, `provides`, `conflicts_with`, `optional`.

## Alternatives Considered

### Separate metadata files (skill.yaml alongside SKILL.md)
- **Pros**: Clean separation of content and metadata
- **Cons**: Two files per skill, easy to get out of sync, more files to manage
- **Rejected**: YAML frontmatter keeps metadata co-located with content

### Hardcoded mapping in phase_governance.py
- **Pros**: Simple, no parsing needed
- **Cons**: Every new skill requires a code change to the governance module; not self-service
- **Rejected**: Skills should be self-describing, not requiring code changes in other modules

### Database / registry file
- **Pros**: Centralized, queryable
- **Cons**: Yet another file to maintain, diverges from skill definitions, adds complexity
- **Rejected**: Frontmatter is the single source of truth, co-located with the skill

## Consequences

- **Backward compatible**: Skills without frontmatter work exactly as before
- **Human-readable**: YAML frontmatter is visible and editable in any text editor
- **Runtime DAG**: Cycle detection catches dependency errors at startup
- **Self-describing**: Skills declare their own phase, dependencies, and capabilities
- **Optional adoption**: Existing 23 skills can be annotated incrementally
