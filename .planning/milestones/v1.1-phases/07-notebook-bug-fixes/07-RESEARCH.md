# Phase 7: Notebook Bug Fixes - Research

**Researched:** 2026-04-06
**Domain:** Jupyter notebook debugging, Python package API alignment, Anthropic agentic loop pattern
**Confidence:** HIGH — all findings based on direct source code inspection

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Fix must mirror how working notebooks (NB00-NB03) construct `ServiceContainer` — use seed data from `src/customer_service/data/`
- Do NOT give `CustomerDatabase.__init__` a default empty dict — the explicit data requirement is correct production pattern
- Both NB04 and NB05 have their own `make_services()` helper defined in a code cell — fix both consistently
- The >$500 escalation rule is enforced in `callbacks.py` as a PostToolUse hook — this is the CCA-correct pattern
- Must trace the actual tool call sequence before fixing — don't assume the cause
- The fix must result in `escalation_queue.get_escalations()` returning at least one entry for the $600 scenario

### Claude's Discretion
- How to structure the `make_services()` helper (inline seed data vs import from data module)
- Whether to add defensive output in notebook cells to help students debug if API behavior varies
- How verbose the verification output should be in each cell

### Deferred Ideas (OUT OF SCOPE)
- NB06 and NB07 completion (Phase 8)
- Any new notebook content or restructuring
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NBFIX-01 | NB04 cost optimization notebook runs end-to-end without TypeError on `make_services()` — seed customer data must be passed to `CustomerDatabase()` | Root cause confirmed: `CustomerDatabase()` called with no args; fix is `CustomerDatabase(CUSTOMERS)` with import of `CUSTOMERS` from `customer_service.data.customers` |
| NBFIX-02 | NB05 context management anti-pattern demo runs end-to-end without TypeError on `make_services()` — same root cause as NBFIX-01 | Same fix as NBFIX-01; also discovered secondary bug: NB05 calls `result.final_response` but `AgentResult` only has `final_text` |
| NBFIX-03 | NB01 correct-pattern escalation cell produces non-empty escalation queue for $600 refund scenario — callbacks.py must fire the >$500 rule | Root cause confirmed: NB01's correct-pattern cell does NOT pass `customer_id` in the message (only says "I need a $600 refund for my damaged order"), so the agent never calls `lookup_customer` → `check_policy` → `process_refund`; it simply asks for customer ID and stops. Escalation requires the full tool call sequence. |
</phase_requirements>

---

## Summary

Phase 7 fixes three runtime bugs across NB01, NB04, and NB05. All bugs have been traced to their root causes via direct source inspection.

**NBFIX-01 and NBFIX-02 share one root cause:** both NB04 and NB05 define a local `make_services()` helper that calls `CustomerDatabase()` with no arguments. The `CustomerDatabase.__init__` requires a `customers: dict[str, CustomerProfile]` argument with no default. The fix is to import `CUSTOMERS` from `customer_service.data.customers` and pass it as `CustomerDatabase(CUSTOMERS)`. This mirrors the working pattern in NB01 (cell id 3).

**NBFIX-02 has a secondary bug:** NB05 calls `result1_anti.final_response` on `AgentResult` objects, but `AgentResult` only has a `final_text` attribute (confirmed in `agent_loop.py` line 44). All five anti-pattern turn cells in NB05 use `final_response` — this will raise `AttributeError` after the `make_services()` fix resolves. Both bugs must be fixed together.

**NBFIX-03 root cause:** NB01's correct-pattern cell uses the `amount_threshold` scenario message: `"I need a $600 refund for my damaged order."` This message contains no customer ID. The agent asks for the customer ID and then stops (`end_turn`) without ever calling `lookup_customer` → `check_policy` → `process_refund`. Since `check_policy_callback` never runs, `context["requires_review"]` is never set, so `escalation_callback` never fires. The scenario message must include customer ID (C003) to allow the full tool sequence to execute.

**Primary recommendation:** Fix all three root causes in notebook cells only — no package code changes needed. Verify each fix with the verification cells already present in each notebook.

---

## Standard Stack

### Core (confirmed in place — no new installs needed)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `customer_service.data.customers` | 0.1.0 | Seed customer data dict `CUSTOMERS` | Already imported in NB01; missing from NB04/NB05 |
| `customer_service.agent.agent_loop` | 0.1.0 | `run_agent_loop()` + `AgentResult` | `AgentResult.final_text` is the correct attribute |
| `customer_service.agent.callbacks` | 0.1.0 | `build_callbacks()` — PostToolUse callback registry | Must be passed to `run_agent_loop(callbacks=callbacks)` |

No new packages are required. All dependencies are already installed.

---

## Architecture Patterns

### Working make_services() Pattern (from NB01, cell id 3)

