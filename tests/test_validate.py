"""Tests for scripts/validate.py — TDD RED → GREEN.

Each test exercises one check function in isolation via tmp_path fixtures.
All tests import from scripts/validate.py which must exist for GREEN to pass.
"""
from __future__ import annotations

import sys
import os

import pytest

# Allow importing scripts/validate.py from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from validate import (  # noqa: E402 — must be after sys.path insert
    check_plugin_yaml,
    check_skills,
    check_agents_yaml,
    check_agent_specifics,
    check_commands,
    check_extensions,
    check_references,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _passes(results):
    return [r for r in results if r[0]]


def _fails(results):
    return [r for r in results if not r[0]]


# ---------------------------------------------------------------------------
# Check 1 — plugin.yaml
# ---------------------------------------------------------------------------

class TestPluginYaml:
    def test_pass_with_all_required_fields(self, tmp_path):
        (tmp_path / "plugin.yaml").write_text(
            "name: myplugin\ntitle: My Plugin\nversion: 1.0.0\ndescription: A plugin\n"
        )
        results = check_plugin_yaml(tmp_path)
        assert _passes(results), "expected at least one PASS"
        assert not _fails(results), f"unexpected FAILs: {_fails(results)}"

    def test_fail_when_file_missing(self, tmp_path):
        results = check_plugin_yaml(tmp_path)
        assert _fails(results), "expected FAIL when plugin.yaml absent"

    def test_fail_when_name_missing(self, tmp_path):
        (tmp_path / "plugin.yaml").write_text(
            "title: My Plugin\nversion: 1.0.0\ndescription: A plugin\n"
        )
        assert _fails(check_plugin_yaml(tmp_path))

    def test_fail_when_title_missing(self, tmp_path):
        (tmp_path / "plugin.yaml").write_text(
            "name: myplugin\nversion: 1.0.0\ndescription: A plugin\n"
        )
        assert _fails(check_plugin_yaml(tmp_path))

    def test_fail_when_version_missing(self, tmp_path):
        (tmp_path / "plugin.yaml").write_text(
            "name: myplugin\ntitle: My Plugin\ndescription: A plugin\n"
        )
        assert _fails(check_plugin_yaml(tmp_path))

    def test_fail_when_description_missing(self, tmp_path):
        (tmp_path / "plugin.yaml").write_text(
            "name: myplugin\ntitle: My Plugin\nversion: 1.0.0\n"
        )
        assert _fails(check_plugin_yaml(tmp_path))


# ---------------------------------------------------------------------------
# Check 2 — skills/*/SKILL.md
# ---------------------------------------------------------------------------

class TestSkills:
    def _make_skill(self, root, name, content):
        d = root / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(content)

    def test_pass_with_valid_skill(self, tmp_path):
        self._make_skill(
            tmp_path, "my-skill",
            "---\nname: my-skill\ndescription: Does things\n---\n\n# My Skill\n",
        )
        results = check_skills(tmp_path)
        assert _passes(results)
        assert not _fails(results)

    def test_fail_when_skill_md_missing(self, tmp_path):
        (tmp_path / "skills" / "empty-skill").mkdir(parents=True)
        assert _fails(check_skills(tmp_path))

    def test_fail_when_name_missing_from_frontmatter(self, tmp_path):
        self._make_skill(
            tmp_path, "bad-skill",
            "---\ndescription: Does things\n---\n\n# Bad Skill\n",
        )
        assert _fails(check_skills(tmp_path))

    def test_fail_when_description_missing_from_frontmatter(self, tmp_path):
        self._make_skill(
            tmp_path, "bad-skill",
            "---\nname: bad-skill\n---\n\n# Bad Skill\n",
        )
        assert _fails(check_skills(tmp_path))

    def test_fail_when_no_frontmatter(self, tmp_path):
        self._make_skill(tmp_path, "no-front", "# Just content\n")
        assert _fails(check_skills(tmp_path))

    def test_no_skills_dir_returns_empty_list(self, tmp_path):
        results = check_skills(tmp_path)
        assert results == []


# ---------------------------------------------------------------------------
# Check 3 — agents/*/agent.yaml
# ---------------------------------------------------------------------------

