"""
Skill Telemetry Extension — a0_agent_skills plugin

Fires after every tool execution. If the tool name starts with 'skills_tool',
logs a structured JSON event to the configured log path in the active project
directory.

Configuration keys (default_config.yaml):
  telemetry_enabled: false          # Disabled by default for privacy — set to true to enable
  telemetry_log_path: .a0proj/skill_activations.jsonl  # Relative to project folder
  telemetry_max_lines: 0            # 0 = unlimited; >0 = rotate after N lines
  telemetry_debug: false            # Set to true to enable debug logging

Must never raise — all logic is wrapped in a top-level try/except so that a
telemetry failure cannot affect normal agent operation.
"""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import pathlib
import json
import os
import sys
import time
import threading
import tempfile
from typing import TYPE_CHECKING

from helpers.extension import Extension
from helpers.tool import Response


_log = logging.getLogger(__name__)
_write_lock = threading.Lock()
MAX_ROTATION_READ = 100_000


def _bootstrap_plugin_loader():
    if '_plugin_loader' not in sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    return sys.modules['_plugin_loader']


def _get_plugin_config(agent) -> dict:
    try:
        return _bootstrap_plugin_loader().get_plugin_config(agent)
    except Exception:
        return {}


def _config_bool(value) -> bool:
    return _bootstrap_plugin_loader().config_bool(value)


def _reconstruct_tool_info(agent, tool_name: str) -> tuple[str, dict]:
    return _bootstrap_plugin_loader().reconstruct_tool_info(agent, tool_name)


def _resolve_log_path(proj_folder: str, log_rel: str) -> str | None:
    try:
        base = pathlib.Path(proj_folder).resolve()
        candidate = (base / log_rel).resolve()
        candidate.relative_to(base)
        return str(candidate)
    except (ValueError, TypeError, OSError):
        return None


def _resolve_log_file(agent, log_rel: str, cfg: dict) -> str | None:
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
    skill_name: str | None = tool_args.get("skill_name") or None
    action: str | None = tool_args.get("action") or None

    # Privacy-safe query handling: for 'search' action, store only the action
    # type and skill_name — never the freeform query text.
    if action == "search":
        query: str | None = action  # store only the action type, not user text
    else:
        raw_query = tool_args.get("query") or None
        query: str | None = str(raw_query)[:200] if raw_query else None

    entry = {
        "ts": time.time_ns() / 1e9,
        "tool": full_tool_name,
        "skill_name": skill_name,
        "query": query,
    }
    return json.dumps(entry) + "\n"


def _build_gate_entry(
    tool_name: str,
    mode: str,
    state: str,
    candidate: str | None,
    reason: str | None,
    phase: str | None = None,
) -> str:
    entry = {
        "ts": time.time_ns() / 1e9,
        "event": "gate_decision",
        "tool": tool_name,
        "mode": mode,
        "state": state,
        "candidate": candidate,
        "reason": reason,
    }
    if phase is not None:
        entry["phase"] = phase
    return json.dumps(entry) + "\n"


async def log_gate_decision(
    agent,
    tool_name: str,
    mode: str,
    state: str,
    candidate: str | None = None,
    reason: str | None = None,
    phase: str | None = None,
) -> None:
    try:
        cfg = _get_plugin_config(agent)

        if not _config_bool(cfg.get("telemetry_enabled", False)):
            return

        log_rel = (
            cfg.get("telemetry_log_path")
            or ".a0proj/skill_activations.jsonl"
        )
        log_path = _resolve_log_file(agent, log_rel, cfg)
        if not log_path:
            return

        line = _build_gate_entry(tool_name, mode, state, candidate, reason, phase)
        max_lines: int = int(cfg.get("telemetry_max_lines", 0))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, _write_log_line, log_path, line, max_lines,
        )
    except Exception:
        pass


class SkillTelemetry(Extension):

    async def execute(
        self,
        response: "Response | None" = None,
        tool_name: "str | None" = None,
        **kwargs,
    ) -> None:
        cfg = {}
        try:
            if not tool_name or not tool_name.startswith("skills_tool"):
                return

            cfg = _get_plugin_config(self.agent)
            if not _config_bool(cfg.get("telemetry_enabled", False)):
                return

            full_tool_name, tool_args = _reconstruct_tool_info(
                self.agent, tool_name
            )

            log_rel = (
                cfg.get("telemetry_log_path")
                or ".a0proj/skill_activations.jsonl"
            )
            log_path = _resolve_log_file(self.agent, log_rel, cfg)
            if not log_path:
                return

            line = _build_entry(full_tool_name, tool_args, response)
            max_lines: int = int(cfg.get("telemetry_max_lines", 0))
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, _write_log_line, log_path, line, max_lines,
            )

        except Exception:
            self._debug_log(cfg, "Telemetry execution failed")

    @staticmethod
    def _debug_log(cfg: dict, message: str) -> None:
        if cfg.get("telemetry_debug", False):
            _log.debug(message)


def _write_log_line(log_path: str, line: str, max_lines: int) -> None:
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True, mode=0o750)

    _fcntl = None
    try:
        import fcntl as _fcntl_mod
        _fcntl = _fcntl_mod
    except ImportError:
        _log.warning("fcntl unavailable — telemetry rotation lacks cross-process locking")

    with _write_lock:
        if max_lines > 0 and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as fh:
                    if _fcntl:
                        try:
                            _fcntl.flock(fh.fileno(), _fcntl.LOCK_EX)
                        except OSError:
                            pass
                    lines = fh.readlines()[:MAX_ROTATION_READ]
                line_count = len(lines)
                if line_count >= max_lines:
                    keep = lines[max_lines // 2 :]
                    tmp_fd, tmp_path = tempfile.mkstemp(dir=log_dir)
                    try:
                        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                            fh.writelines(keep)
                        os.replace(tmp_path, log_path)
                    except Exception:
                        os.unlink(tmp_path)
                        raise
            except Exception:
                pass

        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o640)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(line)
