# Architecture Research

**Domain:** Claude API tool-use agent teaching project (Jupyter + Python package dual format)
**Researched:** 2026-03-25
**Confidence:** HIGH (official Anthropic docs + verified SDK patterns)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      Teaching Layer (Notebooks)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ 00-intro │  │01-06 CCA │  │07-coord  │  │ Anti-pattern     │ │
│  │ setup    │  │patterns  │  │subagent  │  │ contrast cells   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
│       │             │             │                   │           │
│       └─────────────┴─────────────┴───────────────────┘           │
│                             imports                                │
├──────────────────────────────────────────────────────────────────┤
│                   Production Package (customer_service/)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐│
│  │  agents/     │  │  tools/      │  │  services/               ││
│  │  - base      │  │  - schemas   │  │  - customer_db (in-mem)  ││
│  │  - customer  │  │  - dispatch  │  │  - policy_engine         ││
│  │  - coord     │  │  - registry  │  │  - refund_processor      ││
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────────┘│
│         │                 │                                        │
│  ┌──────┴─────────────────┴──────────────────────────────────┐    │
│  │                   callbacks/                               │    │
│  │   PostToolUse enforcement (escalation rules)              │    │
│  └───────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────┤
│                        External API Layer                         │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │   Anthropic Python SDK  (anthropic >= 0.42.0)             │    │
│  │   client.messages.create() — synchronous, raw SDK         │    │
│  └───────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `agents/base_agent.py` | Agentic loop, message accumulation, stop_reason dispatch | Python class wrapping `client.messages.create()` in while loop |
| `agents/customer_agent.py` | 5-tool focused customer support agent | Subclass of base with tool registry, PostToolUse hooks wired |
| `agents/coordinator.py` | Routes tickets to specialized subagents when tool count exceeds 4-5 | Orchestrator that spawns billing, returns, policy subagents |
| `tools/schemas.py` | JSON tool schema definitions (input_schema, descriptions) | Pydantic models or plain dicts matching Claude tool format |
| `tools/dispatch.py` | Maps tool_use block `name` → Python function call | `match` statement or registry dict |
| `callbacks/post_tool_use.py` | Programmatic enforcement: escalation, compliance, logging | Callable run after each tool result, before appending to messages |
| `services/customer_db.py` | In-memory customer/account store | Dict-backed Pydantic models; no external DB |
| `services/policy_engine.py` | Refund policies, escalation thresholds | Pure Python logic — amounts, account types, legal keywords |
| `services/refund_processor.py` | Simulated refund execution | Returns structured result dict |
| `models/` | Pydantic v2 request/response models | `BaseModel` subclasses with strict typing |
| `notebooks/` | 00-07 numbered teaching notebooks | Each imports from package; shows wrong then right |

## Recommended Project Structure

```
customer_service/                   # repo root
├── pyproject.toml                  # Poetry config, src layout
├── .env.example                    # ANTHROPIC_API_KEY placeholder
├── .claude/
│   └── CLAUDE.md                   # CCA best-practice meta-example
├── notebooks/
│   ├── 00_setup_and_intro.ipynb    # Environment check, API connection
│   ├── 01_tool_design.ipynb        # 5-tool vs 15-tool anti-pattern
│   ├── 02_agentic_loop.ipynb       # Manual loop vs helpers
│   ├── 03_post_tool_use.ipynb      # Callback enforcement patterns
│   ├── 04_prompt_caching.ipynb     # cache_control demonstration
│   ├── 05_structured_handoffs.ipynb # tool_choice escalation
│   ├── 06_context_management.ipynb # Summaries vs raw transcript
│   └── 07_coordinator_subagent.ipynb # Multi-agent split pattern
├── src/
│   └── customer_service/           # installable package
│       ├── __init__.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base_agent.py       # Agentic loop core
│       │   ├── customer_agent.py   # 5-tool production agent
│       │   ├── anti_patterns.py    # 15-tool Swiss Army agent
│       │   └── coordinator.py      # Orchestrator for subagents
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── schemas.py          # All tool JSON schemas
│       │   ├── dispatch.py         # name → function routing
│       │   └── implementations.py  # Actual tool functions
│       ├── callbacks/
│       │   ├── __init__.py
│       │   └── post_tool_use.py    # PostToolUse enforcement hooks
│       ├── services/
│       │   ├── __init__.py
│       │   ├── customer_db.py      # In-memory customer store
│       │   ├── policy_engine.py    # Business rules
│       │   └── refund_processor.py # Simulated refund execution
│       ├── models/
│       │   ├── __init__.py
│       │   ├── customer.py         # Customer/account Pydantic models
│       │   ├── ticket.py           # Support ticket models
│       │   └── escalation.py       # Escalation handoff schema
│       └── config.py               # API key, model name, constants
└── tests/
    ├── test_tools.py
    ├── test_callbacks.py
    └── test_agents.py
```

