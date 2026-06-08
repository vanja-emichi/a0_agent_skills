# Extensions — Monologue End Hooks

## Purpose

- Python extension hooks executed when the agent monologue ends (equivalent to a stop/session-complete event).
- Performs cleanup tasks after agent task completion.

## Ownership

- `_10_simplify_ignore.py`: Restores files from simplify-ignore backups and cleans up the cache when the session ends.
- `_15_skill_auto_unload.py`: Unloads skills at session end to keep context clean.
- `__init__.py`: Package marker for the extension directory.

## Local Contracts

- Files are auto-discovered and executed in numeric prefix order (`_10` before `_20`).
- Extensions receive the agent context and monologue state from the Agent Zero runtime.
- Must import utilities from the parent `extensions/python/` directory via `sys.path` insertion.
- Dependencies: stdlib only for simplify-ignore; skill auto-unload references skill files.

## Work Guidance

- Add new monologue-end hooks by creating `_NN_<name>.py` with the next available prefix number.
- Keep hooks focused on a single concern.
- Test hooks via `test_runtime_extensions_and_hooks.py` and `test_e2e_extension_behavior.py`.

## Verification

- Import each hook module to confirm no syntax or dependency errors.
- Run extension-related tests: `pytest -k extension`.

## Child DOX Index

No child DOX files.