```python
from customer_service.data.customers import CUSTOMERS
from customer_service.services.customer_db import CustomerDatabase
# ... other service imports ...

def make_services() -> ServiceContainer:
    """Create a fresh ServiceContainer with seed customer data."""
    return ServiceContainer(
        customer_db=CustomerDatabase(CUSTOMERS),   # CUSTOMERS dict required
        policy_engine=PolicyEngine(),
        financial_system=FinancialSystem(),
        escalation_queue=EscalationQueue(),
        audit_log=AuditLog(),
    )
```

### Broken make_services() Pattern (current NB04 / NB05)

```python
def make_services():
    return ServiceContainer(
        customer_db=CustomerDatabase(),   # BUG: missing required 'customers' arg
        policy_engine=PolicyEngine(),
        ...
    )
```

### CustomerDatabase constructor signature (confirmed)

```python
# src/customer_service/services/customer_db.py
class CustomerDatabase:
    def __init__(self, customers: dict[str, CustomerProfile]) -> None:
        self._customers = {k: v.model_copy() for k, v in customers.items()}
```

No default value. Calling `CustomerDatabase()` raises `TypeError` immediately.

### AgentResult attributes (confirmed)

```python
# src/customer_service/agent/agent_loop.py  (lines 32-45)
@dataclass
class AgentResult:
    stop_reason: str
    messages: list = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    final_text: str = ""          # CORRECT attribute name
    usage: UsageSummary = field(default_factory=UsageSummary)
```

`AgentResult` has `final_text`, NOT `final_response`. NB05 uses `final_response` — raises `AttributeError`.

### Escalation tool call sequence (correct flow for $600 scenario)

The following tool call sequence must happen for escalation to fire:

1. `lookup_customer(customer_id="C003")` → `lookup_customer_callback` → sets `context["vip"]=False`
2. `check_policy(customer_id="C003", amount=600.0)` → `check_policy_callback` → sets `context["requires_review"]=True`
3. `process_refund(...)` → `escalation_callback` → sees `context["requires_review"]`, returns `action="block"` with `action_required="escalate_to_human"`
4. `_has_escalation_required(tool_results)` returns `True` → forced `tool_choice` call to `escalate_to_human`
5. `escalate_to_human` handler records to `escalation_queue`

**The agent cannot execute step 1 without a customer ID in the message.** The current scenario message `"I need a $600 refund for my damaged order."` contains no customer ID, so Claude asks for one and stops.

### How NB01 Correct-Pattern Cell Is Wired (confirmed good — no code change needed)

```python
# NB01, cell id 9 — correct wiring already in place
correct_result = run_agent_loop(
    client,
    correct_services,
    scenario["message"],    # <-- this is the fix target: must include customer ID
    get_system_prompt(),
    callbacks=callbacks,    # callbacks ARE wired correctly
)
```

The `callbacks` parameter is correctly passed. The `build_callbacks()` factory correctly registers `escalation_callback` for `process_refund`. The agent loop correctly dispatches callbacks via `dispatch()`. The only problem is that `scenario["message"]` does not provide a customer ID.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Seed data for tests | Inline customer dicts in notebook cells | Import `CUSTOMERS` from `customer_service.data.customers` | Single source of truth; consistent with working notebooks |
| ServiceContainer construction | Any new helper function signature | Mirror NB01 `make_services()` verbatim | Pedagogical consistency across all notebooks |

---

## Common Pitfalls

### Pitfall 1: Fixing the wrong NB01 thing
**What goes wrong:** Developer sees `callbacks=callbacks` is present and looks for a bug in `callbacks.py` or `agent_loop.py`.
**Why it happens:** The error symptom ("escalation queue empty") looks like a callback wiring bug.
**How to avoid:** Trace the tool call sequence first. The observed output shows `Tool calls: []` — meaning Claude made zero tool calls. Zero tool calls means callbacks never ran. The agent needed a customer ID to do anything.
**Warning signs:** `Tool calls: []` in the printed output is the key diagnostic. No tool calls = no callback opportunity.

### Pitfall 2: Adding a default to CustomerDatabase
**What goes wrong:** Adding `customers: dict = field(default_factory=dict)` to `CustomerDatabase.__init__`.
**Why it happens:** Seems like the easiest fix.
**How to avoid:** The CONTEXT.md decision explicitly locks this: "Do NOT give `CustomerDatabase.__init__` a default empty dict — the explicit data requirement is correct production pattern." Fix the callers, not the interface.
**Warning signs:** Any suggestion to modify `customer_db.py`.

### Pitfall 3: Missing the secondary NB05 bug
**What goes wrong:** Fixing only `make_services()` in NB05, then re-running and hitting `AttributeError: 'AgentResult' object has no attribute 'final_response'`.
**Why it happens:** The `make_services()` bug causes an earlier crash that masks the `final_response` bug.
**How to avoid:** Fix both bugs in the same pass. All five anti-pattern turn cells (cells 8, 10, 12, 14, 16) use `result1_anti.final_response` — change all to `result1_anti.final_text` (or equivalent).
**Warning signs:** Five occurrences of `.final_response` in NB05.