### Structure Rationale

- **`src/` layout:** Poetry installs the package in editable mode (`poetry install`), making `from customer_service.agents import CustomerAgent` work in all notebooks without `sys.path` hacking.
- **`notebooks/` at repo root:** Notebooks are teaching artifacts, not part of the installable package. They import from `customer_service` as a consumer, same as students would.
- **`agents/anti_patterns.py`:** Anti-pattern agents live in the package (not just notebooks) so notebooks can `import` them cleanly for side-by-side demonstration. This keeps notebook cells readable.
- **`callbacks/` as top-level subpackage:** PostToolUse logic is orthogonal to agents — callbacks can be mixed in or swapped. Separating them makes the pattern legible.
- **`services/` fully in-memory:** Zero infrastructure requirement. Students run `poetry install` + set `ANTHROPIC_API_KEY`, nothing else.

## Architectural Patterns

### Pattern 1: Manual Agentic Loop (Raw SDK)

**What:** Explicit `while True` loop calling `client.messages.create()`, appending assistant response to messages, dispatching tool_use blocks, feeding tool_results back as user messages.

**When to use:** This project uses this pattern deliberately — teaching the fundamentals. The loop is visible, auditable, and maps 1:1 to what the CCA exam tests.

**Trade-offs:** More code than `tool_runner` beta helper, but every step is explicit and inspectable. Students see exactly what the API expects.

**Example:**
```python
def run(self, user_message: str) -> str:
    self.messages.append({"role": "user", "content": user_message})

    while True:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_blocks,   # list with cache_control
            tools=self.tool_schemas,     # list with cache_control on last item
            messages=self.messages,
        )
        self.messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return self._extract_text(response)

        if response.stop_reason == "tool_use":
            tool_results = self._dispatch_tools(response.content)
            # PostToolUse callbacks run here, before appending
            tool_results = self._run_post_tool_use(tool_results, response.content)
            self.messages.append({"role": "user", "content": tool_results})
```

### Pattern 2: PostToolUse Callback Enforcement

**What:** After each tool executes and produces a result, a callback function inspects the tool name, input, and result. It can mutate the result, inject a forced escalation, or raise an exception to halt the loop. This is programmatic enforcement — not prompt instructions.

**When to use:** Any compliance rule that must not be bypassed by clever prompting: refund threshold ($500), account closure confirmation, VIP routing, legal keyword detection.

**Trade-offs:** Adds indirection — debugging requires tracing through callback chain. But it guarantees enforcement regardless of what Claude "decides" in the reasoning.

**Example:**
```python
# callbacks/post_tool_use.py
def escalation_enforcement(
    tool_name: str,
    tool_input: dict,
    tool_result: dict,
) -> dict:
    """Programmatic rule: amounts > $500 must escalate. Not a prompt instruction."""
    if tool_name == "process_refund":
        amount = tool_input.get("amount", 0)
        if amount > 500:
            return {
                "forced_escalation": True,
                "reason": f"Refund amount ${amount} exceeds $500 threshold",
                "original_result": tool_result,
            }
    return tool_result
```

### Pattern 3: Tool Schema Design — Focused vs Swiss Army

**What:** The 5-tool focused agent gives Claude exactly what it needs for customer support and nothing else. The 15-tool anti-pattern overwhelms the model with overlapping, ambiguously-named tools, causing selection errors.

**When to use:** Focused tools whenever possible. Split to coordinator-subagent when a domain genuinely requires more than 4-5 tools.

