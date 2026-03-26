---
phase: 03-callbacks-enforcement-and-first-notebooks
verified: 2026-03-26T21:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 3: Callbacks, Enforcement, and First Notebooks — Verification Report

**Phase Goal:** Students can run notebooks 01-03 and observe how deterministic callbacks catch what prompt-only rules miss, and how 5 focused tools outperform 15
**Verified:** 2026-03-26T21:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | PostToolUse callbacks block a $600 refund and force escalation via code, not prompt | VERIFIED | `escalation_callback` in `callbacks.py` L125–167: checks `requires_review` flag set by `check_policy_callback`; returns `action="block"` with `{"status":"blocked","action_required":"escalate_to_human"}`; `test_veto_guarantee_financial_system_untouched` passes |
| 2 | Per-tool callback registry dispatches ONLY to the registered tool's callback | VERIFIED | `build_callbacks()` returns `dict[str,CallbackFn]`; `handlers.py` L93: `cb = callbacks.get(tool_name)`; `TestBuildCallbacks` suite (5 tests) passes confirming per-tool routing |
| 3 | FinancialSystem is untouched after a blocked refund (veto guarantee) | VERIFIED | `_dispatch_process_refund_with_callback` in `handlers.py` L119–153: propose → callback → block returns without calling `commit_refund`; `test_veto_guarantee_financial_system_untouched` and `test_veto_guarantee_vip_customer` both pass |
| 4 | Block-not-bypass: process_refund returns blocked JSON so Claude calls escalate_to_human naturally | VERIFIED | Blocked result JSON has `"action_required": "escalate_to_human"` (callbacks.py L159); no direct enqueue — Claude decides next tool call |
| 5 | NB01 checks escalation_queue (NOT financial_system.get_processed) | VERIFIED | NB01 cells 6 and 10 use `anti_services.escalation_queue.get_queue()` and `correct_services.escalation_queue.get_queue()`; `financial_system` appears only in `make_services()` setup (cells 2–3); `test_notebook_01_checks_escalation_queue` passes |
| 6 | prompt_compliance anti-pattern has no programmatic enforcement | VERIFIED | `prompt_compliance.py` calls `run_agent_loop` with no callbacks; system prompt contains "never log credit card" and "redact before logging" — prompt-only, no code enforcement |
| 7 | swiss_army_agent has exactly 15 tools (5 correct + 10 distractors) | VERIFIED | `SWISS_ARMY_TOOLS = TOOLS + _DISTRACTOR_TOOLS`; `len(TOOLS)==5`, `len(_DISTRACTOR_TOOLS)==10`; `test_swiss_army_tools_has_exactly_15` passes |
| 8 | Three notebooks exist with Setup > Anti-Pattern > Correct > Compare > CCA Exam Tip structure | VERIFIED | All three .ipynb files exist; `test_notebook_0[123]_sections` pass confirming "Anti-Pattern", "Correct Pattern", "Compare", "CCA Exam Tip" markdown sections present |
| 9 | Each notebook uses print_usage and compare_results helpers | VERIFIED | All three notebooks import `print_usage, compare_results` from `helpers`; `compare_results()` called in each final comparison cell |

