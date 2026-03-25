# Pitfalls Research

**Domain:** Claude API tool-use agent teaching project (CCA Exam Prep coding example)
**Researched:** 2026-03-25
**Confidence:** HIGH (primary sources: Anthropic official docs, Claude API reference, verified with multiple sources)

---

## Critical Pitfalls

### Pitfall 1: Agentic Loop Terminates on Content Type Instead of stop_reason

**What goes wrong:**
The agentic loop checks `response.content[0].type == "text"` to decide whether to continue iterating. This breaks silently: Claude often returns a text block ("I'll now look up the customer...") immediately followed by a `tool_use` block in the same response. The loop reads the text block, declares the turn complete, and exits — dropping the pending tool call entirely. The agent appears to "work" on simple cases and fails unpredictably on complex ones.

**Why it happens:**
Developers coming from chat patterns assume a text response means the model is done. It does in chat. In agentic loops, Claude uses inline text as reasoning narration before invoking tools, so text-presence is not a completion signal.

**How to avoid:**
The only reliable loop-control signal is `response.stop_reason`. Continue the loop when `stop_reason == "tool_use"`. Terminate when `stop_reason == "end_turn"`. Never inspect content type for this decision. Add an iteration safety cap (e.g., 25) as a runaway guard, but never as the primary stop mechanism.

```python
# WRONG — used as anti-pattern demo in Notebook 01
while True:
    response = client.messages.create(...)
    if response.content[0].type == "text":  # BREAKS on mixed responses
        break

# CORRECT — used as correct-pattern demo in Notebook 01
MAX_ITERATIONS = 25
for _ in range(MAX_ITERATIONS):
    response = client.messages.create(...)
    if response.stop_reason == "end_turn":
        break
    if response.stop_reason == "tool_use":
        # process tool calls, append results, continue
        ...
```

**Warning signs:**
- Tool calls in the conversation history are never followed by tool results
- The agent gives incomplete answers that stop mid-task without explanation
- Notebook cells run successfully but customer lookup never actually happens

**Phase to address:** Phase 1 (Core Agentic Loop foundation) — this is the first pattern students must get right. All subsequent notebooks inherit the loop implementation.

---

### Pitfall 2: Tool Result Format Violations Cause Silent API Errors

**What goes wrong:**
Two distinct format violations cause the API to return 400 errors that beginners misread as logic bugs:

1. Placing a `text` block before `tool_result` blocks in the user message content array
2. Sending each parallel tool result in a separate user message instead of grouping them in one message

Both fail with the error: `"tool_use ids were found without tool_result blocks immediately after"` — which sounds like a conversation history problem, not a message structure problem.

**Why it happens:**
The API conversation structure is counterintuitive: tool results belong in a `user` role message, not `assistant`. Beginners try to add explanatory text alongside tool results ("Here are the results: [tool_result]") and inadvertently trigger the validation rule. For parallel results, the natural Python instinct is to send each result as it completes — but the API requires all results for a given assistant turn in a single user message.

**How to avoid:**
Tool result blocks must appear first in the content array of the user message. Any text appended for context follows after. When Claude makes multiple parallel tool calls in a single response, all results go into one user message as a list of `tool_result` blocks.

```python
# WRONG — text before tool_result (400 error)
{"role": "user", "content": [
    {"type": "text", "text": "Here are the results:"},
    {"type": "tool_result", "tool_use_id": "toolu_01", "content": "..."}
]}

# CORRECT — tool_result blocks first
{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "toolu_01", "content": "..."},
    {"type": "tool_result", "tool_use_id": "toolu_02", "content": "..."},
]}
```

**Warning signs:**
- Intermittent 400 errors that seem unrelated to model behavior
- Errors only appear when the agent tries to call two tools at once
- Debugging by printing messages shows structurally valid-looking content

**Phase to address:** Phase 1 (Core Agentic Loop) — the conversation history builder must enforce this format from the start. Notebook 01 should show both the wrong format and the error it produces.

---

### Pitfall 3: Prompt Cache Breakpoint Placed on Changing Content

**What goes wrong:**
The developer marks the user message (which contains the customer query and a timestamp) with `cache_control: {"type": "ephemeral"}` instead of the static policy document in the system prompt. Every request produces a cache write (charged at 25%-100% premium over base input tokens) but zero cache reads, because the prefix hash changes with each unique user message. The developer sees `cache_creation_input_tokens > 0` and thinks caching is working — they never notice `cache_read_input_tokens` stays at 0. The feature costs more than no caching at all.

