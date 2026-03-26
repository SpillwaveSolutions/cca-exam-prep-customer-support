---
phase: 02-models-services-and-core-loop
verified: 2026-03-26T00:30:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
gaps: []
human_verification: []
---

# Phase 2: Models, Services, and Core Loop — Verification Report

**Phase Goal:** The 5-tool customer support agent can process a customer message through a complete agentic loop using simulated services
**Verified:** 2026-03-26
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Pydantic models validate data and generate JSON Schema via `model_json_schema()` | VERIFIED | `customer.py` defines all 6 models; `RefundRequest` uses `gt=0`; `test_models.py` asserts `"properties"` key in schema for each model; 17 model+data tests pass |
| 2 | Simulated services return different results based on customer tier, refund amount, and account flags | VERIFIED | `PolicyEngine` has `_REFUND_LIMITS` dict (BASIC/REGULAR=$100, PREMIUM=$500, VIP=$5000) and `_REVIEW_THRESHOLD=500.0`; `CustomerDatabase.get_customer()` returns `None` for unknown IDs; `FinancialSystem` uses `policy_approved` flag; 14 service tests pass |
| 3 | Agentic loop processes a customer message, dispatches tool calls, and terminates on `stop_reason != "tool_use"` (not content-type checking) | VERIFIED | `agent_loop.py` line 88: `if response.stop_reason != "tool_use"` — never inspects content block types for control flow; `test_loop_no_content_type_checking` explicitly verifies this invariant and passes |
| 4 | All 5 tool schemas registered and dispatch registry routes tool_use blocks to correct handlers | VERIFIED | `handlers.py` DISPATCH dict maps all 5 tool names; `definitions.py` TOOLS list has exactly 5 entries; all 14 tool tests pass including unknown-tool error return |
| 5 | Seed data includes customers and scenarios that trigger escalation thresholds ($600 refund, VIP customer, legal mention, account closure) | VERIFIED | `customers.py`: C002=VIP, C004 has `["account_closure"]` flag, C006=VIP+closure; `scenarios.py`: `amount_threshold` uses $600 with C003, `legal_keyword` uses lawsuit message for C005, `vip_escalation` targets C002 |

**Score:** 5/5 truths verified

---

## Required Artifacts

### Plan 02-01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/customer_service/models/customer.py` | CustomerTier, CustomerProfile, RefundRequest, EscalationRecord, PolicyResult, InteractionLog | VERIFIED | All 6 classes present with Field annotations; `gt=0` on RefundRequest.amount |
| `src/customer_service/services/container.py` | ServiceContainer frozen dataclass | VERIFIED | `@dataclass(frozen=True)` on ServiceContainer; all 5 service fields typed |
| `src/customer_service/data/customers.py` | CUSTOMERS dict with C001-C006 | VERIFIED | All 6 CustomerProfile instances; C004 has account_closure flag; C002/C006 are VIP |
| `src/customer_service/data/scenarios.py` | SCENARIOS dict with 6 test scenarios | VERIFIED | All 6 scenarios present with customer_id, message, expected_tools, expected_outcome keys |
| `tests/test_models.py` | Model validation tests | VERIFIED | 9 tests including negative-amount rejection and schema generation |
| `tests/test_services.py` | Service behavior + ServiceContainer tests | VERIFIED | 14 tests including tier limits, boundary conditions, frozen mutation |
| `tests/test_data.py` | Seed data structure tests | VERIFIED | 8 tests including count, IDs, tiers, and scenario structure |