**Trade-offs:** Fewer tools = clearer selection = fewer wrong calls. More tools = more capability but exponential selection confusion risk.

**Focused 5-tool set:**
```python
CUSTOMER_SUPPORT_TOOLS = [
    "lookup_customer",    # read customer record
    "check_policy",       # retrieve relevant policy text
    "process_refund",     # execute refund (triggers PostToolUse checks)
    "escalate_to_human",  # structured handoff
    "log_interaction",    # audit trail
]
```

**Cache_control placement:** Mark the last tool definition with `"cache_control": {"type": "ephemeral"}` to cache all tool schemas across conversation turns.

### Pattern 4: Prompt Caching for Static Context

**What:** The policy document (static, large) goes into the system prompt as a content block with `cache_control: ephemeral`. Tool schemas also receive `cache_control` on the last item. Per-turn costs drop to 10% of input token price on cache hits.

**When to use:** Any content that does not change turn-to-turn: system instructions, policy docs, tool definitions.

**Trade-offs:** Cache writes cost 1.25x normal input price. Cache reads cost 0.1x. Break-even at roughly the second identical turn. Minimum cacheable size is 1,024 tokens (Sonnet) or 4,096 tokens (Opus/Haiku).

**Example structure:**
```python
system_blocks = [
    {
        "type": "text",
        "text": AGENT_ROLE_INSTRUCTIONS,   # ~200 tokens, not worth caching alone
    },
    {
        "type": "text",
        "text": POLICY_DOCUMENT,           # ~2000 tokens, cache this
        "cache_control": {"type": "ephemeral"},
    },
]
# tool_schemas[-1]["cache_control"] = {"type": "ephemeral"}
```

### Pattern 5: Structured Escalation Handoff via tool_choice

**What:** When compliance rules require escalation, the agent is forced to call `escalate_to_human` by setting `tool_choice={"type": "tool", "name": "escalate_to_human"}` on the next API call. Claude cannot talk its way out of escalation — it must produce a structured JSON handoff.

**When to use:** The PostToolUse callback detects an escalation trigger and sets a flag. The agentic loop checks the flag before the next API call and applies `tool_choice`.

**Trade-offs:** `tool_choice` with a specific tool name forces exactly one tool call. The model still generates the arguments, so descriptions must specify exactly what fields are required for the handoff.

### Pattern 6: Coordinator-Subagent Split

**What:** When a workflow legitimately requires more than 4-5 tools, a coordinator agent receives the ticket and routes to specialized subagents (billing agent, returns agent, policy lookup agent). Each subagent has its own 4-5 tool set. The coordinator uses a `route_to_subagent` tool to hand off.

**When to use:** Tool count exceeds 4-5 per agent. Tasks are separable (billing vs. returns have distinct data needs). This project demonstrates the pattern in notebook 07 and `agents/coordinator.py`.

**Trade-offs:** More API calls, more tokens. Justified when tool selection accuracy degrades with a large tool set or when concerns are cleanly separable.

**Example coordinator flow:**
```
User ticket: "My order 12345 didn't arrive and I was charged twice"
    ↓
Coordinator Agent (tools: route_to_subagent, summarize_ticket)
    ↓ route_to_subagent("billing", ticket_summary)
Billing Subagent (tools: lookup_charge, process_refund, escalate_to_human, log_interaction)
    ↓
Coordinator receives result, routes to:
Returns Subagent (tools: lookup_order, check_carrier, initiate_return, log_interaction)
    ↓
Coordinator synthesizes final response
```

## Data Flow

### Single-Agent Request Flow

```
Student/User Message
    ↓
CustomerAgent.run(message)
    ↓
messages.append({role: "user", content: message})
    ↓
client.messages.create(model, system_blocks, tools, messages)
    ↓ (stop_reason == "tool_use")
_dispatch_tools(response.content)
    ↓ for each tool_use block:
        tool_dispatch[block.name](block.input)  →  SimulatedService
            ↓
        PostToolUse callback(tool_name, input, result)
            ↓ (may force escalation or mutate result)
        tool_results.append({type: tool_result, tool_use_id, content})
    ↓
messages.append({role: "user", content: tool_results})
    ↓ (loop back to messages.create)
    ↓ (stop_reason == "end_turn")
return final text response
```