**Why it happens:**
The cache_control marker is placed "near the big content" without understanding the prefix-hashing mechanism. Cache hits require the exact same byte sequence from position 0 up to the breakpoint. Anything that varies per request — timestamps, session IDs, customer IDs in the message, dynamic injections — invalidates the prefix even if the policy text is identical.

**How to avoid:**
Place `cache_control` at the end of the last block that is identical across all requests. For this project: the policy document lives in the system prompt as a static block, and `cache_control` marks the end of that block. The dynamic customer query follows in the user message with no cache marker.

Verify caching is working by checking `response.usage.cache_read_input_tokens` on the second request to the same session — it must be greater than 0. `cache_creation_input_tokens > 0` alone does not confirm working caching.

Model-specific minimum token requirements apply: Claude Sonnet 4.5+ requires at least 1024 tokens before the breakpoint; Sonnet 4.6 and Haiku 4.5 require 2048. Short policy documents cannot be cached regardless of marker placement.

**Warning signs:**
- `cache_creation_input_tokens` is high every request
- `cache_read_input_tokens` is always 0
- API costs scale linearly with request count rather than flattening after the first call
- The system prompt is shorter than 1024 tokens

**Phase to address:** Phase 3 (Prompt Caching demonstration) — Notebook 05 must explicitly show the wrong breakpoint placement and the "all writes, no reads" cost pattern before demonstrating correct placement.

---

### Pitfall 4: Compliance Enforcement in Prompt Instead of Application Layer

**What goes wrong:**
The escalation threshold ("always escalate refunds over $500") lives in the system prompt as an instruction rather than as a programmatic check in application code. In testing it works reliably. In a teaching demo it might work 19 out of 20 times. But the 20th time — when the model is slightly overconfident, when context is long, when a prompt injection is present — the rule is quietly bypassed. For the CCA exam, this is the single most common wrong-answer trap. For the teaching project, shipping this pattern as "correct" would directly contradict CCA exam guidance.

**Why it happens:**
Prompt-based rules are easier to write and easier to understand. They surface in the conversation history. They feel like documentation. The failure mode is rare enough in testing that developers never see it. The pattern feels correct because the model usually follows it.

**How to avoid:**
Business rules with financial or compliance consequences are enforced in Python code, not in prompts. The system prompt can explain why the rule exists and give context, but the PostToolUse callback executes the check unconditionally:

```python
# CORRECT — programmatic enforcement
def post_tool_use_hook(tool_name: str, tool_input: dict, tool_result: dict) -> dict:
    if tool_name == "process_refund":
        amount = tool_input.get("amount", 0)
        if amount > 500:
            return {"action": "escalate", "reason": "refund_amount_exceeds_limit"}
    return {"action": "continue"}
```

The PostToolUse callback fires every time, regardless of what Claude decided or how confident it was.

**Warning signs:**
- The only escalation mechanism is a sentence in the system prompt
- No PostToolUse or similar callback exists in the codebase
- Refund amounts are not validated anywhere except inside the LLM prompt
- Tests pass by checking model output rather than execution path

**Phase to address:** Phase 2 (Callback and Enforcement layer) — Notebook 03 must show the prompt-only anti-pattern failing a test case, then replace it with the programmatic callback that catches every case.

---

### Pitfall 5: Swiss Army Tool Set Reduces Selection Accuracy

**What goes wrong:**
The teaching demo includes a "Swiss Army" agent with 15 tools to demonstrate the anti-pattern. If this agent is implemented with realistic tool descriptions, students may observe it working correctly most of the time, undermining the lesson. Conversely, if descriptions are deliberately bad to force failures, the lesson conflates two separate problems (too many tools, bad descriptions) and students leave confused about which variable caused the failure.

More practically: if the production agent (5 focused tools) is built first and the Swiss Army agent is added later without care, the notebook comparison shows the same output for both, and students conclude the anti-pattern "doesn't matter."

**Why it happens:**
Claude's tool selection degradation from 15 tools is probabilistic, not deterministic. A single demo run may show correct behavior. The teaching value requires controlled conditions that reliably demonstrate the degradation.

**How to avoid:**
Design the 15-tool anti-pattern with overlapping tool names and ambiguous descriptions that systematically trigger selection errors. Include scope-creep tools (HR policy, marketing campaign, inventory) that have no business in a customer support agent, to demonstrate the security/compliance dimension separately from the accuracy dimension. Run both agents against the same 10-question test suite in the notebook, and aggregate results to show the pattern — single runs are unreliable for probabilistic failures.