class TestAgentsYaml:
    def _make_agent(self, root, name, content):
        d = root / "agents" / name
        d.mkdir(parents=True)
        (d / "agent.yaml").write_text(content)

    def test_pass_with_valid_agent_yaml(self, tmp_path):
        self._make_agent(
            tmp_path, "my-agent",
            "title: My Agent\ndescription: Does things\ncontext: Use for tasks\n",
        )
        results = check_agents_yaml(tmp_path)
        assert _passes(results)
        assert not _fails(results)

    def test_fail_when_agent_yaml_missing(self, tmp_path):
        (tmp_path / "agents" / "naked-agent").mkdir(parents=True)
        assert _fails(check_agents_yaml(tmp_path))

    def test_fail_when_title_missing(self, tmp_path):
        self._make_agent(
            tmp_path, "bad-agent",
            "description: Does things\ncontext: Use for tasks\n",
        )
        assert _fails(check_agents_yaml(tmp_path))

    def test_fail_when_description_missing(self, tmp_path):
        self._make_agent(
            tmp_path, "bad-agent",
            "title: My Agent\ncontext: Use for tasks\n",
        )
        assert _fails(check_agents_yaml(tmp_path))

    def test_fail_when_context_missing(self, tmp_path):
        self._make_agent(
            tmp_path, "bad-agent",
            "title: My Agent\ndescription: Does things\n",
        )
        assert _fails(check_agents_yaml(tmp_path))

    def test_no_agents_dir_returns_empty_list(self, tmp_path):
        assert check_agents_yaml(tmp_path) == []


# ---------------------------------------------------------------------------
# Check 4 — agents/*/prompts/agent.system.main.specifics.md
# ---------------------------------------------------------------------------

class TestAgentSpecifics:
    def _make_agent_prompts(self, root, name, include_specifics=True):
        d = root / "agents" / name / "prompts"
        d.mkdir(parents=True)
        if include_specifics:
            (d / "agent.system.main.specifics.md").write_text("# Specifics\n")

    def test_pass_when_specifics_exists(self, tmp_path):
        self._make_agent_prompts(tmp_path, "my-agent")
        results = check_agent_specifics(tmp_path)
        assert _passes(results)
        assert not _fails(results)

    def test_fail_when_specifics_missing(self, tmp_path):
        self._make_agent_prompts(tmp_path, "my-agent", include_specifics=False)
        assert _fails(check_agent_specifics(tmp_path))

    def test_fail_when_no_prompts_dir(self, tmp_path):
        (tmp_path / "agents" / "my-agent").mkdir(parents=True)
        assert _fails(check_agent_specifics(tmp_path))

    def test_no_agents_dir_returns_empty_list(self, tmp_path):
        assert check_agent_specifics(tmp_path) == []


# ---------------------------------------------------------------------------
# Check 5 — commands/*.command.yaml
# ---------------------------------------------------------------------------

