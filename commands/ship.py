"""ship — Pre-launch parallel review orchestrator.

Spawns three specialist agents (code-reviewer, security-auditor, test-engineer)
concurrently via call_subordinate_parallel, collects their reports, then asks
the main agent to merge findings into a single GO / NO-GO decision with a
rollback plan.

Reads the project spec to determine the actual code directory and files to
review, ensuring specialists focus on the correct codebase.

Returns a text prompt injected into the main agent's context window.
"""
from __future__ import annotations

import os
import re
import json
from typing import Any


# ---------------------------------------------------------------------------
# Spec-driven context resolution
# ---------------------------------------------------------------------------


def _find_spec(project_path: str) -> str | None:
    """Find the first spec file in the project's docs/specs/ directory."""
    specs_dir = os.path.join(project_path, "docs", "specs")
    if not os.path.isdir(specs_dir):
        return None
    for name in sorted(os.listdir(specs_dir)):
        if name.endswith("-spec.md"):
            return os.path.join(specs_dir, name)
    return None


def _parse_project_structure(spec_content: str) -> dict[str, Any]:
    """Parse the Project Structure section from a spec file.

    Extracts:
        root: the directory root (e.g. 'plugins/a0_agent_skills')
        files: list of (relative_path, description) tuples from the tree
    """
    result: dict[str, Any] = {"root": "", "files": []}

    ps_match = re.search(
        r"##\s*Project Structure\s*\n(.*?)(?=\n##|\Z)",
        spec_content,
        re.DOTALL,
    )
    if not ps_match:
        return result

    section = ps_match.group(1)

    # Extract the root directory from the first line of the code block
    code_match = re.search(r"```\n([^\s\n]+/)", section)
    if code_match:
        result["root"] = code_match.group(1).strip().rstrip("/")

    # Parse the tree to reconstruct full paths
    # Each nesting level adds 4 chars (├── or │   or └── or    )
    # depth = indent // 4, files live at dir_stack[:depth]
    dir_stack: list[str] = []

    for line in section.splitlines():
        # Check for directory entry: '...dirname/'
        dir_match = re.search(r"([├└│─\s]+)([\w/\-]+)/\s*$", line)
        if dir_match:
            indent = len(dir_match.group(1))
            dir_name = dir_match.group(2)
            depth = indent // 4
            dir_stack = dir_stack[: max(depth - 1, 0)]
            dir_stack.append(dir_name)
            continue

        # Check for file entry with description: '...file.py  ← description'
        file_match = re.search(r"([├└│─\s]+)([\w/\-]+\.\w+)\s*←\s*(.+)", line)
        if not file_match:
            file_match = re.search(r"([├└│─\s]+)([\w/\-]+\.\w+)\s*$", line)
        if file_match:
            indent = len(file_match.group(1))
            filename = file_match.group(2)
            desc = file_match.group(3).strip() if file_match.lastindex and file_match.lastindex >= 3 else ""
            depth = indent // 4
            parent_stack = dir_stack[:depth]
            rel_path = "/".join(parent_stack + [filename]) if parent_stack else filename
            result["files"].append((rel_path, desc))

    return result


def _resolve_code_path(project_path: str, spec_root: str) -> str:
    """Resolve the spec root directory to an absolute filesystem path.

    For 'plugins/X' roots, uses Agent Zero's plugin resolution to find
    the actual directory. For other roots, resolves relative to the
    project workspace.
    """
    if spec_root.startswith("plugins/"):
        plugin_name = spec_root[len("plugins/"):]
        try:
            from helpers.plugins import get_plugin_roots
            for root in get_plugin_roots(plugin_name):
                if os.path.isdir(root):
                    return root
        except Exception:
            pass
        # Fallback: resolve relative to project workspace
        return os.path.join(project_path, spec_root)

    # Default: resolve relative to project workspace
    return os.path.join(project_path, spec_root)


def _read_spec_context(project_path: str) -> dict[str, str]:
    """Read the project spec to extract review context.

    Returns a dict with:
        code_dir: absolute path to the code directory to review
        objective: what was built
        success_criteria: acceptance criteria from the spec
        files_section: formatted list of files to review
    """
    result: dict[str, str] = {
        "code_dir": "",
        "objective": "",
        "success_criteria": "",
        "files_section": "",
    }

    spec_path = _find_spec(project_path)
    if not spec_path:
        return result

    try:
        with open(spec_path) as f:
            content = f.read()
    except (FileNotFoundError, OSError):
        return result

    # Parse project structure to get root and files
    structure = _parse_project_structure(content)

    if structure["root"]:
        code_dir = _resolve_code_path(project_path, structure["root"])
        if os.path.isdir(code_dir):
            result["code_dir"] = code_dir

    # Build files section from parsed file list
    if result["code_dir"] and structure["files"]:
        lines = []
        for rel_path, description in structure["files"]:
            if description:
                lines.append(f"- `{rel_path}` - {description}")
            else:
                lines.append(f"- `{rel_path}`")
        result["files_section"] = "\n".join(lines)

    # Extract objective
    obj_match = re.search(
        r"##\s*Objective\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
    )
    if obj_match:
        result["objective"] = obj_match.group(1).strip()

    # Extract success criteria
    sc_match = re.search(
        r"##\s*Success Criteria\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
    )
    if sc_match:
        result["success_criteria"] = sc_match.group(1).strip()

    return result