**Warning signs:**
- The Swiss Army demo runs exactly once in the notebook
- All 15 tools have good, distinct descriptions (defeats the anti-pattern purpose)
- The comparison only shows one customer query rather than a test suite
- Students cannot reproduce the failure on demand

**Phase to address:** Phase 1 (Tool Design) — Notebook 02 must be designed so the anti-pattern failure is reproducible and observable, not anecdotal.

---

### Pitfall 6: Anti-Pattern Code Shown Before Pattern Is Established

**What goes wrong:**
Cognitive load research on anti-pattern teaching (Cagiltay et al., 2006, ScienceDirect) is clear: showing anti-patterns before the correct pattern is fully established in the learner's mind causes the anti-pattern to be remembered as the primary pattern. Students who see the 15-tool agent first and the 5-tool agent second may internalize the wrong architecture. The notebook structure "here is the wrong way, here is the right way" sounds pedagogically sound but can backfire if the wrong-way code is more memorable (longer, more complex, has more surface area).

**Why it happens:**
Developers teaching from their own knowledge naturally start with contrast ("the naive way vs. the correct way"). This works for experienced practitioners who already know the correct pattern. For students encountering a concept for the first time, the first version they run is the one that sticks.

**How to avoid:**
Each notebook must establish the concept and correct pattern first in explicit prose before showing the anti-pattern. The structure is: (1) explain what the pattern is and why it matters, (2) show the correct implementation and run it, (3) show why the anti-pattern looks plausible, (4) run the anti-pattern and observe the failure, (5) compare. The anti-pattern section must be visually differentiated (distinct cell background or comment header) and followed immediately by the comparison that resolves the cognitive dissonance.

**Warning signs:**
- Notebook cells show anti-pattern code in cell 1 and correct code in cell 10 with no framing
- Anti-pattern cells have the same visual style as correct-pattern cells
- No explicit prose cell explains what students should observe before running the anti-pattern
- The "run this first" instruction is missing from anti-pattern sections

**Phase to address:** Phase 0 (Notebook structure template) — establish the standard notebook section order and visual conventions before building any content notebooks.

---

### Pitfall 7: Escalation Handoff Passes Raw Conversation Transcript

**What goes wrong:**
When the agent escalates to a human via `escalate_to_human`, the tool passes the full conversation messages list as the handoff context. This looks thorough. It is wrong for three reasons: (1) the conversation may be 30+ turns long, forcing a human agent to read everything to find the relevant facts; (2) raw transcript is unstructured, making it hard to extract customer tier, disputed amount, or recommended action programmatically; (3) it directly fails the CCA exam pattern question on escalation handoffs.

**Why it happens:**
Passing the full messages list is the path of least resistance — it is already in scope as a Python variable. The developer adds it to the tool_input without thinking about the receiving side.

**How to avoid:**
The `escalate_to_human` tool accepts a structured Pydantic model as input, not a raw transcript:

```python
class EscalationHandoff(BaseModel):
    customer_id: str
    customer_tier: str
    issue_type: str
    disputed_amount: Optional[float]
    escalation_reason: str  # machine-readable enum value
    agent_findings: str     # one sentence
    recommended_action: str
    conversation_summary: str  # 2-3 sentence human-readable summary
    turns_elapsed: int
```

The anti-pattern demo in the notebook shows the full transcript approach. The correct demo shows the structured handoff and highlights that a human agent can read the `escalation_reason` field to route immediately without reading any further.

**Warning signs:**
- `escalate_to_human` tool input schema has a `messages` field or `conversation` field
- The escalation tool accepts a list type for any parameter
- No Pydantic model exists for escalation handoff data
- Tests for escalation check only that the function was called, not what was passed

**Phase to address:** Phase 2 (Tool Design and Escalation) — Notebook 04 escalation comparison must validate both that the tool was called AND that the handoff contains the correct structured fields.

---

### Pitfall 8: tool_choice Forced Escalation Breaks Natural Language Response

**What goes wrong:**
Using `tool_choice: {"type": "tool", "name": "escalate_to_human"}` forces the model to call the escalation tool immediately on every request where it is present. This is the correct pattern for guaranteed structured output during escalation, but it removes Claude's ability to provide a natural language response or explanation before the tool invocation. Students see the forced tool call working and conclude that `tool_choice: "tool"` should be used broadly for all tools, producing agents that silently skip reasoning narration.

