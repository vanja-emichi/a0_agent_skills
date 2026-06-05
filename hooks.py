"""Agent Skills Plugin - Lifecycle hooks.

Hooks run inside the Agent Zero framework runtime.
Use install() for setup work and uninstall() for cleanup.
"""

import logging
import os


def install():
    """Called when the plugin is installed."""
    logger = logging.getLogger(__name__)
    # Count dynamically so the log stays accurate
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(plugin_dir, "skills")
    agents_dir = os.path.join(plugin_dir, "agents")
    commands_dir = os.path.join(plugin_dir, "commands")
    skills_count = sum(
        1 for d in os.listdir(skills_dir)
        if os.path.isfile(os.path.join(skills_dir, d, "SKILL.md"))
    ) if os.path.isdir(skills_dir) else 0
    agents_count = sum(
        1 for d in os.listdir(agents_dir)
        if os.path.isdir(os.path.join(agents_dir, d))
    ) if os.path.isdir(agents_dir) else 0
    commands_count = sum(
        1 for f in os.listdir(commands_dir)
        if f.endswith('.command.yaml')
    ) if os.path.isdir(commands_dir) else 0
    logger.info(
        "Agent Skills plugin installed — %d skills, %d profiles, %d commands available",
        skills_count, agents_count, commands_count,
    )


def uninstall():
    """No cleanup needed — plugin is stateless."""
    pass
