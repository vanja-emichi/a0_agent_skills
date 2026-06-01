# Security Audit Report: Approval Gate Wiring

**Date:** 2026-06-02
**Auditor:** Security Auditor (security-auditor profile)
**Scope:** Approval Gate Wiring feature — 8 tasks across `/a0/usr/plugins/a0_agent_skills/`
**Phase at time of audit:** PLAN (pre-BUILD)

---

## Overall Risk Assessment: **MEDIUM**

The approval gate wiring is a **development workflow governance** feature running inside a single-user Agent Zero instance. The threat model is inherently limited — there is no multi-tenant exposure, no network-facing surface, and no sensitive data beyond developer workflow state. The implementation demonstrates strong defensive practices (path traversal protection, fail-safe error handling, privacy-aware telemetry). The findings below represent hardening opportunities rather than exploitable vulnerabilities in a production security sense.

**No Critical or High severity findings.** The feature is safe to ship with the Medium items tracked for follow-up.

---

## Findings Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 5 |
| Info | 4 |

---

## Findings

### Critical (must fix before shipping)

**None.**

---

### High (should fix before shipping)

**None.**

---

### Medium (should fix in follow-up)

#### [MEDIUM-1] Fail-Open Exception Handling in `check_phase_approval_gate`

- **Location:** `helpers/phase_governance.py:353-356`
- **Description:** The `check_phase_approval_gate` function catches all exceptions and returns `True` (allow transition). This is a fail-open design: any error during approval validation silently permits the phase transition.
  ```python
  except Exception as exc:
      # Fail-safe: never block the agent loop on errors.
      _log.debug("Approval gate check failed: %s", exc, exc_info=True)
      return True
  ```
- **Impact:** If an attacker can trigger an exception in `is_artifact_approved`, `read_workflow_artifacts`, or any helper in the call chain, the gate is bypassed entirely. The debug-level logging means the bypass would not be visible in normal logs.
- **Proof of concept:** Corrupting `workflow_artifacts.json` with invalid JSON causes `read_workflow_artifacts` to return `None`, which causes `is_artifact_approved` to return `False` cleanly. However, if `resolve_state_dir` raises an unexpected exception (e.g., due to a corrupt project config), the top-level catch in `check_phase_approval_gate` returns `True`, bypassing the gate.
- **Recommendation:** Add a specific allowlist of expected exceptions and return `False` (deny) for unexpected errors:
  ```python
  except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
      _log.warning("Approval gate check failed (expected): %s", exc)
      return False  # Deny on expected errors
  except Exception as exc:
      _log.error("Approval gate check failed (UNEXPECTED): %s", exc, exc_info=True)
      return False  # Deny on unexpected errors too
  ```
  Alternatively, keep the fail-open for the specific `is_artifact_approved` call but add a metric/counter for unexpected gate bypasses so they're observable.

---

#### [MEDIUM-2] Negation Detection Bypasses via Sentence-Level Negation

- **Location:** `extensions/python/tool_execute_before/_20_approval_gate.py:70-75`
- **Description:** The negation check only examines the word immediately before the approval phrase:
  ```python
  prefix = text_lower[:match.start()].rstrip()
  if prefix.endswith(_NEGATION_SUFFIXES):
      continue
  ```
  This misses sentence-level negation where the negation word appears earlier in the sentence.
- **Impact:** A user message like `"I don't think we should approve this yet"` or `"I don't think it looks good"` would be detected as approval because the negation word (`don't`) is not immediately adjacent to the approval phrase.
- **Proof of concept:**
  - `"I don't think we should approve this"` → `approve` matched, prefix `"i don't think we should "` → rstripped → `"i don't think we should"` → does NOT end with `not`/`n't`/`never`/`no` → **FALSE APPROVAL**
  - `"I don't think it looks good"` → `looks good` matched, prefix `"i don't think it "` → rstripped → `"i don't think it"` → does NOT end with negation suffix → **FALSE APPROVAL**
- **Recommendation:** Enhance negation detection to scan the full clause before the matched phrase:
  ```python
  # Check for any negation word in the preceding clause
  prefix_words = text_lower[:match.start()].split()
  negation_window = 5  # Check last N words
  for word in prefix_words[-negation_window:]:
      cleaned = word.strip(".,;:!")
      if cleaned in _NEGATION_WORDS or cleaned.endswith(_NEGATION_SUFFIXES):
          return False  # Negation found → not approval
  ```
  This is a refinement, not a blocker. The question-mark rejection (line 64) already catches many ambiguous cases.

---

#### [MEDIUM-3] Unknown Artifact Types Logged but Not Rejected in `mark_artifact_approved`

- **Location:** `helpers/workflow_state.py:270-274`
- **Description:** When `mark_artifact_approved` receives an artifact type not in `_VALID_ARTIFACT_TYPES`, it logs a warning but proceeds to mark it as approved anyway:
  ```python
  if artifact_type not in _VALID_ARTIFACT_TYPES:
      _log.warning(
          "Unknown artifact type in mark_artifact_approved: %s ...",
          artifact_type, sorted(_VALID_ARTIFACT_TYPES),
      )
  # Falls through to approval logic — no return!
  ```
