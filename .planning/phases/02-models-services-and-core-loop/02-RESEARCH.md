# Phase 2: Models, Services, and Core Loop - Research

**Researched:** 2026-03-25
**Domain:** Anthropic Python SDK agentic loop, Pydantic v2 tool schemas, in-memory simulated services
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Seed data and scenario design:**
- 5-6 targeted customer profiles, each designed to trigger a specific escalation rule:
  - C001: regular tier, $50 refund (happy path)
  - C002: VIP tier, $200 refund (VIP escalation rule)
  - C003: regular tier, $600 refund (amount > $500 rule)
  - C004: closure flag set (account closure rule)
  - C005: mentions lawsuit in message (legal keyword rule)
  - C006: VIP + $600 + closure (multi-trigger edge case)
- Seed data includes pre-built scenarios (customer + message + expected outcome)
- Each scenario: customer_id, message text, expected_tools list, expected_outcome
- Seed data stored as Python dicts in `data/` sub-package

**Service behavior rules:**
- Rule-based lookup tables — fully deterministic, no randomness
- CustomerDatabase: returns different tiers/flags per customer ID
- PolicyEngine: returns different refund limits per tier (basic=$100, premium=$500, VIP=$5000), flags amounts > $500 as requires_review
- FinancialSystem: succeeds/fails based on amount vs policy result, tracks refund state
- EscalationQueue: accepts structured EscalationRecord, stores in memory
- AuditLog: appends all interactions for compliance verification
- ServiceContainer: frozen dataclass holding all 5 services, created once, passed to handlers

**Agent loop termination and error handling:**
- AgentResult dataclass returned from every run: stop_reason, messages, tool_calls, final_text, usage
- Graceful exit with status — never raises exceptions for expected API responses
- Loop terminates on stop_reason == "end_turn" (NEVER content-type checking — CCA rule)
- stop_reason == "tool_use" → dispatch tools, continue loop
- All other stop_reasons (max_tokens, refusal, etc.) → return AgentResult with that stop_reason
- Max 10 iterations safety limit — returns AgentResult with stop_reason="max_iterations"
- Token usage accumulated across all iterations for print_usage reporting

**Tool schema design:**
- Pydantic model_json_schema() for all tool input schemas (single source of truth — CCA rule)
- 5 focused tools (CCA 4-5 tool rule): lookup_customer, check_policy, process_refund, escalate_to_human, log_interaction
- Tool descriptions must include negative bounds (CCA rule)
- Simple dict registry for dispatch: tool name string → handler callable
- Each handler signature: (input_dict: dict, services: ServiceContainer) → str
- All handlers return JSON strings (CCA rule: matching Claude API tool_result format)

**CCA compliance rules (MANDATORY — from source articles):**
- Escalation thresholds: amount > $500, account closure, VIP tier, legal keywords
- Escalation via deterministic business rules, NEVER self-reported confidence
- Tool handlers return JSON strings, never raw objects
- Tool descriptions are precise with negative bounds
- stop_reason-based loop control, never content-type checking
- Services injected via ServiceContainer, never imported directly in tools
- Structured JSON for all data exchange (EscalationRecord, PolicyResult, etc.)

### Claude's Discretion
- Exact Pydantic model field names and types (must include all fields mentioned in scenarios)
- Seed data file organization within data/ sub-package
- System prompt content for the agent (provides context, does NOT enforce rules)
- AgentResult field types beyond the required ones
- Internal service implementation details

### Deferred Ideas (OUT OF SCOPE)
- PostToolUse callbacks — Phase 3
- Prompt caching with cache_control markers — Phase 4
- Structured escalation handoff with tool_choice enforcement — Phase 5
- Coordinator-subagent pattern — Phase 5
- Streamlit UI — TBD
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CORE-01 | Pydantic v2 data models (CustomerProfile, RefundRequest, EscalationRecord, PolicyResult, etc.) | Pydantic v2.12.5 verified; BaseModel, Field, Enum patterns documented with code examples |
| CORE-02 | Simulated in-memory services with input-sensitive behavior (CustomerDB, PolicyEngine, RefundProcessor, EscalationQueue, AuditLog) | Dict-lookup deterministic pattern verified; class-based service design documented |
| CORE-03 | ServiceContainer dataclass for dependency injection across tools | frozen dataclass pattern verified; immutability behavior confirmed |
| CORE-04 | 5 focused tool schemas with JSON Schema via model_json_schema() | Schema generation verified against Anthropic API format; title removal pattern confirmed |
| CORE-05 | Tool dispatch registry routing tool_use blocks to correct handler | Dict-based registry pattern documented; handler signature confirmed |
| CORE-06 | Base agentic loop with stop_reason control | Official Anthropic docs fetched; all stop_reason values documented with handling patterns |
| STUDENT-02 | Seed data (customers, policies, scenarios) designed to trigger specific escalation rules | 6 customer profiles with escalation triggers documented; scenario format specified |
</phase_requirements>

