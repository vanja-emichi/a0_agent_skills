"""Lifecycle hooks for the a0_agent_skills plugin.

NOTE: These hooks are intentionally empty stubs. The original design used
install() to write a routing promptinclude file to the workdir, but that
approach had a critical flaw — workdir promptincludes are NOT injected when
a project is active, so the routing rules were invisible during real work.

Routing is now handled by the system_prompt extension at:
  extensions/python/system_prompt/_15_agent_skills_routing.py

That extension reads prompts/agent.skills.routing.md at runtime and appends
routing rules to the system prompt during assembly — working universally
regardless of whether a project is active.

These stubs are retained for potential future plugin lifecycle needs
(e.g., migration hooks, version upgrade notifications).
"""


def install() -> None:
    """Called when the plugin is installed or enabled.

    Routing injection is handled by the system_prompt extension,
    not by file writing. No install-time action needed.
    """
    pass


def uninstall() -> None:
    """Called when the plugin is uninstalled or disabled."""
    pass


def pre_update() -> None:
    """Called immediately before plugin code is replaced during an update."""
    pass
