# a0_agent_skills Plugin — Commands

## Purpose

- Slash command definitions for the `a0_agent_skills` plugin providing structured workflows for build, review, spec, plan, test, ship, and code-simplify operations.
- Each command pairs a YAML manifest with a text prompt template or Python script.

## Ownership

- `build.command.yaml` / `build.txt`: Incremental build-workflow command.
- `review.command.yaml` / `review.txt`: Code review command.
- `spec.command.yaml` / `spec.txt`: Specification creation command.
- `plan.command.yaml` / `plan.txt`: Planning and task breakdown command.
- `test.command.yaml` / `test.txt`: Test-driven development command.
- `ship.command.yaml` / `ship.py`: Pre-launch review command that fans out to code-reviewer, security-auditor, and test-engineer, then synthesizes a GO/NO-GO decision with rollback plan.
- `code-simplify.command.yaml` / `code-simplify.txt`: Code simplification command.
- `.gitkeep`: Placeholder to preserve directory in git.

## Local Contracts

- YAML manifests define command metadata: `name`, `description`, `type`, `template_path`.
- Text templates (`.txt`) are prompt templates loaded into agent context at invocation.
- `ship.py` is a Python-backed command that orchestrates fan-out to code-reviewer, security-auditor, and test-engineer specialists, then synthesizes a GO/NO-GO decision with rollback plan.
- Commands load skills (e.g., `incremental-implementation`, `test-driven-development`) as part of their workflow. DOX authority lives in root and child `AGENTS.md` files — commands read the applicable `AGENTS.md` chain before mutation.

## Work Guidance

- Add new commands by creating a `.command.yaml` + template pair.
- Follow the naming convention: `<verb>.command.yaml` + `<verb>.txt` (or `.py`).
- Update the plugin manifest if commands affect the plugin surface.

## Verification

- Each `.command.yaml` must reference an existing template or script.
- Test commands via the Commands plugin or direct invocation.

## Child DOX Index

No child DOX files.