### Pitfall 4: NB01 scenario message confusion
**What goes wrong:** Changing the `scenarios.py` seed data to add a customer ID to the `amount_threshold` message.
**Why it happens:** `scenario["message"]` is the source, so editing it there seems logical.
**How to avoid:** NB01 is the only notebook that needs the customer ID in the message. Other notebooks/tests may rely on the current scenario message content. Options: (a) pass the customer_id directly in the user message in the notebook cell, or (b) use a different scenario that includes a customer ID. Prefer (a) to avoid cross-notebook side effects.
**Warning signs:** Any modification to `src/customer_service/data/scenarios.py`.

---

## Code Examples

### Fix for NB04 make_services() (NBFIX-01)

```python
# Replace existing make_services() cell in NB04 (cell id 3)
from customer_service.data.customers import CUSTOMERS  # ADD THIS IMPORT
from customer_service.services.audit_log import AuditLog
from customer_service.services.container import ServiceContainer
from customer_service.services.customer_db import CustomerDatabase
from customer_service.services.escalation_queue import EscalationQueue
from customer_service.services.financial_system import FinancialSystem
from customer_service.services.policy_engine import PolicyEngine

def make_services() -> ServiceContainer:
    """Create a fresh ServiceContainer with seed customer data."""
    return ServiceContainer(
        customer_db=CustomerDatabase(CUSTOMERS),  # FIXED: pass CUSTOMERS
        policy_engine=PolicyEngine(),
        financial_system=FinancialSystem(),
        escalation_queue=EscalationQueue(),
        audit_log=AuditLog(),
    )

client = anthropic.Anthropic()
```

Note: NB04's imports cell (cell id 2) does NOT currently import `CUSTOMERS` — it must be added there or in the `make_services` cell. NB01's imports cell (cell id 2) shows the pattern: `from customer_service.data.customers import CUSTOMERS`.

### Fix for NB05 make_services() (NBFIX-02 part 1)

Same pattern as NB04. NB05 cell id 2 already imports the service classes but not `CUSTOMERS`. Add to imports cell or the `make_services()` cell.

### Fix for NB05 final_response → final_text (NBFIX-02 part 2)

```python
# In cells 8, 10, 12, 14, 16 — change:
raw_transcript.append("assistant", result1_anti.final_response or "(no text response)")
# To:
raw_transcript.append("assistant", result1_anti.final_text or "(no text response)")
```

Five cells require this change: all anti-pattern turn cells that call `run_agent_loop` and then append the result to `raw_transcript`.

### Fix for NB01 escalation not firing (NBFIX-03)

The scenario message must include a customer ID so the agent can call `lookup_customer`:

```python
# In NB01, cell id 9 (correct pattern cell) — change scenario message to include C003:
correct_result = run_agent_loop(
    client,
    correct_services,
    f"Customer ID: {scenario['customer_id']}. {scenario['message']}",  # Include customer ID
    get_system_prompt(),
    callbacks=callbacks,
)
```

Alternatively, if the anti-pattern cell (cell id 5) has the same problem (also produces `Tool calls: []`), it should be fixed consistently. Looking at NB01 cell id 5 output, `Tool calls: []` is shown — the anti-pattern ALSO gets no tool calls. The fix for the anti-pattern cell is the same: include customer ID. However, the anti-pattern is *expected* to not escalate (the failure mode is different), so only the correct-pattern cell strictly needs the fix for NBFIX-03 to pass. Both cells should be fixed for pedagogical consistency.

---

## Discovered Bug Summary

| Bug | Location | Root Cause | Fix Complexity |
|-----|----------|------------|----------------|
| NBFIX-01 | NB04 cell 3 `make_services()` | `CustomerDatabase()` called with no args | 1-line change + 1 import |
| NBFIX-02a | NB05 cell 3 `make_services()` | Same as NBFIX-01 | 1-line change + 1 import |
| NBFIX-02b | NB05 cells 8,10,12,14,16 | `AgentResult.final_response` does not exist; should be `final_text` | 5 × 1-line change |
| NBFIX-03 | NB01 cell 9 scenario message | Scenario message has no customer ID; agent cannot call `lookup_customer` | Prepend `f"Customer ID: {scenario['customer_id']}. "` to message |

---

## State of the Art

| Old (Broken) | Current (Fixed) | Impact |
|--------------|-----------------|--------|
| `CustomerDatabase()` — no args | `CustomerDatabase(CUSTOMERS)` — seed data | NBFIX-01, NBFIX-02a unblock |
| `result.final_response` | `result.final_text` | NBFIX-02b unblocks remaining NB05 cells |
| Message without customer ID | Message with customer ID prepended | NBFIX-03 unblocks escalation flow |

