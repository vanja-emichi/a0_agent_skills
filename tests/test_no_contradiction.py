"""T3: Verify SKILL.md has no Never-directly-edit contradiction.

The lifecycle-runtime SKILL.md must not say "Never directly edit" while
also requiring direct edits to state.md and findings.md/progress.md.
"""
import os
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def test_no_never_edit_contradiction():
    """SKILL.md should not say Never directly edit while also requiring direct edits."""
    path = SKILLS_DIR / "lifecycle-runtime" / "SKILL.md"
    with open(path) as f:
        content = f.read()
    assert "Never directly edit files in" not in content
    assert "Never directly edit" not in content


def test_no_directly_instead_red_flag():
    """Red Flags should not list direct file edits as a red flag."""
    path = SKILLS_DIR / "lifecycle-runtime" / "SKILL.md"
    with open(path) as f:
        content = f.read()
    assert "directly instead of using lifecycle tool" not in content
