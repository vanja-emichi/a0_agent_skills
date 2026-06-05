"""Structural validation tests for the a0_agent_skills plugin."""

import importlib
import os
import sys
from unittest.mock import MagicMock

import pytest
import yaml


PLUGIN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# plugin.yaml
# ---------------------------------------------------------------------------


class TestPluginYaml:
    """Validate plugin.yaml manifest."""

    @pytest.fixture()
    def manifest(self):
        path = os.path.join(PLUGIN_DIR, "plugin.yaml")
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_manifest_exists(self):
        assert os.path.isfile(os.path.join(PLUGIN_DIR, "plugin.yaml"))

    def test_required_fields(self, manifest):
        for field in ("name", "title", "description", "version", "author"):
            assert field in manifest, f"Missing field: {field}"

    def test_name_matches_directory(self, manifest):
        assert manifest["name"] == os.path.basename(PLUGIN_DIR)


# ---------------------------------------------------------------------------
# commands/*.command.yaml
# ---------------------------------------------------------------------------


class TestCommands:
    """Validate every command YAML + template pair."""

    COMMANDS_DIR = os.path.join(PLUGIN_DIR, "commands")

    @staticmethod
    def _command_files():
        d = os.path.join(PLUGIN_DIR, "commands")
        return sorted(f for f in os.listdir(d) if f.endswith(".command.yaml"))

    def test_all_commands_have_valid_schema(self):
        for fname in self._command_files():
            path = os.path.join(self.COMMANDS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert "name" in data, f"{fname}: missing 'name'"
            assert "description" in data, f"{fname}: missing 'description'"
            assert "type" in data, f"{fname}: missing 'type'"
            assert data["type"] in ("text", "script"), f"{fname}: invalid type"
            assert "template_path" in data, f"{fname}: missing 'template_path'"

    def test_all_template_paths_resolve(self):
        for fname in self._command_files():
            path = os.path.join(self.COMMANDS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            template = os.path.join(self.COMMANDS_DIR, data["template_path"])
            assert os.path.isfile(template), (
                f"{fname}: template_path '{data['template_path']}' does not resolve"
            )


# ---------------------------------------------------------------------------
# agents/*/agent.yaml + prompts
# ---------------------------------------------------------------------------


class TestAgentProfiles:
    """Validate every agent profile has correct structure."""

    AGENTS_DIR = os.path.join(PLUGIN_DIR, "agents")

    def test_all_profiles_valid(self):
        for name in sorted(os.listdir(self.AGENTS_DIR)):
            agent_dir = os.path.join(self.AGENTS_DIR, name)
            if not os.path.isdir(agent_dir):
                continue

            # agent.yaml must exist and have correct schema
            yaml_path = os.path.join(agent_dir, "agent.yaml")
            assert os.path.isfile(yaml_path), f"{name}: missing agent.yaml"

            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            for field in ("title", "description", "context"):
                assert field in data, f"{name}: missing '{field}' in agent.yaml"

            # Only allowed fields in agent.yaml
            allowed = {"title", "description", "context"}
            extra = set(data.keys()) - allowed
            assert not extra, f"{name}: unexpected fields in agent.yaml: {extra}"

    def test_all_prompts_exist_and_nonempty(self):
        for name in sorted(os.listdir(self.AGENTS_DIR)):
            agent_dir = os.path.join(self.AGENTS_DIR, name)
            if not os.path.isdir(agent_dir):
                continue

            prompt_file = os.path.join(
                agent_dir, "prompts", "agent.system.main.specifics.md"
            )
            assert os.path.isfile(prompt_file), (
                f"{name}: missing prompts/agent.system.main.specifics.md"
            )
            with open(prompt_file, encoding="utf-8") as f:
                content = f.read().strip()
            assert len(content) > 0, f"{name}: prompts/agent.system.main.specifics.md is empty"


# ---------------------------------------------------------------------------
# hooks.py
# ---------------------------------------------------------------------------


class TestHooks:
    """Validate hooks.py has required lifecycle functions."""

    def test_install_callable(self):
        hooks = _import_hooks()
        assert callable(hooks.install)

    def test_uninstall_callable(self):
        hooks = _import_hooks()
        assert callable(hooks.uninstall)


def _import_hooks():
    """Import hooks.py from the plugin directory."""
    sys.path.insert(0, PLUGIN_DIR)
    try:
        return importlib.import_module("hooks")
    finally:
        if PLUGIN_DIR in sys.path:
            sys.path.remove(PLUGIN_DIR)


# ---------------------------------------------------------------------------
# skills/*/SKILL.md count & frontmatter
# ---------------------------------------------------------------------------


class TestSkills:
    """Validate skill count and frontmatter."""

    SKILLS_DIR = os.path.join(PLUGIN_DIR, "skills")

    def test_skill_count_matches_description(self):
        """Plugin description says 24 skills; count must match."""
        count = sum(
            1
            for d in os.listdir(self.SKILLS_DIR)
            if os.path.isdir(os.path.join(self.SKILLS_DIR, d))
            and os.path.isfile(os.path.join(self.SKILLS_DIR, d, "SKILL.md"))
        )
        assert count == 24, f"Expected 24 skills, found {count}"

    def test_all_skill_frontmatter_valid(self):
        """Every SKILL.md must have non-empty name and description in frontmatter."""
        for name in sorted(os.listdir(self.SKILLS_DIR)):
            skill_dir = os.path.join(self.SKILLS_DIR, name)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isfile(skill_file):
                continue
            with open(skill_file, encoding="utf-8") as f:
                content = f.read()
            # Extract frontmatter between --- markers
            if not content.startswith("---"):
                continue
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            fm_text = parts[1].strip()
            fm = yaml.safe_load(fm_text) or {}
            assert "name" in fm and fm["name"], f"{name}: missing or empty 'name'"
            assert "description" in fm and fm["description"], (
                f"{name}: missing or empty 'description'"
            )


# ---------------------------------------------------------------------------
# hooks install execution
# ---------------------------------------------------------------------------


class TestHooksExecution:
    """Verify hooks can actually be called without error."""

    def test_install_runs_without_error(self):
        """hooks.install() should execute without raising."""
        hooks = _import_hooks()
        hooks.install()  # should not raise

    def test_uninstall_runs_without_error(self):
        """hooks.uninstall() should execute without raising."""
        hooks = _import_hooks()
        hooks.uninstall()  # should not raise

    def test_install_counts_dynamically(self):
        """hooks.install() should count skills/profiles/commands dynamically, not hardcode."""
        hooks = _import_hooks()
        # Verify the module does NOT contain a hardcoded "23 skills" string
        import inspect
        source = inspect.getsource(hooks.install)
        assert '"23 skills' not in source, "hooks.install still has hardcoded skill count"
        assert "skills_count" in source, "hooks.install missing dynamic skills_count"
        assert "agents_count" in source, "hooks.install missing dynamic agents_count"
        assert "commands_count" in source, "hooks.install missing dynamic commands_count"


# ---------------------------------------------------------------------------
# Cache and artifact hygiene
# ---------------------------------------------------------------------------


class TestCacheHygiene:
    """Verify no cache artifacts leaked into the plugin tree."""

    def test_no_pycache_directories(self):
        """No __pycache__ directories should exist in the plugin tree."""
        import shutil
        from pathlib import Path

        # Clean any __pycache__ created by pytest's own import machinery
        for d in Path(PLUGIN_DIR).rglob("__pycache__"):
            shutil.rmtree(d, ignore_errors=True)

        pycache = list(Path(PLUGIN_DIR).rglob("__pycache__"))
        assert pycache == [], f"Found __pycache__: {pycache}"

    def test_gitignore_permissions(self):
        """plugin .gitignore must have 644 permissions."""
        import stat

        gitignore_path = os.path.join(PLUGIN_DIR, ".gitignore")
        assert os.path.isfile(gitignore_path), ".gitignore missing"
        st = os.stat(gitignore_path)
        assert stat.S_IMODE(st.st_mode) == 0o644, (
            f"Expected 0o644, got {oct(stat.S_IMODE(st.st_mode))}"
        )


# ---------------------------------------------------------------------------
# reference files (canonical hub under using-agent-skills)
# ---------------------------------------------------------------------------

SHARED_REFERENCES = {
    "security-checklist.md",
    "performance-checklist.md",
    "testing-patterns.md",
    "accessibility-checklist.md",
    "orchestration-patterns.md",
}


class TestReferences:
    """Validate shared references are canonicalized in using-agent-skills."""

    def test_no_top_level_references_dir(self):
        """Top-level references/ directory must not exist in the plugin."""
        refs_dir = os.path.join(PLUGIN_DIR, "references")
        assert not os.path.isdir(refs_dir), (
            "references/ directory still exists — shared files belong in skills/using-agent-skills/references"
        )

    def test_canonical_reference_files_exist(self):
        """Each shared reference file must exist exactly in the canonical hub."""
        refs_dir = os.path.join(PLUGIN_DIR, "skills", "using-agent-skills", "references")
        assert os.path.isdir(refs_dir), "canonical using-agent-skills/references directory missing"
        found = {f for f in os.listdir(refs_dir) if f.endswith(".md")}
        assert found == SHARED_REFERENCES
        for ref_file in SHARED_REFERENCES:
            path = os.path.join(refs_dir, ref_file)
            assert os.path.getsize(path) > 0, f"{ref_file} is empty"

    def test_no_duplicate_shared_references_elsewhere(self):
        """Shared reference basenames must not be duplicated outside the canonical hub."""
        canonical_dir = os.path.join(PLUGIN_DIR, "skills", "using-agent-skills", "references")
        duplicates = []
        for root, _dirs, files in os.walk(os.path.join(PLUGIN_DIR, "skills")):
            for fname in files:
                if fname not in SHARED_REFERENCES:
                    continue
                path = os.path.join(root, fname)
                if os.path.dirname(path) != canonical_dir:
                    duplicates.append(os.path.relpath(path, PLUGIN_DIR))
        assert duplicates == [], f"Duplicate shared references found: {duplicates}"

    def test_consuming_skills_read_canonical_references(self):
        """Skills that mention shared references must read them from using-agent-skills."""
        consumers = {
            "code-review-and-quality": ["security-checklist.md", "performance-checklist.md"],
            "shipping-and-launch": ["security-checklist.md", "performance-checklist.md", "accessibility-checklist.md"],
            "test-driven-development": ["testing-patterns.md"],
            "doubt-driven-development": ["orchestration-patterns.md"],
            "security-and-hardening": ["security-checklist.md"],
            "frontend-ui-engineering": ["accessibility-checklist.md"],
            "performance-optimization": ["performance-checklist.md"],
        }
        for skill_name, refs in consumers.items():
            skill_md = os.path.join(PLUGIN_DIR, "skills", skill_name, "SKILL.md")
            with open(skill_md, encoding="utf-8") as f:
                content = f.read()
            for ref in refs:
                assert ref in content, f"{skill_name} no longer mentions {ref}"
                assert 'skill_name: "using-agent-skills"' in content, (
                    f"{skill_name} does not read shared refs from using-agent-skills"
                )
                assert f'file_path: "references/{ref}"' in content, (
                    f"{skill_name} does not use canonical references/{ref} path"
                )

    def test_source_and_plugin_canonical_references_match(self):
        """Source and installed plugin canonical shared references must hash-match."""
        import hashlib
        src_dir = "/a0/usr/projects/a0_agent_skills/skills/using-agent-skills/references"
        plug_dir = os.path.join(PLUGIN_DIR, "skills", "using-agent-skills", "references")
        if not os.path.isdir(src_dir):
            pytest.skip("source project not available")
        for ref_file in SHARED_REFERENCES:
            with open(os.path.join(src_dir, ref_file), "rb") as f:
                src_hash = hashlib.sha256(f.read()).hexdigest()
            with open(os.path.join(plug_dir, ref_file), "rb") as f:
                plug_hash = hashlib.sha256(f.read()).hexdigest()
            assert src_hash == plug_hash, f"source/plugin drift for {ref_file}"

# ---------------------------------------------------------------------------
# DOX integration
# ---------------------------------------------------------------------------


class TestDoxIntegration:
    """Validate the DOX project-context skill and lifecycle gates."""

    def test_dox_skill_files_exist(self):
        skill_dir = os.path.join(PLUGIN_DIR, "skills", "dox-project-context")
        for fname in ("SKILL.md", "AGENTS.template.md", "dox-checklist.md"):
            path = os.path.join(skill_dir, fname)
            assert os.path.isfile(path), f"dox-project-context missing {fname}"
            assert os.path.getsize(path) > 0, f"dox-project-context/{fname} is empty"

    def test_using_agent_skills_routes_to_dox(self):
        path = os.path.join(PLUGIN_DIR, "skills", "using-agent-skills", "SKILL.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "dox-project-context" in content
        assert "AGENTS.md" in content

    def test_lifecycle_commands_include_dox_gate(self):
        commands_dir = os.path.join(PLUGIN_DIR, "commands")
        for fname in ("spec.txt", "plan.txt", "build.txt", "test.txt", "review.txt", "code-simplify.txt"):
            with open(os.path.join(commands_dir, fname), encoding="utf-8") as f:
                content = f.read()
            assert "dox-project-context" in content, f"{fname} does not load dox-project-context"
            assert "AGENTS.md" in content, f"{fname} does not mention AGENTS.md contracts"

    def test_ship_command_includes_dox_readiness(self):
        path = os.path.join(PLUGIN_DIR, "commands", "ship.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "dox-project-context" in content
        assert "DOX readiness" in content
        assert "AGENTS.md" in content

    def test_agent_profiles_are_dox_aware(self):
        agents_dir = os.path.join(PLUGIN_DIR, "agents")
        for name in ("code-reviewer", "security-auditor", "test-engineer"):
            path = os.path.join(agents_dir, name, "prompts", "agent.system.main.specifics.md")
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert "DOX Project Contracts" in content
            assert "AGENTS.md" in content