---

## Summary

Phase 2 builds the complete foundation for a 5-tool customer support agent: Pydantic v2 data models, 5 deterministic in-memory services, tool schemas generated from models, a dict-based dispatch registry, and an agentic loop controlled exclusively by `stop_reason`. All patterns have been verified against the installed SDK (anthropic==0.86.0, pydantic==2.12.5) and official Anthropic documentation.

The central design insight is that `model_json_schema()` serves as the single source of truth: the same Pydantic model defines both the runtime data structure used inside the handler and the JSON Schema sent to the Claude API. The top-level `"title"` key must be removed before passing to `input_schema` — the Anthropic API does not use it and it creates noise.

The agentic loop is simple and strict: loop while `stop_reason == "tool_use"`, terminate on any other stop_reason. There are exactly six possible stop_reason values in the current SDK: `end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, `pause_turn`, `refusal`. The loop must handle all six gracefully by returning `AgentResult` without raising exceptions. A max-10-iterations guard adds a final safety net.

**Primary recommendation:** Build models first (Pydantic), then services (pure Python classes with dict lookups), then tool schemas (derived from models), then dispatch registry (dict), then agent loop (stop_reason driven). Each layer depends only on the layer below it, making the dependency graph clean and testable.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.86.0 (installed) | Messages API, tool_use blocks, Usage object | Official Anthropic Python SDK |
| pydantic | 2.12.5 (installed) | Data models, JSON Schema generation, field validation | CCA rule: model_json_schema() single source of truth |
| python-dotenv | >=1.0 (configured) | Load ANTHROPIC_API_KEY from .env | Standard .env pattern |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses (stdlib) | stdlib | ServiceContainer (frozen), AgentResult, UsageSummary | Simpler than Pydantic for internal containers |
| typing (stdlib) | stdlib | Type annotations on all public functions | Python 3.13+ requirement |
| json (stdlib) | stdlib | json.dumps() for handler return values | All handlers return JSON strings |
| types.SimpleNamespace | stdlib | Mock usage objects in tests | Testing AgentResult.usage compatibility |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dataclass for ServiceContainer | Pydantic BaseModel | dataclass(frozen=True) is lighter; services don't need schema generation |
| dataclass for AgentResult | Pydantic BaseModel | AgentResult is internal; dataclass avoids validation overhead |
| dict for dispatch registry | importlib dynamic dispatch | dict is explicit, readable, and testable — preferred for teaching |

**Installation:** All dependencies already installed via `poetry install`.

**Version verification (confirmed live):**
```
anthropic: 0.86.0
pydantic: 2.12.5
```

---

## Architecture Patterns

### Recommended Project Structure

```
src/customer_service/
├── models/
│   ├── __init__.py          # Re-export all models
│   └── customer.py          # CustomerProfile, RefundRequest, EscalationRecord,
│                            # PolicyResult, InteractionLog, CustomerTier
├── services/
│   ├── __init__.py          # Re-export ServiceContainer + all services
│   ├── container.py         # ServiceContainer frozen dataclass
│   ├── customer_db.py       # CustomerDatabase (dict lookup)
│   ├── policy_engine.py     # PolicyEngine (tier-based limits)
│   ├── financial_system.py  # FinancialSystem (refund processing)
│   ├── escalation_queue.py  # EscalationQueue (in-memory list)
│   └── audit_log.py         # AuditLog (in-memory list)
├── tools/
│   ├── __init__.py          # Re-export TOOLS list and dispatch
│   ├── definitions.py       # 5 tool dicts (name, description, input_schema)
│   ├── handlers.py          # dispatch(tool_name, input_dict, services) → str
│   ├── lookup_customer.py   # handle_lookup_customer(input_dict, services) → str
│   ├── check_policy.py      # handle_check_policy(input_dict, services) → str
│   ├── process_refund.py    # handle_process_refund(input_dict, services) → str
│   ├── escalate_to_human.py # handle_escalate_to_human(input_dict, services) → str
│   └── log_interaction.py   # handle_log_interaction(input_dict, services) → str
├── data/
│   ├── __init__.py          # Re-export CUSTOMERS, SCENARIOS
│   ├── customers.py         # 6 CustomerProfile dicts (C001-C006)
│   └── scenarios.py         # Pre-built test scenarios
└── agent/
    ├── __init__.py          # Re-export run_agent_loop, AgentResult
    ├── agent_loop.py        # run_agent_loop() — stop_reason controlled
    └── system_prompts.py    # get_system_prompt() — context only, no rules