### Plan 02-02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/customer_service/tools/definitions.py` | 5 tool schema dicts and TOOLS list | VERIFIED | TOOLS list with 5 entries; all descriptions contain "does NOT"; no title keys in schemas |
| `src/customer_service/tools/handlers.py` | dispatch() function with DISPATCH dict registry | VERIFIED | DISPATCH maps all 5 tool names; dispatch() returns JSON error for unknown tools |
| `src/customer_service/tools/lookup_customer.py` | handle_lookup_customer handler | VERIFIED | Signature `(input_dict: dict, services: ServiceContainer) -> str`; returns JSON |
| `src/customer_service/agent/agent_loop.py` | run_agent_loop(), AgentResult, UsageSummary | VERIFIED | All three defined; loop uses `stop_reason != "tool_use"` control; max_iterations safety limit |
| `src/customer_service/agent/system_prompts.py` | get_system_prompt() | VERIFIED | Returns context-only string; explicitly notes rules enforced in Phase 3 callbacks |
| `tests/test_tools.py` | Tool schema and dispatch tests | VERIFIED | 14 tests including CCA negative-bounds test, no-title test, JSON-string invariant |
| `tests/test_agent_loop.py` | Agent loop unit tests with mocked client | VERIFIED | 10 tests including no-content-type-checking invariant, usage accumulation, max_iterations |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `services/customer_db.py` | `models/customer.py` | CustomerDatabase stores and returns CustomerProfile objects | WIRED | `from customer_service.models.customer import CustomerProfile` in customer_db.py; `get_customer()` returns `CustomerProfile | None` |
| `services/policy_engine.py` | `models/customer.py` | PolicyEngine uses CustomerTier and returns PolicyResult | WIRED | `from customer_service.models.customer import CustomerTier, PolicyResult`; `check_policy()` returns `PolicyResult` |
| `data/customers.py` | `models/customer.py` | Seed data instantiates CustomerProfile objects | WIRED | `from customer_service.models.customer import CustomerProfile, CustomerTier`; all 6 CUSTOMERS entries are CustomerProfile instances |
| `tools/handlers.py` | `tools/lookup_customer.py` | DISPATCH dict maps 'lookup_customer' to handle_lookup_customer | WIRED | `from customer_service.tools.lookup_customer import handle_lookup_customer`; key present in DISPATCH |
| `agent/agent_loop.py` | `tools/handlers.py` | Loop calls dispatch(block.name, block.input, services) | WIRED | `from customer_service.tools.handlers import dispatch`; dispatch() called in tool-use branch at line 110 |
| `agent/agent_loop.py` | `tools/definitions.py` | Loop passes TOOLS list to client.messages.create | WIRED | `from customer_service.tools.definitions import TOOLS`; TOOLS passed at line 74 in messages.create call |
| `tools/definitions.py` | `models/customer.py` | Pydantic input models generate input_schema via model_json_schema() | WIRED | `_make_tool()` calls `model.model_json_schema()`; all 5 tool schemas use this path |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CORE-01 | 02-01 | Pydantic v2 data models (CustomerProfile, RefundRequest, EscalationRecord, PolicyResult, etc.) | SATISFIED | All 6 models in customer.py; all import from customer_service.models |
| CORE-02 | 02-01 | Simulated in-memory services with input-sensitive behavior | SATISFIED | 5 service classes; PolicyEngine uses tier-based lookup table; test_services.py validates behavior per tier |
| CORE-03 | 02-01 | ServiceContainer dataclass for dependency injection across tools | SATISFIED | `@dataclass(frozen=True)` ServiceContainer; all handler signatures take `services: ServiceContainer` |
| CORE-04 | 02-02 | 5 focused tool schemas with JSON Schema via model_json_schema() | SATISFIED | TOOLS list has exactly 5 entries; _make_tool() calls model_json_schema(); test_tool_count passes |
| CORE-05 | 02-02 | Tool dispatch registry routing tool_use blocks to correct handler | SATISFIED | DISPATCH dict in handlers.py; dispatch() returns JSON error for unknown tools; all 5 routes tested |
| CORE-06 | 02-02 | Base agentic loop with stop_reason control (not content-type checking) | SATISFIED | agent_loop.py line 88: `if response.stop_reason != "tool_use"`; test_loop_no_content_type_checking passes |
| STUDENT-02 | 02-01 | Seed data (customers, policies, scenarios) designed to trigger specific escalation rules | SATISFIED | C001=happy path ($50), C002=VIP escalation, C003=$600 amount threshold, C004=account_closure flag, C005=legal keyword, C006=multi-trigger |

