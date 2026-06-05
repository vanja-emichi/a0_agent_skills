"""Auto-load the using-agent-skills meta-skill into every new agent session.

This extension runs at agent initialization (before the first user message)
and directly registers the meta-skill in the agent's loaded_skills data,
so it appears in EXTRAS every turn without needing a tool call or log entry.

Runs before the framework's _10_initial_message via the _00_ filename prefix.

IMPORTANT: Do NOT add log entries here — _10_initial_message.py checks
`if self.agent.context.log.logs: return` and would skip the greeting.
"""

import logging
import os

from helpers.extension import Extension

logger = logging.getLogger(__name__)

# Must match skills_helper.AGENT_DATA_NAME_LOADED_SKILLS
DATA_NAME_LOADED_SKILLS = "loaded_skills"


class InjectMetaSkill(Extension):

    def execute(self, **kwargs):
        """Register using-agent-skills in the agent's loaded skills data.

        This makes the meta-skill appear in EXTRAS every turn, exactly as if
        the user or agent had called `skills_tool load using-agent-skills`.

        Guards:
        - Only runs for the main agent (number == 0), not subordinates.
        - Only runs on first message (no log entries exist yet).
        - Does NOT add log entries (would suppress _10_initial_message greeting).
        """
        if not self.agent:
            return

        # Only inject for the main agent (A0), not subordinate agents
        if self.agent.number != 0:
            return

        # If the context already contains log messages, the session has started;
        # do not inject again (prevents re-injection on subsequent turns)
        if self.agent.context.log.logs:
            return

        # Verify the skill exists before registering it
        if not self._skill_exists():
            logger.debug("using-agent-skills skill not found; skipping registration")
            return

        # Directly register the skill name in the agent's loaded_skills data.
        # This is the same data structure that skills_tool._load() writes to,
        # so the framework will include the skill in EXTRAS every turn.
        if not hasattr(self.agent, "data") or not isinstance(self.agent.data, dict):
            return

        loaded = self.agent.data.get(DATA_NAME_LOADED_SKILLS)
        if not isinstance(loaded, list):
            loaded = []

        skill_name = "using-agent-skills"
        if skill_name in loaded:
            loaded.remove(skill_name)
        loaded.append(skill_name)

        self.agent.data[DATA_NAME_LOADED_SKILLS] = loaded

        # Do NOT add context.log.log() here — it would suppress the greeting
        # from _10_initial_message.py which checks `if log.logs: return`

    def _skill_exists(self) -> bool:
        """Verify the using-agent-skills skill exists in the plugin."""
        # Resolve plugin directory from this extension file's location
        # Extension: extensions/python/agent_init/_00_inject_meta_skill.py
        # Plugin root is 3 levels up
        plugin_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )

        # Boundary validation: directory name or sentinel file
        if os.path.basename(plugin_dir) != "a0_agent_skills" \
           and not os.path.isfile(os.path.join(plugin_dir, "plugin.yaml")):
            return False

        skill_path = os.path.join(
            plugin_dir, "skills", "using-agent-skills", "SKILL.md"
        )

        if os.path.isfile(skill_path) and not os.path.islink(skill_path):
            return True

        # Fallback: check global skill roots
        try:
            from helpers.skills import get_skill_roots
            for root in get_skill_roots():
                candidate = os.path.join(root, "using-agent-skills", "SKILL.md")
                if os.path.isfile(candidate) and not os.path.islink(candidate):
                    return True
        except (ImportError, OSError):
            pass

        return False
