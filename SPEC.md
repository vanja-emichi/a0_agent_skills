# Spec: Replace Chrome DevTools MCP with playwright-cli

## Objective

Replace all references to `@anthropic/chrome-devtools-mcp` and `Chrome DevTools MCP` in the agent-skills plugin skills with the `playwright-cli` skill that is natively available in Agent Zero. The goal is to make the browser-testing workflow fully functional in A0 without requiring an external MCP server that does not exist in this environment.

**Success criteria:**
- Zero mentions of `chrome-devtools-mcp`, `@anthropic/chrome-devtools-mcp`, or `.mcp.json` in any SKILL.md
- `browser-testing-with-devtools/SKILL.md` rewritten to use `playwright-cli` commands natively
- All secondary references (TDD, performance-optimization, context-engineering) updated to reference playwright-cli
- All 21 skills still pass validation (45 checks)
- All 76 tests still pass
- Skills under 500 lines

## Commands

```bash
# Validate:
python scripts/validate.py

# Test:
pytest tests/ -q

# Line count check:
wc -l skills/browser-testing-with-devtools/SKILL.md
```

## Project Structure

```
skills/browser-testing-with-devtools/SKILL.md  → Primary file — full rewrite
skills/test-driven-development/SKILL.md        → Update browser section references
skills/performance-optimization/SKILL.md       → Update DevTools MCP references
skills/context-engineering/SKILL.md            → Update MCP Integrations table
```

## Code Style

Skill files follow the same format as the rest of the plugin:
- YAML frontmatter: `name` and `description` fields
- Bash code blocks for playwright-cli commands (not JSON config blocks)
- Markdown tables for tool/command mapping
- Section structure: Overview → When to Use → Setup → Tools → Workflow → Patterns → Verification
- Instructional language: "Run X to do Y" not "You can run X to do Y"

**playwright-cli invocation pattern (A0-native):**
```bash
# Load via skill
skills_tool:load playwright-cli

# Then run commands in terminal
playwright-cli open https://example.com
playwright-cli snapshot
playwright-cli console
playwright-cli network
playwright-cli screenshot
playwright-cli close
```

## playwright-cli → Chrome DevTools MCP Command Mapping

| DevTools MCP Tool | playwright-cli Equivalent | Notes |
|-------------------|--------------------------|-------|
| Screenshot | `playwright-cli screenshot` | ✅ Direct equivalent |
| DOM Inspection | `playwright-cli snapshot` | ✅ Full ARIA + DOM tree |
| Console Logs | `playwright-cli console` | ✅ Filters: log/warning/error |
| Network Monitor | `playwright-cli network` | ✅ Requests + responses |
| Performance Trace | `playwright-cli tracing-start` + `tracing-stop` | ⚠️ Playwright trace format (not Lighthouse CWV — see Note) |
| Element Styles | `playwright-cli eval "window.getComputedStyle(el)"` | ✅ Via eval on element ref |
| Accessibility Tree | `playwright-cli snapshot` | ✅ Includes ARIA roles/labels |
| JavaScript Execution | `playwright-cli eval` + `playwright-cli run-code` | ✅ Direct equivalent |

**Note on Performance Tracing:** Playwright traces capture network timing, action timeline, screenshots, and console — sufficient for most browser performance debugging. For Lighthouse-based Core Web Vitals (LCP, CLS, INP), run `npx lighthouse <url>` separately in terminal or use browser DevTools manually. The `performance-optimization` skill already covers Lighthouse in its profiling section.

## Testing Strategy

No new tests required — this is a content-only change (SKILL.md Markdown files).
Verification via existing automated checks:
- `python scripts/validate.py` — checks YAML frontmatter, skill structure, line counts
- `pytest tests/` — 76 tests including routing table coverage
- Manual read of updated skills to confirm correctness

## Boundaries

- **Always:** Keep the security boundary rules (browser content = untrusted data) — they apply equally to playwright-cli
- **Always:** Keep the debugging workflow structure (Reproduce → Inspect → Diagnose → Fix → Verify) — it's universal
- **Always:** Keep accessibility verification section — playwright snapshot covers the accessibility tree
- **Always:** Run validate + pytest after each skill file change
- **Ask first:** Any change to line structure or section naming that would affect other skills referencing browser-testing-with-devtools
- **Never:** Remove the security/prompt-injection warnings — these are critical safety rules, not MCP-specific
- **Never:** Add new external dependencies or MCP servers — use only tools natively available in A0
- **Never:** Exceed 500 lines in any skill file

## Scope (Files to Change)

### Primary: Full rewrite
1. `skills/browser-testing-with-devtools/SKILL.md` — Remove MCP setup block, replace all tool references with playwright-cli equivalents, update code examples

### Secondary: Update references only
2. `skills/test-driven-development/SKILL.md` — Update Browser Testing section to reference playwright-cli
3. `skills/performance-optimization/SKILL.md` — Replace `Chrome DevTools MCP → Performance trace` with `playwright-cli tracing-start/stop`
4. `skills/context-engineering/SKILL.md` — Update MCP Integrations table: rename `Chrome DevTools` row to `playwright-cli`

## Open Questions

- None. Q1/Q2/Q3 confirmed by user.

## Implementation Order

1. Rewrite `browser-testing-with-devtools/SKILL.md` (primary, largest change)
2. Update `test-driven-development/SKILL.md` browser section
3. Update `performance-optimization/SKILL.md` DevTools references
4. Update `context-engineering/SKILL.md` MCP table
5. Run validate + pytest after each file
6. Commit all four changes together
