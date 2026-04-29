# lib/constants.py - Centralized context key constants for a0_agent_skills
#
# All context.data[...] key strings are defined here.
# Extensions access constants through lifecycle_state module re-exports.
#
# Usage in tools/lifecycle.py:
#   from lib.constants import CONTEXT_KEY_LIFECYCLE_STATE
#
# Usage in extensions (via import_utils):
#   ls_mod = _get_lifecycle_state()
#   ls_mod.CONTEXT_KEY_LIFECYCLE_STATE

from __future__ import annotations

# Context data keys
CONTEXT_KEY_LIFECYCLE_STATE = "lifecycle_state"
CONTEXT_KEY_LIFECYCLE_STATE_MTIME = "lifecycle_state_mtime"
CONTEXT_KEY_LIFECYCLE_GATE_WARNINGS = "lifecycle_gate_warnings"
CONTEXT_KEY_LIFECYCLE_ACTIONS_SINCE_FINDING = "lifecycle_actions_since_finding"
CONTEXT_KEY_LIFECYCLE_NUDGES = "lifecycle_nudges"
CONTEXT_KEY_LIFECYCLE_RESUME_SHOWN = "lifecycle_resume_shown"

# Plugin identity - matches plugin.yaml name
PLUGIN_NAME = "a0_agent_skills"

# Phase status icons
PHASE_ICONS = {"pending": "⏸️", "in_progress": "🔄", "completed": "✅"}
PHASE_ICON_DEFAULT = "⏸️"
