#!/usr/bin/env python3
"""Shared utilities for description optimization scripts."""

import json
import random
import re
from pathlib import Path
from typing import Any


def split_evals(
    evals: list[dict[str, Any]],
    holdout_pct: float = 0.4,
    seed: int = 42,
    min_per_class: int = 3,
) -> tuple[list[dict], list[dict]]:
    """Split evals into train/test sets, stratified by should_trigger.

    Args:
        evals: List of eval dicts, each with a 'should_trigger' bool
        holdout_pct: Fraction of evals for test set (default 0.4)
        seed: Random seed for reproducibility
        min_per_class: Minimum evals per should_trigger value in each split

    Returns:
        (train_evals, test_evals) tuple
    """
    # Separate evals into two groups by should_trigger value
    true_group = [e for e in evals if e.get("should_trigger", False)]
    false_group = [e for e in evals if not e.get("should_trigger", False)]

    # Shuffle each group deterministically with the seed
    rng = random.Random(seed)
    rng.shuffle(true_group)
    rng.shuffle(false_group)

    train: list[dict] = []
    test: list[dict] = []

    for group in [true_group, false_group]:
        # If too few evals for a meaningful stratified split, all go to train
        min_needed = 2 * min_per_class
        if len(group) < min_needed:
            train.extend(group)
            continue

        # Split each group at the holdout boundary
        split_idx = int(len(group) * (1 - holdout_pct))
        train.extend(group[:split_idx])
        test.extend(group[split_idx:])

    return train, test


def load_json(path: str | Path) -> dict | None:
    """Load JSON file, return None on error."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def extract_frontmatter_description(skill_path: Path) -> str:
    """Extract description from SKILL.md YAML frontmatter (no yaml dependency)."""
    skill_md = skill_path / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return ""
    end = content.find("---", 3)
    if end == -1:
        return ""
    frontmatter = content[3:end]
    # Simple regex parser — only need the description field
    match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if not match:
        return ""
    desc = match.group(1).strip().strip('"').strip("'")
    return desc
