"""Skill-match helper for the enforcement gate.

Centralizes target-tool detection, loaded-skill lookup, search_skills() prefilter,
and utility-model classification with explicit result states.

Result states:
    no_candidate         — no matching skills found or non-target tool
    already_loaded       — a matching skill is already in agent.data['loaded_skills']
    should_correct       — classifier says a skill should have been loaded
    should_not_correct   — classifier says no skill needed
    classifier_unavailable — utility model failed or returned unusable output
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, List, Optional, Set

from helpers.skills import get_loaded_skill_entries, search_skills

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Target-tool set (MVP)
# ---------------------------------------------------------------------------

TARGET_TOOLS: frozenset[str] = frozenset({"code_execution_tool", "text_editor"})

# ---------------------------------------------------------------------------
# Classifier prompt
# ---------------------------------------------------------------------------

_CLASSIFIER_SYSTEM = """\
You are a skill-matching classifier for an AI development agent.
Given the agent's last user message, the tool being used, and candidate skills,
decide whether the agent should have loaded one of these skills first.

Respond with a JSON object:
{ "should_load": true/false, "reason": "short explanation" }

Decision rules (apply in order):

1. TRIVIAL TASKS → false: listing files, printing output, showing contents,\
   checking versions, reading config, simple shell commands, one-line fixes.

2. NEW PROJECT/FEATURE/SERVICE → true: if the user wants to create something\
   substantial (new module, service, feature, system), a spec or planning skill\
   is needed. Keywords: spec, new project, new feature, design and implement.

3. BUG/ERROR/CRASH → true: if the user reports failures, errors, crashes,\
   or unexpected behavior, the debugging skill is needed.\
   Keywords: failing, error, crash, segfault, broken, intermittent, ImportError.

4. TESTS → true: if the user wants to implement logic, write functions, or\
   fix code behavior, the TDD skill is needed. Keywords: implement function,\
   write algorithm, add validation, build parser.

5. REVIEW/AUDIT → true: if the user wants code reviewed for quality,\
   standards, or general issues. But SECURITY-specific audits\
   ("security vulnerabilities", "OWASP") go to security-and-hardening.

6. SIMPLIFY/REFACTOR → true: if the user wants to simplify or clean up\
   code. Keywords: simplify, cleaner, refactor for clarity.

7. DEPLOY/SHIP → true: if the user wants to deploy, launch, or go to\
   production. Keywords: deploy, production, launch, ship, release.

8. If unsure, say false (prefer no correction over false positives).

Key discrimination rules:
- "design the REST API" → api-and-interface-design (not spec-driven)
- "stress-test a plan" → doubt-driven-development (not planning)
- "check for security vulnerabilities" → security-and-hardening (not code-review)
- "audit security" → security-and-hardening (not code-review)
- "simplify this function" → code-simplification (not TDD)
"""


# ===========================================================================
# Public API
# ===========================================================================


def is_target_tool(tool_name: str | None) -> bool:
    """Return True if *tool_name* is one of the MVP target tools."""
    return bool(tool_name and tool_name in TARGET_TOOLS)


def get_loaded_skills(agent: Any) -> Set[str]:
    """Return a set of currently loaded skill names from the agent.

    Reads directly from ``agent.data['loaded_skills']`` when available,
    falling back to ``get_loaded_skill_entries`` from the framework.
    Returns an empty set on any failure.
    """
    try:
        names: Set[str] = set()
        # Fast path: read directly from agent data
        data = getattr(agent, "data", None)
        if isinstance(data, dict):
            loaded = data.get("loaded_skills")
            if isinstance(loaded, list):
                names |= {str(s).strip() for s in loaded if str(s).strip()}
            # Plugin-private rehydrated names, set by the reattach extension
            # after compaction/session resume. Kept separate from the
            # core-rendered 'loaded_skills' key to avoid full-body re-injection,
            # but still counted here so the gate does not re-nag for skills
            # already loaded in a prior turn or session.
            rehydrated = data.get("_a0skills_rehydrated_loaded")
            if isinstance(rehydrated, list):
                names |= {str(s).strip() for s in rehydrated if str(s).strip()}
        if names:
            return names
        # Fallback: use framework helper
        entries = get_loaded_skill_entries(agent)
        return {e["name"] for e in entries if e.get("name")}
    except Exception:
        return set()


def prefilter_match(
    agent: Any,
    last_user_message: str | None,
    *,
    limit: int = 5,
) -> List[Any]:
    """Run a cheap ``search_skills()`` prefilter against *last_user_message*.

    Returns a list of ``Skill`` objects (max *limit*), sorted by relevance.
    Returns an empty list when the query is empty or no skills match.

    The search_skills score is stripped by the framework, so this is a
    **prefilter only** — no threshold tuning is possible or needed.
    """
    query = (last_user_message or "").strip()
    if not query:
        return []
    try:
        return search_skills(query, limit=limit, agent=agent)
    except Exception:
        _log.debug("search_skills failed for query=%r", query, exc_info=True)
        return []


def _extract_json_object(text: str) -> str | None:
    """Extract the first balanced JSON object from text.

    Handles nested braces unlike the simple regex ``r'\{[^}]+\}'``.
    Returns the extracted substring or None.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