- **Impact:** An attacker who can influence the `artifact_type` parameter (e.g., through a crafted agent state or extension) could create arbitrary approval entries in `workflow_artifacts.json`. In practice, the value comes from the hardcoded `_PHASE_ARTIFACT_MAP` in `_20_approval_gate.py`, so this is a defense-in-depth issue rather than directly exploitable.
- **Recommendation:** Add an early return after the warning:
  ```python
  if artifact_type not in _VALID_ARTIFACT_TYPES:
      _log.warning("Unknown artifact type: %s — rejecting", artifact_type)
      return None
  ```

---

### Low / Informational

#### [LOW-1] TOCTOU Race in Mtime-Based Approval Invalidation

- **Location:** `helpers/workflow_state.py:291` (write) and `helpers/workflow_state.py:353` (read)
- **Description:** There is a theoretical time-of-check-time-of-use race between `is_artifact_approved` reading the file mtime and the actual use of that approval decision. An artifact file could be modified between the mtime check and the phase transition.
- **Impact:** Negligible in practice. Agent Zero is single-threaded per agent, and the check-to-use window is microseconds. No multi-instance coordination is needed.
- **Recommendation:** No action required. The comment at `workflow_state.py:30-32` already acknowledges the process-level lock limitation. If multi-instance support is ever added, switch to `fcntl` file locking.

---

#### [LOW-2] Direct Filesystem Tampering of `workflow_artifacts.json`

- **Location:** `.a0proj/state/workflow_artifacts.json`
- **Description:** An attacker with local filesystem access can directly edit `workflow_artifacts.json` to set `"approved": {"spec": true}` and bypass approval gates. File permissions are `0o640` (owner read/write, group read).
- **Impact:** Low. This requires local access to the developer's machine. In that threat model, the attacker already has broader access (can modify source code, environment, etc.).
- **Recommendation:** No action required for current deployment. If Agent Zero ever runs in a shared/multi-user environment, consider:
  - Signing approval entries with an HMAC (key derived from a secret)
  - Storing approvals in a more protected location

---

#### [LOW-3] Classifier Prompt Injection via User Message

- **Location:** `helpers/skill_match.py:222-226`
- **Description:** The user's last message is directly interpolated into the classifier prompt sent to the utility model:
  ```python
  user_msg = (
      f"Tool: {tool_name}\n"
      f"Last user message: {last_user_message or '(empty)'}\n"
      f"Candidate skills:\n" + "\n".join(candidate_descs)
  )
  ```
  A crafted message could attempt to manipulate the classifier's JSON response.
- **Impact:** Low. The worst case is a false negative (skill not loaded when it should be), not a security breach. The response is validated as JSON with a boolean `should_load` field. The system prompt is separate and provides strong framing.
- **Recommendation:** Consider sanitizing or truncating the user message before interpolation:
  ```python
  sanitized_msg = (last_user_message or "")[:500]
  ```
  This limits the injection surface without losing classification quality.

---

#### [LOW-4] Debug-Level Logging for Gate Bypass Events

- **Location:** `helpers/phase_governance.py:355`, `_20_approval_gate.py:250`
- **Description:** Gate bypass events (exceptions in approval checking, failed approval recording) are logged at `DEBUG` level, making them invisible in normal operation:
  ```python
  _log.debug("Approval gate check failed: %s", exc, exc_info=True)
  _log.debug("Approval gate failed", exc_info=True)
  ```
- **Impact:** Operators would not notice if the gate is consistently failing open.
- **Recommendation:** Upgrade gate bypass and failure events to `WARNING` level:
  ```python
  _log.warning("Approval gate check failed (bypassing): %s", exc, exc_info=True)
  ```

---

#### [LOW-5] Shadow Sampling Rate Configurable Without Bounds

- **Location:** `config.json:7`, `_10_skill_enforcer.py:553-556`
- **Description:** The `enforcement_shadow_sample_rate` is read as a float with no bounds checking:
  ```python
  shadow_rate = float(cfg.get("enforcement_shadow_sample_rate", 0.0))
  if shadow_rate > 0.0 and random.random() < shadow_rate:
  ```
  Setting it to `1.0` would cause every observe-mode tool call to invoke the classifier, doubling API costs. Setting it above `1.0` would be equivalent to `1.0`.
- **Impact:** Low. Only affects cost, not security. The rate is in a config file controlled by the operator.
- **Recommendation:** Add bounds validation:
  ```python
  shadow_rate = min(1.0, max(0.0, float(cfg.get("enforcement_shadow_sample_rate", 0.0))))
  ```

---

### Informational (Positive Observations)

#### [INFO-1] Strong Path Traversal Protection

