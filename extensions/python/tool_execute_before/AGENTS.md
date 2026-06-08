# Extensions — Tool Execute Before Hooks

## Purpose

- Python extension hooks executed before each tool invocation in the agent loop.
- Intercepts tool calls for caching, file protection, and context injection.

## Ownership

- `_10_sdd_cache.py`: SDD documentation cache — intercepts tool calls to cache and retrieve documentation artifacts.
- `_20_simplify_ignore.py`: Simplify-ignore file protection — backs up protected files before tool execution modifies them.

## Local Contracts

- Files are auto-discovered and executed in numeric prefix order (`_10` → `_20`).
- Extensions receive the tool name, arguments, and agent context before execution.
- Return values can modify or block the upcoming tool call.
- Must import utilities from the parent `extensions/python/` directory.

## Work Guidance

- Add new pre-execution hooks by creating `_NN_<name>.py` with the next available prefix number.
- Keep hooks idempotent — tool calls may be retried.
- Test via `test_runtime_extensions_and_hooks.py`, `test_extension_inject.py`, and `test_e2e_extensions.py`.

## Verification

- Import each hook module to confirm no syntax or dependency errors.
- Run extension-related tests: `pytest -k extension`.

## Child DOX Index

No child DOX files.
