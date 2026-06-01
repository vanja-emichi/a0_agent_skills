"""Plugin contract consistency tests.

Verifies that the three core documents -- plugin.yaml, README.md, and
ship.command.yaml -- tell the same story about:
- skill count
- telemetry default
- /ship mode (parallel vs sequential)

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_plugin_contract.py -v
"""

import os
import re
import yaml
import pytest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(__file__))


def _read_plugin_yaml():
    path = os.path.join(PLUGIN_ROOT, "plugin.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _read_readme():
    path = os.path.join(PLUGIN_ROOT, "README.md")
    with open(path) as f:
        return f.read()


def _read_ship_command_yaml():
    path = os.path.join(PLUGIN_ROOT, "commands", "ship.command.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _count_skill_dirs():
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    return len([
        d for d in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, d))
        and os.path.isfile(os.path.join(skills_dir, d, "SKILL.md"))
    ])


# ===========================================================================
# Skill count
# ===========================================================================


class TestSkillCount:
    """Skill count must be consistent across plugin.yaml, README, and reality."""

    def test_actual_skill_count(self):
        """Verify we know the real skill count."""
        count = _count_skill_dirs()
        assert count == 23, f"Expected 23 skills, found {count}"

    def test_plugin_yaml_skill_count(self):
        """plugin.yaml description must mention the correct skill count."""
        data = _read_plugin_yaml()
        desc = data.get("description", "")
        match = re.search(r'(\d+)\s+skills', desc)
        assert match, "plugin.yaml description must mention '<N> skills'"
        claimed = int(match.group(1))
        actual = _count_skill_dirs()
        assert claimed == actual, (
            f"plugin.yaml claims {claimed} skills but reality is {actual}"
        )

    def test_readme_skill_count(self):
        """README intro must mention the correct skill count."""
        readme = _read_readme()
        # Look for the first occurrence of a number followed by 'skills'
        # in the opening paragraph
        match = re.search(r'\*\*(\d+)\s+curated\s+skills', readme)
        assert match, "README must contain '**<N> curated skills'"
        claimed = int(match.group(1))
        actual = _count_skill_dirs()
        assert claimed == actual, (
            f"README claims {claimed} skills but reality is {actual}"
        )


# ===========================================================================
# Telemetry default
# ===========================================================================


class TestTelemetryDefault:
    """Telemetry default must be privacy-safe (disabled) across README and config."""

    def test_readme_says_disabled_by_default(self):
        """README must state telemetry is disabled by default."""
        readme = _read_readme()
        assert "disabled by default" in readme.lower() or "off by default" in readme.lower(), (
            "README must state telemetry is 'disabled by default' or 'off by default'"
        )

    def test_readme_does_not_say_enabled_by_default(self):
        """README must NOT state telemetry is enabled by default."""
        readme = _read_readme()
        assert "enabled by default" not in readme.lower(), (
            "README must not claim telemetry is 'enabled by default'"
        )

    def test_default_config_telemetry_disabled(self):
        """default_config.yaml must have telemetry_enabled: false."""
        config_path = os.path.join(PLUGIN_ROOT, "default_config.yaml")
        if not os.path.exists(config_path):
            pytest.skip("default_config.yaml not found")
        with open(config_path) as f:
            data = yaml.safe_load(f)
        telemetry = data.get("telemetry_enabled")
        assert telemetry is False, (
            f"default_config.yaml must have telemetry_enabled: false, got {telemetry}"
        )


# ===========================================================================
# Ship command mode
# ===========================================================================


class TestShipMode:
    """The /ship command must be consistently described as parallel."""

    def test_ship_command_yaml_says_parallel(self):
        """ship.command.yaml description must mention parallel."""
        data = _read_ship_command_yaml()
        desc = data.get("description", "")
        assert "parallel" in desc.lower(), (
            "ship.command.yaml must describe the command as 'parallel'"
        )

    def test_ship_command_yaml_does_not_say_sequential(self):
        """ship.command.yaml must NOT describe the command as sequential."""
        data = _read_ship_command_yaml()
        desc = data.get("description", "")
        assert "sequential" not in desc.lower(), (
            "ship.command.yaml must not describe the command as 'sequential'"
        )

    def test_readme_ship_table_says_parallel(self):
        """README /ship table entry must say parallel."""
        readme = _read_readme()
        # Find the ship row in the commands table (may have backticks around /ship)
        ship_match = re.search(r'\|\s*`?/ship`?\s*\|(.*?)\|', readme)
        assert ship_match, "README must have a /ship row in the commands table"
        ship_desc = ship_match.group(1)
        assert "parallel" in ship_desc.lower(), (
            "README /ship table entry must say 'parallel'"
        )

    def test_readme_ship_table_does_not_say_sequential(self):
        """README /ship table entry must NOT say sequential."""
        readme = _read_readme()
        ship_match = re.search(r'\|\s*`?/ship`?\s*\|(.*?)\|', readme)
        assert ship_match, "README must have a /ship row in the commands table"
        ship_desc = ship_match.group(1)
        assert "sequential" not in ship_desc.lower(), (
            "README /ship table entry must not say 'sequential'"
        )


# ===========================================================================
# Manifest validity
# ===========================================================================


class TestManifestValidity:
    """Basic plugin.yaml validity checks."""

    def test_plugin_yaml_parseable(self):
        """plugin.yaml must be valid YAML."""
        data = _read_plugin_yaml()
        assert isinstance(data, dict)

    def test_plugin_yaml_has_required_fields(self):
        """plugin.yaml must have title and description."""
        data = _read_plugin_yaml()
        assert "title" in data or "name" in data
        assert "description" in data

    def test_plugin_yaml_mentions_agent_zero(self):
        """plugin.yaml should mention Agent Zero."""
        data = _read_plugin_yaml()
        desc = data.get("description", "")
        assert "Agent Zero" in desc, (
            "plugin.yaml description should mention 'Agent Zero'"
        )
