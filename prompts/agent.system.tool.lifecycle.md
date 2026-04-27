# lifecycle tool

## Usage

```
lifecycle:init goal=<str> slug=<str> [project_root=<path>]
lifecycle:status [verbose=<bool>]
lifecycle:archive [promote_adrs=<bool>=true]
```

## Methods

| Method | Description |
|---|---|
| `lifecycle:init` | Create a new lifecycle with goal and slug. 7 phases hardcoded (IDEA→SHIP). Creates `.a0proj/run/current/` with state.md, findings.md, progress.md, errors.md. |
| `lifecycle:status` | Show current lifecycle state: active phase, findings, strikes. Answers the 5-Question Reboot Test. |
| `lifecycle:archive` | Archive lifecycle as completed or abandoned. Promotes trusted findings to `docs/adr/NNNN-slug.md`. Cleans up runtime state. |

## Phase Model

IDEA → SPEC → PLAN → BUILD → VERIFY → REVIEW → SHIP

Phase advance: edit the `phase:` field in `.a0proj/run/current/state.md` YAML frontmatter via `text_editor:patch`.

Always start with `lifecycle:init` before using other methods. The lifecycle state persists across turns in `.a0proj/run/current/`.
