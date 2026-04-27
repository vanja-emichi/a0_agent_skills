#!/usr/bin/env python3
"""Validate SKILL.md files for required section compliance.

Checks every SKILL.md under skills/ for the 7 required sections
defined in agent-skills' docs/skill-anatomy.md. Accepts semantic
heading aliases — exact match is NOT required.

Usage:
    python scripts/validate_skills.py [--verbose] [--skill NAME]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 7 required sections with accepted heading aliases (case-insensitive)
REQUIRED_SECTIONS: dict[str, list[str]] = {
    "Overview": ["overview", "summary", "description"],
    "When to Use": ["when to use", "usage", "use cases"],
    "Core Process": ["core process", "the workflow", "steps", "process", "workflow"],
    "Common Rationalizations": ["common rationalization", "anti-rationalization"],
    "Red Flags": ["red flags", "warning signs"],
    "Verification": ["verification", "exit criteria", "validation"],
    "Boundaries": ["boundaries", "always/never", "rules"],
}

HEADING_PATTERN = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)


def _tokenize(s: str) -> list[str]:
    """Split string into lowercase alphanumeric tokens (word-level)."""
    return re.findall(r"[a-z0-9]+", s.lower())


def _alias_matches(alias: str, heading: str) -> bool:
    """Check if alias matches heading using word-level token comparison.

    Replaces the old substring check (`alias in heading`) which caused
    false positives like 'rule' matching 'ruler'. Word-level matching
    requires every alias token to appear as a complete word in the
    heading. This correctly handles:
    - 'process' matches 'The Simplification Process' ✓
    - 'boundaries' matches 'Security Boundaries' ✓
    - 'rule' does NOT match 'ruler' ✓
    Singular/plural variants handled by stripping trailing 's'.
    """
    alias_tokens = _tokenize(alias)
    heading_tokens = set(_tokenize(heading))
    # Build singular-only set for plural matching
    heading_singular = {t.rstrip("s") for t in heading_tokens}

    if not alias_tokens:
        return False

    for at in alias_tokens:
        if at in heading_tokens:
            continue
        # Try singular/plural match
        if at.rstrip("s") in heading_singular:
            continue
        return False

    return True


def extract_headings(content: str) -> list[str]:
    """Extract all ATX headings (## and ###) from markdown content."""
    return [m.group(1).strip() for m in HEADING_PATTERN.finditer(content)]

def _section_found(aliases: list[str], headings: list[str]) -> bool:
    """Check if any alias matches any heading."""
    return any(
        any(_alias_matches(alias, heading) for heading in headings)
        for alias in aliases
    )


def check_skill(skill_path: Path) -> tuple[bool, list[str], list[str]]:
    """Check a single SKILL.md for required sections.

    Returns (is_compliant, missing_sections, found_aliases).
    """
    try:
        content = skill_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"\u26a0 {skill_path.name}: skipping non-UTF-8 file")
        return False, list(REQUIRED_SECTIONS.keys()), []
    headings = [h.lower() for h in extract_headings(content)]

    missing: list[str] = []
    found: list[str] = []
    for section, aliases in REQUIRED_SECTIONS.items():
        if _section_found(aliases, headings):
            found.append(section)
        else:
            missing.append(section)

    return len(missing) == 0, missing, found


def validate_skills(
    skills_dir: Path,
    verbose: bool = False,
    skill_name: str | None = None,
) -> int:
    """Validate SKILL.md files and print results.

    Returns exit code: 0 if all compliant, 1 if any gaps.
    """
    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}")
        return 1

    # Collect skill directories
    skill_dirs: list[Path] = []
    if skill_name:
        target = skills_dir / skill_name
        if not target.is_dir():
            print(f"Skill not found: {skill_name}")
            return 1
        skill_dirs = [target]
    else:
        skill_dirs = sorted(
            d for d in skills_dir.iterdir() if d.is_dir()
        )

    total = 0
    compliant = 0
    gaps = 0

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            print(f"\u274c {skill_dir.name}: SKILL.md not found")
            gaps += 1
            total += 1
            continue

        is_compliant, missing, found = check_skill(skill_md)
        total += 1

        if is_compliant:
            compliant += 1
            print(f"\u2705 {skill_dir.name}: 7/7")
        else:
            gaps += 1
            print(
                f"\u274c {skill_dir.name}: {7 - len(missing)}/7 "
                f"(missing: {', '.join(missing)})"
            )

        if verbose:
            for section in found:
                print(f"   \u2713 {section}")
            for section in missing:
                print(f"   \u2717 {section}")

    print(f"\n{compliant}/{total} skills compliant")
    return 0 if gaps == 0 else 1


def main() -> int:
    """Entry point for the validate_skills script."""
    import argparse

    # Determine project root (parent of scripts/)
    root = Path(__file__).resolve().parent.parent
    skills_dir = root / "skills"

    parser = argparse.ArgumentParser(
        description="Validate SKILL.md files for required sections"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show per-section breakdown",
    )
    parser.add_argument(
        "--skill", "-s",
        type=str,
        default=None,
        help="Check a single skill by directory name",
    )
    args = parser.parse_args()

    return validate_skills(skills_dir, verbose=args.verbose, skill_name=args.skill)


if __name__ == "__main__":
    sys.exit(main())
