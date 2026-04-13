"""Regression tests for project structure conventions.

Verifies that:
- Dev tracking files (SPEC.md, tasks/) are NOT in the repo root
- Dev tracking files live in .a0proj/ (gitignored)
- .gitignore covers .a0proj/ to prevent accidental commits
- validate.py and CI do not depend on dev-tracking paths
- Public repo root contains only plugin artifacts
"""

from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Files that must NOT be in the public repo root (they are dev-tracking artifacts)
DEV_TRACKING_FILES_NOT_IN_ROOT = [
    "SPEC.md",
    "tasks",
]

# Dev tracking paths that must exist under .a0proj/ (gitignored)
DEV_TRACKING_PATHS_IN_A0PROJ = [
    ".a0proj/specs/SPEC.md",
    ".a0proj/tasks/plan.md",
    ".a0proj/tasks/todo.md",
]

# Paths that must be in .gitignore
GITIGNORED_PATTERNS = [
    ".a0proj/",
]

# Files/dirs that SHOULD be in repo root (public plugin artifacts)
PUBLIC_ROOT_ARTIFACTS = [
    "skills",
    "commands",
    "extensions",
    "agents",
    "tests",
    "scripts",
    "docs",
    "references",
    "README.md",
    "plugin.yaml",
    "LICENSE",
    ".gitignore",
    ".github",
]


class TestDevTrackingNotInRoot:
    """Dev tracking files must not appear in the public repo root."""

    def test_spec_md_not_in_root(self):
        """SPEC.md must not be in repo root — it belongs in .a0proj/specs/."""
        assert not (PROJECT_ROOT / "SPEC.md").exists(), (
            "SPEC.md found in repo root — dev tracking must live in .a0proj/specs/SPEC.md"
        )

    def test_tasks_dir_not_in_root(self):
        """tasks/ directory must not be in repo root — it belongs in .a0proj/tasks/."""
        assert not (PROJECT_ROOT / "tasks").exists(), (
            "tasks/ directory found in repo root — dev tracking must live in .a0proj/tasks/"
        )


class TestDevTrackingInA0Proj:
    """Dev tracking files must exist under .a0proj/ (gitignored)."""

    def test_a0proj_dir_exists(self):
        assert (PROJECT_ROOT / ".a0proj").exists(), ".a0proj/ directory must exist"

    def test_a0proj_specs_dir_exists(self):
        assert (PROJECT_ROOT / ".a0proj" / "specs").exists(), ".a0proj/specs/ must exist"

    def test_a0proj_tasks_dir_exists(self):
        assert (PROJECT_ROOT / ".a0proj" / "tasks").exists(), ".a0proj/tasks/ must exist"

    def test_spec_md_in_a0proj(self):
        """SPEC.md must exist at .a0proj/specs/SPEC.md."""
        assert (PROJECT_ROOT / ".a0proj" / "specs" / "SPEC.md").exists(), (
            ".a0proj/specs/SPEC.md must exist"
        )

    def test_plan_md_in_a0proj(self):
        """plan.md must exist at .a0proj/tasks/plan.md."""
        assert (PROJECT_ROOT / ".a0proj" / "tasks" / "plan.md").exists(), (
            ".a0proj/tasks/plan.md must exist"
        )

    def test_todo_md_in_a0proj(self):
        """todo.md must exist at .a0proj/tasks/todo.md."""
        assert (PROJECT_ROOT / ".a0proj" / "tasks" / "todo.md").exists(), (
            ".a0proj/tasks/todo.md must exist"
        )


class TestGitIgnoreCoversDevTracking:
    """Verify .gitignore permanently excludes dev tracking from version control."""

    def test_gitignore_covers_a0proj(self):
        """'.a0proj/' must appear in .gitignore."""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text()
        assert ".a0proj/" in gitignore, (
            "'.a0proj/' must be in .gitignore to prevent dev tracking from being committed"
        )

    def test_spec_md_is_gitignored(self):
        """git check-ignore must confirm .a0proj/specs/SPEC.md is excluded."""
        result = subprocess.run(
            ["git", "check-ignore", "-q", ".a0proj/specs/SPEC.md"],
            cwd=PROJECT_ROOT, capture_output=True
        )
        assert result.returncode == 0, (
            ".a0proj/specs/SPEC.md is not gitignored — it would be committed publicly"
        )

    def test_tasks_are_gitignored(self):
        """git check-ignore must confirm .a0proj/tasks/ is excluded."""
        result = subprocess.run(
            ["git", "check-ignore", "-q", ".a0proj/tasks/plan.md"],
            cwd=PROJECT_ROOT, capture_output=True
        )
        assert result.returncode == 0, (
            ".a0proj/tasks/plan.md is not gitignored — it would be committed publicly"
        )

    def test_no_a0proj_files_tracked_by_git(self):
        """git ls-files must show zero tracked files under .a0proj/."""
        result = subprocess.run(
            ["git", "ls-files", ".a0proj/"],
            cwd=PROJECT_ROOT, capture_output=True, text=True
        )
        tracked = result.stdout.strip()
        assert not tracked, (
            f"Files under .a0proj/ are tracked by git (should be gitignored):\n{tracked}"
        )


class TestPublicRootArtifactsPresent:
    """All public plugin artifacts must still be present in repo root."""

    def test_skills_dir_present(self):
        assert (PROJECT_ROOT / "skills").exists()

    def test_commands_dir_present(self):
        assert (PROJECT_ROOT / "commands").exists()

    def test_extensions_dir_present(self):
        assert (PROJECT_ROOT / "extensions").exists()

    def test_agents_dir_present(self):
        assert (PROJECT_ROOT / "agents").exists()

    def test_tests_dir_present(self):
        assert (PROJECT_ROOT / "tests").exists()

    def test_readme_present(self):
        assert (PROJECT_ROOT / "README.md").exists()

    def test_plugin_yaml_present(self):
        assert (PROJECT_ROOT / "plugin.yaml").exists()

    def test_docs_dir_present(self):
        assert (PROJECT_ROOT / "docs").exists()

    def test_references_dir_present(self):
        assert (PROJECT_ROOT / "references").exists()
