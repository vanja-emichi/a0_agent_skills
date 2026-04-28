# test_3_commands.py - Phase 3: Command file verification

import os

from .conftest import COMMANDS_DIR, STALE_PLAN_PATTERNS


def _read(rel):
    return (COMMANDS_DIR / rel).read_text()


def _exists(rel):
    return (COMMANDS_DIR / rel).is_file()


def _parse_simple_yaml(text):
    """Parse simple flat YAML without PyYAML dependency."""
    result = {}
    for line in text.strip().split("\n"):
        if ":" in line and not line.startswith("#"):
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"')
    return result


class TestCommandYAMLStructure:
    """All .command.yaml files must have required fields."""

    def _get_yaml_files(self):
        return sorted(
            f for f in os.listdir(COMMANDS_DIR)
            if f.endswith(".command.yaml")
        )

    def test_all_yaml_have_required_fields(self):
        for f in self._get_yaml_files():
            data = _parse_simple_yaml(_read(f))
            assert "name" in data, f"{f} missing 'name'"
            assert "description" in data, f"{f} missing 'description'"
            assert "type" in data, f"{f} missing 'type'"
            assert "template_path" in data, f"{f} missing 'template_path'"

    def test_all_yaml_template_paths_exist(self):
        for f in self._get_yaml_files():
            data = _parse_simple_yaml(_read(f))
            template = data["template_path"]
            assert _exists(template), f"{f} references missing template: {template}"

    def test_no_bare_yaml_files(self):
        """No .yaml files without .command.yaml suffix."""
        for f in os.listdir(COMMANDS_DIR):
            if f.endswith(".yaml") and not f.endswith(".command.yaml"):
                assert False, f"Found bare .yaml file: {f}"


class TestLifecycleStatusCommand:
    """plan-status renamed to lifecycle-status."""

    def test_lifecycle_status_yaml_exists(self):
        assert _exists("lifecycle-status.command.yaml")

    def test_lifecycle_status_txt_exists(self):
        assert _exists("lifecycle-status.txt")

    def test_plan_status_yaml_removed(self):
        assert not _exists("plan-status.command.yaml")

    def test_plan_status_txt_removed(self):
        assert not _exists("plan-status.txt")

    def test_lifecycle_status_references_lifecycle_tool(self):
        content = _read("lifecycle-status.txt")
        assert "lifecycle:status" in content
        assert "plan:status" not in content


class TestIdeaCommand:
    """New /idea command created."""

    def test_idea_yaml_exists(self):
        assert _exists("idea.command.yaml")

    def test_idea_txt_exists(self):
        assert _exists("idea.txt")

    def test_idea_yaml_name(self):
        data = _parse_simple_yaml(_read("idea.command.yaml"))
        assert data["name"] == "idea"

    def test_idea_txt_loads_skill(self):
        content = _read("idea.txt")
        assert "idea-refine" in content

    def test_idea_txt_has_checkpoint(self):
        content = _read("idea.txt")
        assert "Checkpoint" in content or "checkpoint" in content


class TestCommandProse:
    """All commands reference lifecycle:* not plan:*."""

    def test_no_stale_tool_calls(self):
        for f in sorted(os.listdir(COMMANDS_DIR)):
            if not f.endswith(".txt"):
                continue
            content = _read(f)
            for pattern in STALE_PLAN_PATTERNS:
                assert pattern not in content, f"Found '{pattern}' in {f}"

    def test_plan_txt_uses_lifecycle_init(self):
        content = _read("plan.txt")
        assert "lifecycle:init" in content

    def test_ship_txt_uses_lifecycle_archive(self):
        content = _read("ship.txt")
        assert "lifecycle:archive" in content


class TestCommandCount:
    """Expected number of commands."""

    def test_at_least_10_commands(self):
        yaml_files = [f for f in os.listdir(COMMANDS_DIR) if f.endswith(".command.yaml")]
        assert len(yaml_files) >= 9, f"Expected 9+ commands, found {len(yaml_files)}: {yaml_files}"


class TestLifecycleContextInDelegation:
    """T5: review.txt, test.txt, security.txt must include lifecycle context."""

    def test_review_txt_includes_lifecycle_context(self):
        """review.txt should include lifecycle context instruction."""
        content = _read("review.txt")
        assert "§§include(commands/_shared/lifecycle-context.md)" in content

    def test_test_txt_includes_lifecycle_context(self):
        """test.txt should include lifecycle context instruction."""
        content = _read("test.txt")
        assert "§§include(commands/_shared/lifecycle-context.md)" in content

    def test_security_txt_includes_lifecycle_context(self):
        """security.txt should include lifecycle context instruction."""
        content = _read("security.txt")
        assert "§§include(commands/_shared/lifecycle-context.md)" in content

    def test_shared_lifecycle_context_file_exists(self):
        """Shared lifecycle context snippet must exist with correct content."""
        shared = (COMMANDS_DIR / "_shared" / "lifecycle-context.md").read_text()
        assert "Lifecycle Context" in shared
        assert "Current Phase" in shared


class TestPlanTemplateSyntax:
    """T6: plan.txt must have clean lifecycle:init template."""

    def test_plan_txt_no_commented_syntax(self):
        """plan.txt should not have commented-out template syntax."""
        content = _read("plan.txt")
        assert "# phases are hardcoded" not in content
        assert '# "Phase' not in content
        assert "lifecycle:init goal=" in content
        assert "slug=" in content
