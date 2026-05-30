"""Skill contract parsing and dependency graph helper.

Owns contract parsing from SKILL.md YAML frontmatter, the runtime-built
dependency graph (DAG), graph validation, and next-skill query functions.

State I/O is delegated to helpers.workflow_state — this module never
touches state files directly.

All public functions are fail-safe: exceptions return safe defaults.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional

_log = logging.getLogger(__name__)


def _bootstrap_plugin_loader():
    if '_plugin_loader' not in sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..'))
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    return sys.modules['_plugin_loader']


def _get_plugin_root() -> str:
    try:
        return _bootstrap_plugin_loader().get_plugin_root()
    except Exception:
        return os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        )


VALID_PHASES: frozenset[str] = frozenset({
    "DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP",
})

_KNOWN_CONTRACT_FIELDS: frozenset[str] = frozenset({
    "phase", "inputs", "artifacts", "verification",
    "next_skills", "conflicts",
})


try:
    _PLUGIN_ROOT: str = _get_plugin_root()
except Exception:
    _PLUGIN_ROOT: str = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    )

_graph_cache: dict[str, dict] | None = None
_graph_cache_ts: float = 0.0
_GRAPH_CACHE_TTL: float = 300.0


_EMPTY_GRAPH_ENTRY: dict[str, Any] = {
    "phase": None,
    "next_skills": [],
    "conflicts": [],
    "inputs": [],
    "artifacts": [],
    "verification": [],
    "contract": {},
}


def _validate_name_list(
    items: list,
    known_skills: frozenset[str] | set[str] | None,
    field_name: str,
) -> list[str]:
    validated: list[str] = []
    for item in items:
        name = str(item)
        if known_skills is not None and name not in known_skills:
            _log.warning(
                "Invalid %s reference: %r (not in known skills)",
                field_name, name,
            )
        else:
            validated.append(name)
    return validated


def _validate_contract_fields(
    contract_raw: dict,
    known_skills: frozenset[str] | set[str] | None = None,
) -> dict:
    result: dict[str, Any] = {}

    phase = contract_raw.get("phase")
    if phase is not None:
        phase = str(phase).upper()
        if phase in VALID_PHASES:
            result["phase"] = phase
        else:
            _log.warning("Invalid contract phase: %r, treating as absent", phase)

    inputs = contract_raw.get("inputs")
    if inputs is not None:
        if isinstance(inputs, list):
            result["inputs"] = [str(i) for i in inputs if i is not None]
        else:
            result["inputs"] = []

    artifacts = contract_raw.get("artifacts")
    if artifacts is not None:
        if isinstance(artifacts, list):
            validated_artifacts = []
            for a in artifacts:
                if isinstance(a, dict) and "path" in a:
                    validated_artifacts.append({
                        "path": str(a["path"]),
                        "description": str(a.get("description", "")),
                    })
            result["artifacts"] = validated_artifacts
        else:
            result["artifacts"] = []

    verification = contract_raw.get("verification")
    if verification is not None:
        if isinstance(verification, list):
            result["verification"] = [str(v) for v in verification if v is not None]
        else:
            result["verification"] = []

    next_skills = contract_raw.get("next_skills")
    if next_skills is not None:
        result["next_skills"] = (
            _validate_name_list(next_skills, known_skills, "next_skills")
            if isinstance(next_skills, list) else []
        )

    conflicts = contract_raw.get("conflicts")
    if conflicts is not None:
        result["conflicts"] = (
            _validate_name_list(conflicts, known_skills, "conflicts")
            if isinstance(conflicts, list) else []
        )

    return result


def parse_contract_from_frontmatter(
    frontmatter_text: str,
    known_skills: frozenset[str] | set[str] | None = None,
) -> dict:
    try:
        import yaml

        if not frontmatter_text or not frontmatter_text.strip():
            return {}

        parsed = yaml.safe_load(frontmatter_text)
        if not isinstance(parsed, dict):
            return {}

        contract_raw = parsed.get("contract")
        if contract_raw is None:
            return {}

        if not isinstance(contract_raw, dict):
            _log.warning("Contract block is not a dict, ignoring")
            return {}

        return _validate_contract_fields(contract_raw, known_skills)

    except Exception:
        _log.debug("Failed to parse contract from frontmatter", exc_info=True)
        return {}


def read_skill_frontmatter(skill_name: str) -> dict:
    try:
        skill_path = os.path.join(_PLUGIN_ROOT, "skills", skill_name, "SKILL.md")

        import pathlib
        base = pathlib.Path(os.path.join(_PLUGIN_ROOT, "skills")).resolve()
        candidate = pathlib.Path(skill_path).resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            _log.warning(
                "Path traversal in read_skill_frontmatter for '%s': %s",
                skill_name, skill_path,
            )
            return {}

        if not os.path.isfile(skill_path):
            return {}

        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter = _extract_frontmatter_text(content)
        if not frontmatter:
            return {}

        import yaml
        parsed = yaml.safe_load(frontmatter)
        return parsed if isinstance(parsed, dict) else {}

    except Exception:
        _log.debug("Failed to read frontmatter for skill: %s", skill_name, exc_info=True)
        return {}


def _extract_contract_from_dict(parsed: dict, known_skills=None) -> dict:
    try:
        if not isinstance(parsed, dict):
            return {}

        contract_raw = parsed.get("contract")
        if contract_raw is None:
            return {}

        if not isinstance(contract_raw, dict):
            _log.warning("Contract block is not a dict, ignoring")
            return {}

        return _validate_contract_fields(contract_raw, known_skills)

    except Exception:
        _log.debug("Failed to extract contract from dict", exc_info=True)
        return {}


def _extract_frontmatter_text(content: str) -> str:
    if not content or not content.startswith("---"):
        return ""

    rest = content[3:]
    if rest and rest[0] == "\n":
        rest = rest[1:]
    elif rest and rest[0] == "\r":
        rest = rest.lstrip("\r\n")

    match = re.search(r'^---\s*$', rest, re.MULTILINE)
    if not match:
        return ""

    return rest[:match.start()].rstrip()


def discover_skill_names() -> list[str]:
    try:
        skills_dir = os.path.join(_PLUGIN_ROOT, "skills")
        if not os.path.isdir(skills_dir):
            return []

        names = []
        for entry in sorted(os.listdir(skills_dir)):
            skill_md = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.isdir(os.path.join(skills_dir, entry)) and os.path.isfile(skill_md):
                names.append(entry)
        return names

    except Exception:
        _log.debug("Failed to discover skills", exc_info=True)
        return []


def build_skill_graph(
    validate_on_build: bool = True,
) -> dict[str, dict]:
    global _graph_cache, _graph_cache_ts

    if _graph_cache is not None:
        import time as _time
        if _time.time() - _graph_cache_ts > _GRAPH_CACHE_TTL:
            _graph_cache = None
        else:
            return _graph_cache

    try:
        skill_names = discover_skill_names()
        known_skills = frozenset(skill_names)
        graph: dict[str, dict] = {}

        for skill_name in skill_names:
            try:
                frontmatter = read_skill_frontmatter(skill_name)
                if frontmatter:
                    contract = _extract_contract_from_dict(frontmatter, known_skills)
                else:
                    contract = {}

                graph[skill_name] = {
                    "phase": contract.get("phase"),
                    "next_skills": contract.get("next_skills", []),
                    "conflicts": contract.get("conflicts", []),
                    "inputs": contract.get("inputs", []),
                    "artifacts": contract.get("artifacts", []),
                    "verification": contract.get("verification", []),
                    "contract": contract,
                }
            except Exception:
                _log.debug("Failed to process skill: %s", skill_name, exc_info=True)
                graph[skill_name] = dict(_EMPTY_GRAPH_ENTRY)

        if validate_on_build:
            findings = _detect_cycles(graph)
            for finding in findings:
                if finding["type"] == "cycle":
                    _log.warning("Cycle detected: %s", finding["details"])
                    _remove_cycle_edge(graph, finding)

        _graph_cache = graph
        import time as _time
        _graph_cache_ts = _time.time()
        return graph

    except Exception:
        _log.debug("Failed to build skill graph", exc_info=True)
        return {}


def invalidate_graph_cache() -> None:
    global _graph_cache, _graph_cache_ts
    _graph_cache = None
    _graph_cache_ts = 0.0


def get_skill_contract(skill_name: str) -> dict | None:
    try:
        graph = build_skill_graph()
        entry = graph.get(skill_name)
        if entry is None:
            return None
        contract = entry.get("contract", {})
        return contract if contract else None
    except Exception:
        return None


def get_next_skills(skill_name: str) -> list[str]:
    try:
        graph = build_skill_graph()
        entry = graph.get(skill_name)
        if entry is None:
            return []
        return list(entry.get("next_skills", []))
    except Exception:
        return []


def get_skill_conflicts(skill_name: str) -> list[str]:
    try:
        graph = build_skill_graph()
        entry = graph.get(skill_name)
        if entry is None:
            return []
        return list(entry.get("conflicts", []))
    except Exception:
        return []


def get_skills_for_phase(phase: str) -> list[dict]:
    try:
        graph = build_skill_graph()
        phase_upper = phase.upper() if phase else ""
        results = []
        for skill_name, entry in graph.items():
            if entry.get("phase") == phase_upper:
                results.append({
                    "name": skill_name,
                    **{k: v for k, v in entry.items() if k != "contract"},
                })
        return results
    except Exception:
        return []


def get_lifecycle_chain() -> list[str]:
    try:
        graph = build_skill_graph()
        chain: list[str] = []
        visited: set[str] = set()

        define_skills = [
            name for name, entry in graph.items()
            if entry.get("phase") == "DEFINE"
        ]

        current = define_skills[0] if define_skills else None
        while current and current not in visited:
            visited.add(current)
            chain.append(current)
            entry = graph.get(current, {})
            next_list = entry.get("next_skills", [])
            current = next_list[0] if next_list else None

        return chain

    except Exception:
        return []


def validate_graph() -> list[dict]:
    try:
        graph = build_skill_graph(validate_on_build=False)
        findings: list[dict] = []

        findings.extend(_detect_cycles(graph))

        all_skills = set(graph.keys())
        for skill_name, entry in graph.items():
            for ns in entry.get("next_skills", []):
                if ns not in all_skills:
                    findings.append({
                        "type": "broken_ref",
                        "details": f"{skill_name} references non-existent next_skill: {ns}",
                    })
            for c in entry.get("conflicts", []):
                if c not in all_skills:
                    findings.append({
                        "type": "broken_ref",
                        "details": f"{skill_name} references non-existent conflict: {c}",
                    })

        return findings

    except Exception:
        return []


def _detect_cycles(graph: dict[str, dict]) -> list[dict]:
    findings: list[dict] = []
    visited: set[str] = set()
    path: list[str] = []
    path_set: set[str] = set()

    def _dfs(node: str) -> None:
        if node in path_set:
            cycle_start = path.index(node)
            cycle_path = path[cycle_start:] + [node]
            findings.append({
                "type": "cycle",
                "details": f"Cycle detected: {' -> '.join(cycle_path)}",
                "path": cycle_path,
            })
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)
        path_set.add(node)

        entry = graph.get(node)
        if entry:
            for ns in entry.get("next_skills", []):
                if ns in graph:
                    _dfs(ns)

        path.pop()
        path_set.discard(node)

    for skill_name in graph:
        if skill_name not in visited:
            _dfs(skill_name)

    return findings


def _remove_cycle_edge(graph: dict[str, dict], finding: dict) -> None:
    try:
        path = finding.get("path", [])
        if len(path) >= 2:
            source = path[-2]
            target = path[-1]
            entry = graph.get(source)
            if entry and target in entry.get("next_skills", []):
                entry["next_skills"] = [
                    ns for ns in entry["next_skills"] if ns != target
                ]
    except Exception:
        _log.debug("Failed to remove cycle edge", exc_info=True)