---

## Open Questions

1. **Should the NB01 anti-pattern cell also be fixed?**
   - What we know: The anti-pattern cell also shows `Tool calls: []` — Claude never calls any tools because no customer ID is provided.
   - What's unclear: The anti-pattern is *supposed* to fail, but failing before doing any work (no tool calls at all) is a different failure than the intended demonstration (wrong routing after calling tools).
   - Recommendation: Fix the anti-pattern cell too, using the same customer-ID-prepend approach. This makes the demo more instructive: the anti-pattern runs, calls tools, but routes incorrectly; the correct pattern runs, calls tools, and correctly escalates.

2. **NB05 data module import: import cell or make_services cell?**
   - What we know: Both NB04 and NB05 have a separate imports cell (cell id 2) and a `make_services()` cell (cell id 3).
   - What's unclear: Whether to add the `CUSTOMERS` import to cell id 2 (all imports together) or cell id 3 (local to the function).
   - Recommendation: Add to the imports cell (cell id 2) for consistency with NB01's pattern where `CUSTOMERS` is imported with the other `customer_service.data.*` imports.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (Poetry-managed) |
| Config file | `pyproject.toml` (poetry run pytest) |
| Quick run command | `poetry run pytest tests/test_callbacks.py -x` |
| Full suite command | `poetry run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NBFIX-01 | NB04 make_services() runs without TypeError | manual notebook execution | `jupyter nbconvert --to notebook --execute notebooks/04_cost_optimization.ipynb` | ✅ notebook exists |
| NBFIX-02 | NB05 make_services() runs + final_text used | manual notebook execution | `jupyter nbconvert --to notebook --execute notebooks/05_context_management.ipynb` | ✅ notebook exists |
| NBFIX-03 | NB01 escalation queue non-empty for $600 | manual notebook execution | `jupyter nbconvert --to notebook --execute notebooks/01_escalation.ipynb` | ✅ notebook exists |

### Sampling Rate
- **Per task commit:** `poetry run pytest tests/test_callbacks.py -x` — verify callback logic unchanged
- **Per wave merge:** `poetry run pytest` — full suite green
- **Phase gate:** All three notebooks execute without error before `/gsd:verify-work`

### Wave 0 Gaps
None — existing test infrastructure covers callback logic. Notebook execution is validated manually or via `nbconvert --execute`. No new test files needed for Phase 7.

---

## Sources

### Primary (HIGH confidence)
- Direct source inspection: `src/customer_service/services/customer_db.py` — `CustomerDatabase.__init__` signature confirmed, no default
- Direct source inspection: `src/customer_service/agent/agent_loop.py` — `AgentResult.final_text` confirmed (no `final_response`)
- Direct source inspection: `src/customer_service/agent/callbacks.py` — `escalation_callback` confirmed wired, requires `context["requires_review"]` set by `check_policy_callback`
- Direct source inspection: `src/customer_service/data/customers.py` — `CUSTOMERS` dict confirmed with C003 (Carol Martinez, Regular tier)
- Direct source inspection: `src/customer_service/data/scenarios.py` — `amount_threshold` scenario confirmed: customer C003, message has no customer ID
- Direct notebook inspection: `notebooks/01_escalation.ipynb` — cell id 9 output confirms `Tool calls: []`, cell id 10 confirms `Escalation queue length: 0`
- Direct notebook inspection: `notebooks/04_cost_optimization.ipynb` — cell id 3 confirmed broken `make_services()`, TypeError output visible
- Direct notebook inspection: `notebooks/05_context_management.ipynb` — cell id 3 broken, plus 5 cells use `.final_response`
- Direct notebook inspection: `notebooks/00_setup.ipynb` — working environment, no `make_services()` needed
- Direct notebook inspection: `notebooks/01_escalation.ipynb` cell id 3 — canonical working `make_services()` with `CustomerDatabase(CUSTOMERS)`
- Direct source inspection: `src/customer_service/anti_patterns/raw_transcript.py` — `RawTranscriptContext` confirmed has `append()`, `token_estimate()`, `to_context_string()` — all three methods NB05 needs exist

### Secondary (MEDIUM confidence)
- None needed — all claims verified from source

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Root causes: HIGH — verified directly from source code and notebook output
- Fix patterns: HIGH — working pattern confirmed in NB01 cell id 3
- Escalation flow: HIGH — traced completely through `agent_loop.py`, `callbacks.py`, and `handlers.py`
- Secondary NB05 bug: HIGH — `AgentResult` dataclass fields confirmed in `agent_loop.py`

**Research date:** 2026-04-06
**Valid until:** 2026-05-06 (stable codebase — no external dependencies changed)
