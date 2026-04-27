# extensions/python/_functions/agent/Agent/handle_exception/end/_55_lifecycle_strike_tracker.py
#
# Watches for RepairableException results and counts per-error occurrences.
# When any single error reaches >= 3 strikes, gates the response.
#
# Hook point: handle_exception/end — the only hook that fires on RepairableException.
# tool_execute_after only fires on successful execution.

from __future__ import annotations

import hashlib

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[7])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from agent import LoopData

from lib.extension_base import LifecycleExtension
from lib.strike_tracker import StrikeTracker


def _error_hash(error_message: str) -> str:
    """Generate a stable hash for an error message."""
    return hashlib.md5(error_message.encode()).hexdigest()[:12]


class LifecycleStrikeTracker(LifecycleExtension):
    """Track tool errors via RepairableException results and gate after 3 strikes."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        # Check if this is a RepairableException result
        # The handle_exception hook fires when a tool execution raises
        # We inspect the current message/result for error indicators
        try:
            lifecycle_dir = self._resolve_lifecycle_dir()
        except Exception:
            return

        if lifecycle_dir is None:
            return

        # Extract error message from the exception context
        error_msg = self._extract_error_message(loop_data, **kwargs)
        if not error_msg:
            return

        # Record the strike
        tracker = StrikeTracker.rehydrate(lifecycle_dir)
        err_hash = _error_hash(error_msg)
        tracker.record(err_hash)
        tracker.persist(lifecycle_dir)

        # Store in context for the response gate to check
        strike_count = tracker.get_count(err_hash)
        self.agent.context.data["lifecycle_strike_tracker"] = tracker
        self.agent.context.data["lifecycle_last_error_hash"] = err_hash
        self.agent.context.data["lifecycle_last_strike_count"] = strike_count

        # If strike count >= 3, set the blocked flag
        if tracker.should_block(err_hash):
            self.agent.context.data["lifecycle_strike_blocked"] = True

    def _extract_error_message(self, loop_data, **kwargs) -> str | None:
        """Extract error message from A0's @extensible data dict.

        A0's @extensible decorator passes data as:
            kwargs = {"data": {"args": tuple, "kwargs": dict,
                               "result": ..., "exception": BaseException | None}}
        The exception lives at kwargs['data']['exception'].
        """
        # A0's @extensible decorator passes a nested 'data' dict
        data = kwargs.get("data", {})

        # Primary path: exception from data['exception'] (A0's actual format)
        if isinstance(data, dict):
            exc = data.get("exception")
            if exc is not None:
                return str(exc)

        return None
