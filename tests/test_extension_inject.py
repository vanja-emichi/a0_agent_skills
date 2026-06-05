"""Unit tests for _00_inject_meta_skill.py extension."""

import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

PLUGIN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
EXT_DIR = os.path.join(PLUGIN_DIR, "extensions", "python", "agent_init")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(number=0, has_logs=False, has_data=True):
    """Create a mock agent with the attributes the extension checks."""
    agent = MagicMock()
    agent.number = number
    agent.context.log.logs = ["something"] if has_logs else []
    if has_data:
        agent.data = {}
    return agent


def _import_extension():
    """Import the extension module with mocked framework dependencies."""
    class MockExtension:
        def __init__(self):
            self.agent = None

    mock_ext = MagicMock()
    mock_ext.Extension = MockExtension

    with patch.dict(sys.modules, {
        "helpers": MagicMock(),
        "helpers.extension": mock_ext,
    }):
        if "_00_inject_meta_skill" in sys.modules:
            del sys.modules["_00_inject_meta_skill"]
        sys.path.insert(0, EXT_DIR)
        try:
            mod = importlib.import_module("_00_inject_meta_skill")
            return mod
        finally:
            if EXT_DIR in sys.path:
                sys.path.remove(EXT_DIR)


# ---------------------------------------------------------------------------
# Path resolution tests
# ---------------------------------------------------------------------------


class TestPathResolution:
    """Verify the extension resolves to the correct plugin root."""

    def test_three_dots_resolves_to_plugin_root(self):
        """3 '..' segments from extensions/python/agent_init/ must land on a0_agent_skills/."""
        resolved = os.path.normpath(os.path.join(EXT_DIR, "..", "..", ".."))
        assert os.path.basename(resolved) == "a0_agent_skills"
        assert os.path.isdir(resolved)

    def test_path_is_not_off_by_one(self):
        """Resolved path must NOT be /a0/usr/plugins/ (parent of plugin)."""
        resolved = os.path.normpath(os.path.join(EXT_DIR, "..", "..", ".."))
        parent = os.path.normpath(os.path.join(EXT_DIR, "..", "..", "..", ".."))
        assert resolved != parent, f"Path resolved to plugin parent: {resolved}"


# ---------------------------------------------------------------------------
# Guard tests
# ---------------------------------------------------------------------------


