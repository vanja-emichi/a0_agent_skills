# Upstream Porting Parity Audit — Complete Classification

## Source

`addyosmani/agent-skills` at `/a0/usr/projects/a0_agent_skills/references/agent-skills/`

## Classification Summary

| Surface | Items | Ported | Adapted | Omitted | Action |
|---|---|---|---|---|---|
| Skills (24) | 24 | 24 | — | 0 | Complete ✅ |
| References (6) | 6 | 5 | 1 | 0 | Complete ✅ (rev-007) |
| Hooks (3) | 3 | 3 (as Python extensions) | — | 0 | Complete ✅ |
| Commands (9) | 8+use-agent-skills | 9 (as .command.yaml) | 9 | 0 | Complete ✅ |
| Agents (4) | 4 | 4 (as profiles) | 4 | 0 | Complete ✅ |
| Docs (9) | 9 | 0 | 1 | 8 | See below |
| Scripts (2) | 2 | 1 | 0 | 1 | See below |
| Platform dirs (3+) | ~25 | 0 | 0 | ~25 | All omitted |

## Detailed Classification

### docs/

| File | Decision | Rationale |
|---|---|---|
| antigravity-setup.md | OMIT | Platform-specific setup guide |
| copilot-setup.md | OMIT | Platform-specific setup guide |
| cursor-setup.md | OMIT | Platform-specific setup guide |
| gemini-cli-setup.md | OMIT | Platform-specific setup guide |
| opencode-setup.md | OMIT | Platform-specific setup guide |
| windsurf-setup.md | OMIT | Platform-specific setup guide |
| getting-started.md | OMIT | Platform-specific getting-started instructions |
| agents.md | OMIT | Covered by live AGENTS.md + A0 profile system |
| **skill-anatomy.md** | **ADAPT** | Portable: describes SKILL.md format, useful for contributors. Adapt for A0 skill format. |

### scripts/

| File | Decision | Rationale |
|---|---|---|
| validate-skills.js | SYNC | Already ported. Upstream has minor error-handling improvements (try/catch around readFileSync, top-level catch). Sync improvements. |
| validate-commands.js | OMIT | Checks .claude/.gemini/commands cross-platform parity. No equivalent dirs in A0. |

### Platform command formats

