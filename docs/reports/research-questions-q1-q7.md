# Research Report: Open Questions Q1-Q7

> Generated: 2026-05-30 | Agent: Deep Research (researcher) | Sources: DeepWiki + local codebase inspection

---

## Q1: PROMPTINCLUDE FOR ARTIFACT DISCOVERY

### DeepWiki Answer

The `_promptinclude` plugin automatically discovers and injects files into the agent system prompt. Key parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `name_pattern` | `*.promptinclude.md` | Glob pattern for file matching |
| `max_depth` | 10 | Directory traversal depth |
| `max_file_tokens` | 2000 | Per-file token cap (cropped from start if exceeded) |
| `max_total_tokens` | 8000 | Aggregate token budget across all files |
| `max_file_count` | 50 | Maximum number of files included |

The scanner respects `.gitignore` rules. Files exceeding budget are either cropped to fit or skipped entirely. The `name_pattern` is configurable via plugin settings, meaning you can define custom patterns like `*.spec.md` or `*.plan.md`.

The plugin hooks into the `system_prompt` extension point. The `PromptInclude.execute()` method scans and appends content to the system prompt list.

### Local Code Evidence

From `/a0/plugins/_promptinclude/helpers/scanner.py`:

~~~python
def scan_promptinclude_files(
    root: str,
    *,
    name_pattern: str = "*.promptinclude.md",
    max_depth: int = 10,
    max_file_tokens: int = 2000,
    max_file_count: int = 50,
    max_total_tokens: int = 8000,
    gitignore: str = "",
) -> ScanResult:
~~~

The function sorts matched files alphabetically, iterates with budget tracking, and returns `FileEntry` objects with status `ok`, `cropped`, or `skipped`.

### Conclusion for Spec

**Yes, promptinclude CAN be used for artifact auto-injection.** The `name_pattern` is configurable, so a plugin could register additional patterns (e.g., `*-spec.promptinclude.md`) to auto-inject specs/plans. However, the default 8000-token total budget is modest for large specs. Two design options:

1. **Rename approach**: Copy/link spec artifacts as `X.promptinclude.md` for automatic pickup
2. **Pattern config approach**: Extend the promptinclude plugin config to add `*.spec.md` as a secondary pattern

Option 1 is zero-code but clutters the artifact tree. Option 2 is cleaner but requires a plugin config change. The current system prompt guidance says promptinclude is for "persistent project context, reference instructions, and user-authored prompt include files" -- specs and plans fit this definition.

---

## Q2: KNOWLEDGE INDEXING OF MARKDOWN DOCS

### DeepWiki Answer

The knowledge system **does automatically index** project markdown files. The loading process:

1. During `Memory` initialization/reload, the system scans `.a0proj/knowledge/` directories
2. Files are loaded via `TextLoader` (handles `.md` files)
3. Content gets `knowledge_source: True` metadata to distinguish from conversational memories
4. Documents are embedded and added to a FAISS vector index stored at `.a0proj/memory/index.faiss`
5. Checksum-based change detection triggers re-indexing when files change

There is also an explicit `ReindexKnowledge` API at `/plugins/_memory/knowledge_reindex` that clears the existing index and forces all databases to reload. This API is called from the frontend when browsing knowledge files.

The `ImportKnowledge` API allows uploading files which are saved to `.a0proj/knowledge/` and then triggers `Memory.reload`.

### Local Code Evidence

```
/a0/usr/projects/a0_agent_skills/.a0proj/knowledge/
├── fragments/   (empty)
├── main/        (empty - no about/ subdirectory content)
└── solutions/   (empty)
```

The knowledge directory structure exists but is currently **empty** -- no markdown files have been indexed. The FAISS index does exist at `.a0proj/memory/index.faiss` with an accompanying `index.pkl` and `index.faiss.sha256`.

### Conclusion for Spec

**Knowledge indexing is available but currently unused.** Two pathways exist:

1. **Save specs/plans to `.a0proj/knowledge/`**: They would be automatically indexed for vector recall via `memory_load` with `knowledge_source: True` filter. This gives semantic search over spec content.
2. **Use `memory_save` with area metadata**: Saves individual facts/fragments, but not full document recall.

For artifact discovery, knowledge indexing is complementary to promptinclude -- knowledge provides semantic recall ("find the spec about X"), while promptinclude provides always-present context injection. The ReindexKnowledge API could be called after spec/plan updates to refresh the index.

---

## Q3: UPSTREAM IDEA-REFINE SCRIPT PATTERN

### DeepWiki Answer

The `idea-refine.sh` script is a minimal utility that creates the `docs/ideas/` directory. It takes no arguments, has no logic beyond `mkdir -p`, and outputs a JSON status message. The SKILL.md shows the invocation path as `bash /mnt/skills/user/idea-refine/scripts/idea-refine.sh`, implying agent-driven execution. The core of the skill is the three-phase conversational process (Understand & Expand, Evaluate & Converge, Sharpen & Ship), not the script.

### Local Code Evidence

From `/a0/usr/plugins/a0_agent_skills/skills/idea-refine/scripts/idea-refine.sh`:

~~~bash
#!/bin/bash
set -e
IDEAS_DIR="docs/ideas"
if [ ! -d "$IDEAS_DIR" ]; then
  mkdir -p "$IDEAS_DIR"
  echo "Created directory: $IDEAS_DIR" >&2
else
  echo "Directory already exists: $IDEAS_DIR" >&2
fi
echo "{\"status\": \"ready\", \"directory\": \"$IDEAS_DIR\"}"
~~~

### Conclusion for Spec

**The script is trivially replicable via tool calls.** The Agent Zero port does NOT need to execute the bash script. Instead, when the idea-refine skill reaches the point of saving output, the agent should:

1. Ensure `docs/ideas/` exists (via `code_execution_tool: mkdir -p docs/ideas`)
2. Write the refined idea markdown to `docs/ideas/[idea-name].md` (via `text_editor:write`)

This is simpler than calling the script and is already how Agent Zero naturally operates. No special script integration needed.

---

## Q4: UPSTREAM COMPANION-SKILL PATTERNS

### DeepWiki Answer

Upstream has **no formal companion-skill system**. Multi-skill composition is always explicit:

- **Manual loading**: Users/agents explicitly specify which skills to load
- **Slash commands**: Commands like `/build` invoke multiple skills explicitly (e.g., `incremental-implementation` + `test-driven-development`)
- **Lifecycle sequences**: The `using-agent-skills` meta-skill documents recommended sequences but doesn't auto-load

Some agent platforms (OpenCode, Gemini CLI) have **agent-side auto-discovery** where the agent decides which skills to activate based on intent. But this is an agent-level feature, not a skill-level feature.

`spec-driven-development` does NOT automatically load other skills. It's a phase that *leads to* other skills being invoked via explicit commands.

### Local Code Evidence

Grep for companion/auto-load patterns in local SKILL.md files:

```
frontend-ui-engineering/SKILL.md:50:  companion accessibility checklist
performance-optimization/SKILL.md:39:  companion performance checklist
security-and-hardening/SKILL.md:40:  companion security checklist
test-driven-development/SKILL.md:55:  companion reference file
using-agent-skills/SKILL.md:33:      companion orchestration patterns guide
using-agent-skills/SKILL.md:124:     (also load: test-driven-development if TDD)
```

All "companion" references are **manual load instructions** in Supporting files sections. They tell the agent to use `text_editor:read` to open companion files, not to load another skill automatically.

### Conclusion for Spec

**There is no auto-loading companion system to port.** The current Agent Zero port already matches upstream behavior:

- Skills reference companion files via explicit `text_editor:read` instructions
- Multi-skill composition happens via slash commands (`/build` loads two skills) and the lifecycle sequence in `using-agent-skills`
- The `markdown-documents` companion skill pattern (auto-load when creating markdown) is an **Agent Zero port innovation**, not an upstream concept. It should remain a convention documented in the spec, not a runtime enforcement mechanism.

---

## Q5: HOW DOES THE LOCAL SPEC ALREADY GET USED BY DOWNSTREAM COMMANDS

### Local Code Evidence

#### `/build` (build.txt)
```
You MUST invoke the incremental-implementation skill AND the test-driven-development skill.
Pick the next pending task from tasks/todo.md.
```
**No spec reference.** Reads from `tasks/todo.md` only.

#### `/review` (review.txt)
```
You MUST delegate this code review to the code-reviewer specialist.
```
**No spec reference.** Delegates to code-reviewer with generic instructions.

#### `/test` (test.txt)
```
You MUST invoke the test-driven-development skill.
```
**No spec reference.** Pure TDD workflow.

#### `/ship` (ship.py) -- **THE KEY EXCEPTION**

`ship.py` is a 332-line Python command that **actively reads and parses the spec**:

1. `_find_spec(project_path)` -- scans `docs/specs/` for `*-spec.md` files
2. `_parse_project_structure(content)` -- parses the `## Project Structure` section to extract root directory and file tree
3. `_resolve_code_path(project_path, spec_root)` -- resolves plugin roots via Agent Zero's plugin resolution
4. `_read_spec_context(project_path)` -- extracts objective, success criteria, and files list from the spec
5. `_sanitize_spec_text()` / `_sanitize_scope()` -- security sanitization against prompt injection
6. Builds `specialist_context` with code directory, objective, success criteria, and files list
7. Passes this context to all three specialist agents (code-reviewer, security-auditor, test-engineer)

### Conclusion for Spec

**Only `/ship` reads the spec.** The other commands (`/build`, `/review`, `/test`) do NOT reference specs or plans at all. This means:

1. `/build` relies on `tasks/todo.md` but has no awareness of the spec's success criteria or architecture decisions
2. `/review` does generic five-axis review without knowing what was supposed to be built
3. `/test` does pure TDD without checking what the spec requires

This is a **spec gap**. The `/build` command should at minimum read the spec's success criteria and project structure. The `/review` command should compare changes against the spec's boundaries and architecture section. `/ship` is the gold standard -- its spec-reading logic should be extracted into a shared helper that other commands can use.

