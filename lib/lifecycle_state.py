# lib/lifecycle_state.py - LifecycleState core for a0_agent_skills v0.3.0
#
# Cache strategy: mtime (nanosecond) on state.md.
# Phase tracked in YAML frontmatter of state.md.
# metadata.json used as legacy fallback for load().
#
# File layout under plan_dir (.a0proj/run/current/):
#   state.md        - YAML frontmatter (phase, slug, goal) + markdown body
#   findings.md     - append-only, trusted/[untrusted] tagged
#   progress.md     - append-only, timestamped
#   errors.md       - append-only, error log

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional



import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parent.parent)
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from lib.constants import (
    CONTEXT_KEY_LIFECYCLE_STATE,
    CONTEXT_KEY_LIFECYCLE_STATE_MTIME,
    CONTEXT_KEY_LIFECYCLE_GATE_WARNINGS,
    CONTEXT_KEY_LIFECYCLE_ACTIONS_SINCE_FINDING,
    CONTEXT_KEY_LIFECYCLE_NUDGES,
    CONTEXT_KEY_LIFECYCLE_RESUME_SHOWN,
    PHASE_ICONS,
    PHASE_ICON_DEFAULT,
)



def _non_header_lines(content: str) -> str:
    """Filter markdown content to non-empty, non-header lines."""
    return "\n".join(
        l for l in content.splitlines()
        if l.strip() and not l.strip().startswith("#")
    )


# ---------------------------------------------------------------------------
# Dataclasses (preserved from v0.2.x)
# ---------------------------------------------------------------------------


@dataclass
class Phase:
    """A single phase in a lifecycle."""
    title: str
    status: str = "pending"  # pending | in_progress | completed

    _STATUS_NORMALIZE = {
        "active": "in_progress",
        "running": "in_progress",
        "current": "in_progress",
        "done": "completed",
        "finished": "completed",
    }
    _VALID_STATUSES = frozenset({"pending", "in_progress", "completed"})

    def __post_init__(self):
        normalized = self._STATUS_NORMALIZE.get(self.status.lower() if self.status else "", self.status)
        if normalized not in self._VALID_STATUSES:
            normalized = "pending"
        self.status = normalized


@dataclass
class Finding:
    """A finding logged during lifecycle execution."""
    content: str
    source: str = "trusted"  # trusted | untrusted
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ProgressEntry:
    """A progress log entry."""
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ErrorEntry:
    """An error log entry with hash for deduplication."""
    content: str
    error_hash: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# LifecycleState
# ---------------------------------------------------------------------------


