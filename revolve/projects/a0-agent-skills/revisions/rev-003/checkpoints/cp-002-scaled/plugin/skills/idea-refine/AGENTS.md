# Idea Refine Skill

## Purpose

- Skill that refines raw ideas into sharp, actionable concepts through structured divergent and convergent thinking.
- Guides agents through ideation, evaluation criteria application, and concept synthesis.

## Ownership

- `SKILL.md`: Skill definition — trigger conditions, instructions, and workflow.
- `examples.md`: Worked examples demonstrating the refinement process.
- `frameworks.md`: Thinking frameworks used for divergent/convergent analysis.
- `refinement-criteria.md`: Evaluation criteria applied during refinement stages.
- `scripts/`: Helper scripts used by the skill during execution.
- `evals/`: Evaluation prompts for measuring skill quality.

## Local Contracts

- `SKILL.md` is the entry point loaded by `skills_tool`.
- Scripts must be executable in the Agent Zero runtime (Python/Node.js).
- Examples and criteria files are reference material, not executed.

## Work Guidance

- Extend frameworks by editing `frameworks.md`; keep entries self-contained.
- Add new examples to `examples.md` following the existing format.
- Run evals after changes to verify refinement quality.

## Verification

- `SKILL.md` must exist and be valid markdown.
- Scripts in `scripts/` must run without errors.
- Eval prompts in `evals/` should produce meaningful quality signals.

## Child DOX Index

- `scripts/` — Skill helper scripts (no DOX).
- `evals/` — Evaluation prompts (no DOX).