Additionally, `tool_choice` with values other than `"auto"` and `"none"` is incompatible with extended thinking. If the project later adds an extended thinking demonstration, forced tool_choice will produce a hard API error that is confusing to debug.

**Why it happens:**
`tool_choice: "tool"` is taught as the way to guarantee structured output. The incompatibility with extended thinking is not surfaced until both features are combined.

**How to avoid:**
In notebooks, explicitly document when `tool_choice: "tool"` is and is not appropriate. Reserve forced tool choice for terminal actions where a structured handoff is the only acceptable output (escalation, formal refund submission). For intermediate tool calls (lookup, policy check), use `tool_choice: "auto"` and let Claude narrate its reasoning. Add a comment to every forced tool_choice usage: "# forced tool_choice — terminal structured output only, incompatible with extended thinking."

**Warning signs:**
- `tool_choice: "tool"` is used on `lookup_customer` or `check_policy` (non-terminal tools)
- No comment in the code explaining why forced tool_choice is used
- The agent never produces any text narration before tool calls
- Students report "the agent works but never explains what it's doing"

**Phase to address:** Phase 2 (Tool Design) — establish the forced vs. auto distinction in Notebook 02 tool design coverage.

---

### Pitfall 9: Simulated Services Return Deterministic Data That Makes Anti-Patterns Unobservable

**What goes wrong:**
In-memory simulated services always return the same customer data, the same policy results, and the same refund status regardless of input. This means the 5-tool focused agent and the 15-tool Swiss Army agent produce identical outputs for all test queries. The anti-pattern comparison produces no visible difference. Students conclude the patterns are equivalent.

**Why it happens:**
Simulated services are built for simplicity and correctness, not for exposing architectural failures. A `lookup_customer("CUS-001")` that always returns the same record is easy to build and test — but it cannot reveal tool selection errors because any tool called on any input returns plausible results.

**How to avoid:**
Build simulated services with input-sensitive behavior that exposes architectural failures:
- Policy checks that return different results based on customer tier (VIP vs. standard)
- Refund processing that validates amount constraints and returns explicit error states
- Customer lookups that return different account flags (closure pending, legal hold, VIP) to trigger different escalation paths
- An "ambiguous query" test set where the Swiss Army agent is statistically likely to call the wrong tool (e.g., a billing question where both `billing_management` and `process_refund` are plausible choices)

**Warning signs:**
- `lookup_customer` always returns the same hardcoded dictionary regardless of customer_id
- No test query exercises escalation via dollar threshold, account closure, and VIP tier separately
- The Swiss Army agent test suite produces identical results to the focused agent test suite
- No error states exist in the simulated services

**Phase to address:** Phase 1 (Simulated Services layer) — design the service layer to support observable anti-pattern behavior before building notebooks.

---

### Pitfall 10: API Costs Not Made Visible in Teaching Notebooks

**What goes wrong:**
Students run all 8 notebooks sequentially in a single session, accumulating real API costs they did not anticipate. The prompt caching demonstration (Notebook 05) is the most expensive: it makes multiple large-context requests to show cost reduction. Without explicit cost display in each notebook, students do not connect their API usage to charges, cannot see whether caching is actually working (requires reading `cache_read_input_tokens`), and may exhaust their API tier limits mid-session, breaking subsequent notebooks.

**Why it happens:**
Developers building teaching materials focus on conceptual clarity and do not instrument cost visibility because it feels like operational overhead rather than teaching content. Cost data is actually teaching content for CCA exam prep: the 90% reduction from caching vs. 50% from batch API is a core exam concept.

**How to avoid:**
Every notebook cell that calls the API must print usage stats in a standardized format after the response:

```python
def print_usage(response, label: str = "") -> None:
    u = response.usage
    prefix = f"[{label}] " if label else ""
    print(f"{prefix}Tokens: input={u.input_tokens}, output={u.output_tokens}, "
          f"cache_write={getattr(u, 'cache_creation_input_tokens', 0)}, "
          f"cache_read={getattr(u, 'cache_read_input_tokens', 0)}")
```

Use the cheapest model that demonstrates the pattern correctly (claude-haiku-3-5 for structural demos, claude-sonnet-4-5 for caching where token minimums apply). Notebooks 00-01 (structural patterns) should use Haiku. Notebook 05 (caching demo) must use a model that meets the minimum token threshold for caching.

