# CCA Customer Support Resolution Agent: A Deep Tutorial

This tutorial walks through every module in the Customer Support Resolution Agent project, explaining the architecture, the code, and — critically — the **six CCA exam patterns** each piece demonstrates. By the end, you will understand how to build a production-quality Claude-powered agent that enforces business rules programmatically, manages costs, and hands off to humans safely.

The project has two layers:

1. **The Python package** (`src/customer_service/`) — production-quality implementation with only correct patterns.
2. **The anti-patterns** (`src/customer_service/anti_patterns/`) — deliberately wrong implementations that demonstrate what happens when you ignore CCA guidance.

We will cover both, because understanding *why* the wrong way fails is how you internalize the right way before exam day.

---

## Table of Contents

1. [Project Architecture Overview](#1-project-architecture-overview)
2. [Data Models — The Foundation](#2-data-models--the-foundation)
3. [Services — Simulated Business Systems](#3-services--simulated-business-systems)
4. [Seed Data — Customers and Scenarios](#4-seed-data--customers-and-scenarios)
5. [Tool Definitions — Telling Claude What It Can Do](#5-tool-definitions--telling-claude-what-it-can-do)
6. [Tool Handlers — Executing Tool Calls](#6-tool-handlers--executing-tool-calls)
7. [Pattern 1: Escalation — Deterministic Rules vs. LLM Confidence](#7-pattern-1-escalation--deterministic-rules-vs-llm-confidence)
8. [Pattern 2: Compliance — Programmatic Hooks vs. Prompt Instructions](#8-pattern-2-compliance--programmatic-hooks-vs-prompt-instructions)
9. [Pattern 3: Tool Design — 5 Focused Tools vs. 15-Tool Swiss Army Knife](#9-pattern-3-tool-design--5-focused-tools-vs-15-tool-swiss-army-knife)
10. [Pattern 4: Context Management — Structured Summaries vs. Raw Transcripts](#10-pattern-4-context-management--structured-summaries-vs-raw-transcripts)
11. [Pattern 5: Cost Optimization — Prompt Caching vs. Batch API](#11-pattern-5-cost-optimization--prompt-caching-vs-batch-api)
12. [Pattern 6: Handoffs — Structured Records vs. Raw Conversation Dumps](#12-pattern-6-handoffs--structured-records-vs-raw-conversation-dumps)
13. [The Agent Loop — Putting It All Together](#13-the-agent-loop--putting-it-all-together)
14. [The Coordinator — Multi-Topic Queries](#14-the-coordinator--multi-topic-queries)
15. [Notebook Helpers — Cost Tracking and Comparison](#15-notebook-helpers--cost-tracking-and-comparison)
16. [How the Pieces Connect — End-to-End Data Flow](#16-how-the-pieces-connect--end-to-end-data-flow)

---

## 1. Project Architecture Overview

```
src/customer_service/
  models/          Pydantic data models (the nouns)
  services/        5 simulated business services (the verbs)
  data/            Seed customers and test scenarios
  tools/           Claude API tool schemas + per-tool handlers
  agent/           The agentic loop, callbacks, prompts, context, coordinator
  anti_patterns/   6 deliberately wrong implementations
```

The data flows like this:

```
Customer message
  -> agent_loop.py calls client.messages.create()
  -> Claude returns tool_use blocks
  -> callbacks.py validates each tool call against business rules
  -> if approved: handlers.py dispatches to the correct tool handler -> service call
  -> if blocked: error returned as tool_result, agent retries or escalates
  -> loop continues until stop_reason != 'tool_use'
```

Every layer enforces a CCA principle:

| Layer | CCA Principle |
|-------|--------------|
| Models | Type safety via Pydantic — invalid data is rejected at construction |
| Services | Deterministic business logic — no LLM reasoning in policy checks |
| Tools | Exactly 5 focused tools with negative-bound descriptions |
| Callbacks | Programmatic enforcement — business rules in code, not prompts |
| Agent Loop | Stop-reason-controlled loop with forced escalation on blocked refunds |
| Coordinator | Context isolation — subagents see only explicit context strings |

---

## 2. Data Models — The Foundation

**File:** `src/customer_service/models/customer.py`

Every data structure in the system is a Pydantic `BaseModel`. This is not optional — Pydantic provides runtime type validation, which means invalid data fails at construction time rather than silently corrupting downstream logic.

### CustomerTier

```python
class CustomerTier(StrEnum):
    BASIC = "basic"
    REGULAR = "regular"
    PREMIUM = "premium"
    VIP = "vip"
```

`StrEnum` (Python 3.11+) means each variant is both an enum member *and* a string. You can pass `CustomerTier.VIP` anywhere a string is expected, and it serializes cleanly to JSON. The tier drives policy limits — BASIC/REGULAR get $100, PREMIUM gets $500, VIP gets $5,000.

### CustomerProfile

```python
class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    email: str
    tier: CustomerTier
    account_open: bool = True
    flags: list[str] = Field(default_factory=list)
```

The `flags` field is where non-tier escalation triggers live. A customer flagged with `"account_closure"` triggers immediate escalation regardless of refund amount. This is a deliberate design choice: the escalation logic in `callbacks.py` reads flags from the profile, making the trigger *data-driven* rather than hardcoded to specific customer IDs.

### RefundRequest

```python
class RefundRequest(BaseModel):
    customer_id: str
    order_id: str
    amount: float = Field(gt=0)
    reason: str
```

Notice `gt=0` on the amount field. Pydantic enforces this at construction — you cannot create a `RefundRequest(amount=-50)`. This is boundary validation at the model layer, exactly where it belongs.

### PolicyResult

```python
class PolicyResult(BaseModel):
    approved: bool
    limit: float
    requires_review: bool
```

Three booleans from the PolicyEngine: is this within the tier limit? What is the limit? Does it exceed the $500 review threshold? The `requires_review` flag is independent of `approved` — a VIP requesting a $4,000 refund is approved (under the $5,000 limit) but still requires review (above $500).

### EscalationRecord

```python
class EscalationRecord(BaseModel):
    customer_id: str
    customer_tier: str
    issue_type: str
    disputed_amount: float
    escalation_reason: str
    recommended_action: str
    conversation_summary: str
    turns_elapsed: int
```

This is the CCA handoff pattern in data form. When a case escalates to a human agent, they receive exactly these 8 fields — not a raw conversation dump. Every field is purposeful:

- `customer_tier` tells the human agent what service level applies
- `escalation_reason` explains *why* the AI couldn't handle it
- `recommended_action` gives the human a starting point
- `turns_elapsed` signals conversation fatigue

### InteractionLog

```python
class InteractionLog(BaseModel):
    customer_id: str
    action: str
    details: str
    timestamp: str
```

Every tool call gets logged. The `details` field is a JSON string — not a raw dict — because the compliance callback needs to regex-scan it for PII *before* it hits the audit log. If details contained a nested Pydantic model, the redaction would need to understand model structure. A JSON string keeps redaction simple and reliable.

---

## 3. Services — Simulated Business Systems

**Directory:** `src/customer_service/services/`

The project simulates five business services that a real customer support system would integrate with. All are in-memory — students need zero infrastructure setup.

### CustomerDatabase

```python
class CustomerDatabase:
    def __init__(self, customers: dict[str, CustomerProfile]) -> None:
        self._customers = {k: v.model_copy() for k, v in customers.items()}

    def get_customer(self, customer_id: str) -> CustomerProfile | None:
        profile = self._customers.get(customer_id)
        return profile.model_copy() if profile is not None else None
```

Two defensive copies here. The constructor copies each profile so the original `CUSTOMERS` dict is never mutated. The `get_customer` method returns a copy so callers cannot accidentally modify the database. This prevents cross-scenario contamination when running multiple notebook cells.

Why not just use a raw dict? Because `CustomerDatabase` establishes the *contract*: you look up customers by ID, you get a `CustomerProfile` or `None`. This is the interface that tool handlers depend on. If we later replaced this with a real database, only this class changes.

### PolicyEngine

```python
class PolicyEngine:
    _REFUND_LIMITS: dict[CustomerTier, float] = {
        CustomerTier.BASIC: 100.0,
        CustomerTier.REGULAR: 100.0,
        CustomerTier.PREMIUM: 500.0,
        CustomerTier.VIP: 5000.0,
    }
    _REVIEW_THRESHOLD = 500.0

    def check_policy(self, tier: CustomerTier, requested_amount: float) -> PolicyResult:
        limit = self._REFUND_LIMITS[tier]
        approved = requested_amount <= limit
        requires_review = requested_amount > self._REVIEW_THRESHOLD
        return PolicyResult(approved=approved, limit=limit, requires_review=requires_review)
```

This is pure deterministic logic. No LLM reasoning, no probability, no prompt. Given a tier and amount, the result is always the same. This is the CCA escalation principle in its purest form: **business rules belong in code, not in system prompts.**

The `_REVIEW_THRESHOLD` is 500.0 and applies to *all* tiers. A VIP requesting $4,000 is approved (under $5,000 limit) but still flagged for review (above $500). The escalation callback in `callbacks.py` reads `requires_review` and blocks the refund, forcing escalation.

### FinancialSystem

```python
class FinancialSystem:
    def __init__(self) -> None:
        self._processed: list[dict] = []

    def process_refund(self, customer_id, order_id, amount, policy_approved=True) -> dict:
        if policy_approved:
            result = {"status": "approved", ..., "refund_id": f"REF-{len(self._processed) + 1:04d}"}
        else:
            result = {"status": "rejected", ..., "reason": "Policy check failed"}
        self._processed.append(result)
        return result
```

The FinancialSystem *trusts the caller*. It does not re-check policy — it accepts a `policy_approved` boolean and acts accordingly. This is a deliberate design decision: the PolicyEngine is the single source of truth for policy, and FinancialSystem is the single source of truth for financial state. Separation of concerns.

The `_processed` list is the persistent state that tests verify. When we test that a blocked refund doesn't write to FinancialSystem, we check `len(services.financial_system.get_processed()) == 0`. This is the behavior-first testing principle: **test the store, not the API response.**

### EscalationQueue

```python
class EscalationQueue:
    def __init__(self) -> None:
        self._queue: list[EscalationRecord] = []

    def add_escalation(self, record: EscalationRecord) -> None:
        self._queue.append(record)
```

Simple append-only queue. When the `escalate_to_human` tool fires, the structured `EscalationRecord` lands here. Tests verify the queue has the expected entries with the expected fields.

### AuditLog

```python
class AuditLog:
    def __init__(self) -> None:
        self._entries: list[InteractionLog] = []

    def log(self, entry: InteractionLog) -> None:
        self._entries.append(entry)
```

Append-only compliance trail. The compliance callback redacts PII *before* entries reach this log. Tests verify that no credit card numbers appear in `audit_log.get_entries()` — they check the store, not the tool response.

### ServiceContainer

```python
@dataclass(frozen=True)
class ServiceContainer:
    customer_db: CustomerDatabase
    policy_engine: PolicyEngine
    financial_system: FinancialSystem
    escalation_queue: EscalationQueue
    audit_log: AuditLog
```

A frozen dataclass holding all five services. `frozen=True` means you cannot reassign fields after construction — the container is immutable. Every tool handler receives this single object, and accesses exactly the services it needs. Services are never imported directly in tool modules.

This is dependency injection. If you want to swap `CustomerDatabase` for a real database in production, you construct a different `ServiceContainer`. The tool handlers don't change.

---

## 4. Seed Data — Customers and Scenarios

**Directory:** `src/customer_service/data/`

### CUSTOMERS

```python
CUSTOMERS: dict[str, CustomerProfile] = {
    "C001": CustomerProfile(customer_id="C001", name="Alice Johnson",
                            tier=CustomerTier.REGULAR),
    "C002": CustomerProfile(customer_id="C002", name="Bob Chen",
                            tier=CustomerTier.VIP),
    "C003": CustomerProfile(customer_id="C003", name="Carol Martinez",
                            tier=CustomerTier.REGULAR),
    "C004": CustomerProfile(customer_id="C004", name="David Kim",
                            tier=CustomerTier.REGULAR, flags=["account_closure"]),
    "C005": CustomerProfile(customer_id="C005", name="Eva Nowak",
                            tier=CustomerTier.REGULAR),
    "C006": CustomerProfile(customer_id="C006", name="Frank Osei",
                            tier=CustomerTier.VIP, flags=["account_closure"]),
}
```

Six customers, each designed to trigger specific escalation paths:

| ID | Tier | Flags | Purpose |
|----|------|-------|---------|
| C001 | Regular | — | Happy path ($50 refund within $100 limit) |
| C002 | VIP | — | VIP escalation trigger |
| C003 | Regular | — | Amount threshold ($600 > $500 review) |
| C004 | Regular | account_closure | Account closure escalation |
| C005 | Regular | — | Legal keyword escalation (in message) |
| C006 | VIP | account_closure | Multi-trigger (VIP + closure + amount) |

### SCENARIOS

```python
SCENARIOS: dict[str, dict] = {
    "happy_path": {
        "customer_id": "C001",
        "message": "I'd like a $50 refund for order #ORD-001. The item was defective.",
        "expected_tools": ["lookup_customer", "check_policy", "process_refund", "log_interaction"],
        "expected_outcome": "refund_approved",
    },
    "amount_threshold": {
        "customer_id": "C003",
        "message": "I need a $600 refund for my damaged order.",
        "expected_tools": ["lookup_customer", "check_policy", "escalate_to_human"],
        "expected_outcome": "escalated_amount",
    },
    # ... 4 more scenarios
}
```

Each scenario documents its expected tool chain and outcome. This makes scenarios both teaching artifacts (students can trace the expected flow) and test oracles (automated tests can verify the actual flow matches).

Notice the `amount_threshold` scenario: $600 for a REGULAR customer. The $100 tier limit means `approved=False`. The $500 review threshold means `requires_review=True`. Both trigger escalation. The scenario message now includes the customer ID prefix so Claude calls `lookup_customer` immediately without asking.

---

## 5. Tool Definitions — Telling Claude What It Can Do

**File:** `src/customer_service/tools/definitions.py`

This file defines the 5 tools the agent can use. The CCA exam tests whether you know the right number (4-5 per agent) and whether your descriptions include negative bounds.

### Schema Generation from Pydantic

```python
class LookupCustomerInput(BaseModel):
    customer_id: str = Field(description="Customer ID to look up (e.g., 'C001')")

def _make_tool(name: str, description: str, model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema.pop("title", None)  # Claude API rejects top-level 'title'
    return {"name": name, "description": description, "input_schema": schema}
```

Each tool's input schema is a Pydantic model. The `_make_tool` helper converts these to Claude API format. The `schema.pop("title", None)` is important — Pydantic's `model_json_schema()` adds a top-level `"title"` key that the Claude API does not accept.

### Negative-Bound Descriptions

```python
LOOKUP_CUSTOMER_TOOL = _make_tool(
    name="lookup_customer",
    description=(
        "Look up customer profile by ID. Returns customer tier, account status, and flags. "
        "does NOT modify customer data or process any requests."
    ),
    model=LookupCustomerInput,
)
```

Every tool description says what the tool does *and what it does not do*. This is the CCA negative-bound pattern. Without "does NOT modify customer data," Claude might call `lookup_customer` when it wants to update a profile. Without "does NOT check policy eligibility — use check_policy first" on `process_refund`, Claude might skip the policy check.

The `does NOT` phrases use lowercase `does` — this is a deliberate style choice that matches how the CCA exam phrases its tool descriptions.

### The 5-Tool Set

```python
TOOLS: list[dict] = [
    LOOKUP_CUSTOMER_TOOL,    # Read customer data
    CHECK_POLICY_TOOL,       # Evaluate refund eligibility
    PROCESS_REFUND_TOOL,     # Execute approved refund
    ESCALATE_TO_HUMAN_TOOL,  # Transfer to human queue
    LOG_INTERACTION_TOOL,    # Compliance audit trail
]
```

Exactly 5 tools. The CCA exam guidance is 4-5 focused tools per agent. If you need more, use the coordinator-subagent pattern (covered in section 14). The anti-pattern alternative (15+ tools) degrades Claude's tool selection accuracy — more on this in Pattern 3.

---

## 6. Tool Handlers — Executing Tool Calls

**Directory:** `src/customer_service/tools/`

Each tool has its own handler module. All handlers follow the same signature:

```python
def handle_<tool_name>(input_dict: dict, services: ServiceContainer) -> str:
```

Input is a dict (from Claude's `tool_use` block's `input` field). Output is always a JSON string — matching the Claude API's `tool_result` content format.

### lookup_customer.py

```python
def handle_lookup_customer(input_dict: dict, services: ServiceContainer) -> str:
    customer_id = input_dict.get("customer_id", "")
    customer = services.customer_db.get_customer(customer_id)
    if customer is None:
        return json.dumps({"error": f"Customer not found: {customer_id}"})
    return json.dumps(customer.model_dump())
```

Straightforward: look up, return JSON. The `.model_dump()` converts the Pydantic model to a dict, then `json.dumps` serializes it. Errors return structured JSON with an `"error"` key — never raw exceptions.

### check_policy.py

```python
def handle_check_policy(input_dict: dict, services: ServiceContainer) -> str:
    customer = services.customer_db.get_customer(input_dict.get("customer_id", ""))
    if customer is None:
        return json.dumps({"error": f"Customer not found: {customer_id}"})
    result = services.policy_engine.check_policy(customer.tier, input_dict.get("requested_amount", 0.0))
    return json.dumps(result.model_dump())
```

Looks up the customer (to get the tier), then delegates to `PolicyEngine`. The handler does not contain policy logic — it is a thin adapter between Claude's tool call and the service layer.

### process_refund.py — The Two-Step Vetoable Pattern

This is the most architecturally interesting handler. It implements a two-step process:

```python
def propose_refund(input_dict: dict, services: ServiceContainer) -> dict:
    """Step 1: Compute result WITHOUT writing to FinancialSystem."""
    customer = services.customer_db.get_customer(customer_id)
    policy_result = services.policy_engine.check_policy(customer.tier, amount)
    return {
        "status": "proposed",
        "customer_id": customer_id,
        "order_id": order_id,
        "amount": amount,
        "policy_approved": policy_result.approved,
        "requires_review": policy_result.requires_review,
    }

def commit_refund(customer_id, order_id, amount, policy_approved, services) -> str:
    """Step 2: Write to FinancialSystem (only if callback allows)."""
    result = services.financial_system.process_refund(
        customer_id=customer_id, order_id=order_id,
        amount=amount, policy_approved=policy_approved,
    )
    return json.dumps(result)
```

Why two steps? Because the callback needs to inspect the *proposed* result before any financial write occurs. If the callback decides to block (e.g., amount > $500 requires review), the `commit_refund` step never runs. The FinancialSystem is never written to. This is the **CCA veto guarantee**: a blocked refund leaves zero trace in the financial system.

The `handle_process_refund` function is the simple path (no callbacks):

```python
def handle_process_refund(input_dict: dict, services: ServiceContainer) -> str:
    proposed = propose_refund(input_dict, services)
    if "error" in proposed:
        return json.dumps(proposed)
    return commit_refund(...)
```

When callbacks are active, the `dispatch()` function in `handlers.py` uses `_dispatch_process_refund_with_callback()` instead.

### escalate_to_human.py

```python
def handle_escalate_to_human(input_dict: dict, services: ServiceContainer) -> str:
    record = EscalationRecord(
        customer_id=input_dict["customer_id"],
        customer_tier=input_dict["customer_tier"],
        issue_type=input_dict["issue_type"],
        disputed_amount=input_dict["disputed_amount"],
        escalation_reason=input_dict["escalation_reason"],
        recommended_action=input_dict["recommended_action"],
        conversation_summary=input_dict["conversation_summary"],
        turns_elapsed=input_dict["turns_elapsed"],
    )
    services.escalation_queue.add_escalation(record)
    return json.dumps({"status": "escalated", "record": record.model_dump()})
```

Creates a structured `EscalationRecord` and adds it to the queue. The input fields come from Claude — the agent fills in all 8 fields based on conversation context. Compare this to the anti-pattern in section 12, which dumps raw conversation JSON.

### log_interaction.py

```python
def handle_log_interaction(input_dict: dict, services: ServiceContainer) -> str:
    entry = InteractionLog(
        customer_id=input_dict["customer_id"],
        action=input_dict["action"],
        details=input_dict["details"],
        timestamp=datetime.now(UTC).isoformat(),
    )
    services.audit_log.log(entry)
    return json.dumps({"status": "logged", "entry": entry.model_dump()})
```

Logs an interaction for compliance. The `details` field may contain PII — the compliance callback redacts it *before* this handler runs.

### The Dispatch Registry

**File:** `src/customer_service/tools/handlers.py`

```python
DISPATCH: dict[str, Callable[[dict, ServiceContainer], str]] = {
    "lookup_customer": handle_lookup_customer,
    "check_policy": handle_check_policy,
    "process_refund": handle_process_refund,
    "escalate_to_human": handle_escalate_to_human,
    "log_interaction": handle_log_interaction,
}
```

A dict mapping tool names to handler functions. Dict-based dispatch is deterministic and auditable — you can see every tool and its handler in one place.

The `dispatch()` function adds callback support:

```python
def dispatch(tool_name, input_dict, services, context=None, callbacks=None) -> str:
    handler = DISPATCH.get(tool_name)
    if handler is None:
        return json.dumps({"status": "error", "error_type": "unknown_tool", ...})

    # Special case: process_refund with callback uses two-step dispatch
    if tool_name == "process_refund" and callbacks and "process_refund" in callbacks:
        return _dispatch_process_refund_with_callback(input_dict, services, ctx, callbacks["process_refund"])

    # Special case: log_interaction callback runs BEFORE handler (pre-handler redaction)
    if tool_name == "log_interaction" and callbacks and "log_interaction" in callbacks:
        # Redact PII in input_dict["details"] before handler writes to audit log
        ...

    # Standard: run handler, then optional post-handler callback
    result = handler(input_dict, services)
    if callbacks and tool_name in callbacks:
        cb_result = callbacks[tool_name](tool_name, input_dict, result_dict, ctx, services)
        if cb_result.action == "replace_result":
            return cb_result.replacement
    return result
```

Three dispatch patterns:
1. **process_refund**: propose -> callback -> commit/block (two-step vetoable)
2. **log_interaction**: callback -> handler (pre-handler redaction)
3. **Everything else**: handler -> callback (post-handler inspection)

Error handling returns structured JSON with CCA-required fields (`status`, `error_type`, `source`, `retry_eligible`, `fallback_available`, `partial_data`).

---

## 7. Pattern 1: Escalation — Deterministic Rules vs. LLM Confidence

This is the most important CCA pattern. The exam question typically presents two choices: (a) let Claude self-assess its confidence and escalate when uncertain, or (b) use deterministic business rules in code to decide when to escalate. The correct answer is always (b).

### The Anti-Pattern: Confidence-Based Escalation

**File:** `src/customer_service/anti_patterns/confidence_escalation.py`

```python
CONFIDENCE_SYSTEM_PROMPT = """You are a customer support agent.
After each interaction, rate your confidence from 0-100.
If confidence < 70, recommend escalation to human agent.
If confidence >= 70, handle the request directly.
"""
```

The problem: Claude *always* reports high confidence. When you ask it to process a $600 refund for a Regular customer, it confidently processes the refund — even though the amount exceeds the $500 review threshold and should trigger escalation. Claude does not know your business rules unless you enforce them in code.

The `run_confidence_agent()` function runs the agent with this prompt and the standard 5 tools (no callbacks):

```python
def run_confidence_agent(client, user_message, services, tools=None):
    return run_agent_loop(
        client=client,
        system_prompt=CONFIDENCE_SYSTEM_PROMPT,
        user_message=user_message,
        services=services,
        tools=tools or TOOLS,
    )
```

Without callbacks, there is no programmatic check. Claude calls `process_refund` directly, and the FinancialSystem processes it. The $600 refund goes through, violating policy.

### The Correct Pattern: Deterministic Callback Rules

**File:** `src/customer_service/agent/callbacks.py`

The escalation callback implements four deterministic rules:

```python
def escalation_callback(
    tool_name: str, input_dict: dict, result_dict: dict,
    context: dict, services: ServiceContainer,
) -> CallbackResult:
    reasons = []

    # Rule 1: Amount exceeds $500 review threshold
    if context.get("requires_review"):
        reasons.append(f"Amount ${result_dict.get('amount', 0):.2f} exceeds $500 review threshold")

    # Rule 2: VIP customer
    if context.get("is_vip"):
        reasons.append("VIP customer requires specialized handling")

    # Rule 3: Account closure flag
    if context.get("account_closure"):
        reasons.append("Account closure requested — requires supervisor approval")

    # Rule 4: Legal keywords detected
    if context.get("legal_complaint"):
        reasons.append("Legal language detected — immediate escalation required")

    if reasons:
        context["escalation_required"] = True
        blocked_result = json.dumps({
            "status": "blocked",
            "reason": "Escalation required before processing refund",
            "escalation_triggers": reasons,
            "action_required": "escalate_to_human",
        })
        return CallbackResult(action="block", replacement=blocked_result)

    return CallbackResult(action="allow")
```

Each rule checks a context flag that was set by an earlier callback. The `lookup_customer_callback` sets `is_vip`, `account_closure`, and `legal_complaint` flags when it inspects the customer profile and the original user message:

```python
def lookup_customer_callback(
    tool_name: str, input_dict: dict, result_dict: dict,
    context: dict, services: ServiceContainer,
) -> CallbackResult:
    tier = result_dict.get("tier", "")
    if tier == CustomerTier.VIP:
        context["is_vip"] = True

    flags = result_dict.get("flags", [])
    if "account_closure" in flags:
        context["account_closure"] = True

    user_msg = context.get("user_message", "").lower()
    if any(kw in user_msg for kw in LEGAL_KEYWORDS):
        context["legal_complaint"] = True

    return CallbackResult(action="allow")
```

And the `check_policy_callback` sets `requires_review`:

```python
def check_policy_callback(
    tool_name: str, input_dict: dict, result_dict: dict,
    context: dict, services: ServiceContainer,
) -> CallbackResult:
    if result_dict.get("requires_review"):
        context["requires_review"] = True
    return CallbackResult(action="allow")
```

The flow is:
1. Claude calls `lookup_customer` -> `lookup_customer_callback` sets VIP/closure/legal flags
2. Claude calls `check_policy` -> `check_policy_callback` sets `requires_review` flag
3. Claude calls `process_refund` -> `escalation_callback` checks all flags, blocks if any are set
4. Claude receives a `"blocked"` result with `action_required: "escalate_to_human"`
5. The agent loop detects this and forces a `tool_choice` of `escalate_to_human`

No LLM reasoning is involved in the escalation decision. The rules are deterministic and testable.

### The Callback Registry

```python
def build_callbacks(context: dict) -> dict[str, Callable]:
    return {
        "lookup_customer": lambda tn, inp, res, ctx, svc: lookup_customer_callback(tn, inp, res, ctx, svc),
        "check_policy": lambda tn, inp, res, ctx, svc: check_policy_callback(tn, inp, res, ctx, svc),
        "process_refund": lambda tn, inp, res, ctx, svc: escalation_callback(tn, inp, res, ctx, svc),
        "log_interaction": lambda tn, inp, res, ctx, svc: compliance_callback(tn, inp, res, ctx, svc),
    }
```

Per-tool dispatch. Each callback fires only for its registered tool. This prevents cross-tool bugs — a callback meant for `process_refund` cannot accidentally fire on `lookup_customer`.

### CallbackResult

```python
@dataclass
class CallbackResult:
    action: str = "allow"      # "allow", "replace_result", or "block"
    replacement: str | None = None
```

Three possible actions:
- **allow**: tool execution proceeds normally
- **replace_result**: substitute the result returned to Claude (used for PII redaction)
- **block**: veto the tool call entirely (used for escalation)

---

## 8. Pattern 2: Compliance — Programmatic Hooks vs. Prompt Instructions

### The Anti-Pattern: Prompt-Only Compliance

**File:** `src/customer_service/anti_patterns/prompt_compliance.py`

```python
PROMPT_COMPLIANCE_SYSTEM_PROMPT = """You are a customer support agent.
IMPORTANT COMPLIANCE RULES:
- NEVER log raw credit card numbers
- Always redact card numbers to format ****-****-****-NNNN before logging
- If a customer provides a card number, replace all but last 4 digits with asterisks
"""
```

The problem: Claude *usually* follows these instructions. But "usually" is not "always." On a long enough timeline, the LLM will slip and log a raw card number. This is a compliance violation — PCI-DSS does not accept "usually compliant."

### The Correct Pattern: Programmatic PII Redaction

**File:** `src/customer_service/agent/callbacks.py`

```python
CARD_PATTERN = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")

def compliance_callback(
    tool_name: str, input_dict: dict, result_dict: dict,
    context: dict, services: ServiceContainer,
) -> CallbackResult:
    details = result_dict.get("details") or ""
    if not details:
        entry = result_dict.get("entry", {})
        details = entry.get("details", "") if isinstance(entry, dict) else ""

    if CARD_PATTERN.search(details):
        redacted = CARD_PATTERN.sub(
            lambda m: "****-****-****-" + m.group().replace("-", "").replace(" ", "")[-4:],
            details,
        )
        return CallbackResult(
            action="replace_result",
            replacement=json.dumps({"details": redacted}),
        )
    return CallbackResult(action="allow")
```

The regex `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b` matches credit card numbers in any common format (with spaces, dashes, or neither). The replacement preserves only the last 4 digits.

This callback runs *before* the `log_interaction` handler writes to the audit log. The dispatch function replaces `input_dict["details"]` with the redacted version, then calls the handler. The audit log never sees the raw card number.

The key insight: **the system prompt still tells Claude to redact PII** (good for the common case), but the callback guarantees it (catches the edge case). Defense in depth: prompt for guidance, code for enforcement.

### Why Pre-Handler, Not Post-Handler?

Most callbacks run *after* the handler. The compliance callback is special — it runs *before*. Here is why:

If the callback ran after `log_interaction`, the handler would have already written the raw card number to the `AuditLog`. Even if the callback then returned a redacted result to Claude, the damage is done — the audit log contains PII. By running the callback first, the handler receives already-redacted input. The audit log is clean from the start.

This is the behavior-first testing principle applied to architecture: **PII must never reach the audit log — redact before write, not after.**

---

## 9. Pattern 3: Tool Design — 5 Focused Tools vs. 15-Tool Swiss Army Knife

### The Anti-Pattern: Swiss Army Agent

**File:** `src/customer_service/anti_patterns/swiss_army_agent.py`

```python
SWISS_ARMY_TOOLS = [
    # 5 core tools (same as correct pattern)
    LOOKUP_CUSTOMER_TOOL,
    CHECK_POLICY_TOOL,
    PROCESS_REFUND_TOOL,
    ESCALATE_TO_HUMAN_TOOL,
    LOG_INTERACTION_TOOL,
    # 10 distractor tools that overlap with core tools
    _make_tool("get_customer_history", ...),
    _make_tool("file_billing_dispute", ...),   # Overlaps with process_refund
    _make_tool("create_support_ticket", ...),  # Overlaps with escalate_to_human
    _make_tool("send_email_notification", ...),
    _make_tool("update_shipping_status", ...),
    _make_tool("apply_loyalty_discount", ...),
    _make_tool("check_inventory", ...),
    _make_tool("schedule_callback", ...),
    _make_tool("generate_report", ...),
    _make_tool("transfer_to_department", ...),
]
```

15 tools. The canonical misroutes are:
- `file_billing_dispute` overlaps with `process_refund` — Claude may call the wrong one
- `create_support_ticket` overlaps with `escalate_to_human` — ticket creation instead of structured handoff
- `transfer_to_department` overlaps with `escalate_to_human` — unstructured transfer

Research shows tool selection accuracy degrades beyond 4-5 tools. With 15 tools, Claude spends more tokens reasoning about which tool to use, makes more mistakes, and the system becomes harder to test and audit.

### The Correct Pattern: 5 Focused Tools

The correct pattern uses exactly 5 tools (defined in `definitions.py`) with clear, non-overlapping responsibilities and negative-bound descriptions. When you need more capabilities, you use the coordinator-subagent pattern (section 14) to split work across multiple focused agents.

---

## 10. Pattern 4: Context Management — Structured Summaries vs. Raw Transcripts

### The Anti-Pattern: Unbounded Raw Transcript

**File:** `src/customer_service/anti_patterns/raw_transcript.py`

```python
class RawTranscriptContext:
    def __init__(self) -> None:
        self._turns: list[str] = []

    def append(self, role: str, content: str) -> None:
        self._turns.append(f"[{role}] {content}")

    def to_context_string(self) -> str:
        return "\n".join(self._turns)

    def token_estimate(self) -> int:
        return len(self.to_context_string()) // 4
```

Every turn appends to a growing list. Token usage grows O(n) with turn count. After 5-6 turns, the context becomes so large that Claude experiences the "lost in the middle" effect — information buried in the middle of a long context is less likely to be used.

No compaction. No budget. No structure. The entire conversation history is dumped into the system prompt on every API call.

### The Correct Pattern: ContextSummary with Budget Compaction

**File:** `src/customer_service/agent/context_manager.py`

```python
TOKEN_BUDGET = 300  # characters (~75 tokens)

@dataclass
class ContextSummary:
    customer_id: str = ""
    issue_type: str = ""
    tools_called: list[str] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)
    turn_count: int = 0
    token_estimate: int = 0
```

Structured fields instead of a flat string. Each field captures a specific dimension of the conversation state.

The `update()` method adds new information and triggers compaction when the budget is exceeded:

```python
def update(self, tool_name: str = "", decision: str = "", pending: str = "") -> None:
    if tool_name:
        self.tools_called.append(tool_name)
    if decision:
        self.decisions_made.append(decision)
    if pending:
        self.pending_actions.append(pending)
    self.turn_count += 1
    self._update_token_estimate()
    if self.token_estimate > TOKEN_BUDGET:
        self._compact()
```

Compaction keeps only the most recent 2 decisions and truncates `pending_actions`:

```python
def _compact(self) -> None:
    if len(self.decisions_made) > 2:
        self.decisions_made = self.decisions_made[-2:]
    if len(self.pending_actions) > 2:
        self.pending_actions = self.pending_actions[-2:]
    self._update_token_estimate()
```

The `to_system_context()` method renders a structured text block for injection into the system prompt:

```python
def to_system_context(self) -> str:
    lines = [f"Customer: {self.customer_id}"]
    if self.issue_type:
        lines.append(f"Issue: {self.issue_type}")
    if self.tools_called:
        lines.append(f"Tools used: {', '.join(self.tools_called[-5:])}")
    if self.decisions_made:
        lines.append(f"Decisions: {'; '.join(self.decisions_made)}")
    if self.pending_actions:
        lines.append(f"Pending: {'; '.join(self.pending_actions)}")
    lines.append(f"Turns: {self.turn_count}")
    return "\n".join(lines)
```

Note `tools_called[-5:]` — the display shows only the last 5 tools, but the internal list keeps the full history. The token estimate uses `len(text) // 4` as a rough character-to-token heuristic.

The result: context stays within budget regardless of conversation length. Important information (customer ID, pending actions, recent decisions) is always at the top. Compaction fires around turn 7-8, well before the context becomes unwieldy.

---

## 11. Pattern 5: Cost Optimization — Prompt Caching vs. Batch API

### The Anti-Pattern: Batch API for Live Support

**File:** `src/customer_service/anti_patterns/batch_api_live.py`

This file is documentation, not executable code. It explains why Batch API is wrong for live customer support:

1. **Latency**: Batch API has up to 24-hour turnaround. Customers expect real-time responses.
2. **No ZDR eligibility**: Batch requests do not qualify for Zero Data Retention.
3. **Wrong cost lever**: Batch API gives 50% discount on compute, but the real cost driver in customer support is *repeated context* (policy documents, customer data). Prompt caching addresses this directly.

### The Correct Pattern: Prompt Caching with POLICY_DOCUMENT

**File:** `src/customer_service/agent/system_prompts.py`

```python
POLICY_DOCUMENT = """
# Company Refund and Returns Policy
## 1. Customer Tier Definitions
Standard Tier: Basic support with standard refund limits...
...
## 7. Edge Cases and Special Circumstances
...
"""
```

This is a 2,200+ token policy document (4,079 tokens measured). The 2,048-token minimum for caching is important — below it, `cache_creation_input_tokens` stays 0 with no error. We target well above the minimum.

The basic system prompt:

```python
def get_system_prompt() -> str:
    return """You are a customer support agent for an e-commerce company...
    Always look up the customer first using lookup_customer before taking any action...
    """
```

The cached version:

```python
def get_system_prompt_with_caching() -> list[dict]:
    return [
        {
            "type": "text",
            "text": POLICY_DOCUMENT,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": get_system_prompt(),
        },
    ]
```

The `cache_control: {"type": "ephemeral"}` marker tells the Claude API to cache the POLICY_DOCUMENT block. On the first request, you pay 125% of the input cost (cache write). On subsequent requests within the cache TTL, you pay only 10% of the input cost (cache read). For a 4,079-token document repeated across hundreds of customer interactions, this is up to 90% savings.

The agent loop accepts `system_prompt` as either `str` or `list[dict]`:

```python
def run_agent_loop(client, system_prompt, user_message, services, ...):
    # system_prompt can be str or list[dict] — SDK handles both
    response = client.messages.create(
        model=model,
        system=system_prompt,
        messages=messages,
        tools=tool_list,
        ...
    )
```

No conditional logic needed — the Anthropic SDK accepts both formats natively.

---

## 12. Pattern 6: Handoffs — Structured Records vs. Raw Conversation Dumps

### The Anti-Pattern: Raw Conversation Dump

**File:** `src/customer_service/anti_patterns/raw_handoff.py`

```python
def format_raw_handoff(messages: list[dict]) -> str:
    return json.dumps(messages, indent=2)
```

This serializes the entire `messages` list — including tool_use blocks, tool_result blocks, and all the JSON artifacts from every tool call. A typical conversation produces 2,000+ tokens of raw JSON. A human agent receiving this has to dig through tool artifacts to find the 8 pieces of information they actually need.

### The Correct Pattern: Structured EscalationRecord

When escalation is triggered, Claude calls `escalate_to_human` with structured fields:

```python
record = EscalationRecord(
    customer_id="C003",
    customer_tier="regular",
    issue_type="refund",
    disputed_amount=600.0,
    escalation_reason="Amount $600 exceeds $500 review threshold",
    recommended_action="Review refund request with supervisor",
    conversation_summary="Customer requested $600 refund for damaged order. Policy check showed amount exceeds tier limit and review threshold.",
    turns_elapsed=4,
)
```

Compare the size: the raw dump is ~2,000+ tokens. The structured record is ~200 tokens. The human agent gets exactly the 8 fields they need — customer identity, tier, issue, amount, why it escalated, what to do next, what happened so far, and how long the customer has been waiting.

### Forced Escalation via tool_choice

The agent loop implements forced escalation for blocked refunds:

```python
def _has_escalation_required(messages: list[dict]) -> bool:
    """Check if any tool_result contains action_required == 'escalate_to_human'."""
    for msg in messages:
        if msg.get("role") == "user":
            for block in msg.get("content", []):
                if block.get("type") == "tool_result":
                    try:
                        data = json.loads(block.get("content", ""))
                        if data.get("action_required") == "escalate_to_human":
                            return True
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
    return False
```

When `_has_escalation_required` returns True, the loop makes a second API call with `tool_choice={"type": "tool", "name": "escalate_to_human"}`, forcing Claude to call the escalation tool. This ensures that blocked refunds always result in structured handoffs, never abandoned conversations.

---

## 13. The Agent Loop — Putting It All Together

**File:** `src/customer_service/agent/agent_loop.py`

This is the core of the system. It implements the CCA agentic loop pattern.

### AgentResult and UsageSummary

```python
@dataclass
class UsageSummary:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

@dataclass
class AgentResult:
    stop_reason: str
    messages: list[dict]
    tool_calls: list[dict]
    final_text: str
    usage: UsageSummary
```

`UsageSummary` accumulates tokens across all loop iterations. `AgentResult` captures everything the caller needs: why the loop stopped, the full message history, which tools were called, the final text response, and token usage.

### The Loop

```python
def run_agent_loop(
    client, system_prompt, user_message, services,
    tools=None, callbacks=None, model="claude-sonnet-4-6-20250514",
    max_iterations=10,
) -> AgentResult:
    tool_list = tools or TOOLS
    messages = [{"role": "user", "content": user_message}]
    all_tool_calls = []
    usage = UsageSummary()

    # Build callbacks from context if provided
    context = {"user_message": user_message}
    cb = build_callbacks(context) if callbacks is None else callbacks

    for _ in range(max_iterations):
        response = client.messages.create(
            model=model,
            system=system_prompt,
            messages=messages,
            tools=tool_list,
            max_tokens=4096,
        )

        # Accumulate usage
        usage.input_tokens += response.usage.input_tokens
        usage.output_tokens += response.usage.output_tokens
        usage.cache_read_input_tokens += getattr(response.usage, "cache_read_input_tokens", 0) or 0
        usage.cache_creation_input_tokens += getattr(response.usage, "cache_creation_input_tokens", 0) or 0

        # Check stop reason — CCA rule: terminate on anything except tool_use
        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return AgentResult(
                stop_reason=response.stop_reason,
                messages=messages,
                tool_calls=all_tool_calls,
                final_text=final_text,
                usage=usage,
            )

        # Process tool_use blocks
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = dispatch(block.name, block.input, services, context=context, callbacks=cb)
                all_tool_calls.append({"name": block.name, "input": block.input, "result": result})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        # Append assistant response + tool results to messages
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        # HANDOFF-01: Check for forced escalation
        if _has_escalation_required(messages):
            # Force Claude to call escalate_to_human
            response = client.messages.create(
                model=model,
                system=system_prompt,
                messages=messages,
                tools=tool_list,
                tool_choice={"type": "tool", "name": "escalate_to_human"},
                max_tokens=4096,
            )
            # ... process the forced escalation response
```

Key design decisions:

1. **Stop on `stop_reason != "tool_use"`**: Not `== "end_turn"`. This handles `max_tokens` and other stop reasons gracefully.

2. **Tool results are user messages with ONLY `tool_result` blocks**: No text alongside. Mixing text and `tool_result` in the same message is a Claude API pitfall.

3. **Forced escalation**: When a tool result says `action_required: "escalate_to_human"`, the loop makes a second API call with `tool_choice` forcing the escalation tool. This overrides Claude's natural tendency to try alternative approaches.

4. **Max iterations**: 10 iterations prevents infinite loops. In practice, most conversations complete in 3-4 iterations.

5. **Context sharing**: The `context` dict is created once and shared across all tool calls in a session. Callbacks set flags (VIP, closure, legal, review) that accumulate across iterations.

---

## 14. The Coordinator — Multi-Topic Queries

**File:** `src/customer_service/agent/coordinator.py`

When a customer asks about multiple topics ("I want a refund AND a shipping update AND to close my account"), a single 5-tool agent struggles. The coordinator pattern splits the query into subtasks, delegates each to a focused subagent, and synthesizes the results.

### Three-Step Pattern

```python
def run_coordinator(client, user_message, services, model="claude-sonnet-4-6-20250514"):
    # Step 1: DECOMPOSE — Coordinator splits message into subtasks
    response = client.messages.create(
        model=model,
        system=COORDINATOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=1024,
    )
    subtasks = _parse_subtasks(response.content[0].text)

    # Step 2: DELEGATE — Each subagent handles one subtask
    results = {}
    for task in subtasks:
        topic = task.get("topic", "general")
        prompt = SUBAGENT_PROMPTS.get(topic, REFUND_AGENT_PROMPT)
        context_str = (
            f"Customer ID: {task.get('customer_id', 'unknown')}\n"
            f"Tier: {task.get('tier', 'unknown')}\n"
            f"Task: {task.get('task', '')}\n"
            f"Details: {task.get('details', '')}"
        )
        result = run_agent_loop(
            client=client,
            system_prompt=prompt,
            user_message=context_str,
            services=services,
            model=model,
        )
        results[topic] = result.final_text

    # Step 3: SYNTHESIZE — Combine subagent outputs
    synthesis_prompt = "Combine these results into a unified response:\n"
    for topic, text in results.items():
        synthesis_prompt += f"\n## {topic}\n{text}\n"
    synthesis = client.messages.create(...)

    return CoordinatorResult(subagent_results=results, synthesis=synthesis_text)
```

### Context Isolation (CCA Rule)

The critical line is:

```python
context_str = (
    f"Customer ID: {task.get('customer_id', 'unknown')}\n"
    f"Tier: {task.get('tier', 'unknown')}\n"
    f"Task: {task.get('task', '')}\n"
    f"Details: {task.get('details', '')}"
)
result = run_agent_loop(
    client=client,
    system_prompt=prompt,
    user_message=context_str,
    ...
)
```

The subagent receives **only the explicit context string** — never the coordinator's messages list, never the coordinator's system prompt. This is the CCA isolation rule: subagents operate with minimal context to prevent information leakage between subtasks.

### Per-Topic Subagent Prompts

```python
SUBAGENT_PROMPTS = {
    "refund": REFUND_AGENT_PROMPT,
    "shipping": SHIPPING_AGENT_PROMPT,
    "account": ACCOUNT_AGENT_PROMPT,
}
```

Each subagent gets a focused prompt for its domain. The refund agent knows about refund policies. The shipping agent knows about delivery tracking. The account agent knows about account management. None of them know about the others' domains.

---

## 15. Notebook Helpers — Cost Tracking and Comparison

**File:** `notebooks/helpers.py`

### print_usage

```python
_PRICE_INPUT = 3.00    # $ per 1M input tokens
_PRICE_OUTPUT = 15.00  # $ per 1M output tokens
_PRICE_CACHE_READ = 0.30   # 10% of input price
_PRICE_CACHE_WRITE = 3.75  # 125% of input price

def print_usage(response, model="claude-sonnet-4-6"):
    u = response.usage
    inp = u.input_tokens
    out = u.output_tokens
    cr = getattr(u, "cache_read_input_tokens", 0) or 0
    cw = getattr(u, "cache_creation_input_tokens", 0) or 0
    total = inp + out + cr + cw
    cost = (inp * _PRICE_INPUT / 1_000_000
            + out * _PRICE_OUTPUT / 1_000_000
            + cr * _PRICE_CACHE_READ / 1_000_000
            + cw * _PRICE_CACHE_WRITE / 1_000_000)
```

Pricing constants are hardcoded for student visibility — students can see and modify the rates. The function handles cache tokens gracefully with `getattr(..., 0) or 0`, since cache fields may not exist on all response objects.

Token accounting rule: `total = input + output + cache_read + cache_write`. Cache fields are *not* additive on top of `input_tokens` — they are separate components.

### compare_results

```python
def compare_results(anti_result: dict, correct_result: dict):
    # Boolean metrics: FIXED / REGRESSED / same
    # Numeric metrics: percentage change
    # Renders as a tabulate table
```

Used in notebooks to show side-by-side comparisons of anti-pattern vs correct pattern results. For example:

```
Metric             Anti-Pattern    Correct    Delta
-----------------  -------------   --------   -----
escalation_fired   False           True       FIXED
pii_in_audit_log   True            False      FIXED
tool_count         15              5          -66.7%
token_usage        2847            1203       -57.7%
```

---

## 16. How the Pieces Connect — End-to-End Data Flow

Let's trace a complete request through the system. The scenario: Customer C003 (Carol Martinez, Regular tier) requests a $600 refund.

### Step 1: Setup

```python
from customer_service.data.customers import CUSTOMERS
from customer_service.services import *

services = ServiceContainer(
    customer_db=CustomerDatabase(CUSTOMERS),
    policy_engine=PolicyEngine(),
    financial_system=FinancialSystem(),
    escalation_queue=EscalationQueue(),
    audit_log=AuditLog(),
)
```

All 5 services are constructed and injected into a frozen `ServiceContainer`. The `CustomerDatabase` receives the `CUSTOMERS` dict with all 6 pre-built profiles.

### Step 2: Agent Loop Starts

```python
result = run_agent_loop(
    client=anthropic.Anthropic(),
    system_prompt=get_system_prompt(),
    user_message="Customer ID: C003. I need a $600 refund for my damaged order.",
    services=services,
)
```

The context dict is created: `{"user_message": "Customer ID: C003. I need a $600 refund..."}`.
Callbacks are built via `build_callbacks(context)`.

### Step 3: Iteration 1 — Claude calls lookup_customer

Claude sees the customer ID in the message and calls `lookup_customer(customer_id="C003")`.

**Handler**: Returns Carol's profile: `{"customer_id": "C003", "tier": "regular", "flags": []}`.

**Callback** (`lookup_customer_callback`): Checks the profile.
- Tier is `regular`, not VIP -> `is_vip` not set
- No `account_closure` flag -> `account_closure` not set
- Checks user message for legal keywords ("lawsuit", "attorney", etc.) -> none found
- Returns `CallbackResult(action="allow")`

### Step 4: Iteration 1 — Claude calls check_policy

Claude calls `check_policy(customer_id="C003", requested_amount=600.0)`.

**Handler**: Looks up Carol (Regular tier, $100 limit). Returns: `{"approved": false, "limit": 100.0, "requires_review": true}`.

**Callback** (`check_policy_callback`): Sees `requires_review=True` -> sets `context["requires_review"] = True`.

### Step 5: Iteration 2 — Claude calls process_refund

Claude, having seen the policy result, still attempts the refund (or the system forces it through the normal flow).

**Dispatch**: Because `process_refund` has a callback, dispatch uses the two-step vetoable path:

1. `propose_refund()` computes: `{"status": "proposed", "amount": 600.0, "policy_approved": False, "requires_review": True}`
2. `escalation_callback()` checks context:
   - `context["requires_review"]` is `True` -> adds reason "Amount $600.00 exceeds $500 review threshold"
   - Sets `context["escalation_required"] = True`
   - Returns `CallbackResult(action="block", replacement=blocked_json)`
3. `commit_refund()` **never runs**. FinancialSystem is untouched.

Claude receives: `{"status": "blocked", "reason": "Escalation required", "action_required": "escalate_to_human"}`.

### Step 6: Forced Escalation

The agent loop calls `_has_escalation_required(messages)` -> finds `action_required: "escalate_to_human"` -> makes a second API call with `tool_choice={"type": "tool", "name": "escalate_to_human"}`.

Claude is forced to call `escalate_to_human` with structured fields:

```json
{
  "customer_id": "C003",
  "customer_tier": "regular",
  "issue_type": "refund",
  "disputed_amount": 600.0,
  "escalation_reason": "Amount $600 exceeds $500 review threshold",
  "recommended_action": "Review refund request with supervisor",
  "conversation_summary": "Customer requested $600 refund for damaged order...",
  "turns_elapsed": 3
}
```

**Handler**: Creates `EscalationRecord`, adds to `EscalationQueue`.

### Step 7: Loop Terminates

After the forced escalation, Claude's response has `stop_reason="end_turn"`. The loop exits.

### What We Can Verify

```python
# FinancialSystem was NOT written to (veto guarantee)
assert len(services.financial_system.get_processed()) == 0

# EscalationQueue HAS the record
escalations = services.escalation_queue.get_escalations()
assert len(escalations) == 1
assert escalations[0].disputed_amount == 600.0
assert "review threshold" in escalations[0].escalation_reason

# AuditLog has no raw PII (if cards were mentioned)
for entry in services.audit_log.get_entries():
    assert not re.search(r"\b\d{16}\b", entry.details)
```

This is behavior-first testing: test the stores, not the API responses.

---

## Summary: The Six Patterns at a Glance

| # | Pattern | Wrong Way | Right Way | Where in Code |
|---|---------|-----------|-----------|---------------|
| 1 | **Escalation** | LLM self-reports confidence | Deterministic rules in callbacks | `callbacks.py` escalation_callback |
| 2 | **Compliance** | "Always redact PII" in prompt | Regex redaction before audit log write | `callbacks.py` compliance_callback |
| 3 | **Tool Design** | 15 overlapping tools | 5 focused tools with negative bounds | `definitions.py` TOOLS |
| 4 | **Context** | Raw transcript grows O(n) | ContextSummary with budget compaction | `context_manager.py` |
| 5 | **Cost** | Batch API (24h latency) | Prompt caching on POLICY_DOCUMENT | `system_prompts.py` |
| 6 | **Handoffs** | Raw conversation JSON dump | Structured 8-field EscalationRecord | `escalate_to_human.py` |

Each pattern follows the same meta-principle: **programmatic enforcement beats prompt-based guidance.** The system prompt tells Claude what to do. The code guarantees it happens.
