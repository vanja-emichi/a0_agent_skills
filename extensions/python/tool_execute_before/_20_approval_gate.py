"""Approval Gate Extension — natural language approval detection.

Fires before target tool execution (code_execution_tool, text_editor).
Detects explicit approval language in the last user message and marks
the current phase's artifact as approved via ``mark_artifact_approved``.

Approval is only recorded when:
1. The last user message contains an explicit approval phrase
2. A current workflow phase is known
3. The phase's artifact exists in workflow state

Must never raise — all logic is wrapped in a top-level try/except so that
approval gate failures cannot affect normal agent operation.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import re
import sys

from helpers.extension import Extension

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Approval phrase detection
# ---------------------------------------------------------------------------

_APPROVAL_PHRASES = frozenset([
    "approved",
    "approve",
    "looks good",
    "good to go",
    "proceed",
    "ship it",
    "lgtm",
    "let's go",
    "ok",
    "okay",
])

_NEGATION_WORDS = frozenset([
    "not", "don't", "doesn't", "didn't", "won't", "wouldn't",
    "couldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't",
    "never", "no",
])

_NEGATION_WINDOW = 4  # number of preceding words to scan for negation

# Stripped forms of contraction negations (e.g. "don't" → "dont").
# Derived from _NEGATION_WORDS so there is a single source of truth.
_STRIPPED_NEGATIONS = frozenset(
    w.replace("'", "") for w in _NEGATION_WORDS if "'" in w
)

# Characters that separate clauses in natural language.
_CLAUSE_SEPARATORS = re.compile(r'[,;.!]')


def detect_approval_in_text(text: str) -> bool:
    """Detect explicit approval language in user text.

    Returns True only for explicit positive signals.  Does NOT treat
    silence, questions, or negated phrases as approval.

    Args:
        text: The user message text to inspect.

    Returns:
        True if explicit approval language is detected, False otherwise.
    """
    if not text:
        return False
    text_lower = text.lower()

    # Word-boundary matching to avoid false positives like "unapproved".
    for phrase in _APPROVAL_PHRASES:
        # Use finditer to check every occurrence of the phrase
        for match in re.finditer(rf"\b{re.escape(phrase)}\b", text_lower):
            # Check if THIS specific occurrence of the approval phrase is
            # part of a question rather than an assertion.
            after = text_lower[match.end():]
            after_stripped = after.lstrip()

            # 1) Phrase immediately followed by '?' → question ("approved?")
            if after_stripped.startswith("?"):
                continue

            # 2) '?' in the same clause after the phrase → question
            #    Split on clause separators to isolate the current clause.
            #    e.g. "approved by whom?" → same clause → reject
            #    e.g. "looks good, proceed?" → different clause → accept
            clause_after = _CLAUSE_SEPARATORS.split(after_stripped, maxsplit=1)[0]
            if "?" in clause_after:
                continue

            prefix = text_lower[:match.start()].rstrip()

            # 3) Check for negation in a window of preceding words.
            if _has_negation_in_window(prefix, _NEGATION_WINDOW):
                continue

            return True
    return False


def _has_negation_in_window(prefix: str, window: int) -> bool:
    """Check if any negation word appears in the last *window* words of prefix."""
    words = prefix.split()
    window_words = words[-window:] if len(words) >= window else words
    for word in window_words:
        if word in _NEGATION_WORDS:
            return True
        # Handle contractions with stripped apostrophes (e.g. "don't" → "dont")
        if word.replace("'", "") in _STRIPPED_NEGATIONS:
            return True
    return False


# ---------------------------------------------------------------------------
# Bootstrap & module loading (same pattern as _10_skill_enforcer)
# ---------------------------------------------------------------------------

def _bootstrap_plugin_loader():
    if '_plugin_loader' not in sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    return sys.modules['_plugin_loader']


def _load_module_by_path(module_name, file_path):
    return _bootstrap_plugin_loader().load_module_by_path(module_name, file_path)


# Module-level cache for helper functions.
_cached_helpers = None


def _reset_helpers_cache():
    """Clear cached helpers (for test teardown)."""
    global _cached_helpers
    _cached_helpers = None


def _import_helpers():
    """Lazy import of workflow_state and phase_governance helpers.

    Result is cached at module level.  Reset via _reset_helpers_cache().
    """
    global _cached_helpers
    if _cached_helpers is not None:
        return _cached_helpers

    this_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
    helpers_dir = os.path.join(plugin_root, 'helpers')

    _workflow_state = _load_module_by_path(
        'helpers.workflow_state',
        os.path.join(helpers_dir, 'workflow_state.py'),
    )
    _phase_governance = _load_module_by_path(
        'helpers.phase_governance',
        os.path.join(helpers_dir, 'phase_governance.py'),
    )

    _cached_helpers = (_workflow_state, _phase_governance)
    return _cached_helpers


def _get_helpers():
    """Return resolved helper functions from cached modules.

    Returns (mark_artifact_approved, read_workflow_artifacts, get_current_phase).
    """
    _workflow_state, _phase_governance = _import_helpers()
    return (
        _workflow_state.mark_artifact_approved,
        _workflow_state.read_workflow_artifacts,
        _phase_governance.get_current_phase,
    )


def _get_phase_artifact_type(phase: str) -> str | None:
    """Return the artifact type for a phase using the canonical PHASE_ARTIFACT_MAP.

    Single source of truth: helpers.phase_governance.PHASE_ARTIFACT_MAP.
    """
    _, _phase_governance = _import_helpers()
    return _phase_governance.PHASE_ARTIFACT_MAP.get(phase)


# ---------------------------------------------------------------------------
# Artifact key mapping (for existence check in workflow_artifacts.json)
# ---------------------------------------------------------------------------

# Maps artifact_type to the key used in workflow_artifacts.json for
# existence checking.  The phase → artifact_type mapping comes from
# phase_governance.PHASE_ARTIFACT_MAP (single source of truth).
_ARTIFACT_KEY_MAP = {
    "spec": "spec_path",
    "plan": "plan_path",
    "todo": "todo_path",
    "review": "review",
    "report": "checklist_path",
}


# ---------------------------------------------------------------------------
# Extension class
# ---------------------------------------------------------------------------


class ApprovalGate(Extension):
    """Natural language approval detection gate.

    Inspects the last user message for explicit approval phrases.
    When detected, marks the current phase's artifact as approved
    via ``mark_artifact_approved``.

    Only acts when:
    - An approval phrase is detected in the last user message
    - A current workflow phase is known
    - The phase's artifact exists in workflow state

    Fail-safe: all errors are caught and logged, never propagating
    to the agent loop.
    """

    async def execute(
        self,
        tool_args: dict | None = None,
        tool_name: str | None = None,
        **kwargs,
    ) -> None:
        try:
            # Get the last user message text
            msg = getattr(self.agent, "last_user_message", None)
            if msg is None:
                return
            text = getattr(msg, "content", None)
            if not text:
                return

            # Check for approval language
            if not detect_approval_in_text(text):
                return

            # Resolve helpers
            mark_approved, read_artifacts, get_phase = _get_helpers()

            # Determine current phase
            current_phase = get_phase(self.agent)
            if not current_phase:
                _log.debug(
                    "Approval detected but no current phase — skipping",
                )
                return

            # Look up the artifact type for this phase (canonical source)
            artifact_type = _get_phase_artifact_type(current_phase)
            if not artifact_type:
                _log.debug(
                    "Approval detected but phase %s has no artifact mapping",
                    current_phase,
                )
                return

            # Resolve the state dict key for existence check
            artifact_key = _ARTIFACT_KEY_MAP.get(artifact_type, artifact_type)

            # Check if the artifact exists in workflow state
            artifacts = read_artifacts(self.agent)
            if not artifacts or not artifacts.get(artifact_key):
                _log.debug(
                    "Approval detected but no %s artifact tracked — skipping",
                    artifact_key,
                )
                return

            # Mark the artifact as approved
            result = mark_approved(self.agent, artifact_type)
            if result:
                _log.info(
                    "Artifact %s approved in %s phase",
                    artifact_type,
                    current_phase,
                )
            else:
                _log.warning(
                    "Failed to record approval for %s in %s phase",
                    artifact_type,
                    current_phase,
                )

        except Exception:
            # Approval gate MUST NOT break the agent loop.
            _log.debug("Approval gate failed", exc_info=True)
