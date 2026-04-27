# tools/lifecycle.py - Lifecycle tool for a0_agent_skills v0.3.0
#
# Tool dispatcher routing to _<method> handlers.
# Only 3 methods: init, status, archive.
# Phase advance is done by agent editing state.md frontmatter directly.

from __future__ import annotations

import re
from pathlib import Path

# Plugin root must be on sys.path for `from lib.xxx` imports when loaded via importlib
import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parent.parent)
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from lib.constants import (
    CONTEXT_KEY_LIFECYCLE_STATE,
    CONTEXT_KEY_LIFECYCLE_STATE_MTIME,
    CONTEXT_KEY_LIFECYCLE_STRIKE_TRACKER,
    CONTEXT_KEY_STRIKE_BLOCKED,
    CONTEXT_KEY_LIFECYCLE_GATE_WARNINGS,
    CONTEXT_KEY_LIFECYCLE_ACTIONS_SINCE_FINDING,
    PHASE_ICONS,
    PHASE_ICON_DEFAULT,
)
from lib.lifecycle_state import LifecycleState, Phase
from lib.finding_utils import _is_trusted_finding

from helpers.tool import Tool, Response

try:
    from helpers.errors import RepairableException
except ImportError:
    RepairableException = ValueError

_SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')

# The 7 hardcoded lifecycle phases
DEFAULT_PHASES = ["IDEA", "SPEC", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"]

# Valid methods for the lifecycle tool
VALID_METHODS = ["init", "status", "archive"]


def _validate_slug(slug: str) -> None:
    """Validate slug: lowercase alphanumeric + hyphens, 1-64 chars, no leading hyphen."""
    if not _SLUG_RE.match(slug):
        raise RepairableException(
            f"Invalid slug '{slug}'. "
            "Must be 1-64 lowercase alphanumeric characters or hyphens, "
            "starting with alphanumeric."
        )

def _to_bool(val, default=True):
    """Coerce a value to bool, handling strings like 'true'/'1'/'yes'."""
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val) if val is not None else default



