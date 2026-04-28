"""T3: Verify SKILL.md has no Never-directly-edit contradiction.

The using-agent-skills SKILL.md (with merged lifecycle content) must not say "Never directly edit" while
also requiring direct edits to state.md and findings.md/progress.md.
"""
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "using-agent-skills" / "SKILL.md"
SKILL_CONTENT = SKILL_PATH.read_text()


def test_no_never_edit_contradiction():
    """SKILL.md should not say Never directly edit while also requiring direct edits."""
    assert "Never directly edit files in" not in SKILL_CONTENT
    assert "Never directly edit" not in SKILL_CONTENT


def test_no_directly_instead_red_flag():
    """Red Flags should not list direct file edits as a red flag."""
    assert "directly instead of using lifecycle tool" not in SKILL_CONTENT
