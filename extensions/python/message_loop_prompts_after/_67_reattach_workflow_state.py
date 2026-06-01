"""Reattach Workflow State Extension — a0_agent_skills plugin.

Fires during prompt assembly (after main prompts, before loop). Reads all
.a0proj/state/ files and appends a consolidated context block to the
assembled prompt so the agent sees its prior workflow state after
compaction or session resume.

When state files exist:
- Appends a formatted state block to the prompt
- Injects loaded_skills into agent.data['loaded_skills']

When no state files exist:
- Returns the prompt unmodified

Configuration keys (default_config.yaml):
  workflow_state_enabled: true   # Set to false to disable rehydration

Must never raise — all logic is wrapped in a top-level try/except so that a
rehydration failure cannot affect prompt assembly.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import re
import sys
import time as _time
from typing import TYPE_CHECKING

from agent import LoopData
from helpers.extension import Extension

_log = logging.getLogger(__name__)


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


def _is_workflow_state_enabled(cfg: dict) -> bool:
    return _config_bool(cfg.get("workflow_state_enabled", True))


def _format_state_block(state: dict) -> str:
    lines = ["", "# Durable Workflow State (Rehydrated)", ""]

    goal = state.get("active_goal")
    if goal:
        lines.append(f"**Active Goal:** {goal.get('goal', '(unknown)')}")

    phase = state.get("current_phase")
    if phase:
        lines.append(f"**Current Phase:** {phase.get('phase', '(unknown)')}")
        completed = phase.get("phases_completed", [])
        if completed:
            lines.append(f"**Phases Completed:** {', '.join(completed)}")

    artifacts = state.get("workflow_artifacts") or {}
    plan = state.get("active_plan")
    if plan:
        lines.append(f"**Active Plan:** {plan.get('plan_name', '(unknown)')}")
        lines.append(f"**Plan Path:** {artifacts.get('plan_path') or plan.get('plan_path', '(unknown)')}")
        lines.append(f"**Current Task:** {plan.get('current_task', '(unknown)')}")
        total = plan.get("tasks_total", 0)
        done = plan.get("tasks_completed", 0)
        if total:
            lines.append(f"**Task Progress:** {done}/{total} completed")

    skills = state.get("loaded_skills")
    if skills:
        skill_list = skills.get("skills", [])
        if skill_list:
            names = [s.get("name", "?") for s in skill_list]
            lines.append(f"**Loaded Skills:** {', '.join(names)}")

    checkpoints = state.get("checkpoints")
    if checkpoints:
        cp_list = checkpoints.get("checkpoints", [])
        if cp_list:
            last = cp_list[-1]
            lines.append(
                f"**Last Checkpoint:** {last.get('id', '?')} \u2014 {last.get('label', '?')}"
            )

    # Note: "intent" is populated via manual state manipulation (e.g. saving
    # to workflow_artifacts.json directly), not by the resolver or discover_feature_slug.
    if artifacts and isinstance(artifacts, dict):
        artifact_items = []
        approved = artifacts.get("approved") or {}
        # Map stored keys (with _path suffix) to display names
        artifact_key_map = {
            "idea": "idea", "intent": "intent",
            "spec_path": "spec", "plan_path": "plan", "todo_path": "todo",
        }
        for key, display_name in artifact_key_map.items():
            path_val = artifacts.get(key)
            if path_val:
                tag = " (approved)" if approved.get(key) else ""
                artifact_items.append(f"- {display_name}: {path_val}{tag}")
        if artifact_items:
            lines.append("")
            lines.append("**Active Artifacts:**")
            lines.extend(artifact_items)

    lines.append("")
    return "\n".join(lines)


def _format_next_skill_hints(skill_names: list[str], cfg: dict) -> str | None:
    try:
        if not _config_bool(cfg.get("skill_next_skill_hints", True)):
            return None

        _loader = _bootstrap_plugin_loader()
        _load_module_by_path = _loader.load_module_by_path

        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
        helpers_dir = os.path.join(plugin_root, 'helpers')

        _skill_contracts = _load_module_by_path(
            'helpers.skill_contracts', os.path.join(helpers_dir, 'skill_contracts.py'),
        )
        get_next_skills = _skill_contracts.get_next_skills
        get_skill_contract = _skill_contracts.get_skill_contract

        hints = []
        for skill_name in skill_names:
            next_skills = get_next_skills(skill_name)
            if next_skills:
                first_next = next_skills[0]
                contract = get_skill_contract(first_next)
                phase_str = ""
                if contract and contract.get("phase"):
                    phase_str = f" ({contract['phase']} phase)"
                hints.append(
                    f"- After {skill_name}: consider loading {first_next}{phase_str}"
                )

        if not hints:
            return None

        lines = ["", "## Next Skill Hints", ""]
        lines.extend(hints)
        lines.append("")
        return "\n".join(lines)

    except Exception:
        return None


# TTL-based cache for _scan_active_specs — avoids glob + file reads on
# every message loop iteration.  Mirrors the pattern in build_skill_graph().
_specs_cache: list | None = None
_specs_cache_ts: float = 0.0
_SPECS_CACHE_TTL: float = 30.0  # seconds


def _reset_specs_cache() -> None:
    """Clear the specs cache (for test teardown)."""
    global _specs_cache, _specs_cache_ts
    _specs_cache = None
    _specs_cache_ts = 0.0


def _scan_active_specs(agent) -> list[dict]:
    """Scan docs/specs/ for spec files and return non-shipped ones.

    Results are cached for _SPECS_CACHE_TTL seconds to avoid redundant
    filesystem I/O on every message loop iteration.

    Returns list of dicts with 'name', 'path', 'status' keys.
    Specs with Status: SHIPPED or Status: Approved are excluded.
    Fail-safe: returns empty list on any error.
    """
    global _specs_cache, _specs_cache_ts

    # Return cached result if still fresh
    if _specs_cache is not None and (_time.time() - _specs_cache_ts < _SPECS_CACHE_TTL):
        return _specs_cache

    try:
        import glob as _glob

        # Resolve project directory from agent context
        project_dir = None
        try:
            helpers_mod = sys.modules.get("helpers")
            if helpers_mod and hasattr(helpers_mod, "projects"):
                proj_name = helpers_mod.projects.get_context_project_name(agent)
                if proj_name:
                    project_dir = helpers_mod.projects.get_project_folder(proj_name)
        except Exception:
            pass

        if not project_dir:
            return []

        specs_dir = os.path.join(project_dir, "docs", "specs")
        if not os.path.isdir(specs_dir):
            return []

        # Patterns for Status field in markdown header
        _STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.MULTILINE)
        _COMPLETED_STATUSES = frozenset({
            "shipped", "approved", "complete", "completed", "done",
        })

        active_specs = []
        for spec_file in sorted(_glob.glob(os.path.join(specs_dir, "*-spec.md"))):
            try:
                with open(spec_file, "r", encoding="utf-8") as f:
                    # Read only first 2KB for performance
                    header = f.read(2048)

                match = _STATUS_RE.search(header)
                status = match.group(1).strip() if match else "Draft"

                # Filter out completed specs
                if status.lower() in _COMPLETED_STATUSES:
                    continue

                name = os.path.basename(spec_file)
                # Show relative path from project root
                rel_path = os.path.relpath(spec_file, project_dir)
                active_specs.append({
                    "name": name,
                    "path": rel_path,
                    "status": status,
                })
            except Exception:
                continue

        # Cache the result
        _specs_cache = active_specs
        _specs_cache_ts = _time.time()
        return active_specs

    except Exception:
        return []


def _format_active_specs_block(specs: list[dict]) -> str | None:
    """Format active (non-shipped) specs into a state block section."""
    try:
        if not specs:
            return None

        lines = ["", "## Active Specs (Not Yet Shipped)", ""]
        for spec in specs:
            status_tag = f" ({spec['status']})" if spec.get('status') else ""
            lines.append(f"- {spec['path']}{status_tag}")
        lines.append("")
        return "\n".join(lines)

    except Exception:
        return None


def _extract_skill_names(state: dict) -> list[str]:
    skills = state.get("loaded_skills")
    if not skills:
        return []
    skill_list = skills.get("skills", [])
    return [s.get("name", "") for s in skill_list if s.get("name")]


class ReattachWorkflowState(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            if not self.agent:
                return

            cfg = _get_plugin_config(self.agent)
            if not _is_workflow_state_enabled(cfg):
                return

            _loader = _bootstrap_plugin_loader()
            _load_module_by_path = _loader.load_module_by_path

            this_dir = os.path.dirname(os.path.abspath(__file__))
            plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
            helpers_dir = os.path.join(plugin_root, 'helpers')

            _workflow_state = _load_module_by_path(
                'helpers.workflow_state', os.path.join(helpers_dir, 'workflow_state.py'),
            )
            _skill_contracts_mod = _load_module_by_path(
                'helpers.skill_contracts', os.path.join(helpers_dir, 'skill_contracts.py'),
            )

            state = _workflow_state.read_all_state(self.agent)
            if not state:
                return

            skill_names = _extract_skill_names(state)
            if skill_names:
                try:
                    discover_skill_names = _skill_contracts_mod.discover_skill_names
                    known = set(discover_skill_names())
                    validated = []
                    for name in skill_names:
                        if name in known:
                            validated.append(name)
                        else:
                            _log.warning(
                                "Rehydrated unknown skill '%s' \u2014 possible tampering",
                                name,
                            )
                    skill_names = validated
                except Exception:
                    pass

                if skill_names:
                    try:
                        if not isinstance(self.agent.data, dict):
                            self.agent.data = {}
                        # Write rehydrated names to a PLUGIN-PRIVATE key, NOT the
                        # core-rendered 'loaded_skills' key. Writing to
                        # 'loaded_skills' makes the core skills renderer re-inject
                        # full SKILL.md bodies for every prior-session skill on
                        # every message loop (unbounded context flood). The
                        # enforcement gate reads this private key via
                        # skill_match.get_loaded_skills(); the lightweight names
                        # summary already lives in the rehydrated state block.
                        self.agent.data["_a0skills_rehydrated_loaded"] = skill_names
                    except Exception:
                        pass

            state_block = _format_state_block(state)

            if skill_names:
                hints_block = _format_next_skill_hints(skill_names, cfg)
                if hints_block:
                    state_block += hints_block

            # Scan for active (non-shipped) specs to help agent avoid
            # proposing already-completed work.
            active_specs = _scan_active_specs(self.agent)
            specs_block = _format_active_specs_block(active_specs)
            if specs_block:
                state_block += specs_block

            if state_block:
                loop_data.extras_persistent["workflow_state"] = state_block

        except Exception:
            pass  # never break prompt assembly
