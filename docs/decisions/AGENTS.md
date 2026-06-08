# Architecture Decision Records

## Purpose

- Contains all ADRs (Architecture Decision Records) for the `a0_agent_skills` Agent Zero plugin.
- Captures significant architectural decisions with context, rationale, and consequences.

## Ownership

- `README.md`: ADR index table with status, title, and date for each record.
- `ADR-001-python-extensions-over-shell-hooks.md`: Python extensions and YAML commands over shell hooks.
- `ADR-002-dox-runtime-skill-lifecycle-gates.md`: DOX as runtime skill with lifecycle gates.
- `ADR-003-source-historical-plugin-canonical.md`: Source-project as historical reference, plugin as canonical.
- `ADR-004-sdd-documentation-cache.md`: SDD documentation cache.
- `ADR-005-simplify-ignore-file-protection.md`: Simplify-ignore file protection.
- `ADR-006-e2e-test-harness.md`: HTTP-API-driven E2E test harness.
- `ADR-007-eval-framework-and-behavioral-fixes.md`: Eval framework integration and behavioral skill fixes.
- `ADR-008-dox-skills-prompt-restructuring.md`: DOX/skills prompt restructuring — removal of enforcement extensions in favor of prompt-based DOX.

## Local Contracts

- ADRs follow the lifecycle: PROPOSED → ACCEPTED → SUPERSEDED or DEPRECATED.
- Never delete old ADRs; supersede with new ones that reference the original.
- Each ADR file uses the standard ADR format: context, decision, consequences.
- The README index must be updated when new ADRs are added.

## Work Guidance

- Create new ADRs by copying the format of existing ones and assigning the next sequential number.
- Update README.md index table when adding, superseding, or deprecating ADRs.
- ADRs should capture why, not just what — include alternatives considered.

## Verification

- All ADR files referenced in README.md must exist.
- Sequential numbering should have no gaps.
- Each ADR should have a clear status in its front matter.

## Child DOX Index

No child DOX files.