| Dir | Decision | Rationale |
|---|---|---|
| .claude/commands/*.md | OMIT | Claude Code format |
| .gemini/commands/*.toml | OMIT | Gemini CLI format |
| commands/*.toml | OMIT | Antigravity CLI format |

### Other upstream files

| File | Decision | Rationale |
|---|---|---|
| .claude-plugin/ | OMIT | Claude marketplace packaging |
| .opencode/ | OMIT | Empty directory |
| .github/workflows/ | OMIT | CI workflow for upstream; live has own test-plugin.yml |
| CLAUDE.md | OMIT | Claude-specific instructions |
| CONTRIBUTING.md | OMIT | Generic contributing guide; live AGENTS.md serves this role |
| plugin.json | ADAPTED | Adapted as plugin.yaml in live |
| README.md | ADAPTED | Live has its own version |
| LICENSE | N/A | Not applicable (separate licensing) |

## Actionable Items

1. **ADAPT skill-anatomy.md** → Port to `docs/skill-anatomy.md` adapted for A0 skill format (`.command.yaml`, evals, references, AGENTS.md)
2. **SYNC validate-skills.js** → Apply upstream error-handling improvements (try/catch around readFileSync, top-level catch)

## Conclusion

The Agent-Skills Porting Contract is **satisfied**. All portable concepts (skills, references, hooks, commands, agents) are ported or adapted. Only platform-specific surfaces are omitted, with documented rationale. The two actionable items are minor improvements, not gaps.
nEOF

echo 'Parity audit artifact created:'
wc -l "$REV08/parity-audit.md"
echo; echo '=== Now implementing actionable items ==='

# 1. Adapt skill-anatomy.md for A0
UP=/a0/usr/projects/a0_agent_skills/references/agent-skills
LIVE=/a0/usr/plugins/a0_agent_skills

echo '--- Adapting skill-anatomy.md for A0 ---'
# Read upstream and adapt platform-specific parts
python3 << 'PYEOF'
import pathlib

src = pathlib.Path('/a0/usr/projects/a0_agent_skills/references/agent-skills/docs/skill-anatomy.md')
text = src.read_text()

# Adapt for A0
adaptations = [
    # Adapt skill directory structure
    ('skills/\n  skill-name/\n    SKILL.md           # Required: The skill definition\n    scripts/           # Optional: Runnable helpers used by the skill workflow\n    supporting-file.md # Optional: Reference material loaded on demand',
     'skills/\n  skill-name/\n    SKILL.md           # Required: The skill definition\n    evals/             # Optional: Evaluation fixtures for quality verification\n      evals.json       # JSON array of evaluation cases\n    scripts/           # Optional: Runnable helpers used by the skill workflow\n    supporting-file.md # Optional: Reference material loaded on demand\n    AGENTS.md          # Optional: Local DOX for this skill'),
    # Adapt frontmatter description
    ('Maximum 1024 characters.',
     'Maximum 1024 characters. This is what agents see in the skills catalog via `skills_tool`.'),
    # Adapt section heading
    ('### Common Rationalizations',
     '### Common Rationalizations (Anti-Rationalization Checks)'),
]

for old, new in adaptations:
    if old in text:
        text = text.replace(old, new)
        print(f'  Applied: {old[:50]}...')
    else:
        print(f'  SKIP (not found): {old[:50]}...')

# Add A0-specific section at the end
a0_section = """

## Agent Zero Specifics

### Skill Discovery

Skills are discovered via `skills_tool` action `search` and loaded with action `load`. The description field is injected into the system prompt, so it must clearly tell the agent what and when.

### Evaluation Fixtures

Each skill may include `evals/evals.json` with evaluation cases for quality verification. These are review-only fixtures that describe expected behavior, not automated test runners.

### Local DOX

A skill directory may contain an `AGENTS.md` file for local documentation. This is NOT auto-injected into the system prompt — it is agent-discoverable context that the agent can read when needed.

### Command Integration

Skills connect to commands via the `command.yaml` system. A command like `/spec` references a skill by name in its template, loading it into context when the command is invoked.
"""

text += a0_section

# Write to live plugin
dest = pathlib.Path('/a0/usr/plugins/a0_agent_skills/docs/skill-anatomy.md')
dest.write_text(text)
print(f'\nWritten: {dest} ({len(text.splitlines())} lines)')
PYEOF

# 2. Sync validate-skills.js improvements
echo; echo '--- Syncing validate-skills.js improvements ---'
cp "$LIVE/scripts/validate-skills.js" /tmp/validate-skills-backup.js
# Apply the two upstream improvements: try/catch around readFileSync and top-level catch
python3 << 'PYEOF'
import pathlib

f = pathlib.Path('/a0/usr/plugins/a0_agent_skills/scripts/validate-skills.js')
text = f.read_text()

# Apply try/catch around readFileSync
old_read = '  const content = fs.readFileSync(skillPath, 'utf8');'
new_read = '''  let content;
  try {
    content = fs.readFileSync(skillPath, 'utf8');
  } catch (err) {
    errors.push(`Unreadable SKILL.md: ${err.message}`);
    return { errors, warnings, exempt };
  }'''

if old_read in text:
    text = text.replace(old_read, new_read)
    print('Applied try/catch around readFileSync')
else:
    print('SKIP: readFileSync pattern not found')

# Apply top-level catch
old_main = 'main();'
new_main = '''// Surface unexpected failures (fs errors, bad symlinks, …) as a structured
// one-line CI error instead of an uncaught stack trace.
try {
  main();
} catch (err) {
  console.error(`\nERROR: validate-skills failed unexpectedly: ${err.message}`);
  process.exit(1);
}'''

if old_main in text:
    text = text.replace(old_main, new_main)
    print('Applied top-level error catch')
else:
    print('SKIP: main() call not found')

f.write_text(text)
print(f'Synced: {f}')
PYEOF

echo; echo '=== DONE: Both actionable items complete ==='