```

### Pattern 1: Pydantic Model as Tool Schema Source

**What:** Define Pydantic BaseModel for each tool's input, call `model_json_schema()` to get the Anthropic-compatible JSON Schema. Remove the top-level `"title"` key before passing to `input_schema`.

**When to use:** All 5 tool definitions — single source of truth for both validation and schema.

**Example:**
```python
# Source: verified against Anthropic API format (2026-03-25)
from pydantic import BaseModel, Field
import json

class LookupCustomerInput(BaseModel):
    customer_id: str = Field(
        description="Customer ID to look up; does NOT modify customer data"
    )

def _make_tool(name: str, description: str, model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema.pop("title", None)  # Remove top-level title — Anthropic API ignores it
    return {"name": name, "description": description, "input_schema": schema}

LOOKUP_CUSTOMER_TOOL = _make_tool(
    name="lookup_customer",
    description="Look up customer profile by ID; does NOT modify customer data or process any requests",
    model=LookupCustomerInput,
)
```

### Pattern 2: Frozen ServiceContainer for Dependency Injection

**What:** A `dataclass(frozen=True)` holds references to all 5 services. Created once at startup, passed to every handler call.

**When to use:** All tool handlers receive `services: ServiceContainer` as their second argument.

**Example:**
```python
# Source: dataclasses stdlib, frozen=True prevents accidental mutation
from dataclasses import dataclass

@dataclass(frozen=True)
class ServiceContainer:
    customer_db: CustomerDatabase
    policy_engine: PolicyEngine
    financial_system: FinancialSystem
    escalation_queue: EscalationQueue
    audit_log: AuditLog

# Each handler signature:
def handle_lookup_customer(input_dict: dict, services: ServiceContainer) -> str:
    result = services.customer_db.get_customer(input_dict["customer_id"])
    return json.dumps(result.model_dump() if result else {"error": "Customer not found"})
```

### Pattern 3: Dict-Based Dispatch Registry

**What:** A simple `dict[str, Callable]` maps tool names to handler functions. The dispatcher looks up the handler and calls it with `(input_dict, services)`.

**When to use:** `handlers.py` — the single routing point called by the agent loop.

**Example:**
```python
# Source: verified pattern — dict lookup is O(1), explicit, testable
from typing import Callable

DISPATCH: dict[str, Callable[[dict, ServiceContainer], str]] = {
    "lookup_customer": handle_lookup_customer,
    "check_policy": handle_check_policy,
    "process_refund": handle_process_refund,
    "escalate_to_human": handle_escalate_to_human,
    "log_interaction": handle_log_interaction,
}

def dispatch(tool_name: str, input_dict: dict, services: ServiceContainer) -> str:
    handler = DISPATCH.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    return handler(input_dict, services)
```

### Pattern 4: stop_reason-Controlled Agentic Loop

**What:** Loop continues only while `stop_reason == "tool_use"`. All other stop_reasons terminate the loop and return `AgentResult`. Max 10 iterations guards against infinite loops.

**When to use:** `agent_loop.py` — the core execution loop.

**Example:**
```python
# Source: official Anthropic docs (platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)
import anthropic
from dataclasses import dataclass, field

@dataclass
class UsageSummary:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

@dataclass
class AgentResult:
    stop_reason: str
    messages: list = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    final_text: str = ""
    usage: UsageSummary = field(default_factory=UsageSummary)

def run_agent_loop(
    client: anthropic.Anthropic,
    services: ServiceContainer,
    user_message: str,
    system_prompt: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 4096,
    max_iterations: int = 10,
) -> AgentResult:
    messages = [{"role": "user", "content": user_message}]
    accumulated_usage = UsageSummary()
    all_tool_calls: list[dict] = []

    for _ in range(max_iterations):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Accumulate usage across all iterations
        u = response.usage
        accumulated_usage.input_tokens += u.input_tokens
        accumulated_usage.output_tokens += u.output_tokens
        accumulated_usage.cache_read_input_tokens += u.cache_read_input_tokens or 0
        accumulated_usage.cache_creation_input_tokens += u.cache_creation_input_tokens or 0

        # Append assistant response to conversation
        messages.append({"role": "assistant", "content": response.content})

        # CCA RULE: terminate on stop_reason, NEVER content-type checking
        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
                    break
            return AgentResult(
                stop_reason=response.stop_reason,
                messages=messages,
                tool_calls=all_tool_calls,
                final_text=final_text,
                usage=accumulated_usage,
            )

        # Dispatch all tool_use blocks in this response
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                all_tool_calls.append({"name": block.name, "input": block.input})
                result_content = dispatch(block.name, block.input, services)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                })

        # Send tool results back — tool_result only, no additional text
        messages.append({"role": "user", "content": tool_results})

    # Safety: max iterations exceeded
    return AgentResult(
        stop_reason="max_iterations",
        messages=messages,
        tool_calls=all_tool_calls,
        final_text="",
        usage=accumulated_usage,
    )
