#!/usr/bin/env python3
"""Package an Agent Zero skill directory into a distributable .zip file.

Runs quick_validate.py first to ensure the skill is valid,
then bundles SKILL.md and all non-excluded files into a zip archive.
"""

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

# Patterns to exclude from the archive
EXCLUDE_ANYWHERE = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_NAMES = {".DS_Store"}


def should_exclude(path: Path, skill_root: Path) -> bool:
    """Check if a file or directory should be excluded from the archive.

    Exclusion rules:
    - __pycache__/ directories (anywhere)
    - *.pyc files (anywhere)
    - .DS_Store files (anywhere)
    - evals/ directory at skill root only

    Args:
        path: The file or directory path to check.
        skill_root: The root directory of the skill.

    Returns:
        True if the path should be excluded.
    """
    name = path.name

    # .DS_Store files
    if name in EXCLUDE_NAMES:
        return True

    # *.pyc files
    if path.suffix in EXCLUDE_SUFFIXES:
        return True

    # Check for excluded directory names anywhere in the relative path
    parts = path.relative_to(skill_root).parts
    if any(part in EXCLUDE_ANYWHERE for part in parts):
        return True

    # evals/ at skill root only (first directory component)
    if len(parts) > 1 and parts[0] == "evals":
        return True

    return False


def run_validation(skill_path: Path) -> bool:
    """Run quick_validate.py on the skill directory.

    Args:
        skill_path: Resolved path to the skill directory.

    Returns:
        True if validation passed, False otherwise.
    """
    validator = Path(__file__).resolve().parent / "quick_validate.py"
    result = subprocess.run(
        [sys.executable, str(validator), str(skill_path)],
        capture_output=True,
        text=True,
    )

    # Forward validator output
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    return result.returncode == 0


def package_skill(skill_path: Path, output_dir: Path) -> Path:
    """Bundle a skill directory into a .zip archive.

    Args:
        skill_path: Resolved path to the skill directory.
        output_dir: Directory where the .zip will be created.

    Returns:
        Path to the created .zip file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_filename = output_dir / f"{skill_path.name}.zip"

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
        resolved_root = skill_path.resolve()
        for file_path in sorted(skill_path.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.is_symlink():
                continue
            # Guard: skip files that resolve outside the skill root
            try:
                resolved_file = file_path.resolve()
                resolved_file.relative_to(resolved_root)
            except ValueError:
                print(f"  ⚠ Skipping (escapes root): {file_path}")
                continue

            if should_exclude(file_path, skill_path):
                rel = file_path.relative_to(skill_path)
                print(f"  ⏭  Skipping: {rel}")
                continue

            arcname = str(file_path.relative_to(skill_path.parent))
            zf.write(file_path, arcname)
            print(f"  ✅ Added: {arcname}")

    return zip_filename


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Package an Agent Zero skill into a distributable .zip file"
    )
    parser.add_argument(
        "skill_path",
        help="Path to the skill directory to package",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Output directory for the .zip file (default: current directory)",
    )
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()

    # Basic existence check before validation
    if not skill_path.exists():
        print(f"❌ Skill directory not found: {skill_path}", file=sys.stderr)
        return 1

    if not skill_path.is_dir():
        print(f"❌ Not a directory: {skill_path}", file=sys.stderr)
        return 1

    # Check SKILL.md exists before proceeding
    if not (skill_path / "SKILL.md").exists():
        print(f"❌ SKILL.md not found in {skill_path}", file=sys.stderr)
        return 1

    # Step 1: Validate
    print(f"🔍 Validating skill: {skill_path.name}")
    if not run_validation(skill_path):
        print("❌ Validation failed. Aborting packaging.", file=sys.stderr)
        return 1

    # Step 2: Package
    output_dir = Path(args.output_dir).resolve() if args.output_dir else Path.cwd()
    print(f"\n📦 Packaging '{skill_path.name}' → {output_dir}/")

    zip_path = package_skill(skill_path, output_dir)

    print(f"\n✅ Created: {zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