**Score:** 9/9 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/customer_service/agent/callbacks.py` | CallbackResult dataclass, per-tool callbacks, build_callbacks() factory | VERIFIED | 244 lines; exports `CallbackResult`, `escalation_callback`, `compliance_callback`, `lookup_customer_callback`, `check_policy_callback`, `build_callbacks`; no `Any` types |
| `src/customer_service/tools/handlers.py` | Extended dispatch() with context and callbacks parameters | VERIFIED | `dispatch(tool_name, input_dict, services, context=None, callbacks=None)`; L93 `callbacks.get(tool_name)` present; `_dispatch_process_refund_with_callback` helper for two-step veto |
| `src/customer_service/tools/process_refund.py` | Two-step vetoable refund: propose then commit | VERIFIED | `propose_refund()` (no FinancialSystem write, returns dict); `commit_refund()` (writes FinancialSystem, returns JSON string); `handle_process_refund()` kept for backward compat |
| `src/customer_service/agent/agent_loop.py` | dispatch() call with context and callbacks | VERIFIED | L121–123: `dispatch(block.name, block.input, services, context=context, callbacks=callbacks)`; L73: `context = {"user_message": user_message}`; `tools` parameter added for Swiss Army override |
| `src/customer_service/agent/__init__.py` | Exports build_callbacks, CallbackResult | VERIFIED | Line 4: `from customer_service.agent.callbacks import CallbackResult, build_callbacks`; both in `__all__` |
| `src/customer_service/anti_patterns/confidence_escalation.py` | run_confidence_agent(), CONFIDENCE_SYSTEM_PROMPT | VERIFIED | Exports both; CONFIDENCE_SYSTEM_PROMPT contains "rate your confidence from 0-100" and "70" threshold; `run_confidence_agent` calls `run_agent_loop` without callbacks |
| `src/customer_service/anti_patterns/prompt_compliance.py` | run_prompt_compliance_agent(), PROMPT_COMPLIANCE_SYSTEM_PROMPT | VERIFIED | Exports both; prompt contains "never log credit card" and "redact"; no callbacks passed |
| `src/customer_service/anti_patterns/swiss_army_agent.py` | run_swiss_army_agent(), SWISS_ARMY_TOOLS with 15 tools | VERIFIED | SWISS_ARMY_TOOLS = TOOLS + _DISTRACTOR_TOOLS (15 total); `file_billing_dispute` and `create_support_ticket` present as canonical misroute targets; passes `tools=SWISS_ARMY_TOOLS` to run_agent_loop |
| `notebooks/01_escalation.ipynb` | Escalation notebook: confidence anti-pattern vs callback enforcement; checks escalation_queue | VERIFIED | Exists; correct structure; checks `escalation_queue.get_queue()` in both anti-pattern and correct sections |
| `notebooks/02_compliance.ipynb` | Compliance notebook: prompt-only vs programmatic redaction; checks audit_log | VERIFIED | Exists; checks `audit_log.get_entries()` for `"4111"` (anti-pattern) and `"****"` (correct pattern) |
| `notebooks/03_tool_design.ipynb` | Tool design notebook: 15-tool Swiss Army vs 5-tool focused | VERIFIED | Exists; displays both tool counts; runs both agents; `compare_results` with distractor call count |
| `tests/test_callbacks.py` | Unit tests for all callback rules and veto guarantee | VERIFIED | 34 tests; covers VIP/closure/legal/amount escalation, PII redaction, build_callbacks(), veto guarantee, dispatch integration, backward compat |
| `tests/test_anti_patterns.py` | Structural tests for anti-pattern modules | VERIFIED | 33 tests; covers all three modules, exact 15-tool count, canonical misroute names |
| `tests/test_notebooks.py` | Smoke tests for notebook existence and section structure | VERIFIED | 13 tests; existence, section checks, escalation_queue check, audit_log check, SWISS_ARMY check, import checks |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `handlers.py` | `callbacks.py` | `callbacks.get(tool_name)` in dispatch() | WIRED | L93 confirmed; per-tool routing only fires registered callback |
| `handlers.py` | `process_refund.py` | `propose_refund` / `commit_refund` two-step veto | WIRED | L135 `proposed = propose_refund(...)`, L147 `return commit_refund(...)` in `_dispatch_process_refund_with_callback` |
| `agent_loop.py` | `handlers.py` | `dispatch(block.name, block.input, services, context=context, callbacks=callbacks)` | WIRED | L121–123 passes both context and callbacks through |
| `notebooks/01_escalation.ipynb` | `anti_patterns/confidence_escalation.py` | imports `run_confidence_agent` | WIRED | Cell 5 import confirmed; `test_notebook_01_imports_confidence_agent` passes |
| `notebooks/01_escalation.ipynb` | `agent/callbacks.py` | imports `build_callbacks` for correct pattern | WIRED | Cell 9 import confirmed; `test_notebook_01_imports_build_callbacks` passes |
| `notebooks/02_compliance.ipynb` | `anti_patterns/prompt_compliance.py` | imports `run_prompt_compliance_agent` | WIRED | Confirmed; `test_notebook_02_imports_prompt_compliance_agent` passes |
| `notebooks/03_tool_design.ipynb` | `anti_patterns/swiss_army_agent.py` | imports `run_swiss_army_agent` and `SWISS_ARMY_TOOLS` | WIRED | Confirmed; `test_notebook_03_imports_swiss_army_agent` passes |
| `anti_patterns/swiss_army_agent.py` | `agent/agent_loop.py` | `run_agent_loop(..., tools=SWISS_ARMY_TOOLS)` | WIRED | L251–258; uses `tools` parameter added to run_agent_loop in Plan 01 |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ENFORCE-01 | 03-01 | PostToolUse callback framework | SATISFIED | `callbacks.py` with `build_callbacks()` returning per-tool registry; `dispatch()` wired to fire callbacks after (or before commit for process_refund) |
| ENFORCE-02 | 03-01 | Deterministic escalation rules (amount > $500, account closure, VIP, legal) | SATISFIED | `escalation_callback` checks 4 flags; `lookup_customer_callback` detects VIP/closure/legal; `check_policy_callback` detects amount > $500; 34 tests cover all branches |
| ENFORCE-03 | 03-01 | Programmatic compliance enforcement (redaction, audit logging) | SATISFIED | `compliance_callback` regex-redacts card numbers before audit write; handles both flat and nested result shapes; `test_compliance_redaction_in_dispatch` passes |
| ANTI-01 | 03-02 | 15-tool Swiss Army anti-pattern | SATISFIED | `swiss_army_agent.py` with `SWISS_ARMY_TOOLS` (exactly 15); `file_billing_dispute` and `create_support_ticket` as canonical misroutes; 33 structural tests pass |
| ANTI-02 | 03-02 | Prompt-only compliance anti-pattern | SATISFIED | `prompt_compliance.py` with `PROMPT_COMPLIANCE_SYSTEM_PROMPT` containing "never log credit card" / "redact"; no callbacks; no programmatic enforcement |
| ANTI-03 | 03-02 | LLM confidence-based escalation anti-pattern | SATISFIED | `confidence_escalation.py` with `CONFIDENCE_SYSTEM_PROMPT` containing "rate your confidence from 0-100" / "below 70" / "escalate"; no callbacks |
| NB-02 | 03-03 | Notebook 01 — Escalation pattern | SATISFIED | `01_escalation.ipynb` exists; checks `escalation_queue.get_queue()` (not `financial_system.get_processed`); CCA Exam Tip present; `print_usage` and `compare_results` used |
| NB-03 | 03-03 | Notebook 02 — Compliance pattern | SATISFIED | `02_compliance.ipynb` exists; checks `audit_log.get_entries()` for PII leakage; correct pattern verifies `****` redaction; CCA Exam Tip present |
| NB-04 | 03-03 | Notebook 03 — Tool design pattern | SATISFIED | `03_tool_design.ipynb` exists; shows 5 vs 15 tool counts; measures distractor tool calls; CCA Exam Tip present |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | No stub implementations, empty handlers, or placeholder anti-patterns detected in production code | — | — |

Scanned files: `callbacks.py`, `handlers.py`, `process_refund.py`, `agent_loop.py`, all three anti-pattern modules, all three notebooks.

No `TODO/FIXME/PLACEHOLDER` patterns found in the enforcement layer. The anti-pattern modules are intentionally wrong (by design) but contain no accidental stubs — their failures are deliberate and observable.

---

## Human Verification Required

### 1. NB01 Anti-Pattern Observable Failure

**Test:** Run `01_escalation.ipynb` cell by cell with a real Anthropic API key on the C003 $600 refund scenario.
**Expected:** Anti-pattern cell prints "FAILURE: Agent did NOT escalate despite $600 refund" (empty escalation_queue). Correct-pattern cell prints "SUCCESS: Agent correctly escalated the $600 refund case" (non-empty escalation_queue).
**Why human:** The anti-pattern failure is probabilistic — Claude's actual confidence-score routing behavior at runtime. The SUMMARY notes Claude "typically" skips escalation; the notebook handles the edge case where it might escalate anyway. Cannot verify Claude's live LLM behavior programmatically.

### 2. NB03 Distractor Tool Misroute

**Test:** Run `03_tool_design.ipynb` with real API key. Check that the Swiss Army agent calls `file_billing_dispute` (or another distractor) instead of `process_refund` for the $600 scenario.
**Expected:** At least one distractor tool appears in `anti_result.tool_calls`; correct agent uses only the 5-tool set.
**Why human:** Tool selection accuracy degradation is probabilistic — Claude may or may not misroute on any given run. The notebook handles both outcomes, but the teaching point requires the failure to be observable at least some of the time.

---

## CCA Rule Compliance

| CCA Rule | Status | Evidence |
|----------|--------|----------|
| Programmatic enforcement beats prompt-based guidance | COMPLIANT | Business rules in `callbacks.py` (code); system prompts provide context only |
| Per-tool callback registry (dict, not shared list) | COMPLIANT | `build_callbacks()` returns `dict[str, CallbackFn]`; `callbacks.get(tool_name)` fires only registered callback |
| Veto guarantee: FinancialSystem untouched on block | COMPLIANT | Two-step veto in `_dispatch_process_refund_with_callback`; `test_veto_guarantee_financial_system_untouched` passes |
| Block-not-bypass: blocked refund returns escalation instruction | COMPLIANT | `{"status":"blocked","action_required":"escalate_to_human"}` returned; Claude calls `escalate_to_human` naturally |
| NB01 checks escalation_queue not financial_system | COMPLIANT | Verified: `escalation_queue.get_queue()` used for comparison; `financial_system` only in `make_services()` setup |
| Anti-patterns live ONLY in anti_patterns/ | COMPLIANT | All three anti-pattern modules in `src/customer_service/anti_patterns/`; no enforcement code in them |
| All tool handlers return JSON strings | COMPLIANT | `process_refund.py`, `callbacks.py` block result all return JSON strings |
| Services injected via ServiceContainer | COMPLIANT | No direct service imports in handlers or callbacks |
| 5 focused tools per agent (correct pattern) | COMPLIANT | TOOLS list in definitions.py has exactly 5; Swiss Army agent confined to anti_patterns/ |

---

## Gaps Summary

None. All must-haves from all three plans are satisfied. 156 tests pass (108 Phase 2 + 34 callbacks + 33 anti-patterns + 13 notebook smoke tests + backward-compat tests). Ruff lint clean across all files.

---

## Test Results Summary

| Suite | Tests | Status |
|-------|-------|--------|
| test_callbacks.py | 34 | All passed |
| test_anti_patterns.py | 33 | All passed |
| test_notebooks.py | 13 | All passed |
| All prior tests (Phase 1 + 2) | 76 | All passed (no regressions) |
| **Total** | **156** | **All passed** |

---

_Verified: 2026-03-26T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