```

### Pattern 5: Deterministic In-Memory Service with Dict Lookup

**What:** Services hold their state in `__init__` as dicts. Behavior is determined entirely by input values — no randomness, no external calls. Each service has a focused interface.

**When to use:** All 5 service classes.

**Example:**
```python
# Source: verified pattern for teaching projects (2026-03-25)
from customer_service.models.customer import CustomerProfile, CustomerTier

class CustomerDatabase:
    """Simulated in-memory customer database.

    Returns pre-seeded CustomerProfile objects by customer_id.
    Behavior is fully deterministic — same input always produces same output.
    """

    def __init__(self, customers: dict[str, CustomerProfile]) -> None:
        self._customers = customers  # injected from seed data

    def get_customer(self, customer_id: str) -> CustomerProfile | None:
        """Look up a customer by ID. Returns None if not found."""
        return self._customers.get(customer_id)

class PolicyEngine:
    """Simulated policy engine with tier-based refund limits."""

    # CCA source article limits — do NOT change
    _REFUND_LIMITS: dict[CustomerTier, float] = {
        CustomerTier.BASIC: 100.0,
        CustomerTier.REGULAR: 100.0,
        CustomerTier.PREMIUM: 500.0,
        CustomerTier.VIP: 5000.0,
    }
    # CCA rule: amounts > $500 require_review regardless of tier
    _REVIEW_THRESHOLD = 500.0

    def check_policy(self, tier: CustomerTier, requested_amount: float) -> PolicyResult:
        limit = self._REFUND_LIMITS[tier]
        return PolicyResult(
            approved=requested_amount <= limit,
            limit=limit,
            requires_review=requested_amount > self._REVIEW_THRESHOLD,
        )