**Warning signs:**
- No `usage` field printing in any notebook
- Prompt caching notebook uses `claude-haiku-3` (minimum token threshold is 4096 on older Haiku)
- No warning cell at the start of the caching notebook about expected cost
- Students cannot tell from the notebook output whether a cache hit occurred

**Phase to address:** Phase 0 (Notebook template) — add the `print_usage` helper and cost-visible pattern to the base template before any content notebook is written.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode customer data in tool functions | Removes need for service layer | Anti-pattern demos cannot produce observable failures; all agents look equivalent | Never — defeats teaching purpose |
| Single `messages` list mutated in place | Simple loop code | Tool results get appended out of order in parallel tool call scenarios; hard to debug | Never for production reference code; acceptable in first anti-pattern demo only |
| Print statements instead of `print_usage` helper | Fast to write | Cost and caching visibility disappears; students cannot observe caching behavior | Never for notebooks students run |
| Inline tool schemas as dicts | Fewer files | No type checking, easy to introduce schema errors that produce mysterious 400 errors | Never — use typed Pydantic-derived schemas |
| System prompt compliance rules only | Easy to write | Directly contradicts CCA exam guidance; students learn the wrong pattern | Never for compliance-critical rules |
| `tool_choice: "tool"` on all tools | Guarantees tool calls | Removes reasoning narration; incompatible with extended thinking | Only on terminal structured-output tools (escalation, formal refund) |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Anthropic Python SDK tool_result | Sending `{"type": "tool_result", "content": result}` without `tool_use_id` | Always include `tool_use_id` matching the assistant's `tool_use` block id |
| Prompt caching with tools | Changing tool definitions between requests invalidates cache | Keep tool definitions identical across all requests in a cached session |
| Parallel tool calls | Separate user messages for each tool result | All results for a single assistant turn in one user message content list |
| PostToolUse callback (raw SDK pattern) | Implementing as prompt injection ("System: the tool returned X") | Implement as Python function in the application layer that inspects tool results before passing them back |
| `cache_control` with images | Adding/removing images anywhere in the request | Keep image usage consistent; any change invalidates the cached prefix |
| Poetry + Jupyter | `poetry run jupyter notebook` fails to find kernel | Run `poetry run python -m ipykernel install --user --name=<name>` to register kernel |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Rebuilding full conversation history on every iteration | Slow notebook cells; context grows linearly with turns | Maintain messages list across loop iterations; only append new messages | Any session over 5 turns |
| No iteration cap on agentic loop | Notebook cell runs indefinitely; kernel must be interrupted | Always set `MAX_ITERATIONS = 25` as upper bound | When tool returns an error Claude tries to retry indefinitely |
| Prompt caching on short policy documents | `cache_creation_input_tokens = 0`; caching silently ignored | Verify policy documents exceed model's minimum token threshold (1024-2048 tokens depending on model) | Policy document under minimum token threshold |
| Tool responses returning full customer records | Context fills fast in multi-turn sessions | Return only fields relevant to the current decision | After 10+ turns with large tool responses |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| ANTHROPIC_API_KEY in notebook cell | Key committed to git, exposed in GitHub | Use `python-dotenv` with `.env` file in `.gitignore`; load with `os.getenv("ANTHROPIC_API_KEY")` |
| System prompt contains actual compliance rules as the only enforcement | Prompt injection can override compliance behavior | Programmatic checks in application layer; prompt provides context only |
| Tool error messages expose internal service state | Leaks implementation details visible in conversation history | Return user-facing error descriptions; log technical details separately |
| Agentic loop with no iteration cap | Runaway agent runs indefinitely, accumulating costs | Always set `MAX_ITERATIONS` guard; log when limit is reached |

---

## "Looks Done But Isn't" Checklist