class TestCommands:
    def _make_command(self, root, name, yaml_content, txt_name=None, txt_content="Do something\n"):
        d = root / "commands"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.command.yaml").write_text(yaml_content)
        if txt_name:
            (d / txt_name).write_text(txt_content)

    def test_pass_with_valid_command(self, tmp_path):
        self._make_command(
            tmp_path, "mycmd",
            "name: mycmd\ndescription: Does stuff\ntype: text\ntemplate_path: mycmd.txt\n",
            txt_name="mycmd.txt",
        )
        results = check_commands(tmp_path)
        assert _passes(results)
        assert not _fails(results)

    def test_fail_when_name_missing(self, tmp_path):
        self._make_command(
            tmp_path, "badcmd",
            "description: Does stuff\ntype: text\ntemplate_path: badcmd.txt\n",
            txt_name="badcmd.txt",
        )
        assert _fails(check_commands(tmp_path))

    def test_fail_when_description_missing(self, tmp_path):
        self._make_command(
            tmp_path, "badcmd",
            "name: badcmd\ntype: text\ntemplate_path: badcmd.txt\n",
            txt_name="badcmd.txt",
        )
        assert _fails(check_commands(tmp_path))

    def test_fail_when_type_missing(self, tmp_path):
        self._make_command(
            tmp_path, "badcmd",
            "name: badcmd\ndescription: Does stuff\ntemplate_path: badcmd.txt\n",
            txt_name="badcmd.txt",
        )
        assert _fails(check_commands(tmp_path))

    def test_fail_when_template_path_missing(self, tmp_path):
        self._make_command(
            tmp_path, "badcmd",
            "name: badcmd\ndescription: Does stuff\ntype: text\n",
            txt_name="badcmd.txt",
        )
        assert _fails(check_commands(tmp_path))

    def test_fail_when_paired_txt_missing(self, tmp_path):
        self._make_command(
            tmp_path, "badcmd",
            "name: badcmd\ndescription: Does stuff\ntype: text\ntemplate_path: badcmd.txt\n",
            # no txt_name — .txt absent
        )
        assert _fails(check_commands(tmp_path))

    def test_no_commands_dir_returns_empty_list(self, tmp_path):
        assert check_commands(tmp_path) == []

    def test_fail_when_template_path_escapes_commands_dir(self, tmp_path):
        """I3: template_path: ../../README.md must FAIL even when the file exists."""
        # Create the target that would be reached by path traversal
        readme = tmp_path / "README.md"
        readme.write_text("# Root readme\n")
        self._make_command(
            tmp_path, "escapecmd",
            "name: escapecmd\ndescription: Escape test\ntype: text\ntemplate_path: ../../README.md\n",
            # No txt_name — the point is path escape, not missing file
        )
        results = check_commands(tmp_path)
        assert _fails(results), "expected FAIL for template_path that escapes commands dir"
        fail_msgs = [msg for _, msg in _fails(results)]
        assert any("escapes" in m for m in fail_msgs), (
            f"expected 'escapes' in failure message, got: {fail_msgs}"
        )


# ---------------------------------------------------------------------------
# Check 6 — extensions/**/*.py syntax
# ---------------------------------------------------------------------------

class TestExtensions:
    def _make_ext(self, root, subdir, filename, content):
        d = root / "extensions" / subdir
        d.mkdir(parents=True, exist_ok=True)
        (d / filename).write_text(content)

    def test_pass_with_valid_python(self, tmp_path):
        self._make_ext(tmp_path, "python/agent_init", "_10_register.py", "x = 1\n")
        results = check_extensions(tmp_path)
        assert _passes(results)
        assert not _fails(results)

    def test_fail_with_invalid_python(self, tmp_path):
        self._make_ext(tmp_path, "python/agent_init", "_20_bad.py", "def broken(\n")
        assert _fails(check_extensions(tmp_path))

    def test_utility_module_syntax_error_is_caught(self, tmp_path):
        """I4: simplify_ignore_utils.py (non-_NN_ name) must be caught too."""
        self._make_ext(tmp_path, "python", "simplify_ignore_utils.py", "def broken(\n")
        results = check_extensions(tmp_path)
        assert _fails(results), (
            "expected FAIL for syntax error in simplify_ignore_utils.py"
        )

    def test_utility_module_valid_syntax_passes(self, tmp_path):
        """I4: simplify_ignore_utils.py with valid syntax produces PASS."""
        self._make_ext(tmp_path, "python", "simplify_ignore_utils.py", "CACHE_KEY = 'x'\n")
        results = check_extensions(tmp_path)
        assert _passes(results)
        assert not _fails(results)

    def test_no_extensions_dir_returns_empty_list(self, tmp_path):
        assert check_extensions(tmp_path) == []


# ---------------------------------------------------------------------------
# Check 7 — references/*.md non-empty
# ---------------------------------------------------------------------------

class TestReferences:
    def test_pass_with_non_empty_md(self, tmp_path):
        d = tmp_path / "references"
        d.mkdir()
        (d / "checklist.md").write_text("# Checklist\nItem 1\n")
        results = check_references(tmp_path)
        assert _passes(results)
        assert not _fails(results)

    def test_fail_with_empty_md(self, tmp_path):
        d = tmp_path / "references"
        d.mkdir()
        (d / "empty.md").write_text("")
        assert _fails(check_references(tmp_path))

    def test_non_md_files_ignored(self, tmp_path):
        d = tmp_path / "references"
        d.mkdir()
        (d / "notes.txt").write_text("")
        # .txt file ignored, no failures
        assert not _fails(check_references(tmp_path))

    def test_no_references_dir_returns_empty_list(self, tmp_path):
        assert check_references(tmp_path) == []
