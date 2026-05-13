"""
Skill Telemetry Extension — a0_agent_skills plugin

Fires after every tool execution. If the tool name starts with 'skills_tool',
logs a structured JSON event to the configured log path in the active project
directory.

Configuration keys (default_config.yaml):
  telemetry_enabled: true           # Enabled by default — set to false to disable
  telemetry_log_path: .a0proj/skill_activations.jsonl  # Relative to project folder
  telemetry_max_lines: 0            # 0 = unlimited; >0 = rotate after N lines
  telemetry_debug: false            # Set to true to enable debug logging

Must never raise — all logic is wrapped in a top-level try/except so that a
telemetry failure cannot affect normal agent operation.
"""

from __future__ import annotations

import asyncio
import logging
import pathlib
import json
import os
import time
import threading
import tempfile
from typing import TYPE_CHECKING

from helpers.extension import Extension
from helpers.tool import Response


_log = logging.getLogger(__name__)
_write_lock = threading.Lock()
MAX_ROTATION_READ = 100_000


def _resolve_log_path(proj_folder: str, log_rel: str) -> str | None:
    """Resolve log_rel relative to proj_folder, rejecting path traversal.

    Returns None if log_rel is absolute or attempts to escape proj_folder.
    """
    try:
        base = pathlib.Path(proj_folder).resolve()
        candidate = (base / log_rel).resolve()
        candidate.relative_to(base)  # raises ValueError if outside base
        return str(candidate)
    except (ValueError, TypeError, OSError):
        return None


def _get_plugin_config(agent) -> dict:
    """Read plugin config, returning empty dict on any failure."""
    try:
        from helpers import plugins as _plugins
        return _plugins.get_plugin_config("a0_agent_skills", agent=agent) or {}
    except Exception:
        return {}


def _reconstruct_tool_info(agent, tool_name: str) -> tuple[str, dict]:
    """Reconstruct full tool name (base:method) and args from loop_data.

    Returns (full_tool_name, tool_args).
    """
    full_tool_name = tool_name
    tool_args: dict = {}
    try:
        if agent and hasattr(agent, "loop_data") and agent.loop_data:
            current_tool = agent.loop_data.current_tool
            if current_tool is not None:
                if current_tool.method:
                    full_tool_name = f"{tool_name}:{current_tool.method}"
                tool_args = current_tool.args or {}
    except Exception:
        pass
    return full_tool_name, tool_args


def _resolve_log_file(agent, log_rel: str, cfg: dict) -> str | None:
    """Resolve the log file path from project context or agent context dir.

    Tries project folder first, then falls back to agent context data dir.
    """
    # Primary: project-scoped path
    try:
        from helpers import projects as _projects
        if agent and agent.context:
            proj_name = _projects.get_context_project_name(agent.context)
            if proj_name:
                proj_folder = _projects.get_project_folder(proj_name)
                path = _resolve_log_path(proj_folder, log_rel)
                if path:
                    return path
    except Exception:
        pass

    # Fallback: agent context data dir
    try:
        if agent and agent.context:
            ctx_data = getattr(agent.context, "data", {})
            ctx_dir = (
                ctx_data.get("context_dir")
                if isinstance(ctx_data, dict)
                else None
            )
            if ctx_dir:
                if os.path.isabs(ctx_dir):
                    validated = _resolve_log_path(ctx_dir, os.path.basename(log_rel))
                    if validated:
                        return validated
    except Exception:
        pass

    return None


def _build_entry(
    full_tool_name: str,
    tool_args: dict,
    response: "Response | None",
) -> str:
    """Build a JSONL log line from tool call details."""
    skill_name: str | None = tool_args.get("skill_name") or None
    query: str | None = tool_args.get("query") or None

    result_preview: str | None = None
    try:
        if response and response.message:
            result_preview = str(response.message)[:200]
    except Exception:
        pass

    entry = {
        "ts": time.time(),
        "tool": full_tool_name,
        "skill_name": skill_name,
        "query": query,
        "result_preview": result_preview,
    }
    return json.dumps(entry) + "\n"


class SkillTelemetry(Extension):
    """Log skills_tool activations to a project-scoped JSONL file."""

    async def execute(
        self,
        response: "Response | None" = None,
        tool_name: "str | None" = None,
        **kwargs,
    ) -> None:
        cfg = {}
        try:
            # ── Gate: only intercept skills_tool calls ───────────────────
            if not tool_name or not tool_name.startswith("skills_tool"):
                return

            # ── Gate: check telemetry_enabled in plugin config ──────────
            cfg = _get_plugin_config(self.agent)
            enabled = cfg.get("telemetry_enabled", True)
            if isinstance(enabled, str):
                enabled = enabled.lower() in ("true", "1", "yes")
            if not enabled:
                return

            # ── Reconstruct tool name and args ──────────────────────────
            full_tool_name, tool_args = _reconstruct_tool_info(
                self.agent, tool_name
            )

            # ── Resolve log file path ────────────────────────────────────
            log_rel = (
                cfg.get("telemetry_log_path")
                or ".a0proj/skill_activations.jsonl"
            )
            log_path = _resolve_log_file(self.agent, log_rel, cfg)
            if not log_path:
                return

            # ── Build and write log entry ────────────────────────────────
            line = _build_entry(full_tool_name, tool_args, response)
            max_lines: int = int(cfg.get("telemetry_max_lines", 0))
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, _write_log_line, log_path, line, max_lines,
            )

        except Exception:
            # Telemetry MUST NOT break agent operation under any circumstances.
            self._debug_log(cfg, "Telemetry execution failed")

    @staticmethod
    def _debug_log(cfg: dict, message: str) -> None:
        """Emit a debug log if telemetry_debug is enabled in config."""
        if cfg.get("telemetry_debug", False):
            _log.debug(message)


def _write_log_line(log_path: str, line: str, max_lines: int) -> None:
    """Synchronous file write — runs in a thread via run_in_executor.

    If max_lines > 0 and the file already contains >= max_lines entries,
    the oldest half is discarded (simple rotation without external deps).
    """
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True, mode=0o750)

    with _write_lock:
        # Rotation: read existing lines, trim, rewrite, then append.
        if max_lines > 0 and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as fh:
                    existing = fh.readlines()[:MAX_ROTATION_READ]
                if len(existing) >= max_lines:
                    keep = existing[max_lines // 2 :]  # drop oldest half
                    tmp_fd, tmp_path = tempfile.mkstemp(dir=log_dir)
                    try:
                        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                            fh.writelines(keep)
                        os.replace(tmp_path, log_path)
                    except Exception:
                        os.unlink(tmp_path)  # cleanup on failure
                        raise
            except Exception:
                pass  # Rotation failure is non-fatal; we still append below

        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o640)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(line)
