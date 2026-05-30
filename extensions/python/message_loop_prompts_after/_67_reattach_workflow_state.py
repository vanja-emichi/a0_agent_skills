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
import sys
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

    plan = state.get("active_plan")
    if plan:
        lines.append(f"**Active Plan:** {plan.get('plan_name', '(unknown)')}")
        lines.append(f"**Plan Path:** {plan.get('plan_path', '(unknown)')}")
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
                        self.agent.data["loaded_skills"] = skill_names
                    except Exception:
                        pass

            state_block = _format_state_block(state)

            if skill_names:
                hints_block = _format_next_skill_hints(skill_names, cfg)
                if hints_block:
                    state_block += hints_block

            if state_block:
                loop_data.extras_persistent["workflow_state"] = state_block

        except Exception:
            pass  # never break prompt assembly