**No orphaned requirements.** REQUIREMENTS.md traceability table lists all 7 Phase 2 requirements (CORE-01 through CORE-06, STUDENT-02) as "Complete". All 7 are covered by the two plans above.

---

## CCA Compliance Verification

| CCA Rule | Check | Status | Evidence |
|----------|-------|--------|---------|
| Tool descriptions have negative bounds ("does NOT") | 5/5 tool descriptions | VERIFIED | All 5 descriptions in definitions.py contain "does NOT"; test_tool_descriptions_have_negative_bounds passes |
| Handlers return JSON strings | All 5 handlers | VERIFIED | Every handler returns `json.dumps(...)` or `json.dumps(result.model_dump())`; test_all_handlers_return_json_strings uses `json.loads()` assert on all 5 |
| stop_reason-based loop control, never content-type checking | agent_loop.py | VERIFIED | Line 88 checks `response.stop_reason != "tool_use"` only; test_loop_no_content_type_checking confirms end_turn with tool_use content does NOT dispatch |
| $500 review threshold | policy_engine.py | VERIFIED | `_REVIEW_THRESHOLD = 500.0`; `requires_review = requested_amount > self._REVIEW_THRESHOLD` (strictly greater than); test_policy_review_threshold_below and _above validate boundary |
| Services injected via ServiceContainer | All 5 handlers | VERIFIED | Each handler imports only `ServiceContainer` from container module; services accessed via `services.customer_db`, `services.policy_engine`, etc. — no direct service class imports in handler modules |

---

## Anti-Pattern Scan

Files scanned: all files in `src/customer_service/models/`, `src/customer_service/services/`, `src/customer_service/tools/`, `src/customer_service/agent/`, `src/customer_service/data/`.

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| No files | No TODO/FIXME/placeholder found | — | — |
| No files | No `return null` / `return {}` / `return []` stubs | — | — |
| No files | No console.log-only implementations | — | — |

Zero anti-patterns found. All implementations are substantive.

**One notable observation (not a gap):** `agent_loop.py` lines 105-106 use content-type inspection (`block.type == "tool_use"`) inside the tool-use dispatch branch — this is correct. The CCA rule prohibits using content-type to decide whether to terminate; this code uses it only to filter which blocks within a known-tool-use response to dispatch, which is the required behavior. The control flow decision (continue vs terminate) is exclusively governed by `stop_reason`.

---

## Human Verification Required

None. All success criteria for Phase 2 are programmatically verifiable. Callbacks (PostToolUse enforcement) are Phase 3 — not in scope here.

---

## Gaps Summary

No gaps. All 5 observable truths verified, all 7 artifacts from Plan 01 verified, all 7 artifacts from Plan 02 verified, all 7 key links wired, all 7 requirements satisfied, full CCA compliance confirmed, 79 tests pass, ruff clean.

---

## Commit Evidence

| Commit | Description | Verified |
|--------|-------------|---------|
| `d8db646` | feat(02-01): Pydantic models, seed data, and tests | Present in git log |
| `a48ccd3` | feat(02-01): Five services, frozen ServiceContainer, and service tests | Present in git log |
| `7d2390b` | feat(02-02): Tool schemas, 5 handlers, dispatch registry, and tool tests | Present in git log |
| `1d6fb84` | feat(02-02): Agentic loop, system prompt, package re-exports, and loop tests | Present in git log |
| `1421a49` | fix(02): address review findings — spec drift and mutable seed data | Present in git log — CustomerDatabase now copies profiles on init and get |

---

_Verified: 2026-03-26_
_Verifier: Claude (gsd-verifier)_
