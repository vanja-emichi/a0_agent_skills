# extensions/python/tool_execute_after/_30_lifecycle_auto_progress.py
#
# Auto-progress nudge: after 2 file-mutating tool calls without a
# lifecycle:status, appends a gentle reminder to lifecycle_gate_warnings.
# Counter persisted to auto_progress.json for compaction survival.

from __future__ import annotations

import json
import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from helpers.print_style import PrintStyle

from lib.extension_base import LifecycleExtension

# Tools that mutate files on disk
FILE_MUTATING_TOOLS = frozenset({
    "code_execution_tool",
    "text_editor:write",
    "text_editor:patch",
    "text_editor_remote",
})

COUNTER_KEY = "lifecycle_actions_since_finding"
WARNINGS_KEY = "lifecycle_gate_warnings"
LAST_ACTION_KEY = "lifecycle_auto_progress_last_action"
NUDGE_MSG = "Consider calling lifecycle:status to record what you've learned."
NUDGE_THRESHOLD = 2
AUTO_PROGRESS_FILENAME = "auto_progress.json"


class PlanAutoProgress(LifecycleExtension):
    """After file-mutating tool calls, track a 2-action counter.

    When the counter reaches 2 without a lifecycle:status call, nudge the
    agent by appending a warning to context.data["lifecycle_gate_warnings"].
    lifecycle:status resets the counter (see tools/plan.py).

    Counter is persisted to auto_progress.json in the lifecycle plan_dir
    so it survives context compaction.
    """

    def _get_counter_file(self) -> _Path | None:
        """Resolve the auto_progress.json file path from lifecycle dir."""
        plan_dir = self._resolve_lifecycle_dir()
        if plan_dir is None:
            return None
        return plan_dir / AUTO_PROGRESS_FILENAME

    def _read_counter_from_file(self) -> int:
        """Read persisted counter from auto_progress.json."""
        counter_file = self._get_counter_file()
        if counter_file is None or not counter_file.exists():
            return 0
        try:
            data = json.loads(counter_file.read_text(encoding="utf-8"))
            return data.get("counter", 0)
        except (json.JSONDecodeError, OSError):
            return 0

    def _write_counter_to_file(self, count: int) -> None:
        """Persist counter to auto_progress.json."""
        counter_file = self._get_counter_file()
        if counter_file is None:
            return
        try:
            counter_file.parent.mkdir(parents=True, exist_ok=True)
            counter_file.write_text(
                json.dumps({"counter": count}),
                encoding="utf-8"
            )
        except OSError:
            pass  # Best-effort persistence

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except Exception as exc:
            # Never raises — auto-logger is a sink
            PrintStyle.error(f"[plan-auto-progress] unexpected error: {exc}")

    async def _run(self, **kwargs):
        tool_name: str = kwargs.get("tool_name", "")

        # Only act on file-mutating tools
        if tool_name not in FILE_MUTATING_TOOLS:
            return

        # No state = no-op
        state = self._load_lifecycle()
        if state is None:
            return

        # Derive file path from current_tool for de-duplication
        file_path: str = ""
        try:
            current_tool = self.agent.loop_data.current_tool
            if current_tool and current_tool.args:
                file_path = current_tool.args.get("path", "")
        except (AttributeError, TypeError):
            pass

        # De-duplication: skip if same tool+path fired consecutively
        data = self.agent.context.data
        action_id = f"{tool_name}:{file_path}"
        last_action = data.get(LAST_ACTION_KEY, "")
        if action_id == last_action:
            return
        data[LAST_ACTION_KEY] = action_id

        # Read counter: prefer context.data, fall back to file
        count = data.get(COUNTER_KEY, None)
        if count is None:
            count = self._read_counter_from_file()

        count += 1
        data[COUNTER_KEY] = count

        # Persist to file
        self._write_counter_to_file(count)

        if count >= NUDGE_THRESHOLD:
            # Nudge: add warning
            data.setdefault(WARNINGS_KEY, []).append(NUDGE_MSG)
            # Reset counter so we don't nudge on every subsequent action
            data[COUNTER_KEY] = 0
            self._write_counter_to_file(0)
