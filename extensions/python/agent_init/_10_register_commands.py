"""Register agent-skills slash commands into the Commands plugin on agent init.

The Commands plugin only reads from its own scope directory. This extension
creates symlinks from the Commands plugin's commands/ dir to our command files
so they appear automatically when the Commands plugin is active.
"""
from __future__ import annotations

import os
from pathlib import Path

from helpers.extension import Extension
from helpers.print_style import PrintStyle


PLUGIN_NAME = "agent-skills"
COMMANDS_PLUGIN_DIR = Path("/a0/usr/plugins/commands/commands")


class RegisterCommands(Extension):
    async def execute(self, **kwargs):
        try:
            # Find our commands directory — resolve through symlink
            this_plugin = Path(__file__).resolve().parents[3]  # plugin root
            our_commands_dir = this_plugin / "commands"

            if not our_commands_dir.is_dir():
                return

            if not COMMANDS_PLUGIN_DIR.exists():
                # Commands plugin not installed — skip silently
                return

            # Symlink each command file pair into the Commands plugin directory
            registered = []
            for src_file in our_commands_dir.iterdir():
                if not src_file.is_file():
                    continue
                dest = COMMANDS_PLUGIN_DIR / src_file.name
                if dest.exists() or dest.is_symlink():
                    # Already registered — update symlink if target changed
                    if dest.is_symlink() and os.readlink(dest) == str(src_file):
                        continue
                    dest.unlink()
                dest.symlink_to(src_file)
                registered.append(src_file.name)

            if registered:
                PrintStyle.hint(
                    f"[{PLUGIN_NAME}] Registered {len(registered)} slash commands"
                )
        except Exception as e:
            PrintStyle.error(f"[{PLUGIN_NAME}] Failed to register commands: {e}")
