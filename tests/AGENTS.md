# a0_agent_skills Plugin — Tests

## Purpose

- Comprehensive test suite for the `a0_agent_skills` plugin covering DOX behavior, extensions, commands, skill loading, e2e flows, eval reporting, and structural validation.

## Ownership

- `conftest.py`: Shared pytest fixtures and test configuration.
- `_a0_e2e_client.py`: HTTP client helper for end-to-end tests against the Agent Zero API.
- `test_dox_behavior.py`: Unit tests for DOX contract routing and closeout behavior.
- `test_dox_interpreter.py`: Structural and runtime tests for the DOX system-prompt interpreter and canonical scaffold template.
- `test_e2e_agent_profiles.py`: E2e agent profile loading, behavior, and ADR-009 subordinate DOX propagation (project root AGENTS.md + catch-all traversal rule inherited by subordinate via shared context).
- `test_e2e_command_execution.py`: E2e command execution via scheduler tasks.
- `test_e2e_command_rendering.py`: E2e command template rendering.
- `test_e2e_dox_behavior.py`: E2e DOX chain reading through live agent sessions.
- `test_e2e_dox_closeout.py`: E2e DOX closeout compliance checks.
- `test_e2e_extension_behavior.py`: E2e extension injection and behavior tests.
- `test_e2e_extensions.py`: E2e extension presence and compilation checks.
- `test_e2e_prompt_override.py`: E2e verification that the agent0 specifics override is injected at position 1 of the main system prompt.
- `test_e2e_reference_access.py`: E2e reference checklist access via skills_tool.
- `test_e2e_skill_loading.py`: E2e skill loading and content verification.
- `test_eval_report.py`: Tests for eval report generation and quality metrics.
- `test_extension_imports_isolated.py`: Isolated import tests for extension modules.
- `test_framework_conformance.py`: LogItem dataclass conformance against framework source.
- `test_runtime_commands.py`: Runtime command resolution and execution.
- `test_runtime_extensions_and_hooks.py`: Runtime extension and hook loading.
- `test_runtime_skills_and_agents.py`: Runtime skill and agent profile discovery.
- `test_sdd_cache.py`: Tests for the SDD documentation cache.
- `test_ship_command.py`: Tests for the ship command workflow.
- `test_simplify_ignore.py`: Tests for simplify-ignore file protection.
- `test_structure.py`: Structural validation of the plugin directory layout.

## Local Contracts

- Tests run via `pytest` from the plugin root using `pytest.ini` configuration.
- E2E tests require a running Agent Zero instance; the client helper manages HTTP sessions.
- Unit tests should not depend on live services.
- Credentials resolved from env vars (`A0_E2E_USERNAME`, `A0_E2E_PASSWORD`) first, then fallback to framework dotenv `/a0/usr/.env` (`AUTH_LOGIN`, `AUTH_PASSWORD`) via `_resolve_credentials()` in conftest.py

## Work Guidance

- Add new test files for new plugin features following the `test_<feature>.py` naming convention.
- Keep e2e and unit tests in separate files for clarity.
- Update `_a0_e2e_client.py` when the Agent Zero API changes.

## Verification

- `pytest /a0/usr/plugins/a0_agent_skills/tests/` should pass.
- New features must have corresponding test coverage before merge.

## Child DOX Index

No child DOX files.