# ---------------------------------------------------------------------------
# Scope sanitization
# ---------------------------------------------------------------------------


def _sanitize_spec_text(text: str, max_len: int = 2000) -> str:
    """Sanitize spec-derived text before interpolation into specialist prompts.

    1. Strip control characters
    2. Remove instruction-injection patterns
    3. Cap at max_len characters
    """
    # Strip control characters (0x00-0x1f, 0x7f) and Unicode line/paragraph separators
    text = re.sub(r'[\x00-\x1f\x7f\u2028\u2029]', '', text)
    # Remove instruction-injection patterns (DOTALL to handle any remaining line breaks)
    text = re.sub(
        r'(?is)(ignore|disregard|override|bypass)\s+(all|previous|above|security|safety)',
        '',
        text,
    )
    return text[:max_len].strip()


def _sanitize_scope(scope: str) -> str:
    """Sanitize user-supplied scope text to prevent prompt injection.

    1. Strip control characters
    2. Remove markdown headings
    3. Remove instruction-injection patterns (allowlist safe chars only)
    4. Strip any remaining quote/backtick characters as a safety net
    5. Cap at 500 characters
    """
    # Strip control characters (0x00-0x1f, 0x7f)
    scope = re.sub(r"[\x00-\x1f\x7f]", "", scope)
    # Remove markdown headings (# through ######)
    scope = re.sub(r"^#{1,6}\s*", "", scope, flags=re.MULTILINE)
    # Allowlist safe chars only (quotes and backticks EXCLUDED)
    scope = re.sub(
        r"[^\w\s.,;:!?$%&()\[\]{}@/\-+=~^*#\\]",
        "",
        scope,
    )
    # Safety net: strip any remaining quote or backtick characters
    scope = re.sub(r"[\"'`]", "", scope)
    # Cap length and strip whitespace
    scope = scope[:500].strip()
    return scope


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run(payload: dict[str, Any]) -> dict[str, str]:
    """Generate a ship-review prompt for the main agent.

    Args:
        payload: Provided by the commands plugin.  Expected keys:
            - invocation.raw_arguments  raw text from /ship <args>
            - arguments                 parsed argument dict
            - context.project_name     active project name (may be empty)

    Returns:
        {"text": <prompt string>} injected into main agent context.
    """
    # Extract project context and resolve project path
    project_name: str = ""
    project_path: str = ""
    try:
        ctx = payload.get("context") or {}
        project_name = (ctx.get("project_name") or "").strip()
        if project_name:
            from helpers import projects as proj_helper
            resolved = proj_helper.get_project_folder(project_name)
            if os.path.isdir(resolved):
                project_path = resolved
    except Exception:
        pass

    # Read spec to determine code directory and design context
    spec = _read_spec_context(project_path) if project_path else {}
    code_dir = spec.get("code_dir", "")

    # Build specialist preamble with spec-derived context
    specialist_context = ""
    if code_dir:
        files_section = spec.get("files_section", "")
        objective = spec.get("objective", "")
        success_criteria = spec.get("success_criteria", "")

        specialist_context = f"You are reviewing code under `{code_dir}/`.\n\n"
        if files_section:
            specialist_context += f"**Files to review:**\n{_sanitize_spec_text(files_section)}\n\n"
        if objective:
            specialist_context += f"**What was built:** {_sanitize_spec_text(objective)}\n\n"
        if success_criteria:
            specialist_context += f"**Success criteria:**\n{_sanitize_spec_text(success_criteria)}\n\n"

        project_file_scope = f"Focus on files under {code_dir}/."
    else:
        project_file_scope = (
            f"Focus on files under {project_path}."
            if project_path
            else "Review all recent changes."
        )

    # Escape specialist_context for safe JSON interpolation
    specialist_context_safe = json.dumps(specialist_context)[1:-1]

    # Build project scope line
    project_scope = ""
    if project_path:
        project_scope = f"\n**Project root:** `{project_path}`"
        if project_name:
            project_scope += f"\n**Project:** {project_name}"
    if code_dir:
        project_scope += f"\n**Code directory:** `{code_dir}/`"

    # Extract optional scope / PR description from invocation
    invocation = payload.get("invocation") or {}
    scope = (invocation.get("raw_arguments") or "").strip()

    # Security: scope comes from the /ship CLI argument in a single-user local
    # deployment. Sanitize to limit prompt injection surface.
    scope = _sanitize_scope(scope)
    scope_line = f"\n**Scope:**\n```\n{scope}\n```\n" if scope else ""
    def _scope_desc(verb: str) -> str:
        if scope:
            return f"Scope: {scope}. {project_file_scope}"
        return f"{project_file_scope} {verb} all files listed above."

    scope_desc_review = _scope_desc("Review")
    scope_desc_audit = _scope_desc("Audit")
    scope_desc_coverage = _scope_desc("Analyze test coverage for")

    # Load prompt template from file
    _template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "prompts", "ship_review.md",
    )
    _template_path = os.path.normpath(_template_path)
    with open(_template_path, "r", encoding="utf-8") as _tf:
        prompt = _tf.read().format(
            scope_line=scope_line,
            project_scope=project_scope,
            specialist_context_safe=specialist_context_safe,
            scope_desc_review=scope_desc_review,
            scope_desc_audit=scope_desc_audit,
            scope_desc_coverage=scope_desc_coverage,
        )
    return {"text": prompt.strip()}
