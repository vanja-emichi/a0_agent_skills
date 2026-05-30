# Changelog

## v0.4.0 — 2025-05-13

### Major Rewrite — Lean Architecture

Complete rewrite from the ground up, replacing the heavy lifecycle runtime
(5,000+ lines of Python, 13 extensions, 8 hook points) with a focused, reliable
architecture (519 lines, 2 extensions, 2 hook points).

#### What Changed

- **Removed lifecycle state machine** — The 9-module `lib/` directory with
  `LifecycleState`, phase tracking, enforcement gates, and simplify-ignore
  locking has been removed. Routing is now purely declarative via a Markdown
  prompt injected at system prompt assembly time.

- **Removed 11 extensions** — Reduced from 13 extensions across 8 hook points
  to 2 focused extensions:
  - `system_prompt/_15_agent_skills_routing.py` — Injects routing rules
  - `tool_execute_after/_05_skill_telemetry.py` — Logs skill activations

- **Consolidated agent profiles** — Reduced from 7 to 3 core specialist
  profiles: `code-reviewer`, `security-auditor`, `test-engineer`.

- **Consolidated commands** — Reduced from 10 to 7 core SDLC commands.
  Removed `/idea`, `/lifecycle-status`, `/security` (functionality covered by skills).

- **Added telemetry** — New `tool_execute_after` extension logs skill
  activations to a project-scoped JSONL file with rotation, thread safety,
  and path traversal protection.

#### Security Hardening

- Path traversal protection in telemetry log path resolution
- Scope sanitization in `/ship` command (strips control chars, injection patterns)
- Thread-safe file writes with `threading.Lock`
- Atomic file rotation using `tempfile.mkstemp` + `os.replace`
- Restrictive file permissions: directories `0o750`, log files `0o640`

#### Test Suite

- All 118 tests pass (previous version's tests were broken)
- Covers: telemetry config parsing, thread safety, rotation, routing injection,
  command templates, enforcement language, hook stubs

#### Breaking Changes from v0.3.x

- `settings_sections` changed from `lifecycle` to `agent`
- Removed `always_enabled: true` — user controls plugin activation
- Removed `lib/` directory and all lifecycle-related imports
- Removed `references/` directory (checklists moved into skill directories)
- Agent profiles `skill-analyzer`, `skill-comparator`, `skill-creator`, `skill-grader` removed

---

## v0.3.1 — Previous Release

- Full lifecycle runtime with state machine
- 13 extensions across 8 hook points
- 7 agent profiles
- 10 slash commands
- 22 skills