The codebase demonstrates excellent path traversal mitigation:
- `_state_path()` uses `pathlib.Path.relative_to()` to validate all state file paths (line 410-418)
- `_sanitize_slug()` strips path separators and leading dots (line 120-130)
- `resolve_state_dir()` validates the resolved state directory stays within the project root (line 88-94)
- `_safe_write_json()` refuses to write to symlinks (line 385-386)
- `_resolve_log_path()` in telemetry validates against project root (line 68-75)

This is exemplary defense-in-depth.

---

#### [INFO-2] Privacy-Conscious Telemetry Design

The telemetry system is well-designed for privacy:
- Search queries are NOT stored (line 120-121 of telemetry)
- Gate decision logs contain only tool names, states, and skill names — no user message text
- Classifier reasons are sanitized (newlines stripped, truncated to 200 chars) before logging or injection
- Telemetry is disabled by default (`telemetry_enabled: false` in default config)

---

#### [INFO-3] Atomic File Writes with Proper Permissions

State files are written atomically using the write-to-temp-then-rename pattern:
```python
with _write_lock:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)  # Atomic on POSIX
    os.chmod(path, 0o640)  # Owner/group only
```
File permissions are set to `0o640` and directories to `0o750`, limiting access to owner and group.

---

#### [INFO-4] Regex Safety via `re.escape()` and Hardcoded Patterns

The approval phrase detection uses `re.escape()` on hardcoded phrases:
```python
match = re.search(rf"\b{re.escape(phrase)}\b", text_lower)
```
Since the phrases come from a `frozenset` (not user input), there is zero ReDoS risk. The patterns are simple word-boundary matches with no quantifiers, backreferences, or grouping.

---

## Per-Area Assessment

### 1. Input Handling & Injection: **LOW RISK**

Regex patterns are safe from ReDoS (hardcoded phrases with `re.escape()`). The classifier prompt accepts user text but the impact of injection is limited to false negatives in skill matching. The approval phrase detection has a known limitation with sentence-level negation (MEDIUM-2) but is adequate for the development workflow context.

### 2. Authorization & Approval State: **LOW RISK**

Approval state is stored in a local JSON file with proper permissions (`0o640`). Direct tampering requires local filesystem access (LOW-2). The fail-open exception handling in `check_phase_approval_gate` (MEDIUM-1) is the most notable finding but is mitigated by the single-user deployment model. Mtime-based invalidation provides a reasonable integrity check against accidental modifications.

### 3. Path Traversal & File Access: **MINIMAL RISK**

Path traversal is thoroughly mitigated with `pathlib.relative_to()` validation, slug sanitization, symlink refusal, and bounded state directory resolution. This is the strongest security area in the implementation.

### 4. Telemetry & Logging: **MINIMAL RISK**

Telemetry is privacy-conscious: search queries are not stored, gate logs contain no user text, and log paths are validated against the project root. The only gap is debug-level logging for gate bypass events (LOW-4), which should be upgraded to warning level.

### 5. Configuration Security: **LOW RISK**

Configuration uses real booleans (not strings), enforcement mode is set to the stricter `"enforce"`, and defaults are safe (observe mode). The shadow sample rate has no bounds validation (LOW-5) but this is a cost concern, not a security concern. Config file access requires local filesystem permissions.

### 6. Denial of Service: **MINIMAL RISK**

Regex patterns are O(n) with no backtracking. Shadow sampling is bounded by the sample rate and only runs in observe mode. The classifier is called once per target tool call at most. No unbounded loops or resource accumulation patterns found.

### 7. Secrets & Sensitive Data: **NO RISK**

No secrets, API keys, or credentials are present in the codebase. The classifier uses `agent.call_utility_model()` which handles authentication internally. Approval timestamps and mtimes are the only stored data — no PII, no user messages, no credentials.

---

## Recommendations (Priority Order)

| Priority | Finding | Action |
|----------|---------|--------|
| 1 | MEDIUM-1 | Change `check_phase_approval_gate` exception handler to return `False` (deny) instead of `True` (allow). At minimum, upgrade logging to WARNING level. |
| 2 | MEDIUM-3 | Add early return in `mark_artifact_approved` for unknown artifact types. |
| 3 | MEDIUM-2 | Enhance negation detection to scan a window of preceding words, not just the immediately preceding suffix. |
| 4 | LOW-4 | Upgrade gate bypass logging from DEBUG to WARNING. |
| 5 | LOW-5 | Add bounds validation on shadow sample rate config value. |
| 6 | LOW-3 | Truncate user message in classifier prompt to limit injection surface. |

---

## Ship Decision

**RECOMMENDATION: SHIP** — with MEDIUM items tracked for next sprint.

The feature has no Critical or High findings. The three Medium findings represent hardening opportunities that are appropriate for a follow-up PR. The implementation demonstrates strong security practices in the areas that matter most for a local development tool: path traversal prevention, atomic file writes, proper permissions, privacy-aware logging, and ReDoS-safe regex patterns.