- [ ] **Agentic loop:** Verify `stop_reason` is checked, not content type — run a query that generates a reasoning text block before a tool call and confirm the loop continues
- [ ] **Tool result format:** Verify tool_result blocks appear first in user message content — intentionally add a text block before a tool_result and confirm the API error appears in the anti-pattern demo
- [ ] **Prompt caching:** Verify `cache_read_input_tokens > 0` on the second request — `cache_creation_input_tokens` alone does not confirm working caching
- [ ] **PostToolUse enforcement:** Verify a $600 refund is blocked even when Claude's reasoning says it should approve — the programmatic check must fire regardless of model output
- [ ] **Escalation handoff:** Verify the `escalate_to_human` tool input contains all required Pydantic fields and no raw `messages` list
- [ ] **Simulated services:** Verify a VIP customer triggers escalation, a $600 refund triggers escalation, and an account closure triggers escalation — each via a separate test query
- [ ] **API key hygiene:** Verify `.env` is in `.gitignore` and no notebook cell contains the API key literal
- [ ] **Model selection:** Verify the prompt caching notebook uses a model whose cached prefix meets the minimum token threshold for that model
- [ ] **Swiss Army anti-pattern:** Verify the 15-tool agent produces at least one observable wrong tool call in the test suite — not just identical output to the 5-tool agent

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Agentic loop terminates on content type | LOW | Single-function fix in loop control; all notebooks using the loop fix automatically |
| Tool result format violations | LOW | Fix message history builder; existing conversation history may need reconstruction |
| Cache breakpoint on wrong block | LOW | Move cache_control marker; no data loss |
| Compliance in prompt only | MEDIUM | Add PostToolUse callback layer; test all escalation paths against callback, not prompt |
| Anti-pattern shows same output as correct pattern | HIGH | Redesign simulated services to be input-sensitive; requires rebuilding service layer and re-running all notebooks to verify observable differences |
| API key committed to git | HIGH | Rotate key immediately; clean git history with BFG Repo Cleaner; add pre-commit hook |
| All notebooks use expensive model | MEDIUM | Replace model strings throughout; re-run to verify output equivalence |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Agentic loop terminates on content type | Phase 1: Core Loop | Run a multi-tool query and verify loop continues past first text response |
| Tool result format violations | Phase 1: Core Loop | Intentionally trigger the error in anti-pattern demo; confirm correct format never triggers it |
| Cache breakpoint on wrong content | Phase 3: Prompt Caching | Check `cache_read_input_tokens > 0` on second request to same session |
| Compliance in prompt only | Phase 2: Callbacks and Enforcement | Unit test: $600 refund must be blocked even when Claude's reasoning approves it |
| Swiss Army anti-pattern not observable | Phase 1: Tool Design | Run 10-query test suite; Swiss Army agent must show at least one wrong tool call |
| Anti-pattern shown before pattern established | Phase 0: Notebook Template | Audit all notebooks: correct pattern prose and demo must precede anti-pattern section |
| Escalation handoff passes raw transcript | Phase 2: Escalation Design | Assert escalation tool input is EscalationHandoff type; assert no `messages` field present |
| Forced tool_choice overused | Phase 2: Tool Design | Audit all tool_choice usage; non-terminal tools must use "auto" |
| Simulated services not input-sensitive | Phase 1: Service Layer | Integration test: VIP, $600, account_closure each trigger separate escalation paths |
| API costs not visible | Phase 0: Notebook Template | Every API cell must print usage stats; verify `cache_read_input_tokens` is printed |

---

## Sources

- [How to implement tool use — Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — tool schema format, tool_result structure, parallel tool calls (HIGH confidence)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — cache_control placement, minimum token thresholds, TTL, verification via usage fields (HIGH confidence)
- [How the agent loop works — Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/agent-loop) — stop_reason as loop control signal (HIGH confidence)
- [Claude's agentic loop explained — DEV Community](https://dev.to/ajbuilds/claudes-agentic-loop-explained-stopreason-tooluse-and-the-pattern-behind-every-ai-agent-2l61) — stop_reason vs content-type anti-pattern (MEDIUM confidence)
- [Intercept and control agent behavior with hooks — Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/hooks) — PostToolUse, PreToolUse hook patterns (HIGH confidence)
- [Don't do this: Pitfalls in using anti-patterns in teaching — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0360131506001485) — cognitive load in anti-pattern pedagogy (MEDIUM confidence)
- [Tool choice — Claude API Docs cookbook](https://platform.claude.com/cookbook/tool-use-tool-choice) — tool_choice values and forced-tool behavior (HIGH confidence)
- [CCA Customer Support article — companion article](../../../articles/articles/cca-customer-support/work/final/article_publication_ready.md) — 6 CCA exam anti-patterns confirmed by exam scenario analysis (HIGH confidence, domain-specific)
- [Anthropic educational courses — GitHub](https://github.com/anthropics/courses) — Haiku model preference for teaching cost reduction (MEDIUM confidence)

---
*Pitfalls research for: Claude API tool-use agent teaching project (CCA Exam Prep)*
*Researched: 2026-03-25*
