---
phase: 02-models-services-and-core-loop
plan: "02"
subsystem: tools-agent-loop
tags: [tools, handlers, dispatch, agent-loop, tdd, cca-compliance]
dependency_graph:
  requires:
    - customer_service.models (CustomerTier, CustomerProfile, EscalationRecord, PolicyResult, InteractionLog)
    - customer_service.services (CustomerDatabase, PolicyEngine, FinancialSystem, EscalationQueue, AuditLog, ServiceContainer)
  provides:
    - customer_service.tools (TOOLS list, DISPATCH dict, dispatch() function)
    - customer_service.tools.definitions (5 tool schema dicts with Pydantic-generated input_schema)
    - customer_service.tools.handlers (dispatch() routing function)
    - customer_service.tools.lookup_customer (handle_lookup_customer)
    - customer_service.tools.check_policy (handle_check_policy)
    - customer_service.tools.process_refund (handle_process_refund)
    - customer_service.tools.escalate_to_human (handle_escalate_to_human)
    - customer_service.tools.log_interaction (handle_log_interaction)
    - customer_service.agent.agent_loop (run_agent_loop, AgentResult, UsageSummary)
    - customer_service.agent.system_prompts (get_system_prompt)
    - customer_service (top-level re-exports: run_agent_loop, AgentResult, ServiceContainer, all models)
  affects:
    - Phase 03 (callbacks hook into agent loop and tool dispatch)
    - Phase 04 (system_prompts.py extended with prompt caching)
    - Phase 05 (coordinator imports run_agent_loop for subagent orchestration)
tech_stack:
  added:
    - Pydantic model_json_schema() for tool input_schema generation (single source of truth)
    - dataclasses for AgentResult and UsageSummary (lightweight, no Pydantic overhead)
    - collections.abc.Callable for DISPATCH type annotation (ruff UP035 compliance)
    - datetime.UTC for timezone-aware timestamps in log_interaction
  patterns:
    - TDD: RED tests first, GREEN implementation, ruff fix pass
    - Dict-based DISPATCH registry for deterministic tool routing
    - stop_reason-only loop control (CCA: never content-type checking)
    - ServiceContainer DI: handlers receive services parameter, never import services directly
    - Tool descriptions with 'does NOT' negative bounds (CCA tool design rule)
key_files:
  created:
    - src/customer_service/tools/definitions.py
    - src/customer_service/tools/lookup_customer.py
    - src/customer_service/tools/check_policy.py
    - src/customer_service/tools/process_refund.py
    - src/customer_service/tools/escalate_to_human.py
    - src/customer_service/tools/log_interaction.py
    - src/customer_service/tools/handlers.py
    - src/customer_service/agent/agent_loop.py
    - src/customer_service/agent/system_prompts.py
    - tests/test_tools.py
    - tests/test_agent_loop.py
  modified:
    - src/customer_service/tools/__init__.py
    - src/customer_service/agent/__init__.py
    - src/customer_service/__init__.py
    - src/customer_service/__main__.py
decisions:
  - "Tool descriptions use lowercase 'does NOT' (not 'Does NOT') so test's exact string match passes — both are CCA-compliant negative bounds"
  - "process_refund handler reads reason from input_dict but does not pass it to FinancialSystem (FinancialSystem signature is customer_id, order_id, amount, policy_approved)"
  - "Agent loop uses stop_reason != 'tool_use' check (not == 'end_turn') to handle all non-tool stop reasons gracefully (max_tokens, stop_sequence, etc.)"
  - "Tool result messages contain ONLY tool_result blocks — no text alongside (avoids Claude API pitfall)"
  - "Pre-existing __main__.py formatting fixed (ruff format) as part of this plan to keep ruff format --check passing"
metrics:
  duration: "3 minutes 52 seconds"
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 11
  tests_added: 24
---

# Phase 02 Plan 02: Tool Schemas, Handlers, Dispatch, and Agent Loop Summary

**One-liner:** 5 Pydantic-schema tools with 'does NOT' negative bounds, dict-based dispatch routing, and stop_reason-controlled agentic loop with per-iteration usage accumulation.

## What Was Built

### Task 1: Tool schemas, 5 handlers, dispatch registry, and tool tests (commit `7d2390b`)

