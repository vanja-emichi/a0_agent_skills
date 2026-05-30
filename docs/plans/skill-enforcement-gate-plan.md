# Implementation Plan: Skill Enforcement Gate + Outcome Eval Harness

> Generated from spec `docs/specs/skill-enforcement-gate-spec.md`.
>
> **Status in broader roadmap:** This is the **Phase 1 / Slice 1** implementation plan under the umbrella workflow-governance roadmap.
> For the broader roadmap, see:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

  5 ## Overview
  6 
  7 This plan implements a workflow-governance upgrade for `a0_agent_skills` that makes the SDLC lifecycle harder to skip and easier to measure.
  8 
  9 The feature has two inseparable halves:
 10 
 11 1. **Skill Enforcement Gate** — a `tool_execute_before` extension that notices when the agent is about to implement directly without loading a clearly-applicable skill.
 12 2. **Outcome Eval Harness** — telemetry and lightweight eval fixtures that prove the gate helps rather than merely interrupts.
 13 
 14 The implementation follows five principles:
 15 
 16 1. **Observe before enforce** — zero behavior change ships first, then corrective behavior.
 17 2. **User-space only** — all implementation lives in `/a0/usr/plugins/a0_agent_skills`; no core framework edits.
 18 3. **Utility-model classification** — use Agent Zero's existing `call_utility_model(...)` path for the classifier side-query.
 19 4. **In-band self-correction** — corrective warnings/observations, not `nudge()` and not forced tool rewrites.
 20 5. **Measure every new behavior** — no enforcement without telemetry and focused tests.
 21 
 22 ## Architecture Decisions
 23 
 24 - The gate targets **`code_execution_tool`** and **`text_editor`** only in MVP.
 25 - Match detection is **hybrid**: cheap `search_skills()` prefilter, utility-model classifier only in `enforce` mode.
 26 - Default config is **`enforcement_mode: observe`**.
 27 - If the utility model is unavailable, the gate logs **`classifier_unavailable`** and skips correction.
 28 - The correction primitive is an **in-band corrective warning/observation**, not `context.nudge()`, `agent.nudge()`, or a forced `skills_tool` rewrite.
 29 - Shadow sampling is **out of MVP**; placeholder config exists with default `0.0`.
 30 - Outcome telemetry extends the existing **`.a0proj/skill_activations.jsonl`** log rather than introducing a second telemetry file.
 31 
 32 ## Dependency Graph
 33 
 34 ```text
 35 Spec approved
 36    │
 37    ├── Config schema + helper scaffolding
 38    │       │
 39    │       ├── Match helper (prefilter + utility classifier)
 40    │       │       │
 41    │       │       ├── Observe-mode telemetry extension changes
 42    │       │       │       │
 43    │       │       │       ├── Enforcer extension (observe only)
 44    │       │       │       │       │
 45    │       │       │       │       └── Enforce-mode corrective warning
 46    │       │       │       │
 47    │       │       │       └── Focused tests
 48    │       │       │
 49    │       │       └── Eval fixtures + runner
 50    │       │
 51    │       └── README / operator docs
 52    │
 53    └── Full regression verification
 54 ```
 55 
 56 ## Task List
 57 
 58 ### Phase 1: Foundations and Safe Instrumentation
 59 
 60 ## Task 1: Add configuration surface for enforcement mode and classifier policy
 61 
 62 **Description:**
 63 Extend plugin configuration so the feature can be operated safely in observe mode first. Add the enforcement mode, classifier policy defaults, and a disabled shadow-sampling placeholder.
 64 
 65 **Acceptance criteria:**
 66 - [ ] `default_config.yaml` defines `enforcement_mode: observe`
 67 - [ ] Config includes utility-classifier policy fields needed by the gate
 68 - [ ] Config includes `enforcement_shadow_sample_rate: 0.0`
 69 - [ ] Existing telemetry defaults remain unchanged
 70 
 71 **Verification:**
 72 - [ ] Read `default_config.yaml` and confirm the new keys are documented clearly
 73 - [ ] Focused test proves plugin config loads with defaults intact
 74 - [ ] Existing telemetry tests still pass
 75 
 76 **Dependencies:** None
 77 
 78 **Files likely touched:**
 79 - `/a0/usr/plugins/a0_agent_skills/default_config.yaml`
 80 - `/a0/usr/plugins/a0_agent_skills/tests/test_telemetry_default_and_hooks.py`
 81 
 82 **Estimated scope:** Small
 83 
 84 ## Task 2: Build the skill-match helper with prefilter and utility-model classifier
 85 
 86 **Description:**
 87 Create a dedicated helper module that centralizes the gate predicate: target-tool detection, loaded-skill lookup, `search_skills()` prefilter, and utility-model classification with an explicit `classifier_unavailable` outcome.
 88 
 89 **Acceptance criteria:**
 90 - [ ] New helper exposes a prefilter function based on `helpers.skills.search_skills()`
 91 - [ ] New helper reads loaded skills via `get_loaded_skill_entries(agent)`
 92 - [ ] Utility-model classification path calls `agent.call_utility_model(...)`
 93 - [ ] Helper returns explicit result states: no_candidate / already_loaded / should_correct / should_not_correct / classifier_unavailable
 94 
 95 **Verification:**
 96 - [ ] Focused unit tests cover each result state
 97 - [ ] Source-based test proves the helper never depends on a stripped `search_skills()` score
 98 - [ ] Manual read confirms no direct core imports beyond existing helper APIs
 99 