@dataclass
class LifecycleState:
    """Structured lifecycle state - disk is source of truth, cache is read-through.

    Cached in AgentContext.data['lifecycle_state'] with mtime cache key.
    Phase tracked in YAML frontmatter of state.md.
    """

    goal: str
    phases: list[Phase] = field(default_factory=list)
    slug: str = ""
    current_phase_index: int = 0
    plan_dir: Optional[Path] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        goal: str,
        phases: list[str],
        slug: str,
        plan_dir: Path | None = None,
    ) -> LifecycleState:
        """Create a new lifecycle with validation.

        Raises RepairableException if goal too short or too few phases.
        Hardcodes 4 files: state.md, findings.md, progress.md, errors.md.
        No template parameter - templates removed in v0.3.0.
        """
        try:
            from helpers.errors import RepairableException
        except ImportError:
            RepairableException = ValueError

        if len(goal) < 20:
            raise RepairableException(
                f"Lifecycle goal must be at least 20 characters (got {len(goal)}): '{goal}'"
            )
        if len(goal) > 500:
            raise RepairableException(
                f"Lifecycle goal must be at most 500 characters (got {len(goal)})."
            )
        if len(phases) < 2:
            raise RepairableException(
                f"Lifecycle must have at least 2 phases (got {len(phases)}). "
                f"A single-phase lifecycle can bypass the no-lifecycle gate."
            )

        if plan_dir is None:
            plan_dir = cls._get_fallback_dir()
        plan_dir = Path(plan_dir)
        plan_dir.mkdir(parents=True, exist_ok=True)

        state = cls(
            goal=goal,
            phases=[Phase(title=t) for t in phases],
            slug=slug,
            plan_dir=plan_dir,
        )

        state._write_initial_files()
        return state

    # ------------------------------------------------------------------
    # Load (with mtime cache)
    # ------------------------------------------------------------------

    @classmethod
    def load(
        cls,
        plan_dir: Path,
        context=None,
    ) -> LifecycleState | None:
        """Load lifecycle state from disk with mtime-based cache.

        Returns None if no state exists.
        Primary source: YAML frontmatter in state.md.
        Fallback: metadata.json (legacy v0.2.x format).
        """
        plan_dir = Path(plan_dir)
        state_md_path = plan_dir / "state.md"
        metadata_path = plan_dir / "metadata.json"

        if not state_md_path.exists() and not metadata_path.exists():
            return None

        mtime_path = state_md_path if state_md_path.exists() else metadata_path
        current_mtime = os.stat(mtime_path).st_mtime_ns

        if context is not None and hasattr(context, "data"):
            cached_mtime = context.data.get(CONTEXT_KEY_LIFECYCLE_STATE_MTIME)
            cached_state = context.data.get(CONTEXT_KEY_LIFECYCLE_STATE)
            if cached_mtime == current_mtime and cached_state is not None:
                return cached_state

        state = None
        if state_md_path.exists():
            state = cls._load_from_frontmatter(plan_dir, state_md_path)

        if state is None and metadata_path.exists():
            state = cls._load_from_metadata_json(plan_dir, metadata_path)

        if state is None:
            return None

        if context is not None and hasattr(context, "data"):
            context.data[CONTEXT_KEY_LIFECYCLE_STATE] = state
            context.data[CONTEXT_KEY_LIFECYCLE_STATE_MTIME] = current_mtime

        return state

    @classmethod
    def _load_from_frontmatter(cls, plan_dir, state_md_path):
        """Parse LifecycleState from YAML frontmatter in state.md."""
        try:
            import yaml
        except ImportError:
            yaml = None

        content = state_md_path.read_text(encoding="utf-8")

        if not content.startswith("---"):
            return None

        end_idx = content.find("---", 3)
        if end_idx == -1:
            return None

        fm_text = content[3:end_idx].strip()

        fm = None
        if yaml is not None:
            try:
                fm = yaml.safe_load(fm_text)
            except Exception:
                pass

        if fm is None:
            fm = cls._parse_frontmatter_manual(fm_text)

        if fm is None or not isinstance(fm, dict):
            return None

        raw_phases = fm.get("phases", [])
        phases = []
        for p in raw_phases:
            if isinstance(p, dict):
                phases.append(Phase(title=p.get("title", ""), status=p.get("status", "pending")))
            elif isinstance(p, str):
                phases.append(Phase(title=p, status="pending"))

        return cls(
            goal=fm.get("goal", ""),
            phases=phases,
            slug=fm.get("slug", ""),
            current_phase_index=fm.get("current_phase_index", 0),
            plan_dir=plan_dir,
            created_at=fm.get("created_at", ""),
        )

    @staticmethod
    def _parse_frontmatter_manual(text: str) -> dict | None:
        """Parse simple YAML frontmatter when PyYAML is unavailable.

        Handles: string values, int values, list-of-dict (phases).
        Returns None if parsing fails.
        """
        result = {}
        current_list_key = None
        current_item = None

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # List item with dict: "  - key: value"
            if stripped.startswith("- ") and current_list_key:
                # Save previous item
                if current_item is not None:
                    result[current_list_key].append(current_item)
                current_item = {}
                kv = stripped[2:].split(": ", 1)
                if len(kv) == 2:
                    current_item[kv[0]] = kv[1].strip('"')
                continue

            # Continuation of dict item: "    key: value"
            if line.startswith("    ") and current_item is not None:
                kv = stripped.split(": ", 1)
                if len(kv) == 2:
                    current_item[kv[0]] = kv[1].strip('"')
                continue

            # Top-level key: value
            if ": " in stripped or stripped.endswith(":"):
                # Save pending list item
                if current_item is not None and current_list_key:
                    result[current_list_key].append(current_item)
                    current_item = None
                    current_list_key = None

                if stripped.endswith(":"):
                    # Start of a list
                    key = stripped[:-1]
                    result[key] = []
                    current_list_key = key
                    current_item = None
                else:
                    kv = stripped.split(": ", 1)
                    key = kv[0]
                    val = kv[1].strip('"')
                    # Try int
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        pass
                    result[key] = val
                    current_list_key = None

        # Save last pending item
        if current_item is not None and current_list_key:
            result[current_list_key].append(current_item)

        return result if result else None

    @classmethod
    def _load_from_metadata_json(cls, plan_dir, metadata_path):
        """Load from legacy metadata.json (v0.2.x fallback)."""
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        raw_phases = metadata.get("phases", [])
        phases = []
        for p in raw_phases:
            if isinstance(p, dict):
                title = p.get("title", "")
                if isinstance(title, dict):
                    title = title.get("name", title.get("title", str(title)))
                phases.append(Phase(title=str(title), status=p.get("status", "pending")))

        return cls(
            goal=metadata.get("goal", ""),
            phases=phases,
            slug=metadata.get("slug", ""),
            current_phase_index=metadata.get("current_phase_index", 0),
            plan_dir=plan_dir,
            created_at=metadata.get("created_at", ""),
        )

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------

    def persist(self) -> None:
        """Write state to disk with YAML frontmatter in state.md."""
        if self.plan_dir is None:
            return

        self.plan_dir.mkdir(parents=True, exist_ok=True)

        state_content = self._render_state_md()
        self._atomic_write(self.plan_dir / "state.md", state_content)

    def append_finding(self, finding: Finding) -> None:
        """Append a finding to findings.md."""
        if self.plan_dir is None:
            return

        if finding.source != "trusted":
            prefix = "[untrusted] "
            content = "\n".join(f"{prefix}{line}" for line in finding.content.split("\n"))
        else:
            content = finding.content
        line = f"{content}\n"
        self._append_to_file(self.plan_dir / "findings.md", line)

    def append_progress(self, entry: ProgressEntry) -> None:
        """Append a progress entry to progress.md."""
        if self.plan_dir is None:
            return

        line = f"{entry.timestamp} {entry.content}\n"
        self._append_to_file(self.plan_dir / "progress.md", line)

    def append_error(self, entry: ErrorEntry) -> None:
        """Append an error entry to errors.md."""
        if self.plan_dir is None:
            return

        line = f"{entry.timestamp} [{entry.error_hash}] {entry.content}\n"
        self._append_to_file(self.plan_dir / "errors.md", line)

    # ------------------------------------------------------------------
    # Archive / cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Remove all lifecycle files from disk."""
        import shutil
        if self.plan_dir is None or not self.plan_dir.exists():
            return
        shutil.rmtree(str(self.plan_dir))

    def read_findings_summary(self) -> str:
        """Read all findings from findings.md and return summary."""
        if self.plan_dir is None:
            return ""
        findings_path = self.plan_dir / "findings.md"
        if not findings_path.exists():
            return "No findings logged."
        text = findings_path.read_text(encoding="utf-8")
        filtered = _non_header_lines(text)
        if not filtered:
            return "No findings logged."
        return "\n".join(f"- {l}" for l in filtered.splitlines())
    def render_abandoned_brief(self, reason: str = "") -> str:
        """Render a brief abandoned-lifecycle document."""
        lines = [
            f"# {self.slug} (Abandoned)",
            "",
            f"**Goal:** {self.goal}",
            f"**Abandoned:** {datetime.now(timezone.utc).isoformat()}",
            "",
        ]
        if reason:
            lines.extend(["## Reason", "", reason, ""])
        lines.extend(["## Findings Summary", ""])
        lines.append(self.read_findings_summary())
        lines.extend(["", "## Phases at Time of Abandonment", ""])
        for line in self.render_phase_list(marker_current="", marker_other="", show_status=True):
            lines.append(line.lstrip())
        return "\n".join(lines)

    def render_phase_list(self, marker_current: str = " ->", marker_other: str = "  ", show_status: bool = False) -> list[str]:
        """Render phase list with status icons and optional current marker."""
        lines = []
        for i, phase in enumerate(self.phases):
            icon = PHASE_ICONS.get(phase.status, PHASE_ICON_DEFAULT)
            marker = marker_current if i == self.current_phase_index else marker_other
            status = f" ({phase.status})" if show_status else ""
            lines.append(f"{marker} {i+1}. {icon} {phase.title}{status}")
        return lines

    def count_findings(self) -> int:
        """Count non-empty, non-header lines in findings.md."""
        if self.plan_dir is None:
            return 0
        return len(self._read_tail_lines(self.plan_dir / "findings.md", n=0))


    # ------------------------------------------------------------------
    # Render EXTRAS (for KV-cache stability)
    # ------------------------------------------------------------------

    @staticmethod
    def _read_tail_lines(file_path: Path, n: int) -> list[str]:
        """Read last n non-empty, non-header lines from a file."""
        if not file_path.exists():
            return []
        content = file_path.read_text(encoding="utf-8")
        lines = [
            l for l in content.splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
        return lines[-n:] if n > 0 else lines

    def render_extras(self, max_suffix: int = 12, budget: int = 2000) -> str:
        """Render a KV-cache-stable EXTRAS block with character budget.

        Args:
            max_suffix: Max number of tail lines to read from files.
            budget: Max character budget. Prefix (goal + phases) is always
                    preserved. Findings and progress are truncated from
                    the oldest entries when budget is exceeded.
        """
        # --- Stable prefix: always preserved ---
        prefix_lines: list[str] = []
        prefix_lines.append("Lifecycle: " + self.slug)
        prefix_lines.append("Goal: " + self.goal)
        prefix_lines.append("")
        prefix_lines.append("Phases:")
        prefix_lines.extend(self.render_phase_list())
        prefix_lines.append("")

        prefix = "\n".join(prefix_lines)

        if self.plan_dir is None:
            return prefix

        # --- Dynamic content: findings + progress, budget-controlled ---
        all_findings = self._read_tail_lines(self.plan_dir / "findings.md", max_suffix)
        all_progress = self._read_tail_lines(self.plan_dir / "progress.md", max_suffix)

        if not all_findings and not all_progress:
            return prefix

        remaining = max(0, budget - len(prefix))
        truncated_findings = 0
        truncated_progress = 0

        # Build findings block - keep most recent that fit
        findings_lines: list[str] = []
        if all_findings:
            findings_lines.append("Recent findings:")
            included: list[str] = []
            for fl in reversed(all_findings):
                candidate = "  " + fl
                test_block = "\n".join(findings_lines + [candidate] + included)
                if len(test_block) > remaining // 2:
                    truncated_findings += 1
                else:
                    included.insert(0, candidate)
            findings_lines.extend(included)
            findings_lines.append("")

        findings_text = "\n".join(findings_lines)

        # Build progress block - keep most recent that fit
        progress_lines: list[str] = []
        if all_progress:
            progress_lines.append("Recent progress:")
            included_p: list[str] = []
            for pl in reversed(all_progress):
                candidate = "  " + pl
                test_block = "\n".join(progress_lines + [candidate] + included_p)
                if len(test_block) > remaining // 2:
                    truncated_progress += 1
                else:
                    included_p.insert(0, candidate)
            progress_lines.extend(included_p)
            progress_lines.append("")

        progress_text = "\n".join(progress_lines)

        # Combine prefix + dynamic content
        result = prefix + "\n" + findings_text + "\n" + progress_text

        # Add truncation notices if needed
        notices = []
        if truncated_findings > 0:
            notices.append("[..." + str(truncated_findings) + " more findings entries truncated]")
        if truncated_progress > 0:
            notices.append("[..." + str(truncated_progress) + " more progress entries truncated]")
        if notices:
            result += "\n".join(notices) + "\n"

        return result
    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Return a short human-readable summary."""
        current = self.phases[self.current_phase_index] if self.phases else None
        lines = [
            f"Lifecycle: {self.slug}",
            f"Goal: {self.goal}",
            f"Current phase: {current.title} ({current.status})" if current else "No phases",
            f"Phases: {len(self.phases)} total, {self.current_phase_index} completed",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_fallback_dir() -> Path:
        return Path.home() / ".a0_plan" / "current"

    def _write_initial_files(self) -> None:
        """Write the initial 4 hardcoded lifecycle files.

        v0.3.0: No templates. Hardcodes state.md, findings.md, progress.md, errors.md.
        """
        if self.plan_dir is None:
            return

        self.persist()

        for name in ("findings.md", "progress.md", "errors.md"):
            target = self.plan_dir / name
            if not target.exists():
                header = f"# {name.replace('.md', '').title()}\n"
                target.write_text(header, encoding="utf-8")

    def _render_state_md(self) -> str:
        """Render state.md content with YAML frontmatter."""
        try:
            import yaml
        except ImportError:
            yaml = None

        fm_data = {
            "slug": self.slug,
            "goal": self.goal,
            "created_at": self.created_at,
            "current_phase_index": self.current_phase_index,
            "phases": [{"title": p.title, "status": p.status} for p in self.phases],
        }

        if yaml is not None:
            fm_str = yaml.dump(fm_data, default_flow_style=False, allow_unicode=True)
        else:
            fm_str = self._manual_yaml_dump(fm_data)

        body_lines = [f"# Lifecycle: {self.slug}", ""]
        body_lines.append("## Goal")
        body_lines.append(self.goal)
        body_lines.append("")
        body_lines.append("## Phases")
        for i, phase in enumerate(self.phases):
            icon = PHASE_ICONS.get(phase.status, PHASE_ICON_DEFAULT)
            marker = " -> " if i == self.current_phase_index else "   "
            body_lines.append(f"{marker}{i+1}. {icon} {phase.title} [{phase.status}]")
        body_lines.append("")

        return "---\n" + fm_str + "---\n" + "\n".join(body_lines)

    @staticmethod
    def _manual_yaml_dump(data: dict) -> str:
        """Minimal YAML dump for frontmatter when PyYAML is unavailable."""
        lines = []
        for key, val in data.items():
            if isinstance(val, str):
                if ":" in val or "#" in val or val.startswith(" "):
                    lines.append(f'{key}: "{val}"')
                else:
                    lines.append(f"{key}: {val}")
            elif isinstance(val, int):
                lines.append(f"{key}: {val}")
            elif isinstance(val, list):
                lines.append(f"{key}:")
                for item in val:
                    if isinstance(item, dict):
                        first = True
                        for k, v in item.items():
                            prefix = "  - " if first else "    "
                            if isinstance(v, str) and (":" in v or "#" in v):
                                lines.append(f'{prefix}{k}: "{v}"')
                            else:
                                lines.append(f"{prefix}{k}: {v}")
                            first = False
                    else:
                        lines.append(f"  - {item}")
            elif val is None:
                lines.append(f"{key}: null")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Atomic write via temp file + rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, str(path))
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def _append_to_file(path: Path, content: str) -> None:
        """Append content to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("", encoding="utf-8")
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