---

## Q6: UPSTREAM HOOKS AND VALIDATION

### DeepWiki Answer

Upstream has a **rich hook system** with four lifecycle events:

| Event | Hook Scripts | Purpose |
|-------|-------------|----------|
| `SessionStart` | `session-start.sh` | Injects `using-agent-skills` meta-skill into every session |
| `PreToolUse` | `sdd-cache-pre.sh`, `simplify-ignore.sh` | Cache revalidation for WebFetch; block-level code protection before edits |
| `PostToolUse` | `sdd-cache-post.sh`, `simplify-ignore.sh` | Cache storage after WebFetch; placeholder expansion after edits |
| `Stop` | `simplify-ignore.sh` | Restore original files, remove placeholders |

**session-start.sh** reads `using-agent-skills/SKILL.md` and injects it with `IMPORTANT` priority via JSON output. Requires `jq`.

**sdd-cache-pre/post.sh** implement a cross-session citation cache for source-driven-development, using ETag/Last-Modified headers and HTTP 304 revalidation.

**simplify-ignore.sh** implements block-level protection: before reading, protected code blocks are replaced with `BLOCK_<hash>` placeholders; after writing, placeholders are expanded back.

### Local Code Evidence

**hooks.json:**
~~~json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
      }]
    }]
  }
}
~~~

**validate-skills.js** (CI validator):
- Checks every SKILL.md has YAML frontmatter with `name` and `description`
- Validates `name` matches directory name
- Validates description <= 1024 characters
- Checks for required sections: Overview, When to Use, Common Rationalizations, Red Flags, Verification
- Warns on dead cross-skill references
- Exempts `using-agent-skills` and `idea-refine` from section checks
- Exit code 0 = pass, 1 = errors

**session-start.sh:** Injects `using-agent-skills` meta-skill content via `jq`-constructed JSON with `IMPORTANT` priority.

### Conclusion for Spec

**Upstream hooks are Claude Code specific** (they use Claude's hook protocol with `${CLAUDE_PLUGIN_ROOT}` and JSON output format). The Agent Zero port cannot directly replicate these hooks because:

1. Agent Zero doesn't have a `SessionStart` hook equivalent -- the system prompt already includes `using-agent-skills` via the plugin's promptinclude mechanism
2. The `sdd-cache` hooks are optimization features (cross-session caching) that could be ported as utility scripts but aren't critical
3. The `simplify-ignore` block protection is an advanced feature that could be ported as a code_execution_tool helper

**validate-skills.js IS worth porting.** The Agent Zero port should have a validation script (Python, since the runtime is Python) that checks:
- SKILL.md exists in every skill directory
- YAML frontmatter has name, description, version, author, tags, triggers
- Required sections present
- Cross-skill references point to existing skills

---

## Q7: WORKDIR STATE VERIFICATION

### Local Code Evidence

```
/a0/usr/workdir/
├── .gitkeep
├── agent_zero_skill_catalog.json     (37KB)
├── all_analysis_messages.txt         (529KB)
├── all_chats_consolidated.txt        (1.1MB)
├── analysis_messages.txt             (274KB)
├── big_chat_erk.txt                  (642KB)
├── harness_component_extraction.json (51KB)
├── key_analysis.txt                  (172KB)
├── last_messages_only.txt            (86KB)
├── security-audit-report-*.md        (15KB)
├── small_chats.txt                   (520KB)
└── venice_utility_model_comparison.md (9KB)
```

- **No `.a0_agent_skills/` directory** exists in workdir
- **No `*.promptinclude.md` files** exist in workdir
- **No plugin state or tracking** in workdir -- only analysis/research artifacts from prior sessions
- The workdir is used as a scratch space for temporary outputs, not for durable plugin state

### Conclusion for Spec

**Workdir is clean with no existing plugin state.** For no-project mode, the spec should define:

1. Plugin state location: `/a0/usr/workdir/.a0_agent_skills/state/` (consistent with memory note)
2. Promptinclude files: could be placed in workdir for no-project mode, but currently none exist
3. The workdir is not a pseudo-project -- it's a general workspace. Plugin state should use a dedicated subdirectory to avoid collision with user files

---

## Summary: Key Spec Implications

| Question | Key Finding | Spec Action Required |
|----------|-------------|---------------------|
| Q1 | Promptinclude supports configurable patterns with token budgets | Decide: rename artifacts vs. extend pattern config |
| Q2 | Knowledge auto-indexing available but currently empty | Decide: save specs/plans to knowledge for semantic recall |
| Q3 | idea-refine.sh is trivial mkdir -p | No script needed; agent uses text_editor directly |
| Q4 | No formal companion-skill system | Document markdown-documents as convention, not enforcement |
| Q5 | Only /ship reads specs; /build, /review, /test do not | Extract ship's spec-reading logic into shared helper |
| Q6 | Hooks are Claude-specific; validate-skills.js is portable | Port validation script to Python; skip hooks |
| Q7 | Workdir is clean, no plugin state | Define .a0_agent_skills/state/ path for no-project mode |