async def classify_skill(
    agent: Any,
    tool_name: str | None,
    tool_args: dict,
    candidates: list[Any],
    last_user_message: str | None,
) -> dict:
    """Classify whether the agent should have loaded a skill.

    Returns a dict with keys:
        state (str)      — one of the five result states
        candidate (str|None) — skill name when state is should_correct
        reason (str|None)   — classifier reason when available

    The function is fail-safe: any exception from the utility model results
    in ``classifier_unavailable`` rather than propagating.
    """
    # ---- Fast paths (no LLM needed) ----

    if not is_target_tool(tool_name):
        return {"state": "no_candidate", "candidate": None, "reason": None}

    if not candidates:
        return {"state": "no_candidate", "candidate": None, "reason": None}

    loaded = get_loaded_skills(agent)

    # Find the first candidate that isn't already loaded
    unloaded = [c for c in candidates if c.name not in loaded]

    if not unloaded:
        # All candidates are already loaded — nothing to correct
        return {"state": "already_loaded", "candidate": None, "reason": None}

    # ---- Utility-model classifier ----

    candidate_names = [c.name for c in unloaded]
    candidate_descs = [
        f"- {c.name}: {getattr(c, 'description', '')[:250]}" for c in unloaded
    ]

    user_msg = (
        f"Tool: {tool_name}\n"
        f"Last user message: {last_user_message or '(empty)'}\n"
        f"Candidate skills:\n" + "\n".join(candidate_descs)
    )

    try:
        raw = await agent.call_utility_model(
            system=_CLASSIFIER_SYSTEM,
            message=user_msg,
        )
    except Exception as exc:
        _log.debug("Utility model call failed: %s", exc)
        return {
            "state": "classifier_unavailable",
            "candidate": None,
            "reason": str(exc),
        }

    if not raw or not isinstance(raw, str) or not raw.strip():
        return {
            "state": "classifier_unavailable",
            "candidate": None,
            "reason": "empty response",
        }

    # ---- Parse classifier response ----

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Try to extract JSON from markdown code fences using balanced brace scanning
        json_match = _extract_json_object(raw)
        if json_match:
            try:
                parsed = json.loads(json_match)
            except (json.JSONDecodeError, TypeError):
                return {
                    "state": "classifier_unavailable",
                    "candidate": None,
                    "reason": f"malformed response: {raw[:80]}",
                }
        else:
            return {
                "state": "classifier_unavailable",
                "candidate": None,
                "reason": f"malformed response: {raw[:80]}",
            }

    should_load = parsed.get("should_load", False)
    reason = parsed.get("reason", "")

    if should_load:
        # Pick the first unloaded candidate as the correction target
        return {
            "state": "should_correct",
            "candidate": unloaded[0].name,
            "reason": reason,
        }
    else:
        return {
            "state": "should_not_correct",
            "candidate": None,
            "reason": reason,
        }