### Coordinator-Subagent Data Flow

```
Coordinator receives ticket
    ↓
Coordinator calls route_to_subagent tool
    ↓
Dispatcher instantiates SubAgent(tools=specialized_set)
    ↓
SubAgent runs its own agentic loop
    ↓
SubAgent returns structured result (Pydantic model serialized to JSON)
    ↓
Coordinator receives result as tool_result content
    ↓
Coordinator synthesizes and returns to user
```

### State Management

```
AgentSession
    messages: list[dict]          # accumulates user/assistant/tool_result turns
    ├── role: "user"              # initial message + all tool_results
    ├── role: "assistant"         # all Claude responses (may contain tool_use blocks)
    └── (no mutable state elsewhere — all state is in messages list)

SimulatedServices (in-memory, singleton per session)
    CustomerDB: dict[str, Customer]
    PolicyEngine: immutable rules
    RefundProcessor: stateless execution
```

### Key Data Flows

1. **Tool schema → API:** Tool JSON schemas (defined once in `tools/schemas.py`) are passed as the `tools` parameter on every `messages.create()` call. Cache_control on the last schema causes Claude to cache the entire tool list after the first call.

2. **tool_use block → dispatch → service → tool_result:** Claude returns a `tool_use` content block with `id`, `name`, `input`. The dispatch layer looks up `name` in a registry, calls the corresponding service function with `input` kwargs, and wraps the return value as `{"type": "tool_result", "tool_use_id": id, "content": json.dumps(result)}`.

3. **PostToolUse callback chain:** After dispatch and before appending tool_results to messages, each result passes through registered callbacks. Callbacks are pure functions: `(tool_name, tool_input, tool_result) -> tool_result`. They can replace the result dict (e.g., inject escalation flag) or raise `EscalationRequired` to break the loop and force escalation on the next call.

4. **Notebook → package import:** Notebooks do `from customer_service.agents import CustomerAgent`. Poetry editable install ensures this resolves to `src/customer_service/`. No sys.path manipulation needed. Anti-pattern cells import `AntiPatternAgent` from the same package for side-by-side comparison.

## Scaling Considerations

This is a teaching project — scaling is not a goal. These notes frame the patterns taught, not production deployment concerns.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single student, in-memory | Current architecture — in-memory services, synchronous, no persistence |
| Classroom demo (shared API key) | Rate limiting becomes relevant; add sleep/backoff to base agent loop |
| Production customer support | Replace SimulatedServices with real DB; add async (out of scope for this project) |

### Scaling Priorities (Teaching Implications)

1. **First constraint in this project:** Anthropic API rate limits — add retry logic with exponential backoff in `base_agent.py`; teach this as production-readiness concern.
2. **Second constraint:** Context window filling up on long conversations — notebook 06 teaches context management (structured summaries) exactly for this reason.

## Anti-Patterns

### Anti-Pattern 1: 15-Tool Swiss Army Agent

**What people do:** Define every conceivable action as a separate tool — `get_customer_name`, `get_customer_email`, `get_customer_tier`, `get_order_by_id`, `get_order_by_date`, `cancel_order`, `refund_order_full`, `refund_order_partial`, etc.

**Why it's wrong:** Claude's tool selection accuracy degrades significantly with large overlapping tool sets. Ambiguous names cause wrong tool selection. Token cost rises because all 15 schemas are sent every turn. This is the CCA exam trap — it looks thorough but performs worse.

**Do this instead:** 5 focused tools where `lookup_customer` returns a full customer record including orders. One tool, one lookup, complete information.

### Anti-Pattern 2: Compliance via Prompt Instructions

**What people do:** Add to the system prompt: "Never process refunds over $500 without escalating. Always escalate VIP customers."

**Why it's wrong:** Prompt instructions are advisory. A sufficiently creative user input or edge case reasoning path can bypass them. Claude follows instructions probabilistically, not deterministically.

**Do this instead:** PostToolUse callback that inspects `process_refund` tool results and forces escalation when `amount > 500`. The application layer enforces compliance, not the model.

