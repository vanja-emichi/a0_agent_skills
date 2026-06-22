#!/usr/bin/env python3
"""Agent Zero runtime-contract semantic-depth audit.

Goes beyond static presence/absence checks (rev-005 static harness) to evaluate
whether skill guidance is genuinely A0-native or merely boilerplate with correct
tool names swapped in.

Measures 5 semantic dimensions per skill:
  D1: A0 Runtime Model Awareness (Protocol/Extras, two Python envs, plugin paths)
  D2: Non-Boilerplate Guidance Quality (unique vocabulary ratio, domain specificity)
  D3: Correct Tool Usage Patterns (parallel only for independent work, subordinate
      boundary ownership, skills_tool lifecycle)
  D4: Project Context Depth (AGENTS.md chain, .a0proj behavior, live-plugin awareness)
  D5: Eval Fixture A0-Specificity (assertions reference real A0 behaviors)

Each dimension scored 0-3. Total 0-15 per skill.

Usage:
    python3 check_semantic_depth.py --plugin /path/to/plugin [--json-out out.json]
"""

from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any

# A0 runtime model terms that prove genuine framework awareness
A0_RUNTIME_TERMS = [
    "protocol", "extras", "loopdata",  # context layering
    "/opt/venv-a0", "/opt/venv",  # two python envs
    "agentcontext", "context.id", "context type",  # context model
    "monologue", "message_loop", "tool_execute",  # lifecycle hooks
    "helpers.", "extension.py", "plugin.yaml",  # framework internals
    "scheduler task", "chat.json", "loaded_skills",  # runtime evidence
    "promptinclude", "behaviour_adjustment",  # persistent behavior
    "code_execution_tool", "vision_load",  # A0-native tools beyond basic set
]

GENERIC_BOILERPLATE_PHRASES = [
    "use parallel to", "use call_subordinate to",  # without domain context
    "the main agent owns", "the main agent integrates",  # bare ownership boilerplate
    "check the project's ag", "respect .a0proj",  # bare project boilerplate
]