```

### Anti-Patterns to Avoid

- **Content-type checking for loop control:** Never check `if any(block.type == "tool_use" for block in response.content)` — always use `response.stop_reason == "tool_use"` (CCA RULE).
- **Raising exceptions for expected API states:** `max_tokens`, `refusal`, `pause_turn` are not errors — return `AgentResult` with the stop_reason.
- **Including text with tool_results:** Do not add text blocks to the user message that contains `tool_result` blocks — this causes empty follow-up responses from Claude.
- **Importing services directly in handlers:** Always receive `services: ServiceContainer` as parameter, never `from customer_service.services.customer_db import CustomerDatabase` inside a handler.
- **Returning non-JSON from handlers:** Every handler must return `json.dumps(...)` — never return a dict, Pydantic model, or None.
- **Adding `title` to Anthropic tool input_schema:** Call `schema.pop("title", None)` on the output of `model_json_schema()` before using as `input_schema`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool input validation | Custom validator in handler | Pydantic Field descriptions in input model | CCA single-source-of-truth rule |
| JSON Schema generation | Manual schema dict | `model.model_json_schema()` | Stays in sync with model; catches typos |
| Usage accumulation struct | Raw dict | `dataclass UsageSummary` | Type-safe; compatible with print_usage |
| Service state isolation | Global variables | Constructor-injected dicts | Testable, notebook-resettable |
| Dispatch routing | `if/elif` chain | Dict registry | O(1), extensible, independently testable |

**Key insight:** Pydantic models are the single definition point — they generate JSON Schema for the API, validate handler inputs at runtime, and serialize outputs to JSON. Using a separate hand-written schema dict is always wrong in this project.

---

## Common Pitfalls

### Pitfall 1: Double-Counting Cache Tokens in Usage Accumulation

**What goes wrong:** `cache_read_input_tokens` and `cache_creation_input_tokens` are NOT additive on top of `input_tokens` per the Anthropic docs. Summing all four fields naively inflates the total.

**Why it happens:** The print_usage helper in `notebooks/helpers.py` uses `total = inp + out + cr + cw` — this is correct per Anthropic's accounting, but only if `inp` already excludes cache tokens (which it does). However, when accumulating across iterations, each field must be accumulated separately.

**How to avoid:** Accumulate each field independently in `UsageSummary`. Never add cache fields to `input_tokens` when building the summary.

**Warning signs:** Total token count is suspiciously high compared to expected conversation length.

### Pitfall 2: Empty Response After Tool Results

**What goes wrong:** Claude returns `stop_reason: "end_turn"` with empty `content` immediately after receiving tool results.

**Why it happens:** Adding text blocks alongside `tool_result` blocks in the user message teaches Claude to expect user text after tool use, causing it to end its turn prematurely.

**How to avoid:** The tool results user message MUST contain ONLY `tool_result` blocks. Do not add any text, commentary, or system notes alongside tool results.

**Warning signs:** Agent loop exits with `stop_reason="end_turn"` and empty `final_text` after only 1-2 iterations.

### Pitfall 3: Pydantic model_json_schema() Title Pollution

**What goes wrong:** Anthropic API receives `input_schema` with a top-level `"title"` key (e.g., `"title": "LookupCustomerInput"`). While the API does not reject it, it appears in debug output and can confuse students comparing schemas.

**Why it happens:** `model_json_schema()` always includes `"title"` at the top level (the class name).

**How to avoid:** Always call `schema.pop("title", None)` after `model_json_schema()` before using as `input_schema`.

**Warning signs:** Tool definitions printed for students show `"title"` keys.

### Pitfall 4: Frozen ServiceContainer Breaks Notebook Re-runs

**What goes wrong:** The `frozen=True` dataclass prevents mutation, but services themselves hold mutable state (e.g., `FinancialSystem` tracks processed refunds, `AuditLog` accumulates entries). After one notebook run, the services have stale state.

**Why it happens:** `frozen=True` prevents reassigning service references but does NOT make the service objects themselves immutable.

**How to avoid:** Create a fresh `ServiceContainer` with fresh service instances at the start of each notebook scenario. Provide a `create_services()` factory function that students call once per scenario.

**Warning signs:** Scenario 2 fails because FinancialSystem thinks refund for C001 was already processed.

### Pitfall 5: stop_reason Type Is a Literal, Not a String Class

**What goes wrong:** Code like `if response.stop_reason == StopReason.end_turn:` fails because the SDK uses `Literal["end_turn", ...]` not an Enum.

**Why it happens:** The Anthropic SDK defines `StopReason = Literal["end_turn", "max_tokens", "stop_sequence", "tool_use", "pause_turn", "refusal"]` — these are plain strings.

**How to avoid:** Always compare with string literals: `if response.stop_reason == "tool_use":`.

**Warning signs:** `AttributeError: type object 'StopReason' has no attribute 'end_turn'`.

---

## Code Examples

Verified patterns from official sources and live SDK inspection:

### Tool Use Block Structure (from API response)

```python
# Source: verified against anthropic.types.ToolUseBlock (SDK 0.86.0)
# Fields: id, name, input, type, caller
# block.type == "tool_use"
# block.id   == "toolu_01abc..."
# block.name == "lookup_customer"
# block.input == {"customer_id": "C001"}  (dict, already parsed from JSON)

