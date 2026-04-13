"""Register agent-skills slash commands into the Commands plugin on agent init.

The Commands plugin scopes commands differently depending on whether a project
is active:
  - No project: scope = /a0/usr/plugins/commands/commands/
  - Project active: scope = /a0/usr/projects/<project>/.a0proj/plugins/commands/commands/

When validating a command path, it checks ONLY against the active scope.
So we must create symlinks in BOTH scopes to handle either case.
"""
from __future__ import annotations

from pathlib import Path

from helpers.extension import Extension
from helpers.print_style import PrintStyle


PLUGIN_NAME = "agent-skills"
# Derive plugin root from this file's location — works on any install path.
# _10_register_commands.py lives at: <plugin_root>/extensions/python/agent_init/
# parents[0] = agent_init, parents[1] = python, parents[2] = extensions, parents[3] = plugin_root
PLUGIN_ROOT = Path(__file__).resolve().parents[3]

# Global scope: when no project is active
GLOBAL_COMMANDS_DIR = Path("/a0/usr/plugins/commands/commands")

# Project scope: when agent_skills project is active
# Commands plugin resolves this as: projects.get_project_meta('agent_skills') / plugins/commands/commands
PROJECT_COMMANDS_DIR = PLUGIN_ROOT / ".a0proj" / "plugins" / "commands" / "commands"


class RegisterCommands(Extension):
    def execute(self, **kwargs):
        try:
            our_commands_dir = PLUGIN_ROOT / "commands"

            if not our_commands_dir.is_dir():
                return

            # Determine which scope directories to populate
            scopes: list[Path] = []

            # Global scope — only if Commands plugin is installed
            if GLOBAL_COMMANDS_DIR.parent.parent.exists():
                scopes.append(GLOBAL_COMMANDS_DIR)

            # Project scope — always register so commands work when project is active
            scopes.append(PROJECT_COMMANDS_DIR)

            registered = 0
            for scope_dir in scopes:
                scope_dir.mkdir(parents=True, exist_ok=True)
                for src_file in sorted(our_commands_dir.iterdir()):
                    # Skip non-files and symlinks in the source directory
                    if not src_file.is_file() or src_file.is_symlink():
                        continue
                    dest = scope_dir / src_file.name
                    if dest.is_symlink():
                        if dest.readlink() == src_file:
                            continue  # Already correct
                        dest.unlink()
                    elif dest.exists():
                        PrintStyle.warning(f"[{PLUGIN_NAME}] Replacing non-symlink file: {dest}")
                        dest.unlink()
                    dest.symlink_to(src_file)
                    registered += 1

            if registered:
                PrintStyle.hint(
                    f"[{PLUGIN_NAME}] Registered {registered} slash command symlinks"
                )
        except Exception as e:
            PrintStyle.error(f"[{PLUGIN_NAME}] Failed to register commands: {e}")
