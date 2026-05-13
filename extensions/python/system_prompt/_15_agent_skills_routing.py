"""System prompt extension that injects agent-skills routing rules.

This extension appends the routing rules from prompts/agent.skills.routing.md
into the system_prompt list during prompt assembly. It works regardless of
whether a project is active — unlike the old promptinclude approach which
only scanned the workdir when no project was active.

Follows the same pattern as:
  - /a0/plugins/_memory/extensions/python/system_prompt/_20_behaviour_prompt.py
  - /a0/plugins/_browser/extensions/python/system_prompt/_20_browser_context.py
"""
import os
import logging

from helpers.extension import Extension

_log = logging.getLogger(__name__)


# Module-level cache for routing template (S-1)
_routing_cache: dict = {"content": None, "mtime": None}


def _load_routing_template(prompt_file: str) -> str | None:
    """Load routing template with mtime-based cache.

    Reads the file only when it has changed (or on first call).
    Returns None if the file does not exist or cannot be read.
    """
    try:
        stat = os.stat(prompt_file)
    except OSError:
        return None

    mtime = stat.st_mtime
    if _routing_cache["mtime"] == mtime and _routing_cache["content"] is not None:
        return _routing_cache["content"]

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            _routing_cache["content"] = f.read()
            _routing_cache["mtime"] = mtime
            return _routing_cache["content"]
    except OSError:
        return None


class AgentSkillsRouting(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data=None,
        **kwargs,
    ):
        # Read routing rules from the prompt template file
        prompt_file = _get_routing_prompt_path()
        content = _load_routing_template(prompt_file)

        if content and content.strip():
            system_prompt.append(content)


def _get_routing_prompt_path() -> str:
    """Resolve the path to the routing prompt template.

    The template lives at:
      <plugin_root>/prompts/agent.skills.routing.md

    This file is at:
      <plugin_root>/extensions/python/system_prompt/_15_agent_skills_routing.py

    So we go up 3 levels from this file's directory to reach plugin_root.
    extensions/python/system_prompt/ → a0_agent_skills/
    That is 3 levels up.
    """
    this_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.normpath(
        os.path.join(this_dir, "..", "..", "..")
    )
    prompt_path = os.path.join(plugin_root, "prompts", "agent.skills.routing.md")
    if not os.path.exists(prompt_path):
        _log.warning("Routing prompt not found at %s", prompt_path)
    return prompt_path