for block in response.content:
    if block.type == "tool_use":
        result = dispatch(block.name, block.input, services)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": result,          # Must be a JSON string
        })
```

### Tool Result Message Structure

```python
# Source: official Anthropic docs (platform.claude.com, 2026-03-25)
# tool_result blocks must be the ONLY content in the user message
# Do NOT mix with text blocks

messages.append({
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": "toolu_01abc...",
            "content": '{"customer_id": "C001", "name": "Alice", "tier": "regular"}',
            # "is_error": True  # Only if handler threw an error
        }
    ]
})
```

### Handler Returns JSON String

```python
# Source: CCA-RULES.md — "All tool handlers return JSON strings"
import json
from customer_service.services.container import ServiceContainer

def handle_lookup_customer(input_dict: dict, services: ServiceContainer) -> str:
    """Look up customer by ID. Returns JSON string."""
    customer_id = input_dict["customer_id"]
    customer = services.customer_db.get_customer(customer_id)
    if customer is None:
        return json.dumps({"error": f"Customer {customer_id!r} not found", "status": "not_found"})
    return json.dumps(customer.model_dump())  # Pydantic model → dict → JSON string
```

### Usage Fields (SDK 0.86.0)

```python
# Source: verified via anthropic.types.Usage.model_fields inspection
# Required: input_tokens (int), output_tokens (int)
# Optional: cache_read_input_tokens (int | None), cache_creation_input_tokens (int | None)
# Also present: cache_creation (CacheCreation | None), server_tool_use, service_tier, inference_geo

u = response.usage
input_tokens = u.input_tokens          # int, always present
output_tokens = u.output_tokens        # int, always present
cache_read = u.cache_read_input_tokens or 0    # int | None → int
cache_write = u.cache_creation_input_tokens or 0  # int | None → int
```

### All Stop Reason Values (SDK 0.86.0)

```python
# Source: verified via anthropic.types.StopReason inspection
# Literal["end_turn", "max_tokens", "stop_sequence", "tool_use", "pause_turn", "refusal"]

TERMINAL_STOP_REASONS = {"end_turn", "max_tokens", "stop_sequence", "pause_turn", "refusal"}

# Agent loop exit condition:
if response.stop_reason != "tool_use":
    return AgentResult(stop_reason=response.stop_reason, ...)
```

### Seed Data Format

```python
# Source: CONTEXT.md decisions — scenarios section
# Each scenario designed to trigger a specific CCA escalation rule

