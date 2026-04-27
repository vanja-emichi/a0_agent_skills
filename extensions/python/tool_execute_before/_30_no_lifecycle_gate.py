# extensions/python/tool_execute_before/_30_no_lifecycle_gate.py — tool_execute_before hook
#
# Fires before write/code tools execute.
# When no lifecycle exists in .a0proj/run/current/, applies gate behaviour
# configured via plugin config planning.gates.no_plan (off / nudge / block).
#
# Heuristic: skip the gate for short, casual messages (<200 chars AND
# no trigger keywords like implement, build, design, etc.).

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from helpers.print_style import PrintStyle
from helpers import plugins, projects
from helpers.errors import RepairableException

from lib.extension_base import LifecycleExtension
from lib.lifecycle_state import LifecycleState

PLUGIN_NAME = "a0_agent_skills"

GATED_TOOLS = {"text_editor:write", "text_editor:patch", "code_execution_tool", "call_subordinate"}

TRIGGER_KEYWORDS = frozenset({
    "implement", "build", "design", "architect", "refactor", "migrate",
})


def _resolve_lifecycle_dir(agent) -> _Path | None:
    """Resolve the plan directory from project context."""
    project_name = projects.get_context_project_name(agent.context)
    if project_name:
        project_folder = projects.get_project_folder(project_name)
        return _Path(project_folder, ".a0proj", "run", "current")
    return LifecycleState._get_fallback_dir()


def _get_user_message_text(agent) -> str:
    """Extract the last user message as plain text for heuristic matching."""
    if agent is None:
        return ""
    msg = getattr(agent, "last_user_message", None)
    if msg is None:
        return ""
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    # Fallback: use output_text() for complex content types
    output_fn = getattr(msg, "output_text", None)
    if callable(output_fn):
        return output_fn()
    return str(content)


def _should_skip_heuristic(agent) -> bool:
    """Return True if the current user message is short and casual
    (no trigger keywords), meaning the gate should be skipped."""
    text = _get_user_message_text(agent)
    if len(text) >= 200:
        return False  # Long message — always apply gate
    # Short message: skip gate only if no trigger keywords present
    lower = text.lower()
    return not any(kw in lower for kw in TRIGGER_KEYWORDS)


def _get_gate_mode(agent) -> str:
    """Read the gate mode from plugin config. Defaults to 'nudge'."""
    config = plugins.get_plugin_config(PLUGIN_NAME, agent=agent)
    if not config:
        return "nudge"
    return (
        config
        .get("planning", {})
        .get("gates", {})
        .get("no_plan", "nudge")
    )


class NoPlanGate(LifecycleExtension):
    """Gate that warns or blocks write/code tools when no lifecycle exists."""

    # Override to delegate to module-level function (test-mockable)
    def _resolve_lifecycle_dir(self) -> _Path | None:
        return _resolve_lifecycle_dir(self.agent)

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except RepairableException:
            raise  # Propagate to abort the tool call
        except Exception as exc:
            PrintStyle.error(f"[no-lifecycle-gate] unexpected error: {exc}")

    async def _run(self, **kwargs):
        tool_name: str = kwargs.get("tool_name", "")

        # Only gate write/code tools
        if tool_name not in GATED_TOOLS:
            return

        # Determine gate mode
        mode = _get_gate_mode(self.agent)

        # Off mode: complete no-op
        if mode == "off":
            return

        # Check if lifecycle exists
        lifecycle_dir = self._resolve_lifecycle_dir()
        if lifecycle_dir is not None and (lifecycle_dir / "state.md").exists():
            return  # Plan exists — always pass through

        # Apply heuristic: skip gate for short/casual messages
        if _should_skip_heuristic(self.agent):
            return

        # Gate is triggered — apply configured behaviour
        warning_msg = (
            f"[no-lifecycle-gate] No active lifecycle found. "
            f"Tool '{tool_name}' was called without a plan. "
            f"Consider calling lifecycle:init first."
        )

        if mode == "nudge":
            PrintStyle.warning(warning_msg)
            if self.agent and hasattr(self.agent, "context"):
                self.agent.context.data.setdefault(
                    "lifecycle_gate_warnings", []
                ).append(warning_msg)
            return  # Let the tool execute

        if mode == "block":
            raise RepairableException(
                "No active lifecycle. Call lifecycle:init with goal and phases, or use /plan."
            )
