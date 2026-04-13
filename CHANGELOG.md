# Changelog

All notable changes to the Agent Skills plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-13

### Added
- 21 engineering skills covering Define → Plan → Build → Verify → Review → Ship
- 3 specialist agent personas (code-reviewer, test-engineer, security-auditor)
- 7 slash commands (/spec, /plan, /build, /test, /review, /code-simplify, /ship)
- 4 reference checklists (security, performance, testing, accessibility)
- 5 extension hooks (agent_init, message_loop_prompts_after, tool_execute_before, tool_execute_after, monologue_end)
- Shared utility library (lib/simplify_ignore_utils.py)
- CI pipeline with validation (44 checks) and test suite (174 tests)
- Setup docs for various IDEs/tools

### Fixed
- tool_execute_after hook now derives file_path from current_tool.args (A0 core limitation workaround)
- PrintStyle consistency across all simplify-ignore hooks
- inject_meta_skill removed default LoopData() parameter
- Skill conventions standardized (idea-refine, using-agent-skills)
- README skill count corrected (20 → 21)
- getting-started.md path corrected (.claude/commands/ → commands/)
- CI pip caching added and install steps consolidated

### Changed
- Plugin name set to `a0_agent_skills` (regex compliance for Plugin Index)
- simplify_ignore_utils.py moved to lib/ (clean extension layout)
- GLOBAL_COMMANDS_DIR derived dynamically from PLUGIN_ROOT
- Stale Claude Code path removed from idea-refine skill
- PrintStyle tests parametrized (3 classes → 1)

[0.1.0]: https://github.com/vanja-emichi/a0_agent_skills/releases/tag/v0.1.0