SCENARIOS = {
    "happy_path": {
        "customer_id": "C001",
        "message": "I'd like a $50 refund for order #ORD-001. The item was defective.",
        "expected_tools": ["lookup_customer", "check_policy", "process_refund", "log_interaction"],
        "expected_outcome": "refund_approved",
    },
    "vip_escalation": {
        "customer_id": "C002",
        "message": "I need a $200 refund immediately. I'm a VIP customer.",
        "expected_tools": ["lookup_customer", "check_policy", "escalate_to_human"],
        "expected_outcome": "escalated_vip",
    },
    "amount_threshold": {
        "customer_id": "C003",
        "message": "I need a $600 refund for my damaged order.",
        "expected_tools": ["lookup_customer", "check_policy", "escalate_to_human"],
        "expected_outcome": "escalated_amount",
    },
    "account_closure": {
        "customer_id": "C004",
        "message": "I want a refund and to close my account.",
        "expected_tools": ["lookup_customer", "escalate_to_human"],
        "expected_outcome": "escalated_closure",
    },
    "legal_keyword": {
        "customer_id": "C005",
        "message": "This is unacceptable. I'm considering a lawsuit over this matter.",
        "expected_tools": ["lookup_customer", "escalate_to_human"],
        "expected_outcome": "escalated_legal",
    },
    "multi_trigger": {
        "customer_id": "C006",
        "message": "I'm a VIP and I want a $600 refund before I close my account.",
        "expected_tools": ["lookup_customer", "check_policy", "escalate_to_human"],
        "expected_outcome": "escalated_multi",
    },
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tool_choice="auto"` with if/elif dispatch | Dict registry + `dispatch()` | Established by SDK 0.20+ | Cleaner, testable routing |
| Content-type checking for loop control | `stop_reason == "tool_use"` only | CCA rule, always | Correctness guarantee |
| Manual JSON Schema dicts | `model.model_json_schema()` | Pydantic v2 (2023) | Single source of truth |
| Global service singletons | ServiceContainer injection | Standard DI pattern | Notebook-safe, testable |

**Deprecated/outdated:**
- `response.completion` field: Removed in SDK 0.5+. Use `response.content[0].text`.
- `tool_choice={"type": "auto"}` as string: Always pass as dict `{"type": "auto"}`.
- `pydantic.schema()`: Removed in Pydantic v2. Use `model_json_schema()`.

---

## Open Questions

1. **Pydantic `$defs` in model_json_schema() with enum fields**
   - What we know: When a model uses an Enum field (like `CustomerTier`), `model_json_schema()` produces a `$defs` section with the enum definition and a `$ref` in the property. This was verified live.
   - What's unclear: Whether the Anthropic API handles `$defs` with `$ref` in `input_schema` correctly, or whether the schema must be "flattened".
   - Recommendation: Keep `CustomerTier` out of the tool input schemas. Tool inputs use `str` for tier fields; the CustomerProfile model (returned from the handler as JSON) can use the Enum internally.

2. **`model_json_schema()` per-property `title` keys**
   - What we know: Each property in the schema gets a `"title": "Customer Id"` key. The Anthropic API does not reject these but they add noise.
   - What's unclear: Whether students find this confusing when reading tool definitions.
   - Recommendation: Accept the per-property titles as harmless. Only remove the top-level `"title"`. Documenting this behavior in code comments is sufficient.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (installed via Poetry dev deps) |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` testpaths = ["tests"] |
| Quick run command | `poetry run pytest tests/test_models.py tests/test_services.py tests/test_tools.py tests/test_agent_loop.py -x` |
| Full suite command | `poetry run pytest` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORE-01 | CustomerProfile, EscalationRecord, PolicyResult models validate correctly | unit | `poetry run pytest tests/test_models.py -x` | Wave 0 |
| CORE-01 | CustomerTier enum has expected values (basic, regular, premium, vip) | unit | `poetry run pytest tests/test_models.py::test_customer_tier_values -x` | Wave 0 |
| CORE-02 | CustomerDatabase returns correct profile per customer ID | unit | `poetry run pytest tests/test_services.py::test_customer_db_lookup -x` | Wave 0 |
| CORE-02 | PolicyEngine returns correct limit per tier (basic=$100, VIP=$5000) | unit | `poetry run pytest tests/test_services.py::test_policy_limits -x` | Wave 0 |
| CORE-02 | PolicyEngine flags amounts > $500 as requires_review | unit | `poetry run pytest tests/test_services.py::test_policy_review_threshold -x` | Wave 0 |
| CORE-02 | FinancialSystem processes refund within limit; rejects over limit | unit | `poetry run pytest tests/test_services.py::test_financial_system_approve_reject -x` | Wave 0 |
| CORE-02 | EscalationQueue stores escalation records | unit | `poetry run pytest tests/test_services.py::test_escalation_queue -x` | Wave 0 |
| CORE-02 | AuditLog appends interactions | unit | `poetry run pytest tests/test_services.py::test_audit_log -x` | Wave 0 |
| CORE-03 | ServiceContainer is frozen (mutation raises FrozenInstanceError) | unit | `poetry run pytest tests/test_services.py::test_service_container_frozen -x` | Wave 0 |
| CORE-04 | All 5 tool schemas have name, description, input_schema fields | unit | `poetry run pytest tests/test_tools.py::test_tool_schema_structure -x` | Wave 0 |
| CORE-04 | No top-level "title" key in any input_schema | unit | `poetry run pytest tests/test_tools.py::test_no_title_in_input_schema -x` | Wave 0 |
| CORE-04 | All tool descriptions contain "does NOT" negative bound | unit | `poetry run pytest tests/test_tools.py::test_tool_descriptions_have_negative_bounds -x` | Wave 0 |
| CORE-05 | Dispatch routes "lookup_customer" to correct handler | unit | `poetry run pytest tests/test_tools.py::test_dispatch_routing -x` | Wave 0 |
| CORE-05 | Dispatch returns JSON string for unknown tool name | unit | `poetry run pytest tests/test_tools.py::test_dispatch_unknown_tool -x` | Wave 0 |
| CORE-06 | Agent loop returns AgentResult with stop_reason="end_turn" on natural completion | integration | `poetry run pytest tests/test_agent_loop.py::test_loop_end_turn -x` | Wave 0 |
| CORE-06 | Agent loop stops on max_iterations and returns stop_reason="max_iterations" | unit | `poetry run pytest tests/test_agent_loop.py::test_loop_max_iterations -x` | Wave 0 |
| CORE-06 | Agent loop accumulates usage across all iterations | unit | `poetry run pytest tests/test_agent_loop.py::test_loop_usage_accumulation -x` | Wave 0 |
| STUDENT-02 | All 6 seed customers exist with correct tier and escalation flags | unit | `poetry run pytest tests/test_data.py::test_seed_customers -x` | Wave 0 |
| STUDENT-02 | All 6 scenarios have expected_tools and expected_outcome fields | unit | `poetry run pytest tests/test_data.py::test_scenario_structure -x` | Wave 0 |

**Note on integration tests:** `test_loop_end_turn` requires a real API call. Mark with `@pytest.mark.integration` and skip in CI unless `ANTHROPIC_API_KEY` is set. All other tests are unit tests with mocked services and no API calls.

### Sampling Rate

- **Per task commit:** `poetry run pytest tests/test_models.py tests/test_services.py tests/test_tools.py tests/test_data.py -x`
- **Per wave merge:** `poetry run pytest` (full suite, excluding integration tests)
- **Phase gate:** Full suite green (excluding integration) before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_models.py` — covers CORE-01 (Pydantic model validation)
- [ ] `tests/test_services.py` — covers CORE-02, CORE-03 (service behavior + ServiceContainer)
- [ ] `tests/test_tools.py` — covers CORE-04, CORE-05 (schema structure + dispatch)
- [ ] `tests/test_agent_loop.py` — covers CORE-06 (loop control, usage accumulation)
- [ ] `tests/test_data.py` — covers STUDENT-02 (seed data structure)
- [ ] `tests/conftest.py` — shared fixtures: `make_services()`, `mock_anthropic_client()`

No new framework install needed — pytest 8.x already installed.

---

## Sources

### Primary (HIGH confidence)

- Anthropic official docs — [platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — agentic loop, tool_use handling, tool_result format
- Anthropic official docs — [platform.claude.com/docs/en/api/handling-stop-reasons](https://platform.claude.com/docs/en/api/handling-stop-reasons) — all stop_reason values and handling patterns
- Live SDK inspection (anthropic==0.86.0): `ToolUseBlock.model_fields`, `Usage.model_fields`, `StopReason` Literal type, `Message.model_fields`
- Live Pydantic inspection (pydantic==2.12.5): `model_json_schema()` output format, Enum handling, frozen dataclass behavior

### Secondary (MEDIUM confidence)

- WebSearch: Anthropic Python SDK agentic loop patterns 2025 — confirmed stop_reason control pattern, tool_result structure

### Tertiary (LOW confidence)

- None — all critical claims verified via live SDK or official docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified installed versions, live type inspection
- Architecture patterns: HIGH — verified against official Anthropic docs and live SDK
- Tool schema format: HIGH — verified model_json_schema() output against Anthropic API format
- Stop reason values: HIGH — verified via `anthropic.types.StopReason` Literal inspection
- Usage accumulation: HIGH — verified `Usage.model_fields` including cache fields
- Pitfalls: HIGH — empty response pitfall from official docs; others from live testing
- Seed data design: HIGH — 6 customers from CONTEXT.md locked decisions

**Research date:** 2026-03-25
**Valid until:** 2026-06-25 (stable SDK, 90-day window)