class Lifecycle(Tool):
    """Lifecycle-spanning state anchor tool.

    Methods: init, status, archive.
    Phase advance is done by agent editing state.md frontmatter.
    State is persisted to .a0proj/run/current/ via LifecycleState.
    """

    async def execute(self, **kwargs):
        """Dispatch to _<method> handler based on self.method."""
        method = self.method or ""

        handler = getattr(self, f"_{method}", None)
        if handler is None:
            valid = ", ".join(VALID_METHODS)
            raise RepairableException(
                f"Unknown lifecycle method '{method}'. Valid methods: {valid}"
            )

        return await handler(**kwargs)

    # ------------------------------------------------------------------
    # _init - Create a new lifecycle
    # ------------------------------------------------------------------

    async def _init(self, **kwargs):
        """Initialize a new lifecycle with hardcoded 7 phases.

        Args (from self.args):
            goal: Lifecycle goal (>= 20 chars)
            slug: URL-safe lifecycle identifier
            project_root: Optional path override

        No phases param - 7 phases are hardcoded: IDEA through SHIP.
        No template param - templates removed in v0.3.0.
        """
        goal = self.args.get("goal", "")
        slug = self.args.get("slug", "unnamed-lifecycle")
        _validate_slug(slug)

        # Resolve lifecycle directory
        plan_dir = self._resolve_lifecycle_dir()

        # Create lifecycle state with hardcoded phases
        state = LifecycleState.create(
            goal=goal,
            phases=DEFAULT_PHASES,
            slug=slug,
            plan_dir=plan_dir,
        )

        # Cache in context
        self.agent.context.data[CONTEXT_KEY_LIFECYCLE_STATE] = state
        self.agent.context.data[CONTEXT_KEY_LIFECYCLE_STATE_MTIME] = None

        return Response(
            message=state.summary(),
            break_loop=False,
        )

    # ------------------------------------------------------------------
    # _status - Show current lifecycle status
    # ------------------------------------------------------------------

    async def _status(self, **kwargs):
        """Return the 5-Question Reboot Test answer.

        When no lifecycle exists, returns a friendly "no active lifecycle" message.
        """
        plan_dir = self._resolve_lifecycle_dir()
        state = LifecycleState.load(plan_dir=plan_dir, context=self.agent.context)

        if state is None:
            return Response(
                message="No active lifecycle. Use `lifecycle:init` to create one.",
                break_loop=False,
            )

        lines = []

        # Where am I?
        idx = state.current_phase_index
        if state.phases and idx < len(state.phases):
            current = state.phases[idx]
            icon = PHASE_ICONS.get(current.status, PHASE_ICON_DEFAULT)
            lines.append(f"Current: {icon} {current.title} ({current.status})")
        else:
            lines.append("Current: All phases complete")

        # Goal
        lines.append(f"Goal: {state.goal}")

        # What's done?
        completed = [p for p in state.phases if p.status == "completed"]
        lines.append(f"Done: {len(completed)}/{len(state.phases)} phases")

        # Phase overview
        lines.append("")
        lines.append("Phases:")
        lines.extend(state.render_phase_list())

        # Findings count
        findings_count = state.count_findings()
        lines.append("")
        lines.append(f"Findings: {findings_count} logged")

        return Response(
            message="\n".join(lines),
            break_loop=False,
        )

    # ------------------------------------------------------------------
    # _archive - Archive a lifecycle (completed or abandoned)
    # ------------------------------------------------------------------

    async def _archive(self, **kwargs):
        """Archive the current lifecycle.

        For completed: promotes trusted findings to docs/adr/, cleans up.
        For abandoned: writes brief to docs/ideas/, cleans up.

        Args (from self.args):
            status: 'completed' | 'abandoned' (default: 'completed')
            promote_adrs: bool (default: true)
            reason: Optional reason for abandoned
            slug: Optional slug override
        """
        status = self.args.get("status", "completed")
        promote_adrs = _to_bool(self.args.get("promote_adrs", True))
        reason = self.args.get("reason", "")
        slug_override = self.args.get("slug", None)
        emit_spec = _to_bool(self.args.get("emit_spec", False))

        valid_statuses = {"completed", "abandoned"}
        if status not in valid_statuses:
            valid = ", ".join(sorted(valid_statuses))
            raise RepairableException(
                f"Invalid archive status '{status}'. Must be one of: {valid}"
            )

        plan_dir = self._resolve_lifecycle_dir()
        state = self._load_or_raise(plan_dir)

        slug = slug_override or state.slug
        _validate_slug(slug)

        if status == "abandoned":
            project_root = self._resolve_project_root()
            ideas_dir = project_root / "docs" / "ideas"
            ideas_dir.mkdir(parents=True, exist_ok=True)
            brief_path = ideas_dir / f"{slug}-abandoned.md"
            brief_content = state.render_abandoned_brief(reason=reason)
            brief_path.write_text(brief_content, encoding="utf-8")
            state.cleanup()
            self._clear_lifecycle_cache()
            return Response(
                message=f"Lifecycle abandoned: {slug}\nBrief written to docs/ideas/{slug}-abandoned.md",
                break_loop=False,
            )

        # Completed path
        if promote_adrs:
            self._promote_adrs(state)

        # Emit SPEC.md if requested
        spec_path = None
        if emit_spec:
            spec_path = self._emit_spec(state)

        state.cleanup()
        self._clear_lifecycle_cache()

        msg = f"Lifecycle archived as completed: {slug}."
        if spec_path:
            msg += f"\nSPEC.md written to {spec_path}"
        return Response(message=msg, break_loop=False)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _promote_adrs(self, state) -> None:
        """Promote trusted findings to ADR files in docs/adr/."""
        project_root = self._resolve_project_root()
        adr_dir = project_root / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)

        findings_path = state.plan_dir / "findings.md"
        if not findings_path.exists():
            return

        content = findings_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        trusted = [l.strip() for l in lines if _is_trusted_finding(l)]

        if not trusted:
            return

        nums = [int(p.stem.split("-", 1)[0]) for p in adr_dir.glob("*.md") if p.stem.split("-", 1)[0].isdigit()]
        next_num = max(nums, default=0) + 1

        for finding in trusted:
            title = finding[:80]
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]
            if not slug:
                slug = "adr"
            num = f"{next_num:04d}"
            adr_path = adr_dir / f"{num}-{slug}.md"
            adr_content = (
                f"# {title}\n\n"
                f"**Status:** Accepted\n\n"
                f"## Context\n\n"
                f"Finding from lifecycle: {state.goal}\n\n"
                f"## Decision\n\n"
                f"{finding}\n"
            )
            adr_path.write_text(adr_content, encoding="utf-8")
            next_num += 1

    def _load_or_raise(self, plan_dir):
        """Load lifecycle state or raise if none exists."""
        state = LifecycleState.load(plan_dir=plan_dir, context=self.agent.context)
        if state is None:
            raise RepairableException(
                "No active lifecycle. Call lifecycle:init first."
            )
        return state

    def _resolve_lifecycle_dir(self):
        """Resolve the lifecycle directory from project context."""
        try:
            from helpers import projects
            project_name = projects.get_context_project_name(self.agent.context)
            if project_name:
                project_folder = projects.get_project_folder(project_name)
                return Path(project_folder, ".a0proj", "run", "current")
        except (ImportError, Exception):
            pass
        return LifecycleState._get_fallback_dir()

    def _resolve_project_root(self):
        """Resolve the project root directory."""
        try:
            from helpers import projects
            project_name = projects.get_context_project_name(self.agent.context)
            if project_name:
                project_folder = projects.get_project_folder(project_name)
                return Path(project_folder)
        except (ImportError, Exception):
            pass
        plan_dir = self._resolve_lifecycle_dir()
        current = plan_dir
        while current != current.parent:
            if (current / ".a0proj").exists():
                return current
            current = current.parent
        return plan_dir.parent.parent

    def _emit_spec(self, state) -> "Path | None":
        """Generate SPEC.md from lifecycle state before archiving."""
        project_root = self._resolve_project_root()
        spec_path = project_root / "SPEC.md"

        # Read findings
        findings_path = state.plan_dir / "findings.md"
        findings_content = ""
        if findings_path.exists():
            findings_content = findings_path.read_text(encoding="utf-8").strip()

        # Build phase summary
        completed = [p for p in state.phases if p.status == "completed"]
        phase_lines = []
        for p in state.phases:
            icon = PHASE_ICONS.get(p.status, PHASE_ICON_DEFAULT)
            phase_lines.append(f"- {icon} {p.title} ({p.status})")

        # Build SPEC content
        lines = [
            f"# Specification: {state.goal}",
            "",
            f"**Generated from lifecycle:** {state.slug}",
            "",
            "## Completed Phases",
            "",
        ]
        lines.extend(phase_lines)
        lines.extend([
            "",
            f"**Progress:** {len(completed)}/{len(state.phases)} phases completed",
            "",
        ])

        if findings_content:
            lines.extend([
                "## Findings Summary",
                "",
                findings_content,
                "",
            ])

        spec_path.write_text("\n".join(lines), encoding="utf-8")
        return spec_path

    def _clear_lifecycle_cache(self) -> None:
        """Clear the lifecycle state cache after archiving."""
        self.agent.context.data.pop(CONTEXT_KEY_LIFECYCLE_STATE, None)
        self.agent.context.data.pop(CONTEXT_KEY_LIFECYCLE_STATE_MTIME, None)