DOMAIN_SPECIFIC_MARKERS = {
    "api-and-interface-design": ["endpoint", "schema", "versioning", "backward compat", "breaking change"],
    "browser-testing-with-devtools": ["browser action", "screenshot", "content", "evaluate", "devtools"],
    "ci-cd-and-automation": ["pipeline", "quality gate", "shift-left", "deploy", "build"],
    "code-review-and-quality": ["severity", "correctness", "readability", "architecture", "finding"],
    "code-simplification": ["guard clause", "chesterton", "nesting", "complexity", "refactor"],
    "context-engineering": ["rules file", "spec", "context layer", "promptinclude", "hierarchy"],
    "debugging-and-error-recovery": ["root cause", "stack trace", "reproduce", "bisect", "regression"],
    "deprecation-and-migration": ["deprecat", "migrat", "consumer", "backward compat", "feature flag"],
    "documentation-and-adrs": ["adr", "decision record", "architecture decision", "context", "consequence"],
    "doubt-driven-development": ["adversarial", "fresh context", "challenge", "assumption", "steelman"],
    "frontend-ui-engineering": ["component", "react", "css", "accessib", "render"],
    "git-workflow-and-versioning": ["branch", "commit", "merge", "tag", "changelog"],
    "idea-refine": ["divergent", "convergent", "hypothesis", "refine", "sharp"],
    "incremental-implementation": ["vertical slice", "increment", "checkpoint", "integration", "shippable"],
    "interview-me": ["hypothesis", "restate", "confirm", "terminal answer", "one question"],
    "observability-and-instrumentation": ["metric", "log", "trace", "instrument", "telemetry"],
    "performance-optimization": ["latency", "throughput", "profil", "bottleneck", "benchmark"],
    "planning-and-task-breakdown": ["dependency", "decompose", "task list", "plan", "sprint"],
    "security-and-hardening": ["vulnerab", "threat", "injection", "sanitiz", "attack surface"],
    "shipping-and-launch": ["deploy", "rollout", "canary", "production", "launch"],
    "source-driven-development": ["official doc", "authoritative", "source", "reference doc"],
    "spec-driven-development": ["spec", "requirement", "acceptance criter", "definition of done"],
    "test-driven-development": ["red", "green", "refactor", "failing test", "test first"],
    "using-agent-skills": ["skill discovery", "routing", "orchestration", "lifecycle", "meta-skill"],
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def score_d1_runtime_model(content: str, lower: str) -> tuple[int, list[str]]:
    """D1: A0 Runtime Model Awareness."""
    found = []
    for term in A0_RUNTIME_TERMS:
        if term.lower() in lower:
            found.append(term)
    if len(found) >= 5:
        return 3, found
    elif len(found) >= 3:
        return 2, found
    elif len(found) >= 1:
        return 1, found
    return 0, found


def score_d2_non_boilerplate(content: str, lower: str, skill_name: str) -> tuple[int, dict]:
    """D2: Non-Boilerplate Guidance Quality.
    Measures unique vocabulary ratio and domain-specific marker density.
    """
    words = re.findall(r'\b[a-z]{4,}\b', lower)
    unique_words = set(words)
    unique_ratio = len(unique_words) / max(len(words), 1)

    markers = DOMAIN_SPECIFIC_MARKERS.get(skill_name, [])
    marker_hits = [m for m in markers if m in lower]
    marker_density = len(marker_hits) / max(len(markers), 1)

    # Check for bare boilerplate phrases without surrounding domain context
    boilerplate_hits = []
    for phrase in GENERIC_BOILERPLATE_PHRASES:
        if phrase in lower:
            # Check if it's surrounded by domain context (at least 50 chars before or after with domain terms)
            for m in re.finditer(re.escape(phrase), lower):
                start = max(0, m.start() - 100)
                end = min(len(lower), m.end() + 100)
                context = lower[start:end]
                has_domain = any(dm in context for dm in markers) if markers else False
                if not has_domain:
                    boilerplate_hits.append(phrase)
                    break

    info = {
        'unique_ratio': round(unique_ratio, 3),
        'marker_hits': marker_hits,
        'marker_density': round(marker_density, 3),
        'bare_boilerplate': boilerplate_hits,
    }

    score = 0
    if marker_density >= 0.4 and not boilerplate_hits:
        score = 3
    elif marker_density >= 0.3:
        score = 2
    elif marker_density >= 0.15:
        score = 1
    return score, info


def score_d3_tool_patterns(content: str, lower: str) -> tuple[int, list[str]]:
    """D3: Correct Tool Usage Patterns.
    Checks if parallel/call_subordinate guidance demonstrates correct patterns.
    """
    issues = []

    # parallel should be for independent work
    if 'parallel' in lower:
        has_independence = bool(re.search(r'independent|concurrent|isolated|no (?:shared|depend|sibling)', lower))
        if not has_independence:
            issues.append('parallel mentioned without independence/dedependence guidance')

    # call_subordinate should mention profiles
    if 'call_subordinate' in lower:
        has_profiles = bool(re.search(r'profile.*(?:code-reviewer|developer|test-engineer|security-auditor|researcher|default)', lower))
        if not has_profiles:
            issues.append('call_subordinate mentioned without profile guidance')

    # Check JSON examples use correct tool_name values
    fences = re.findall(r'```json\s*(.*?)\s*```', content, re.S)
    valid_tools = {'parallel','call_subordinate','code_execution_tool','skills_tool','text_editor','browser','search_engine','document_query','response','scheduler','notify_user','input','wait','vision_load','behaviour_adjustment','a2a_chat'}
    bad_tools = []
    for block in fences:
        if 'tool_name' not in block:
            continue
        for m in re.finditer(r'"tool_name"\s*:\s*"([^"]+)"', block):
            if m.group(1) not in valid_tools:
                bad_tools.append(m.group(1))
    if bad_tools:
        issues.append(f'invalid tool names in JSON: {bad_tools}')

    score = 3
    if len(issues) >= 2:
        score = 1
    elif len(issues) == 1:
        score = 2
    return score, issues


def score_d4_project_depth(content: str, lower: str) -> tuple[int, list[str]]:
    """D4: Project Context Depth.
    Checks if project context references go beyond surface mentions.
    """
    depth_markers = []

    if re.search(r'agents\.md.*(chain|read|update|binding|before|after)', lower):
        depth_markers.append('AGENTS.md chain behavior')
    if re.search(r'\.a0proj.*(project\.json|metadata|config|boundary|respect|edit|modify)', lower):
        depth_markers.append('.a0proj metadata behavior')
    if re.search(r'(active project|project dir).*(relative|path|work from|inside)', lower):
        depth_markers.append('active project path awareness')
    if re.search(r'(preserve|persist).*(context|decision|state|file).*(session|tool|across)', lower):
        depth_markers.append('cross-session context preservation')
    if re.search(r'(installed plugin|usr/plugins|live plugin).*(runtime|override|active|behavior)', lower):
        depth_markers.append('live plugin runtime awareness')

    if len(depth_markers) >= 4:
        return 3, depth_markers
    elif len(depth_markers) >= 2:
        return 2, depth_markers
    elif len(depth_markers) >= 1:
        return 1, depth_markers
    return 0, depth_markers


def score_d5_eval_specificity(skill_dir: Path) -> tuple[int, dict]:
    """D5: Eval Fixture A0-Specificity."""
    eval_path = skill_dir / 'evals' / 'evals.json'
    if not eval_path.exists():
        return 0, {'reason': 'missing evals.json'}
    text = read(eval_path)
    lower = text.lower()

    a0_terms_found = [t for t in ['skills_tool','call_subordinate','parallel','.a0proj','agents.md','active project','project context','browser tool','chat.json','loaded_skills','text_editor','code_execution_tool'] if t in lower]
    has_llm_judge = '"llm judge"' in lower or "'llm judge'" in lower
    has_mutation = '_mutation_check' in lower

    info = {
        'a0_terms': a0_terms_found,
        'has_llm_judge': has_llm_judge,
        'has_mutation_check': has_mutation,
    }

    if len(a0_terms_found) >= 4 and has_llm_judge:
        return 3, info
    elif len(a0_terms_found) >= 2:
        return 2, info
    elif len(a0_terms_found) >= 1:
        return 1, info
    return 0, info


def analyze_skill(skill_dir: Path) -> dict:
    name = skill_dir.name
    content = read(skill_dir / 'SKILL.md')
    lower = content.lower()

    d1, d1_found = score_d1_runtime_model(content, lower)
    d2, d2_info = score_d2_non_boilerplate(content, lower, name)
    d3, d3_issues = score_d3_tool_patterns(content, lower)
    d4, d4_markers = score_d4_project_depth(content, lower)
    d5, d5_info = score_d5_eval_specificity(skill_dir)

    total = d1 + d2 + d3 + d4 + d5
    return {
        'skill': name,
        'total': total,
        'max': 15,
        'd1_runtime_model': d1,
        'd2_non_boilerplate': d2,
        'd3_tool_patterns': d3,
        'd4_project_depth': d4,
        'd5_eval_specificity': d5,
        'd1_found': d1_found,
        'd2_info': d2_info,
        'd3_issues': d3_issues,
        'd4_markers': d4_markers,
        'd5_info': d5_info,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plugin', default='/a0/usr/plugins/a0_agent_skills')
    ap.add_argument('--json-out')
    args = ap.parse_args()

    plugin = Path(args.plugin).resolve()
    skills_dir = plugin / 'skills'
    results = [analyze_skill(p.parent) for p in sorted(skills_dir.glob('*/SKILL.md')) if p.is_file()]
    results = [r for r in results if r]

    total_score = sum(r['total'] for r in results)
    max_score = sum(r['max'] for r in results)
    avg = total_score / max(len(results), 1)

    by_dimension = {}
    for dim in ['d1_runtime_model', 'd2_non_boilerplate', 'd3_tool_patterns', 'd4_project_depth', 'd5_eval_specificity']:
        scores = [r[dim] for r in results]
        by_dimension[dim] = {'avg': round(sum(scores)/max(len(scores),1), 2), 'count_0': scores.count(0), 'count_1': scores.count(1), 'count_3': scores.count(3)}

    weakest = sorted(results, key=lambda r: r['total'])[:8]

    output = {
        'revision': 'rev-005',
        'harness': 'semantic_depth_v1',
        'plugin': str(plugin),
        'total_skills': len(results),
        'total_score': total_score,
        'max_possible': max_score,
        'average_score': round(avg, 2),
        'average_pct': round(avg / 15 * 100, 1),
        'by_dimension': by_dimension,
        'weakest_skills': [{'skill': r['skill'], 'total': r['total'], 'd1': r['d1_runtime_model'], 'd2': r['d2_non_boilerplate'], 'd3': r['d3_tool_patterns'], 'd4': r['d4_project_depth'], 'd5': r['d5_eval_specificity']} for r in weakest],
        'results': results,
    }

    text = json.dumps(output, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in output.items() if k != 'results'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