class TestGuards:
    """Verify the extension guards prevent unwanted injection."""

    def test_agent_none_silent_return(self):
        """If self.agent is None, execute() returns silently."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = None
        # Should not raise
        ext.execute()

    def test_subordinate_agent_no_injection(self):
        """agent.number != 0 means no injection (subordinate agents)."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=1)
        ext.execute()
        assert "loaded_skills" not in ext.agent.data

    def test_existing_logs_no_injection(self):
        """Non-empty logs means session already started — no injection."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=True)
        ext.execute()
        assert "loaded_skills" not in ext.agent.data

    def test_no_data_attribute_no_injection(self):
        """If agent has no .data dict, execute() returns without error."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        agent = MagicMock()
        agent.number = 0
        agent.context.log.logs = []
        # Remove .data entirely
        del agent.data
        ext.agent = agent
        # Should not raise
        ext.execute()

    def test_data_not_dict_no_injection(self):
        """If agent.data is not a dict, execute() returns without error."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        agent = MagicMock()
        agent.number = 0
        agent.context.log.logs = []
        agent.data = "not a dict"
        ext.agent = agent
        # Should not raise
        ext.execute()


# ---------------------------------------------------------------------------
# Direct data injection tests
# ---------------------------------------------------------------------------


class TestDirectDataInjection:
    """Verify the extension directly registers the skill in agent.data."""

    def test_skill_registered_in_loaded_skills(self):
        """After execute, agent.data['loaded_skills'] contains 'using-agent-skills'."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)
        ext.execute()
        assert "loaded_skills" in ext.agent.data
        assert "using-agent-skills" in ext.agent.data["loaded_skills"]

    def test_loaded_skills_is_a_list(self):
        """agent.data['loaded_skills'] must be a list."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)
        ext.execute()
        assert isinstance(ext.agent.data["loaded_skills"], list)

    def test_skill_appended_to_existing_list(self):
        """If loaded_skills already has entries, the skill is appended."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)
        ext.agent.data["loaded_skills"] = ["other-skill"]
        ext.execute()
        assert ext.agent.data["loaded_skills"] == ["other-skill", "using-agent-skills"]

    def test_skill_not_duplicated(self):
        """If skill is already in the list, it is moved to the end (no duplicate)."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)
        ext.agent.data["loaded_skills"] = ["using-agent-skills", "other-skill"]
        ext.execute()
        assert ext.agent.data["loaded_skills"].count("using-agent-skills") == 1
        assert ext.agent.data["loaded_skills"][-1] == "using-agent-skills"

    def test_no_log_entry_created(self):
        """Extension must NOT create log entries (would suppress greeting)."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)
        ext.execute()
        ext.agent.context.log.log.assert_not_called()

    def test_no_hist_add_ai_response_called(self):
        """Extension must NOT call hist_add_ai_response (no content injection)."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)
        ext.execute()
        ext.agent.hist_add_ai_response.assert_not_called()


# ---------------------------------------------------------------------------
# _skill_exists tests
# ---------------------------------------------------------------------------


class TestSkillExists:
    """Verify _skill_exists checks boundary and SKILL.md presence."""

    def test_returns_true_for_real_plugin(self):
        """_skill_exists returns True when skill exists in the real plugin."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        assert ext._skill_exists() is True

    def test_returns_false_for_wrong_directory(self, tmp_path):
        """_skill_exists returns False when plugin dir has wrong name and no sentinel."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()

        wrong_dir = tmp_path / "wrong-name"
        wrong_dir.mkdir()
        ext_dir = wrong_dir / "extensions" / "python" / "agent_init"
        ext_dir.mkdir(parents=True)
        original_file = mod.__file__
        mod.__file__ = str(ext_dir / "_00_inject_meta_skill.py")
        try:
            result = ext._skill_exists()
        finally:
            mod.__file__ = original_file

        assert result is False

    def test_returns_true_with_sentinel_fallback(self, tmp_path):
        """_skill_exists returns True when basename doesn't match but plugin.yaml exists."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()

        renamed_dir = tmp_path / "my-renamed-plugin"
        renamed_dir.mkdir()
        (renamed_dir / "plugin.yaml").write_text("name: test\n", encoding="utf-8")
        skill_dir = renamed_dir / "skills" / "using-agent-skills"
        skill_dir.mkdir(parents=True)
        skill_dir.joinpath("SKILL.md").write_text("---\nname: using-agent-skills\n---\nBody", encoding="utf-8")

        ext_dir = renamed_dir / "extensions" / "python" / "agent_init"
        ext_dir.mkdir(parents=True)
        original_file = mod.__file__
        mod.__file__ = str(ext_dir / "_00_inject_meta_skill.py")
        try:
            result = ext._skill_exists()
        finally:
            mod.__file__ = original_file

        assert result is True

    def test_returns_false_with_sentinel_but_no_skill(self, tmp_path):
        """_skill_exists returns False when plugin.yaml exists but skill file missing."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()

        renamed_dir = tmp_path / "my-renamed-plugin"
        renamed_dir.mkdir()
        (renamed_dir / "plugin.yaml").write_text("name: test\n", encoding="utf-8")
        # No skills/using-agent-skills/SKILL.md created

        ext_dir = renamed_dir / "extensions" / "python" / "agent_init"
        ext_dir.mkdir(parents=True)
        original_file = mod.__file__
        mod.__file__ = str(ext_dir / "_00_inject_meta_skill.py")
        try:
            result = ext._skill_exists()
        finally:
            mod.__file__ = original_file

        assert result is False

    def test_rejects_symlink_skill_file(self, tmp_path):
        """_skill_exists returns False when the skill file is a symlink."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()

        plugin_dir = tmp_path / "a0_agent_skills"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.yaml").write_text("name: test\n", encoding="utf-8")
        skill_dir = plugin_dir / "skills" / "using-agent-skills"
        skill_dir.mkdir(parents=True)

        # Create a real file and a symlink pointing to it
        real_file = tmp_path / "real_skill.md"
        real_file.write_text("---\nname: using-agent-skills\n---\nBody", encoding="utf-8")
        symlink_path = skill_dir / "SKILL.md"
        symlink_path.symlink_to(real_file)

        ext_dir = plugin_dir / "extensions" / "python" / "agent_init"
        ext_dir.mkdir(parents=True)
        original_file = mod.__file__
        mod.__file__ = str(ext_dir / "_00_inject_meta_skill.py")
        try:
            result = ext._skill_exists()
        finally:
            mod.__file__ = original_file

        assert result is False


# ---------------------------------------------------------------------------
# Boundary validation tests
# ---------------------------------------------------------------------------


class TestBoundaryValidation:
    """Verify skill missing prevents injection entirely."""

    def test_no_injection_when_skill_missing(self, tmp_path):
        """If skill doesn't exist, execute() skips injection entirely."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)

        # Point __file__ to a directory without the skill
        wrong_dir = tmp_path / "wrong-name"
        wrong_dir.mkdir()
        ext_dir = wrong_dir / "extensions" / "python" / "agent_init"
        ext_dir.mkdir(parents=True)
        original_file = mod.__file__
        mod.__file__ = str(ext_dir / "_00_inject_meta_skill.py")
        try:
            ext.execute()
        finally:
            mod.__file__ = original_file

        assert "loaded_skills" not in ext.agent.data

    def test_injection_with_real_plugin(self):
        """With the real plugin, execute() successfully registers the skill."""
        mod = _import_extension()
        ext = mod.InjectMetaSkill()
        ext.agent = _make_agent(number=0, has_logs=False)
        ext.execute()
        assert "using-agent-skills" in ext.agent.data["loaded_skills"]
