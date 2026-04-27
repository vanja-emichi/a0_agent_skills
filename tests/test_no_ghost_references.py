import os
import re

PLUGIN_ROOT = "/home/debian/agent-zero/development/usr/plugins/a0_agent_skills"
SKILLS_DIR = os.path.join(PLUGIN_ROOT, "skills")

GHOST_PATTERNS = [
    r"#\s*(\w+)\s+removed",
    r"#\s*(phase_start|phase_complete|extend|log_finding|log_progress|log_error|migrate)\s+removed",
]

def test_no_ghost_references_in_skills():
    """No SKILL.md should contain ghost removed patterns."""
    ghost_refs = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        for f in files:
            if f == "SKILL.md":
                path = os.path.join(root, f)
                rel = os.path.relpath(path, PLUGIN_ROOT)
                with open(path) as fh:
                    for i, line in enumerate(fh, 1):
                        for pattern in GHOST_PATTERNS:
                            if re.search(pattern, line):
                                ghost_refs.append(f"{rel}:{i}: {line.strip()}")
    assert len(ghost_refs) == 0, f"Found {len(ghost_refs)} ghost references:\n" + "\n".join(ghost_refs)
