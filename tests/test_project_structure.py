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
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Files that must NOT exist in the public repo root.
# Adding an entry here automatically adds a failing test if that path
# re-appears in the root — no other change needed.
DEV_TRACKING_FILES_NOT_IN_ROOT = [
    "SPEC.md",
    "tasks",
]

# Dev tracking paths that must exist under .a0proj/ (gitignored).
# Adding an entry here automatically adds a failing test if that path
# goes missing from .a0proj/ — no other change needed.
DEV_TRACKING_PATHS_IN_A0PROJ = [
    ".a0proj/specs/SPEC.md",
    ".a0proj/tasks/plan.md",
    ".a0proj/tasks/todo.md",
]

# Patterns that must appear in .gitignore.
# Adding a pattern here automatically tests that it is gitignored.
GITIGNORED_PATTERNS = [
    ".a0proj/",
]

# Plugin artifacts that must remain in the public repo root.
# Adding an entry here automatically guards it against accidental deletion.
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
    """Dev tracking files must not appear in the public repo root.

    Parametrized over DEV_TRACKING_FILES_NOT_IN_ROOT — add a path to that
    list to automatically require it to be absent from the root.
    """

    @pytest.mark.parametrize("name", DEV_TRACKING_FILES_NOT_IN_ROOT)
    def test_dev_tracking_file_not_in_root(self, name):
        assert not (PROJECT_ROOT / name).exists(), (
            f"'{name}' found in repo root — dev tracking must live in .a0proj/"
        )


class TestDevTrackingInA0Proj:
    """Dev tracking files must exist under .a0proj/ (gitignored).

    Parametrized over DEV_TRACKING_PATHS_IN_A0PROJ — add a path to that
    list to automatically require it to exist under .a0proj/.
    """

    def test_a0proj_dir_exists(self):
        assert (PROJECT_ROOT / ".a0proj").exists(), ".a0proj/ directory must exist"

    def test_a0proj_specs_dir_exists(self):
        assert (PROJECT_ROOT / ".a0proj" / "specs").exists(), ".a0proj/specs/ must exist"

    def test_a0proj_tasks_dir_exists(self):
        assert (PROJECT_ROOT / ".a0proj" / "tasks").exists(), ".a0proj/tasks/ must exist"

    @pytest.mark.parametrize("rel_path", DEV_TRACKING_PATHS_IN_A0PROJ)
    def test_dev_tracking_file_in_a0proj(self, rel_path):
        assert (PROJECT_ROOT / rel_path).exists(), (
            f"Dev tracking file missing: {rel_path} — should exist under .a0proj/"
        )


class TestGitIgnoreCoversDevTracking:
    """Verify .gitignore permanently excludes dev tracking from version control."""

    @pytest.mark.parametrize("pattern", GITIGNORED_PATTERNS)
    def test_pattern_in_gitignore(self, pattern):
        """Each GITIGNORED_PATTERNS entry must appear literally in .gitignore."""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text()
        assert pattern in gitignore, (
            f"'{pattern}' must be in .gitignore to prevent dev tracking from being committed"
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
    """All public plugin artifacts must still be present in repo root.

    Parametrized over PUBLIC_ROOT_ARTIFACTS — add an entry to that list
    to automatically guard it against accidental deletion.
    """

    @pytest.mark.parametrize("artifact", PUBLIC_ROOT_ARTIFACTS)
    def test_public_artifact_present(self, artifact):
        assert (PROJECT_ROOT / artifact).exists(), (
            f"Public artifact '{artifact}' missing from repo root"
        )