**Tool Definitions** (`src/customer_service/tools/definitions.py`):
- 5 Pydantic input models: LookupCustomerInput, CheckPolicyInput, ProcessRefundInput, EscalateToHumanInput, LogInteractionInput
- `_make_tool()` helper calls `model.model_json_schema()` and pops the top-level `"title"` key (required by Claude API)
- All 5 descriptions contain `"does NOT"` negative bounds (CCA tool design rule #3)
- TOOLS list = exactly 5 tool dicts passed to `client.messages.create(tools=TOOLS)`

**5 Tool Handlers** (each: `(input_dict: dict, services: ServiceContainer) -> str`):
- `handle_lookup_customer` — dict lookup, returns `customer.model_dump()` JSON or error
- `handle_check_policy` — looks up customer for tier, then calls PolicyEngine, returns `result.model_dump()` JSON
- `handle_process_refund` — looks up customer, checks policy, passes `policy_approved` flag to FinancialSystem
- `handle_escalate_to_human` — creates EscalationRecord, adds to queue, returns `{"status": "escalated", "record": ...}`
- `handle_log_interaction` — creates InteractionLog with UTC timestamp, logs to AuditLog, returns `{"status": "logged", ...}`

**Dispatch Registry** (`src/customer_service/tools/handlers.py`):
- `DISPATCH: dict[str, Callable[[dict, ServiceContainer], str]]` — all 5 tools
- `dispatch(tool_name, input_dict, services)` — returns JSON error for unknown tools (silent failure prevention)

**Tests**: 14 tool tests covering schema structure, CCA compliance, all 5 dispatch routes, unknown tool error, JSON string return invariant.

### Task 2: Agentic loop, system prompt, package re-exports, and loop tests (commit `1d6fb84`)

**Agent Loop** (`src/customer_service/agent/agent_loop.py`):
- `UsageSummary` dataclass: 4 int fields (input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens), all default 0
- `AgentResult` dataclass: stop_reason, messages, tool_calls, final_text, usage (UsageSummary)
- `run_agent_loop()` — CCA-compliant loop:
  - Accumulates usage across all iterations with `or 0` guard for cache fields
  - Terminates on `stop_reason != "tool_use"` (never checks content block types)
  - Dispatches all tool_use blocks per iteration, sends ONLY tool_result blocks back
  - Returns `stop_reason="max_iterations"` when safety limit exceeded

**System Prompt** (`src/customer_service/agent/system_prompts.py`):
- `get_system_prompt()` — context-only prompt (no business rule enforcement)
- CCA rule: enforcement lives in Phase 3 callbacks, not system prompt text

**Package Re-exports** (`src/customer_service/__init__.py`):
- All key items importable: `from customer_service import run_agent_loop, ServiceContainer, AgentResult`

**Tests**: 10 agent loop tests covering end_turn, tool_use_then_end, max_iterations, usage accumulation, max_tokens stop, no-content-type-checking invariant, system prompt structure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tool description case: 'Does NOT' vs 'does NOT'**
- **Found during:** Task 1, GREEN phase
- **Issue:** Tool descriptions used `"Does NOT"` (capital D), but the test checks for `"does NOT"` or `"does not"` (lowercase d). Python string `in` is case-sensitive, so `"does NOT" in "Does NOT text..."` returns False.
- **Fix:** Changed all 5 descriptions from `"Does NOT"` to `"does NOT"` — both are CCA-compliant negative bounds, the test's exact string expectation is what matters
- **Files modified:** `src/customer_service/tools/definitions.py`
- **Commit:** `7d2390b`

**2. [Rule 1 - Lint] ruff UP035: `from typing import Callable` -> `from collections.abc import Callable`**
- **Found during:** Task 1, after GREEN (pre-commit hook)
- **Issue:** ruff UP035 flagged `from typing import Callable` — Python 3.9+ should use `collections.abc`
- **Fix:** Auto-fixed by `ruff check --fix`
- **Files modified:** `src/customer_service/tools/handlers.py`
- **Commit:** `7d2390b`

**3. [Rule 1 - Lint] ruff F841: unused `reason` variable in process_refund.py**
- **Found during:** Task 1, after GREEN (ruff check)
- **Issue:** `reason = input_dict.get("reason", "")` extracted but never used — FinancialSystem doesn't take reason parameter
- **Fix:** Removed the unused assignment
- **Files modified:** `src/customer_service/tools/process_refund.py`
- **Commit:** `7d2390b`

**4. [Rule 1 - Lint] Pre-existing __main__.py formatting**
- **Found during:** Task 2, verification phase
- **Issue:** `ruff format --check src/` failed due to pre-existing formatting in `src/customer_service/__main__.py` (from Phase 01 commit `8de4deb`)
- **Fix:** Applied `ruff format` to fix — required to keep CI-equivalent check passing
- **Files modified:** `src/customer_service/__main__.py`
- **Commit:** `1d6fb84`

## Verification

```
poetry run pytest -x -q         -> 79 passed
poetry run ruff check src/      -> All checks passed
poetry run ruff format --check  -> 26 files already formatted
```

CCA compliance verified:
- All 5 tool descriptions contain "does NOT" (grep confirmed)
- No input_schema has top-level "title" key (schema.pop("title", None) applied)
- Agent loop checks `stop_reason != "tool_use"` — never content block types
- All 5 handlers return JSON strings (json.loads tested for all)
- Services accessed via ServiceContainer parameter — never imported directly in handlers

## Self-Check

### Files Created
- `src/customer_service/tools/definitions.py` — FOUND
- `src/customer_service/tools/lookup_customer.py` — FOUND
- `src/customer_service/tools/check_policy.py` — FOUND
- `src/customer_service/tools/process_refund.py` — FOUND
- `src/customer_service/tools/escalate_to_human.py` — FOUND
- `src/customer_service/tools/log_interaction.py` — FOUND
- `src/customer_service/tools/handlers.py` — FOUND
- `src/customer_service/agent/agent_loop.py` — FOUND
- `src/customer_service/agent/system_prompts.py` — FOUND
- `tests/test_tools.py` — FOUND
- `tests/test_agent_loop.py` — FOUND

### Commits
- `7d2390b` — feat(02-02): Tool schemas, 5 handlers, dispatch registry, and tool tests
- `1d6fb84` — feat(02-02): Agentic loop, system prompt, package re-exports, and loop tests

## Self-Check: PASSED
