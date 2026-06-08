"""Auto-unload non-persistent skills at monologue end.

Skills can declare `persist: true` in their SKILL.md YAML frontmatter.
Skills without this declaration (or with `persist: false`) are automatically
unloaded when the monologue ends, freeing context for the next task.

The `using-agent-skills` meta-skill is always persisted (included in the
agent0 system prompt via `agent.system.main.specifics.md` override).

Frontmatter format in SKILL.md:
    ---
    persist: true
    ---

Or simply include a line `persist: true` between the two `---` delimiters.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from helpers.extension import Extension

logger = logging.getLogger(__name__)

# Must match skills_helper.AGENT_DATA_NAME_LOADED_SKILLS
DATA_NAME_LOADED_SKILLS = "loaded_skills"

# Skills that are ALWAYS persisted regardless of frontmatter
ALWAYS_PERSIST = {"using-agent-skills"}


def _read_persist_from_skill_md(skill_name: str, agent: Any) -> bool:
    """Read the `persist` frontmatter field from a skill's SKILL.md.

    Returns True if the skill declares `persist: true`, False otherwise.
    """
    try:
        from helpers.skills import get_skill_roots
    except ImportError:
        return False

    for root in get_skill_roots():
        skill_path = os.path.join(root, skill_name, "SKILL.md")
        if os.path.isfile(skill_path):
            try:
                with open(skill_path, encoding="utf-8") as f:
                    content = f.read()
                return _parse_persist(content)
            except (OSError, UnicodeDecodeError):
                continue
    return False


def _parse_persist(skill_md_content: str) -> bool:
    """Parse YAML frontmatter for `persist: true`.

    Handles:
    ---
    persist: true
    ---
    """
    match = re.match(r'^---\s*\n(.*?)\n---', skill_md_content, re.DOTALL)
    if not match:
        return False
    frontmatter = match.group(1)
    for line in frontmatter.splitlines():
        line = line.strip()
        if line.lower().startswith("persist:"):
            value = line.split(":", 1)[1].strip().lower()
            return value in ("true", "yes", "1")
    return False


class SkillAutoUnload(Extension):

    def execute(self, **kwargs):
        """Unload non-persistent skills at monologue end."""
        if not self.agent:
            return

        # Only for main agent
        if getattr(self.agent, "number", -1) != 0:
            return

        data = getattr(self.agent, "data", None)
        if not isinstance(data, dict):
            return

        loaded = data.get(DATA_NAME_LOADED_SKILLS)
        if not isinstance(loaded, list) or not loaded:
            return

        # Check each loaded skill
        to_unload = []
        for skill_name in list(loaded):
            # Always-persist skills are never unloaded
            if skill_name in ALWAYS_PERSIST:
                continue

            # Check if skill declares persist: true
            if _read_persist_from_skill_md(skill_name, self.agent):
                continue

            to_unload.append(skill_name)

        # Unload non-persistent skills
        if to_unload:
            try:
                from helpers.skills import unload_agent_skill
                for skill_name in to_unload:
                    unload_agent_skill(self.agent, skill_name)
                logger.info(
                    "Auto-unloaded %d skill(s): %s",
                    len(to_unload),
                    ", ".join(to_unload),
                )
            except ImportError:
                logger.debug("helpers.skills not available; skipping auto-unload")
