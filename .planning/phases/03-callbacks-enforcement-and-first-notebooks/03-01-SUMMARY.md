---
phase: 03-callbacks-enforcement-and-first-notebooks
plan: 01
subsystem: agent/callbacks + tools/dispatch
tags: [callbacks, escalation, compliance, pii-redaction, veto-guarantee, tdd]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [ENFORCE-01, ENFORCE-02, ENFORCE-03]
  affects: [agent_loop, handlers, process_refund]
tech_stack:
  added: []
  patterns:
    - PostToolUse callback registry (per-tool dict, not list)
    - Two-step vetoable dispatch for process_refund
    - Context dict threaded through dispatch to accumulate escalation flags
    - Regex-based PII redaction (CARD_PATTERN) in compliance_callback
key_files:
  created:
    - src/customer_service/agent/callbacks.py
    - tests/test_callbacks.py
  modified:
    - src/customer_service/tools/handlers.py
    - src/customer_service/tools/process_refund.py
    - src/customer_service/agent/agent_loop.py
    - src/customer_service/agent/__init__.py
decisions:
  - compliance_callback handles both flat {"details": "..."} and nested {"entry": {"details": "..."}} shapes to match log_interaction handler output
  - context dict created in run_agent_loop (not injected) so all tool calls in a session share escalation state
  - handlers.py uses _dispatch_process_refund_with_callback helper to keep dispatch() readable
  - propose_refund returns "status": "proposed" to signal pre-commit state; commit_refund writes to FinancialSystem
metrics:
  duration_seconds: 314
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 2
  files_modified: 4
  tests_added: 34
---

# Phase 03 Plan 01: Callbacks Enforcement and Dispatch Integration Summary

**One-liner:** Per-tool PostToolUse callback registry with two-step vetoable process_refund dispatch, deterministic escalation rules, and PII redaction — all enforced in code, not prompts.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | CallbackResult dataclass, per-tool callbacks, test suite | b4c5765 | callbacks.py, test_callbacks.py |
| 2 | Two-step vetoable dispatch, agent_loop integration, veto guarantee | ecb1c9d | handlers.py, process_refund.py, agent_loop.py, agent/__init__.py |

## What Was Built

### callbacks.py

`CallbackResult` dataclass with `action: Literal["allow", "replace_result", "block"]` plus optional `replacement` and `reason` fields.

Four per-tool callback functions:
- `lookup_customer_callback` — reads tier/flags from result, scans `user_message` for legal keywords, sets `context["vip"]`, `context["account_closure"]`, `context["legal_complaint"]`
- `check_policy_callback` — reads `requires_review` from PolicyResult, sets `context["requires_review"]`
- `escalation_callback` — checks any of four flags in context; returns `action="block"` with `{"status": "blocked", "action_required": "escalate_to_human"}` JSON if triggered
- `compliance_callback` — redacts 16-digit credit card numbers (dashes or spaces) using CARD_PATTERN regex; handles both flat and nested `entry.details` output shapes

`build_callbacks()` factory returns `dict[str, CallbackFn]` mapping tool names to callbacks.

### Two-step vetoable dispatch

`process_refund.py` split into:
- `propose_refund(input_dict, services) -> dict` — customer lookup + policy check, NO FinancialSystem write
- `commit_refund(customer_id, order_id, amount, policy_approved, services) -> str` — writes to FinancialSystem
- `handle_process_refund()` kept as simple path for backward compat (propose + commit, no callbacks)

`handlers.py` extended with `context=None, callbacks=None` parameters. For `process_refund` with callbacks: propose -> callback -> block or commit. For other tools: run handler, then callback; return replacement if `action="replace_result"`.

`agent_loop.py` creates `context = {"user_message": user_message}` and threads it plus `callbacks` through every `dispatch()` call in the loop.

## CCA Compliance Verification

- Escalation triggers: deterministic code checks (amount > $500, VIP, account_closure, legal keywords) — NEVER LLM confidence scores
- Compliance enforcement: regex redaction in callback code — not system prompt instructions
- Veto guarantee: FinancialSystem.get_processed() returns [] after any blocked refund
- Per-tool registry: only the registered callback fires for its tool
- Backward compatible: all 108 existing Phase 2 tests continue to pass

## Test Coverage

34 new tests added to tests/test_callbacks.py:
- 7 escalation_callback tests (VIP, account_closure, legal, requires_review, allow)
- 4 compliance_callback tests (dash format, space format, no PII, last-4 preserved)
- 4 lookup_customer_callback tests (VIP flag, closure flag, legal keyword, no flags)
- 2 check_policy_callback tests (requires_review true/false)
- 5 build_callbacks() tests (type, keys, callable, per-tool routing)
- 5 veto guarantee + dispatch integration tests
- Total passing: 143 (108 prior + 34 new + 1 test from Task 1 merged into Task 2)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] compliance_callback result shape mismatch with log_interaction output**
- **Found during:** Task 2 integration test
- **Issue:** compliance_callback read `result_dict.get("details")` but log_interaction returns `{"status": "logged", "entry": {"customer_id": ..., "details": "..."}}` — details is nested under "entry"
- **Fix:** Updated compliance_callback to handle both flat (`{"details": "..."}`) and nested (`{"entry": {"details": "..."}}`) shapes. Also updated the dispatch integration test assertion to check `parsed["entry"]["details"]`.
- **Files modified:** src/customer_service/agent/callbacks.py, tests/test_callbacks.py
- **Commit:** ecb1c9d (included in Task 2 commit)

## Self-Check: PASSED

Files exist:
- src/customer_service/agent/callbacks.py: FOUND
- tests/test_callbacks.py: FOUND
- src/customer_service/tools/handlers.py: FOUND
- src/customer_service/tools/process_refund.py: FOUND
- src/customer_service/agent/agent_loop.py: FOUND
- src/customer_service/agent/__init__.py: FOUND

Commits:
- b4c5765: feat(03-01): CallbackResult dataclass, per-tool callbacks, and test suite — FOUND
- ecb1c9d: feat(03-01): two-step vetoable dispatch, agent_loop integration, veto guarantee — FOUND

All 143 tests pass. Ruff lint clean on all modified files.