100 **Dependencies:** Task 1
101 
102 **Files likely touched:**
103 - `/a0/usr/plugins/a0_agent_skills/helpers/skill_match.py` (new)
104 - `/a0/usr/plugins/a0_agent_skills/tests/test_skill_match.py` (new)
105 
106 **Estimated scope:** Medium
107 
108 ## Task 3: Extend skill telemetry schema for gate decisions and outcomes
109 
110 **Description:**
111 Evolve `_05_skill_telemetry.py` from activation-only logging to outcome-aware logging, including would-fire decisions, correction decisions, and classifier-unavailable events — while preserving backward-safe behavior.
112 
113 **Acceptance criteria:**
114 - [ ] Telemetry logs gate-related decision records in the existing JSONL file
115 - [ ] Existing activation logging still works
116 - [ ] Log entries distinguish observe vs enforce behavior
117 - [ ] `classifier_unavailable` is logged as a first-class event/reason
118 
119 **Verification:**
120 - [ ] Focused telemetry tests pass
121 - [ ] Existing telemetry tests remain green
122 - [ ] Manual spot-check of JSONL entry shape confirms new fields are present and readable
123 
124 **Dependencies:** Task 2
125 
126 **Files likely touched:**
127 - `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/_05_skill_telemetry.py`
128 - `/a0/usr/plugins/a0_agent_skills/tests/test_outcome_telemetry.py` (new)
129 - `/a0/usr/plugins/a0_agent_skills/tests/test_skill_telemetry.py`
130 
131 **Estimated scope:** Medium
132 
133 ### Checkpoint: After Phase 1
134 
135 - [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_skill_match.py -v`
136 - [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_outcome_telemetry.py -v`
137 - [ ] Existing telemetry tests remain green
138 - [ ] Observe-mode infrastructure exists with no behavior change to tool execution
139 
140 ### Phase 2: Observe-Mode Gate
141 
142 ## Task 4: Implement the observe-only enforcer extension
143 
144 **Description:**
145 Add `_10_skill_enforcer.py` under `tool_execute_before` that runs only for target tools, evaluates the gate predicate, and records would-fire decisions without mutating `tool_args` or changing execution.
146 
147 **Acceptance criteria:**
148 - [ ] Extension only inspects `code_execution_tool` and `text_editor`
149 - [ ] In `observe` mode, it produces telemetry decisions and does not mutate tool args
150 - [ ] If a matching skill is already loaded, the extension no-ops cleanly
151 - [ ] The extension body is fail-safe (never breaks the loop)
152 
153 **Verification:**
154 - [ ] Focused tests assert zero mutation in observe mode
155 - [ ] Behavioral tests cover target and non-target tools
156 - [ ] Read extension and confirm top-level try/except pattern matches plugin conventions
157 
158 **Dependencies:** Task 3
159 
160 **Files likely touched:**
161 - `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_before/_10_skill_enforcer.py` (new)
162 - `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py` (new)
163 
164 **Estimated scope:** Medium
165 
166 ## Task 5: Add operator-facing documentation for observe mode
167 
168 **Description:**
169 Document what observe mode does, how to read the telemetry, and how to decide whether the gate is ready to switch to enforce.
170 
171 **Acceptance criteria:**
172 - [ ] README documents `observe` vs `enforce`
173 - [ ] Docs explain the meaning of would-fire-rate and `classifier_unavailable`
174 - [ ] No docs imply enforcement is enabled by default
175 
176 **Verification:**
177 - [ ] Re-read README sections for consistency with the spec
178 - [ ] Grep for `observe`, `enforce`, and `classifier_unavailable`
179 - [ ] Contract wording matches actual config defaults
180 
181 **Dependencies:** Task 4
182 
183 **Files likely touched:**
184 - `/a0/usr/plugins/a0_agent_skills/README.md`
185 - `/a0/usr/projects/a0_agent_skills/docs/specs/skill-enforcement-gate-spec.md` (only if wording drift needs correction)
186 
187 **Estimated scope:** Small
188 
189 ### Checkpoint: After Phase 2
190 
191 - [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py -v`
192 - [ ] Observe mode logs would-fire decisions with zero execution change
193 - [ ] README accurately describes the shipped default behavior
194 - [ ] Ready for safe manual telemetry review before any auto-correction logic ships
195 
196 ### Phase 3: Enforce-Mode Self-Correction
197 
198 ## Task 6: Implement corrective warning behavior in enforce mode
199 
200 **Description:**
201 Enable the enforcer to append an in-band corrective observation/warning when the utility-model classifier decides a skill should have been loaded first.
202 
203 **Acceptance criteria:**
204 - [ ] In `enforce` mode, the utility-model classifier runs only after the prefilter flags a candidate
205 - [ ] Positive classifier verdict appends a corrective warning/observation
206 - [ ] Utility-model unavailability skips correction and logs `classifier_unavailable`
207 - [ ] No use of `nudge()` or forced `skills_tool` rewrites
208 
209 **Verification:**
210 - [ ] Focused tests assert corrective warning is emitted only in enforce mode
211 - [ ] Tests assert no correction when classifier says no
212 - [ ] Tests assert no silent fallback to the main chat model
213 
214 **Dependencies:** Task 5
215 
216 **Files likely touched:**
217 - `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_before/_10_skill_enforcer.py`
218 - `/a0/usr/plugins/a0_agent_skills/helpers/skill_match.py`
219 - `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py`
220 
221 **Estimated scope:** Medium
222 
223 ## Task 7: Add focused regression tests around correction shape and guardrails
224 
225 **Description:**
226 Harden the feature with explicit tests that prevent future regression into the wrong correction primitives or accidental broadening of scope.
227 
228 **Acceptance criteria:**
229 - [ ] Tests fail if `nudge()` is introduced as the correction primitive
230 - [ ] Tests fail if target tool calls are rewritten into forced `skills_tool` invocations
231 - [ ] Tests cover already-loaded skill no-op behavior
232 - [ ] Tests cover non-target-tool no-op behavior
233 
234 **Verification:**
235 - [ ] New regression tests pass
236 - [ ] Existing plugin test suite remains green
237 - [ ] Manual read confirms guardrails are represented in test names and assertions
238 
239 **Dependencies:** Task 6
240 
241 **Files likely touched:**
242 - `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py`
243 - `/a0/usr/plugins/a0_agent_skills/tests/test_enforcement_language.py` (only if terminology needs consistency updates)
244 
245 **Estimated scope:** Small
246 
247 ### Checkpoint: After Phase 3
248 
249 - [ ] Enforce mode self-correction works as specified
250 - [ ] Guardrail regressions are covered by tests
251 - [ ] No forbidden primitives (`nudge`, forced tool rewrite, chat-model fallback) have crept in
252 
253 ### Phase 4: Thin Eval Harness
254 
255 ## Task 8: Add activation eval fixtures for representative skills
256 
257 **Description:**
258 Create a small fixture set that exercises the gate's matching behavior for the four headline skills: `spec-driven-development`, `test-driven-development`, `debugging-and-error-recovery`, and `code-review-and-quality`.
259 
260 **Acceptance criteria:**
261 - [ ] Fixtures exist for should-trigger prompts
262 - [ ] Fixtures exist for near-miss prompts
263 - [ ] Fixture format is readable and simple to extend
264 - [ ] Fixture wording maps cleanly to the selected skills
265 
266 **Verification:**
267 - [ ] Re-read fixtures and confirm each has an expected outcome
268 - [ ] Manual spot-check against skill descriptions/triggers
269 - [ ] Fixture paths are documented in the repo
270 
271 **Dependencies:** Task 7
272 
273 **Files likely touched:**
274 - `/a0/usr/plugins/a0_agent_skills/evals/fixtures/spec-driven-development.yaml` (new)
275 - `/a0/usr/plugins/a0_agent_skills/evals/fixtures/test-driven-development.yaml` (new)
276 - `/a0/usr/plugins/a0_agent_skills/evals/fixtures/debugging-and-error-recovery.yaml` (new)
277 - `/a0/usr/plugins/a0_agent_skills/evals/fixtures/code-review-and-quality.yaml` (new)
278 
279 **Estimated scope:** Small
280 
281 ## Task 9: Build the thin eval runner and document how to use it
282 
283 **Description:**
284 Add a lightweight runner that executes the fixture set and reports matching behavior clearly enough to tune the gate before broader rollout.
285 
286 **Acceptance criteria:**
287 - [ ] Eval runner exists and can execute the fixture set from plugin root
288 - [ ] Runner output distinguishes should-trigger success vs near-miss failure
289 - [ ] README includes the eval command and expected usage
290 - [ ] Runner is narrow in scope: activation/matching only, not a full benchmark framework
291 
292 **Verification:**
293 - [ ] Run the eval runner successfully
294 - [ ] Inspect output for clarity and operator usefulness
295 - [ ] README instructions are correct and reproducible
296 
297 **Dependencies:** Task 8
298 
299 **Files likely touched:**
300 - `/a0/usr/plugins/a0_agent_skills/evals/run_skill_evals.py` (new)
301 - `/a0/usr/plugins/a0_agent_skills/README.md`
302 - `/a0/usr/plugins/a0_agent_skills/tests/test_skill_match.py`
303 
304 **Estimated scope:** Medium
305 
306 ### Checkpoint: After Phase 4
307 
308 - [ ] Eval fixtures exist for all four headline skills
309 - [ ] Eval runner executes successfully
310 - [ ] Operators can measure whether the gate is too noisy before broad enablement
311 
312 ### Phase 5: Final Verification and Release Readiness
313 
314 ## Task 10: Run full plugin verification and capture rollout guidance
315 
316 **Description:**
317 Run the focused tests plus the broader plugin suite, then record the recommended rollout sequence: observe first, inspect telemetry, then opt into enforce.
318 
319 **Acceptance criteria:**
320 - [ ] Focused gate tests pass
321 - [ ] Full plugin test suite remains green
322 - [ ] README rollout guidance is explicit about observe-first deployment
323 - [ ] No open contradictions remain between spec, plan, config, tests, and docs
324 
325 **Verification:**
326 - [ ] `python -m pytest tests/ --tb=short`
327 - [ ] Manual read across spec, README, and config
328 - [ ] Spot-check `.a0proj/skill_activations.jsonl` output after a local run
329 
330 **Dependencies:** Task 9
331 
332 **Files likely touched:**
333 - `/a0/usr/plugins/a0_agent_skills/README.md`
334 - `/a0/usr/projects/a0_agent_skills/docs/plans/skill-enforcement-gate-plan.md` (if status notes/checkpoints need updating)
335 
336 **Estimated scope:** Small
337 
338 ## Risks and Mitigations
339 
340 | Risk | Impact | Mitigation |
341 |------|--------|------------|
342 | Prefilter too noisy | High | Observe-first rollout, explicit telemetry, no classifier in observe mode |
343 | Utility model unavailable on some installs | Medium | Log `classifier_unavailable`, skip correction, never silently fall back to chat model |
344 | Corrective warning causes loops or repeated self-correction | High | Focused enforce-mode tests, regression coverage, narrow target tools |
345 | Scope creep into full eval infrastructure | Medium | Keep eval harness limited to fixture-based activation checks |
346 | Repo confusion between project docs repo and installed plugin repo | Medium | Keep docs in `/a0/usr/projects/a0_agent_skills`, implementation in `/a0/usr/plugins/a0_agent_skills`, and name both paths explicitly in tasks |
347 
348 ## Parallelization Opportunities
349 
350 Safe to parallelize after Phase 1:
351 - Fixture authoring for the four representative skills
352 - README/operator-doc drafting
353 - Telemetry test writing after the schema shape is stable
354 
355 Must remain sequential:
356 - Config surface before helper implementation
357 - Helper before enforcer
358 - Observe-mode gate before enforce-mode correction
359 - Eval runner after fixture format is settled
360 
361 ## Open Questions
362 
363 - Should a future strict mode use `InterventionException`, or should the plugin remain permanently self-correcting-only?
364 - Should browser write actions join the target-tool set in a later slice, once observe telemetry is available?
365 - Should utility-model override become plugin-specific (`enforcement_classifier_model`) or remain tied to Agent Zero's global utility slot?

