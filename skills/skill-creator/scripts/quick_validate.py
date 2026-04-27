#!/usr/bin/env python3
"""Quick validation for Agent Zero skill directories."""

import argparse
import re
import sys
from pathlib import Path


def validate_skill(skill_path: str) -> tuple[bool, str]:
    """Validate a skill directory structure.

    Checks:
    - Path exists and is a directory
    - SKILL.md exists
    - YAML frontmatter contains 'name' and 'description' fields

    Args:
        skill_path: Path to the skill directory

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    path = Path(skill_path).resolve()

    # Check path exists
    if not path.exists():
        return False, f"Skill directory not found: {path}"

    # Check is a directory
    if not path.is_dir():
        return False, f"Path is not a directory: {path}"

    # Check SKILL.md exists
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found in {path}"

    # Size check
    if skill_md.stat().st_size > 1_000_000:
        return False, "SKILL.md exceeds 1MB limit"

    # Read SKILL.md
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Cannot read SKILL.md: {e}"

    # Extract YAML frontmatter
    frontmatter = _extract_frontmatter(content)
    if frontmatter is None:
        return False, "SKILL.md has no YAML frontmatter (missing --- delimiters)"

    # Check for required fields
    if not _has_field(frontmatter, "name"):
        return False, "SKILL.md frontmatter missing required field: name"

    if not _has_field(frontmatter, "description"):
        return False, "SKILL.md frontmatter missing required field: description"

    return True, f"Valid skill: {path.name}"


def _extract_frontmatter(content: str) -> str | None:
    """Extract YAML frontmatter from SKILL.md content.

    Frontmatter is delimited by --- at the start and end.
    Returns the frontmatter text, or None if not found.
    """
    if not content.startswith("---"):
        return None

    # Find the closing ---
    rest = content[3:]
    # Skip optional newline after opening ---
    if rest.startswith("\n"):
        rest = rest[1:]
    elif rest.startswith("\r\n"):
        rest = rest[2:]

    end_match = re.search(r"^---", rest, re.MULTILINE)
    if end_match is None:
        return None

    return rest[:end_match.start()]


def _has_field(frontmatter: str, field_name: str) -> bool:
    """Check if a YAML field exists in frontmatter text.

    Simple regex check — looks for 'field_name:' at the start of a line
    with at least one non-whitespace character.
    """
    pattern = rf"^{field_name}\s*:\s*\S"
    return bool(re.search(pattern, frontmatter, re.MULTILINE))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agent Zero skill directory")
    parser.add_argument("skill_path", help="Path to the skill directory")
    args = parser.parse_args()

    valid, msg = validate_skill(args.skill_path)

    emoji = "\u2705" if valid else "\u274c"
    print(f"{emoji} {msg}")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
