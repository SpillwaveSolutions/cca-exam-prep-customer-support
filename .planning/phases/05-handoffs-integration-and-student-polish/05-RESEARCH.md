# Phase 5: Handoffs, Integration, and Student Polish - Research

**Researched:** 2026-03-27
**Domain:** Anthropic SDK tool_choice enforcement, coordinator-subagent orchestration, Jupyter notebook pedagogy
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Structured handoff via tool_choice enforcement:** When callback blocks a refund (returns `action_required: escalate_to_human`), the agent loop detects this and re-calls Claude with `tool_choice={"type": "tool", "name": "escalate_to_human"}`. Claude is FORCED to call `escalate_to_human` with all EscalationRecord fields. Modify `agent_loop.py` to detect blocked results and issue the forced tool_choice call.
- **Raw handoff anti-pattern (raw_handoff.py):** Anti-pattern dumps the entire messages array as raw text. Scenario: C003 $600 refund. Observable failure: human gets 2000+ tokens of raw conversation including tool_use/tool_result blocks.
- **Coordinator-subagent pattern:** CCA rule — subagents do NOT inherit coordinator context; everything must be explicitly passed. Subagents never communicate directly; all through coordinator. Implement `agent/coordinator.py`. Demo: customer message spanning refund + shipping + account question.
- **Integration notebook (07) scenario:** Single scenario touching all 6 CCA patterns: (1) Escalation $600 refund triggers callback, (2) Compliance PII redacted, (3) Tool design 5 focused tools, (4) Context ContextSummary across turns, (5) Cost prompt caching with cache_read tokens visible, (6) Handoffs tool_choice forces structured EscalationRecord. Use C003 + PII in message.
- **Student TODO placeholders:** At least 3 TODOs that do not break notebook execution. Good TODOs: new escalation rule, new customer profile, custom callback. Bad TODOs: boilerplate, config changes. Each has description, expected behavior, hints. Use try/except or conditional checks so notebooks still run.
- **Notebook 06 (Handoffs):** Template: Setup > Anti-Pattern (raw dump) > Correct (tool_choice structured) > Compare. Scenario: C003 $600 refund. Compare: token count (raw >> structured) + readability.
- **Verification rules (behavior-first):** Test tool_choice produces actual EscalationRecord fields (test stored escalation, not just returned JSON). Test coordinator passes explicit context to subagents (subagent does NOT see coordinator's full history). Test raw_handoff anti-pattern includes tool_use blocks in output.

### Claude's Discretion

- Coordinator routing logic (how to detect multi-topic queries)
- Subagent system prompts
- Integration notebook exact cell structure and turn sequence
- TODO placement and wording
- Raw handoff formatting (how to dump messages as text)

### Deferred Ideas (OUT OF SCOPE)

- Streamlit UI — still TBD, could be a separate phase or post-milestone addition

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HANDOFF-01 | Structured JSON escalation handoff via `tool_choice` enforcement (EscalationRecord) | tool_choice={"type":"tool","name":"escalate_to_human"} is a first-class Anthropic SDK feature; stop_reason="tool_use" on forced call; agent_loop.py modification is localized |
| HANDOFF-02 | Coordinator-subagent pattern for multi-agent orchestration | Raw SDK implementation: coordinator calls run_agent_loop for each subagent; explicit context string passed in user message; no shared state |
| ANTI-05 | Raw conversation dump handoff anti-pattern (unstructured escalation) | Dump messages list as JSON text via json.dumps; attach to str() representation; observable by token count and tool_use artifact noise |
| NB-07 | Notebook 06 - Handoff pattern (structured JSON vs raw conversation dump) | Follows established notebook template; uses C003 $600 canonical scenario |
| NB-08 | Notebook 07 - Integration notebook combining all 6 patterns | Capstone: one scenario naturally exercises all 6 CCA patterns; C003 + PII trigger 3 patterns simultaneously |
| STUDENT-01 | Student TODO placeholders that do not break notebook execution | try/except guard pattern with fallback; TODO as optional extension; 3+ placements across notebooks |

</phase_requirements>

---

## Summary

Phase 5 delivers the final production feature (tool_choice-forced structured handoffs), the capstone integration notebook, and the raw_handoff anti-pattern. It also adds the coordinator-subagent demonstration and student TODO placeholders.

The two technically novel pieces are: (1) modifying `agent_loop.py` to detect a blocked refund result and issue a second `messages.create()` call with `tool_choice={"type": "tool", "name": "escalate_to_human"}`, and (2) implementing `coordinator.py` as a hub-and-spoke orchestrator that calls `run_agent_loop()` for each subagent with explicitly constructed context strings.

The teaching structure for both new notebooks (NB-07, NB-08) follows the existing template from Phase 3/4 notebooks — the only new convention is the integration notebook's per-pattern markdown section with CCA Exam Tip.

**Primary recommendation:** Implement tool_choice enforcement as a targeted addition to the bottom of the agent loop's tool-dispatch block — detect `action_required: escalate_to_human` in any blocked result and immediately issue one forced call. This keeps the loop's stop_reason logic untouched and adds minimal branching.

---

## Standard Stack

### Core (already installed — no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | already installed | tool_choice parameter in messages.create() | Native SDK feature; no extra library needed |
| pydantic | already installed | EscalationRecord already defined | Single source of truth for schema |
| pytest | already installed | behavior-first tests for new modules | Established test pattern for this project |

### No New Dependencies
This phase adds no new pip packages. All required libraries (anthropic, pydantic, pytest, nbformat) are already installed from earlier phases.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw SDK coordinator loop | Claude Agent SDK | Agent SDK is out-of-scope (REQUIREMENTS.md explicitly excludes it) |
| try/except TODO guard | assert-based guard | try/except lets notebooks run; asserts raise on incomplete TODO |

**Version verification:** No new packages. Existing versions verified in earlier phases.

---

## Architecture Patterns

### Recommended Project Structure (additions only)
```
src/customer_service/
├── agent/
│   ├── agent_loop.py        # MODIFY: add tool_choice forced-call block
│   └── coordinator.py       # NEW: hub-and-spoke coordinator
├── anti_patterns/
│   └── raw_handoff.py       # NEW: raw conversation dump anti-pattern
notebooks/
├── 06_handoffs.ipynb        # NEW: NB-07 (handoff pattern)
└── 07_integration.ipynb     # NEW: NB-08 (capstone integration)
tests/
└── test_handoffs.py         # NEW: behavior-first tests for HANDOFF-01, HANDOFF-02, ANTI-05
```

### Pattern 1: tool_choice Forced Escalation (HANDOFF-01)

**What:** When `escalation_callback` returns `action="block"` with `action_required: escalate_to_human`, `agent_loop.py` detects this in the tool_results list and immediately issues a second `messages.create()` call with `tool_choice={"type": "tool", "name": "escalate_to_human"}`.

**When to use:** Exactly one condition — any tool result in the current iteration contains `action_required: escalate_to_human`.

**Verified behavior from official docs (HIGH confidence):**
- `tool_choice={"type": "tool", "name": "escalate_to_human"}` forces Claude to call exactly that tool
- stop_reason is `"tool_use"` on the forced call — identical to normal tool use
- The API prefills the assistant message when `type: "tool"` is set, meaning no natural language preamble before the tool_use block
- This is a first-class Anthropic API feature, not a workaround

**Source:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools

**Minimal implementation pattern:**
```python
# Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
# In agent_loop.py, after collecting tool_results in the iteration:

def _has_escalation_required(tool_results: list[dict]) -> bool:
    """Check if any tool result contains action_required: escalate_to_human."""
    import json
    for tr in tool_results:
        content = tr.get("content", "")
        try:
            data = json.loads(content)
            if data.get("action_required") == "escalate_to_human":
                return True
        except (json.JSONDecodeError, AttributeError):
            pass
    return False

# After tool_results are collected, before appending to messages:
if _has_escalation_required(tool_results):
    # Append current tool results to messages
    messages.append({"role": "user", "content": tool_results})
    # Forced escalation call
    forced_response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        tools=active_tools,
        messages=messages,
        tool_choice={"type": "tool", "name": "escalate_to_human"},
    )
    # Accumulate usage for the forced call
    usage.input_tokens += forced_response.usage.input_tokens
    usage.output_tokens += forced_response.usage.output_tokens
    # Dispatch the forced escalate_to_human call
    messages.append({"role": "assistant", "content": forced_response.content})
    escalation_results = []
    for block in forced_response.content:
        if hasattr(block, "type") and block.type == "tool_use":
            tool_calls.append({"name": block.name, "input": block.input, "id": block.id})
            result_content = dispatch(block.name, block.input, services, context=context)
            escalation_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_content,
            })
    messages.append({"role": "user", "content": escalation_results})
    # End turn after escalation
    return AgentResult(
        stop_reason="escalated",
        messages=messages,
        tool_calls=tool_calls,
        final_text="",
        usage=usage,
    )
```

**Key decision:** Return `stop_reason="escalated"` (not "end_turn") so callers can distinguish a forced escalation from a natural end. This also lets notebooks display a clear teaching signal.

**Pitfall — extended thinking incompatibility (HIGH confidence):** `tool_choice: {"type": "tool"}` and `tool_choice: {"type": "any"}` are NOT compatible with extended thinking. Since this project does not use extended thinking, this does not affect implementation. Documented for completeness.

**Source:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools

### Pattern 2: Coordinator-Subagent with Raw SDK (HANDOFF-02)

**What:** A coordinator Claude call decomposes a multi-topic customer message and delegates to specialized subagents via separate `run_agent_loop()` invocations. Each subagent receives only its relevant task context, not the full conversation history.

**CCA Rules (from CCA-RULES.md — authoritative):**
- Subagents do NOT inherit coordinator context (blank slate)
- Everything needed must be explicitly passed
- Subagents never communicate directly — all through coordinator
- Coordinator is responsible for global planning, delegation, and state

**Raw SDK implementation pattern (MEDIUM confidence — verified by multiple Anthropic sources):**
```python
# Source: https://www.anthropic.com/research/building-effective-agents
# coordinator.py — hub-and-spoke pattern with explicit context passing

def run_coordinator(
    client,
    services: ServiceContainer,
    user_message: str,
    system_prompt: str,
    model: str = "claude-sonnet-4-6",
) -> CoordinatorResult:
    """Decompose multi-topic query and delegate to specialized subagents."""

    # Step 1: Coordinator decomposes the query (no tools, just analysis)
    decomposition_response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=COORDINATOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    # Parse subtasks from decomposition (structured output or simple parsing)
    subtasks = _parse_subtasks(decomposition_response)

    # Step 2: Delegate each subtask to a specialized subagent
    # CCA Rule: each subagent gets ONLY its task context, not full history
    subagent_results = []
    for subtask in subtasks:
        # Explicit context string — subagent gets only what it needs
        subagent_context = (
            f"Customer ID: {subtask.customer_id}\n"
            f"Task: {subtask.task_description}\n"
            f"Relevant info: {subtask.relevant_context}\n"
        )
        result = run_agent_loop(
            client=client,
            services=services,
            user_message=subagent_context,       # task-specific, not full history
            system_prompt=subtask.system_prompt, # specialized for this agent
            callbacks=subtask.callbacks,
        )
        subagent_results.append(result)

    # Step 3: Coordinator assembles results into customer response
    synthesis = _synthesize_results(client, user_message, subagent_results)
    return CoordinatorResult(subagent_results=subagent_results, synthesis=synthesis)
```

**Context isolation — why it matters (HIGH confidence, from CCA-RULES.md):**
The CCA exam specifically tests this. "Subagent unexpected output" symptom on the exam maps directly to "instructions not explicitly passed." The test for HANDOFF-02 should confirm that a subagent's messages list does NOT contain the coordinator's full conversation history — only the explicit context string passed to it.

**Multi-topic detection (Claude's discretion — implement simply):**
The coordinator system prompt should instruct Claude to identify topics from a fixed list (refund, shipping, account). Simple approach: coordinator returns a JSON list of `{topic, relevant_details}` pairs. No complex NLP needed — Claude handles this reliably when the prompt is clear.

### Pattern 3: Raw Handoff Anti-Pattern (ANTI-05)

**What:** `raw_handoff.py` runs the normal agent loop for a C003 $600 refund, then instead of extracting the EscalationRecord, dumps the entire `messages` list as a raw text block.

**Observable failure (HIGH confidence — design is straightforward):**
```python
# Source: anti_patterns/raw_handoff.py pattern
def format_raw_handoff(messages: list) -> str:
    """Anti-pattern: dump entire conversation as raw text.

    WHY IT FAILS:
    - Human agent receives 2000+ tokens of raw JSON with tool_use artifacts
    - tool_use blocks contain API-internal IDs not relevant to human
    - tool_result blocks contain internal JSON structures
    - The actual issue (customer_id, amount, reason) is buried 10+ turns in
    - Human must read entire transcript to extract 7 key fields
    CCA CORRECT PATTERN: EscalationRecord JSON with 8 clean fields at top.
    """
    import json
    # Serialize every message turn including tool_use/tool_result blocks
    return json.dumps(messages, indent=2, default=str)
```

**Consistent scenario:** Use C003 (Carol Martinez, $600 refund, order O003) — same as NB01 and NB03. Consistent teaching scenario helps students compare patterns.

### Pattern 4: Student TODO Placeholders (STUDENT-01)

**Design principle (HIGH confidence from CONTEXT.md):** TODOs must be genuinely educational AND must not break execution. Use try/except or conditional guards.

**Three canonical TODO placements:**

**TODO-1: New escalation rule (place in NB-02 or NB-06)**
```python
# TODO: Add a new escalation rule — e.g., escalate when refund_count > 3 in 30 days
# HINTS:
#   1. Add "refund_count" tracking to CustomerProfile flags
#   2. Check context["refund_count"] in escalation_callback
#   3. Add a test in test_callbacks.py
# EXPECTED: A customer with 4 prior refunds triggers escalation even for $50
# GUARD: fallback runs existing scenario without new rule if TODO is skipped
try:
    # Student implements here
    pass  # Replace with: context["high_frequency_refunder"] = ...
except NotImplementedError:
    print("TODO not yet implemented — running baseline scenario")
```

**TODO-2: New customer profile (place in NB-07 or integration NB)**
```python
# TODO: Add a premium-tier customer with a partial refund scenario
# HINTS:
#   1. Create CustomerProfile(customer_id="C007", tier=CustomerTier.PREMIUM, ...)
#   2. Add to a local customers dict (no need to modify seed data)
#   3. Trigger check_policy to see PREMIUM tier limit
# EXPECTED: PREMIUM tier limit is higher than REGULAR; $400 should not require review
# GUARD: notebook uses C003 if C007 is not defined
student_customer = None  # Replace with: CustomerProfile(...)
if student_customer is None:
    print("Using default C003 scenario (implement TODO to use custom customer)")
    customer_id = "C003"
else:
    customer_id = student_customer.customer_id
```

**TODO-3: Custom PostToolUse callback (place in NB-06 or integration NB)**
```python
# TODO: Write a callback that flags interactions with sentiment keywords
# HINTS:
#   1. Add a sentiment keyword list (e.g., ["frustrated", "terrible", "unacceptable"])
#   2. Check context["user_message"] in the callback
#   3. Set context["sentiment_flag"] = True if found
#   4. Return CallbackResult(action="allow") — this callback only flags, not blocks
# EXPECTED: Angry customer message sets sentiment_flag in context
# GUARD: uses build_callbacks() default if student callback is None
def student_sentiment_callback(*args, **kwargs):
    # Replace with real implementation
    from customer_service.agent.callbacks import CallbackResult
    return CallbackResult(action="allow")  # placeholder — returns allow
```

### Pattern 5: Notebook 06 Cell Structure (NB-07)

Follows established template. New element: raw handoff token count comparison.

```
## Section 1 — Setup
- ServiceContainer setup (make_services() helper)
- C003 scenario variables

## Section 2 — Anti-Pattern: Raw Conversation Dump
- run anti-pattern: confidence_agent equivalent but for handoffs
- show raw handoff output (truncated with "... N more lines")
- measure token length with tiktoken or len(text) proxy
- RED box: "ANTI-PATTERN: Human agent gets {N} chars / ~{T} tokens of raw JSON"

## Section 3 — Correct Pattern: Structured EscalationRecord
- run_agent_loop with callbacks (triggers escalation)
- show EscalationRecord JSON (8 clean fields)
- measure token length
- GREEN box: "CORRECT: Human agent gets {N} chars / ~{T} tokens — clean JSON"

## Section 4 — Compare
- Side-by-side: raw token count vs structured token count
- Readability comparison (which fields are immediately visible)
- CCA Exam Tip blockquote

## Optional: Student TODO-3 cell
```

### Pattern 6: Notebook 07 Cell Structure (NB-08 — Integration Capstone)

```
## Setup
- Import all 6 modules (agent, callbacks, context_manager, system_prompts, etc.)
- C003 scenario with PII injected in user message
- make_services()

## Pattern 1: Escalation (callback blocks $600 refund)
- Run agent loop with callbacks enabled
- Show: blocked result in tool_calls
- CCA Exam Tip: "Deterministic business rules in code, not LLM confidence"

## Pattern 2: Compliance (PII redacted)
- Same run — inspect audit log for redacted credit card
- Show: ****-****-****-1234 in log entry
- CCA Exam Tip: "Programmatic redaction, not prompt instructions"

## Pattern 3: Tool Design (5 tools used, not 15)
- Show tool_calls list — exactly 5 tool types
- CCA Exam Tip: "4-5 focused tools per agent; split to coordinator-subagent for more"

## Pattern 4: Context Management (ContextSummary tracks facts)
- Show context_manager.to_system_context() at turn 3
- CCA Exam Tip: "Structured summaries, not raw transcript"

## Pattern 5: Cost (prompt caching active)
- Show AgentResult.usage.cache_read_input_tokens > 0
- Show cost comparison: cache hit vs cache miss
- CCA Exam Tip: "Prompt caching (90% savings) for repeated context"

## Pattern 6: Handoffs (tool_choice forces EscalationRecord)
- Show forced escalation via tool_choice
- Show clean EscalationRecord JSON
- CCA Exam Tip: "Structured JSON handoff, not raw conversation dump"

## Student TODOs — optional extension cells
```

### Anti-Patterns to Avoid

- **Detecting blocked status by exception:** The block signal is in the tool result JSON (`action_required: escalate_to_human`), not an exception. Parse the JSON string.
- **Sharing messages list between coordinator and subagent:** Pass only an explicit context string, not a slice of messages. Subagents get a fresh conversation with one user message.
- **Storing raw_handoff.py in agent/:** Anti-patterns live ONLY in `anti_patterns/` — never in `agent/`.
- **Tool result alongside text block:** CCA pitfall: `messages.append({"role": "user", "content": tool_results})` must contain ONLY tool_result blocks. No text blocks.
- **Checking content block types to exit loop:** Loop exits on `stop_reason`, never on presence/absence of text blocks.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Forcing a specific tool call | Custom prompt injection ("You MUST call escalate_to_human") | `tool_choice={"type": "tool", "name": "escalate_to_human"}` | API-level enforcement is deterministic; prompt guidance is probabilistic (CCA Layer 2 vs Layer 1) |
| EscalationRecord schema | Custom dict construction | `EscalationRecord.model_dump()` (already defined in models/customer.py) | Pydantic validates all 8 required fields; custom dict misses required fields silently |
| Multi-agent context isolation | Thread-local storage, global state | Explicit string argument to `run_agent_loop()` | CCA rule: subagents start blank; explicit passing is the ONLY correct approach |
| Subagent message routing | Direct agent-to-agent calls | Coordinator dispatches via separate `run_agent_loop()` calls | CCA rule: all communication through coordinator |
| Notebook TODO fallbacks | Assertions that halt execution | try/except with print fallback | Students learn patterns by running notebooks; broken execution stops learning |

**Key insight:** The tool_choice parameter is the CCA-correct Layer 2 enforcement for structured outputs. Building a prompt-only version would be a deliberate anti-pattern — which is exactly what the raw_handoff anti-pattern demonstrates at the output level.

---

## Common Pitfalls

### Pitfall 1: Double-appending messages for forced call
**What goes wrong:** Agent appends tool_results to messages, then the forced escalation call also processes those same tool_results, resulting in duplicate messages.
**Why it happens:** The forced call must come AFTER appending the current tool_results but BEFORE the next loop iteration.
**How to avoid:** Detect escalation BEFORE the normal `messages.append({"role": "user", "content": tool_results})` step. Append tool_results first, then issue forced call, then return immediately — do not continue the loop.
**Warning signs:** `messages` list contains duplicate tool_result entries; EscalationRecord appears twice in escalation_queue.

### Pitfall 2: Passing messages slice to subagent instead of explicit context
**What goes wrong:** Coordinator passes `messages[-3:]` to subagent user_message, leaking coordinator internal state.
**Why it happens:** Developer intuition says "give subagent the recent context."
**How to avoid:** Always construct an explicit context string for each subagent — no slices of the coordinator's messages list.
**Warning signs:** Subagent test shows coordinator message content in subagent's messages; CCA exam would mark this wrong.

### Pitfall 3: stop_reason check breaks when tool_choice adds "escalated"
**What goes wrong:** Callers that check `result.stop_reason == "end_turn"` miss successful escalations.
**Why it happens:** New `stop_reason="escalated"` value was added to AgentResult but callers were not updated.
**How to avoid:** Notebooks and tests should check `result.stop_reason in ("end_turn", "escalated")` for "agent finished." Document the new stop_reason value in AgentResult docstring.
**Warning signs:** Integration notebook shows no final text AND no escalation record.

### Pitfall 4: Raw handoff token count understated
**What goes wrong:** Comparison shows raw handoff is only slightly larger than structured handoff.
**Why it happens:** Messages list was truncated before serialization.
**How to avoid:** Dump the FULL messages list including all tool_use and tool_result blocks from a real run. Do not pre-filter. The pedagogical value is showing the full 2000+ token dump vs 8-field JSON.
**Warning signs:** Token count comparison is less than 5:1 ratio.

### Pitfall 5: TODO guard uses assert instead of try/except
**What goes wrong:** Incomplete TODO raises AssertionError and stops notebook execution.
**Why it happens:** Developer uses assert as placeholder.
**How to avoid:** All TODO guards must use try/except or conditional fallbacks. If TODO is not implemented, notebook prints an explanation and continues with baseline.
**Warning signs:** Running notebook unmodified raises any exception in TODO cells.

### Pitfall 6: tool_choice cache invalidation (minor, worth knowing)
**What goes wrong:** Switching to `tool_choice={"type": "tool"}` invalidates cached message blocks if prompt caching is active.
**Why it happens:** Official docs confirm: changes to tool_choice parameter invalidate cached message blocks. Tool definitions and system prompts remain cached.
**How to avoid:** The forced escalation call is a one-time call at end of session — cache invalidation cost is acceptable. Document in code comment.
**Source:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools

---

## Code Examples

### Forced tool_choice call in agent_loop.py
```python
# Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
# Tool_choice={"type": "tool"} forces exactly that tool; stop_reason is still "tool_use"
# API prefills assistant message — no natural language preamble before tool_use block

forced_response = client.messages.create(
    model=model,
    max_tokens=max_tokens,
    system=system_prompt,
    tools=active_tools,
    messages=messages,
    tool_choice={"type": "tool", "name": "escalate_to_human"},
)
# stop_reason will be "tool_use" — identical to normal tool dispatch
```

### Coordinator explicit context passing
```python
# Source: https://www.anthropic.com/research/building-effective-agents
# CCA Rule: explicit context string; subagent never sees coordinator messages

subagent_context = (
    f"Customer: {customer_id} (tier: {customer_tier})\n"
    f"Task: Process refund inquiry for ${amount}\n"
    f"Policy result: approved={policy_approved}, requires_review={requires_review}\n"
)
subagent_result = run_agent_loop(
    client=client,
    services=services,
    user_message=subagent_context,         # task-specific only
    system_prompt=REFUND_AGENT_PROMPT,     # specialized system prompt
    callbacks=build_callbacks(),
)
```

### Raw handoff anti-pattern (observable failure)
```python
# Source: anti_patterns/raw_handoff.py (new module, Phase 5)
# Observable: N chars / ~T tokens of raw JSON vs 8-field EscalationRecord

import json

def format_raw_handoff(messages: list) -> str:
    """Dump entire conversation as raw text — the CCA anti-pattern."""
    return json.dumps(messages, indent=2, default=str)

# Correct pattern comparison:
escalation_record = services.escalation_queue.get_latest()
structured_handoff = json.dumps(escalation_record.model_dump(), indent=2)
# structured_handoff: ~8 fields, ~200 chars
# raw_handoff: full messages list, ~2000+ chars with API artifacts
```

### Student TODO guard pattern
```python
# Source: this project's established pattern
# All TODOs must not break execution when left as-is

try:
    # TODO: Implement new escalation rule
    # Description: escalate when customer has 4+ refunds in 30 days
    # Hints: check context["refund_count"] > 3
    # Expected: high-frequency refunders are auto-escalated
    raise NotImplementedError("TODO: implement this callback")
except NotImplementedError:
    print("TODO not yet implemented — skipping extension. Core scenario still runs.")
```

### EscalationRecord field names (verified)
```python
# Source: customer_service/models/customer.py (confirmed via Python import)
# All 8 fields required — tool_choice forces Claude to provide all:
# customer_id, customer_tier, issue_type, disputed_amount,
# escalation_reason, recommended_action, conversation_summary, turns_elapsed
from customer_service.models.customer import EscalationRecord
# model_fields.keys() = ['customer_id', 'customer_tier', 'issue_type', 'disputed_amount',
#                        'escalation_reason', 'recommended_action',
#                        'conversation_summary', 'turns_elapsed']
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prompt-only escalation routing | tool_choice enforcement (Layer 2) | CCA defined | Deterministic structured output; cannot be bypassed by LLM reasoning |
| Framework-based multi-agent (LangGraph etc.) | Raw SDK with explicit run_agent_loop() calls | Anthropic 2025 guidance | Reduces abstraction; explicit context passing is visible and auditable |
| Full conversation handoff to human | EscalationRecord 8-field JSON | CCA handoff pattern | Human agent gets actionable summary in ~200 chars vs 2000+ chars |
| Claude Agent SDK subagents | Raw SDK with explicit context passing | Out of scope for this project | Raw SDK pattern is testable, visible, and pedagogically valuable |

**Deprecated/outdated:**
- "Pass full conversation history to subagent": explicitly wrong per CCA rules and Anthropic's building-effective-agents guidance
- "Use agent_choice=auto and hope Claude escalates": Layer 1 only; CCA requires Layer 2 enforcement

---

## Open Questions

1. **Coordinator routing — how many subtopics to support?**
   - What we know: CONTEXT.md specifies "refund + shipping + account question" as the demo scenario
   - What's unclear: Whether coordinator.py needs to handle arbitrary topic counts or just the 3 fixed topics
   - Recommendation: Implement for exactly 3 topics (refund, shipping, account) — simpler coordinator prompt, easier to test, matches the stated demo scenario

2. **Integration notebook multi-turn count**
   - What we know: Need enough turns to show context management (Pattern 4) and cache_read tokens (Pattern 5)
   - What's unclear: Exact number of turns for compelling demonstration
   - Recommendation: 3 turns — T1: customer intro + PII, T2: refund inquiry (triggers escalation), T3: escalation handoff. Claude's discretion on cell structure.

3. **CoordinatorResult return type — new dataclass or dict?**
   - What we know: coordinator.py is a new module; no existing return type applies
   - What's unclear: Whether a formal dataclass adds teaching value or just complexity
   - Recommendation: Simple dataclass with `subagent_results: list[AgentResult]` and `synthesis: str` fields — matches project conventions (dataclasses throughout)

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already installed and configured) |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `poetry run pytest tests/test_handoffs.py -x` |
| Full suite command | `poetry run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HANDOFF-01 | tool_choice forced call produces EscalationRecord fields in escalation_queue | unit | `poetry run pytest tests/test_handoffs.py::TestToolChoiceEnforcement -x` | Wave 0 |
| HANDOFF-01 | agent_loop detects action_required in blocked result | unit | `poetry run pytest tests/test_handoffs.py::TestBlockedResultDetection -x` | Wave 0 |
| HANDOFF-01 | AgentResult.stop_reason == "escalated" after forced call | unit | `poetry run pytest tests/test_handoffs.py::TestEscalatedStopReason -x` | Wave 0 |
| HANDOFF-02 | subagent messages list does NOT contain coordinator history | unit | `poetry run pytest tests/test_handoffs.py::TestSubagentContextIsolation -x` | Wave 0 |
| HANDOFF-02 | coordinator assembles results from all subagents | unit | `poetry run pytest tests/test_handoffs.py::TestCoordinatorAssembly -x` | Wave 0 |
| ANTI-05 | raw handoff output contains tool_use block artifacts | unit | `poetry run pytest tests/test_handoffs.py::TestRawHandoffAntiPattern -x` | Wave 0 |
| ANTI-05 | raw handoff token count > structured handoff token count | unit | `poetry run pytest tests/test_handoffs.py::TestHandoffTokenComparison -x` | Wave 0 |
| STUDENT-01 | TODO guard cells do not raise when TODO is not implemented | unit | `poetry run pytest tests/test_notebooks.py -x` | Partial (test_notebooks.py exists) |

### Sampling Rate
- **Per task commit:** `poetry run pytest tests/test_handoffs.py -x`
- **Per wave merge:** `poetry run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_handoffs.py` — covers HANDOFF-01, HANDOFF-02, ANTI-05
- [ ] `src/customer_service/agent/coordinator.py` — stub needed before tests can import
- [ ] `src/customer_service/anti_patterns/raw_handoff.py` — stub needed before tests can import

*(test_notebooks.py already exists — Wave 0 check: confirm it handles NB-07 and NB-08 once created)*

---

## Sources

### Primary (HIGH confidence)
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools — tool_choice parameter format, forced tool behavior, stop_reason, cache invalidation
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works — agentic loop mechanics, stop_reason "tool_use" on forced calls
- `.planning/CCA-RULES.md` — coordinator-subagent rules, handoff pattern, subagent context isolation (authoritative project source)
- `src/customer_service/models/customer.py` — EscalationRecord 8 fields confirmed via live import
- `src/customer_service/agent/agent_loop.py` — current loop structure; tool_choice addition point identified
- `src/customer_service/agent/callbacks.py` — escalation_callback returns `action_required: escalate_to_human` in blocked result

### Secondary (MEDIUM confidence)
- https://www.anthropic.com/research/building-effective-agents — orchestrator-workers pattern, explicit context passing to subagents, raw SDK recommendation
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — context isolation, subagent summary distillation

### Tertiary (LOW confidence)
- WebSearch results for coordinator pattern: confirmed by CCA-RULES.md authoritative source; WebSearch results consistent but not primary authority

---

## Metadata

**Confidence breakdown:**
- tool_choice enforcement: HIGH — verified against current official docs; format confirmed; stop_reason behavior confirmed
- Coordinator-subagent pattern: HIGH — CCA-RULES.md is the authoritative source; raw SDK pattern confirmed by Anthropic's building-effective-agents article
- Raw handoff anti-pattern: HIGH — straightforward JSON serialization; design is deterministic
- Student TODO pattern: HIGH — project pattern from CONTEXT.md; try/except guard is standard Python
- Notebook structure: HIGH — follows established template from Phases 3 and 4

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (tool_choice API is stable; 30-day window)
