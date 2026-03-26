---
phase: 03-callbacks-enforcement-and-first-notebooks
plan: 02
subsystem: anti_patterns
tags: [anti-patterns, cca-traps, confidence-escalation, prompt-compliance, swiss-army, tdd]
dependency_graph:
  requires:
    - 03-01 (agent_loop.py with tools/callbacks params, handlers.py dispatch, callbacks.py)
    - 02-02 (tools/definitions.py TOOLS list, agent_loop.py run_agent_loop)
  provides:
    - src/customer_service/anti_patterns/confidence_escalation.py
    - src/customer_service/anti_patterns/prompt_compliance.py
    - src/customer_service/anti_patterns/swiss_army_agent.py
    - src/customer_service/anti_patterns/__init__.py (updated)
    - tests/test_anti_patterns.py
  affects:
    - notebooks/ (imported by NB01, NB02, NB03 for comparison sections)
tech_stack:
  added: []
  patterns:
    - TDD (RED: test imports fail, GREEN: modules implemented, no REFACTOR needed)
    - Anti-pattern as teaching artifact (wrong code is the point)
    - run_agent_loop tools parameter for Swiss Army override
    - Per-tool callback registry (callbacks dict, not passed to anti-patterns)
key_files:
  created:
    - src/customer_service/anti_patterns/confidence_escalation.py
    - src/customer_service/anti_patterns/prompt_compliance.py
    - src/customer_service/anti_patterns/swiss_army_agent.py
    - tests/test_anti_patterns.py
  modified:
    - src/customer_service/anti_patterns/__init__.py
    - src/customer_service/agent/callbacks.py
decisions:
  - run_agent_loop tools parameter (tools=None defaults to TOOLS) used for Swiss Army override — avoids code duplication, backward compatible
  - compliance_callback handles both flat {"details":...} and nested {"status":"logged","entry":{"details":...}} shapes to cover unit tests and integration tests
  - Anti-pattern modules intentionally omit callbacks — this is the CCA trap being demonstrated
key-decisions:
  - run_agent_loop extended with optional tools parameter; Swiss Army agent passes SWISS_ARMY_TOOLS there
  - compliance_callback updated to expose top-level "details" field from nested entry shape for audit inspection
metrics:
  duration: ~5 minutes
  completed_date: "2026-03-26T19:49:56Z"
  tasks_completed: 1
  files_created: 4
  files_modified: 2
---

# Phase 3 Plan 02: Anti-Pattern Modules Summary

Three CCA anti-pattern modules for notebooks demonstrating observable failures in confidence-based escalation, prompt-only compliance, and 15-tool Swiss Army agents.

## What Was Built

### confidence_escalation.py
- `CONFIDENCE_SYSTEM_PROMPT`: Full system prompt containing "rate your confidence from 0-100" instruction with 70 threshold. Anti-pattern: self-reported LLM confidence as routing signal.
- `run_confidence_agent(client, services, user_message, model)`: Calls `run_agent_loop` with no callbacks. For C003 $600 refund scenario, Claude reports high confidence and handles the refund directly instead of escalating.
- CCA exam lesson: self-reported confidence is ALWAYS the wrong answer for escalation routing.

### prompt_compliance.py
- `PROMPT_COMPLIANCE_SYSTEM_PROMPT`: Contains "never log credit card" and "redact before logging" instructions. Anti-pattern: PCI compliance enforced only via system prompt text.
- `run_prompt_compliance_agent(client, services, user_message, model)`: Calls `run_agent_loop` with no callbacks. Claude sometimes logs raw card numbers (4111-1111-1111-1111) anyway.
- CCA exam lesson: prompts are probabilistic guidance; programmatic hooks are deterministic enforcement.

### swiss_army_agent.py
- `SWISS_ARMY_TOOLS`: 15 tools = 5 correct (from `definitions.py`) + 10 distractors. Canonical misroutes: `file_billing_dispute` (overlaps `process_refund` for $600 refund), `create_support_ticket` (overlaps `escalate_to_human` for closure/legal).
- `SWISS_ARMY_SYSTEM_PROMPT`: No special guidance about tool selection — the overload is the trap.
- `run_swiss_army_agent(client, services, user_message, model)`: Calls `run_agent_loop` with `tools=SWISS_ARMY_TOOLS` override parameter.
- CCA exam lesson: beyond 4-5 tools, tool selection accuracy degrades measurably.

### tests/test_anti_patterns.py
- 33 structural tests covering all three modules.
- Tests verify: system prompt content, exports, tool count (exactly 15), all 5 correct tools present, all 10 named distractors present, no empty distractor descriptions.
- Deterministic — no API calls, no mocking needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed compliance_callback for nested log_interaction result shape**
- **Found during:** Task 1 implementation (running full test suite to check for regressions)
- **Issue:** `compliance_callback` in `callbacks.py` looked for `result_dict.get("details")` but `log_interaction` handler returns `{"status": "logged", "entry": {"action": ..., "details": ..., "timestamp": ...}}` — `details` is nested inside `entry`. The unit test used a simplified flat shape that didn't expose this mismatch.
- **Fix:** Updated `compliance_callback` to handle both flat shape (for unit tests) and nested `entry.details` shape (actual handler output). Also exposes a top-level `details` field from the nested shape so audit inspection and test assertions work uniformly.
- **Files modified:** `src/customer_service/agent/callbacks.py`
- **Commit:** 179d8e3 (included in main task commit)

## Self-Check

### Files created/modified

- [x] `src/customer_service/anti_patterns/confidence_escalation.py` — exists
- [x] `src/customer_service/anti_patterns/prompt_compliance.py` — exists
- [x] `src/customer_service/anti_patterns/swiss_army_agent.py` — exists
- [x] `src/customer_service/anti_patterns/__init__.py` — updated with exports
- [x] `tests/test_anti_patterns.py` — exists, 33 tests pass

### Commits

- [x] 179d8e3 — feat(03-02): three anti-pattern modules with structural tests

### Test results

- 33/33 anti-pattern tests pass
- 143/143 full test suite passes
- ruff check: all checks passed

## Self-Check: PASSED