### Anti-Pattern 3: Raw Transcript as Context Summary

**What people do:** Append every message turn to the context window indefinitely.

**Why it's wrong:** Tokens accumulate, cost rises, older relevant information gets buried in the middle of the context where attention is weakest, and eventually the window fills.

**Do this instead:** After N turns, call Claude with `tool_choice={"type": "tool", "name": "summarize_context"}` to produce a structured summary (open issues, actions taken, customer info) and replace the message history with the summary. Notebook 06 demonstrates both approaches with token counts.

### Anti-Pattern 4: Subagent Without Structured Output Contract

**What people do:** Coordinator calls a subagent and receives free-text response, then tries to parse it or passes it directly back to user.

**Why it's wrong:** Free text from subagents is unparseable, untestable, and forces the coordinator to re-interpret the result. Errors compound.

**Do this instead:** Define a Pydantic model for each subagent's return type (e.g., `BillingResult`, `ReturnsResult`). Subagent always calls a final `finalize_result` tool with `tool_choice` enforcement, producing JSON that matches the schema. Coordinator deserializes with Pydantic.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Anthropic API | `client.messages.create()` synchronous | Uses `anthropic` Python SDK; no streaming in this project |
| ANTHROPIC_API_KEY | Environment variable via `python-dotenv` | Students set this once; all notebooks/scripts pick it up |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Notebook → Package | Python import (`from customer_service.x import Y`) | Editable install via Poetry; no path hacking |
| Agent → Tools | Function call via dispatch dict | `tool_dispatch: dict[str, Callable]` populated at agent init |
| Agent → Callbacks | Callback list iteration | `post_tool_callbacks: list[Callable]` — ordered, each receives output of previous |
| Agent → Services | Direct function call | Services are injected into agent at construction (dependency injection) |
| Coordinator → Subagent | Instantiation + `.run()` | Coordinator creates subagent instance, calls run, gets string/Pydantic result |
| Services → Data | In-memory dict access | No I/O; deterministic for testing and demos |

## Build Order Implications

The architecture has a clear dependency graph that should drive notebook and phase ordering:

```
1. models/          (Pydantic schemas — no dependencies)
2. services/        (business logic using models)
3. tools/schemas    (JSON tool definitions — no code deps)
4. tools/dispatch   (maps names to service functions)
5. callbacks/       (pure functions on tool results)
6. agents/base      (loop + dispatch + callbacks wired together)
7. agents/customer  (5-tool agent using base)
8. agents/anti_patterns (15-tool agent using base — needs base working first)
9. agents/coordinator   (depends on all subagent types existing)
```

Notebook order follows the same dependency graph: foundation first (tools, loop), then enforcement (callbacks), then optimization (caching, context), then advanced patterns (coordinator).

## Sources

- [How to implement tool use — Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — HIGH confidence, official docs, verified March 2026
- [Programmatic tool calling — Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) — HIGH confidence
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — HIGH confidence, official docs
- [Basic Agentic Loop with Claude and Tool Calling — Temporal](https://docs.temporal.io/ai-cookbook/agentic-loop-tool-call-claude-python) — MEDIUM confidence, verified against SDK docs
- [Building Effective AI Agents — Anthropic Research](https://www.anthropic.com/research/building-effective-agents) — HIGH confidence, Anthropic first-party
- [Writing effective tools for AI agents — Anthropic Engineering](https://www.anthropic.com/engineering/writing-tools-for-agents) — HIGH confidence
- [How we built our multi-agent research system — Anthropic Engineering](https://www.anthropic.com/engineering/multi-agent-research-system) — HIGH confidence
- [Agent SDK reference Python — Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/python) — HIGH confidence (for PostToolUse callback structure)
- [Agentic Workflows with Claude — Medium](https://medium.com/@reliabledataengineering/agentic-workflows-with-claude-architecture-patterns-design-principles-production-patterns-72bbe4f7e85a) — LOW confidence, community article
- [Poetry basic usage](https://python-poetry.org/docs/basic-usage/) — HIGH confidence, official Poetry docs

---
*Architecture research for: CCA Exam Prep Customer Support Agent — Claude API tool-use teaching project*
*Researched: 2026-03-25*
