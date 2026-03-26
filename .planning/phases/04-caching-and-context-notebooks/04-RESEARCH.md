# Phase 4: Caching and Context Notebooks - Research

**Researched:** 2026-03-26
**Domain:** Anthropic prompt caching API, structured context management, Python package design
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Prompt caching strategy:**
- Add a large static POLICY_DOCUMENT (~2000 tokens) as a separate system message block with `cache_control: {"type": "ephemeral"}`
- System message becomes a list of content blocks: [AGENT_INSTRUCTIONS, POLICY_DOCUMENT(cached)]
- AGENT_INSTRUCTIONS: existing 31-line prompt (not cached — small, changes per agent variant)
- POLICY_DOCUMENT: detailed refund policies, tier limits, compliance rules (static — the cacheable content)
- `system_prompts.py` updated to support `get_system_prompt_with_caching()` returning the list-of-blocks format
- First call: `cache_creation_input_tokens > 0`, second call: `cache_read_input_tokens > 0`
- Students see the cost difference in print_usage between cached and uncached runs

**Cost anti-pattern (Notebook 04):**
- Both demos in one notebook:
  1. Batch API trap: markdown explanation of why Batch API is wrong for live support (24h latency, NOT ZDR-eligible). CCA Exam Tip box. No code execution needed.
  2. Cached vs uncached comparison: run the same scenario twice — once with plain string system prompt (no caching), once with cache_control blocks. Show token accounting difference with print_usage and compare_results.
- CCA exam lesson: "Someone waiting? → Real-Time API + Prompt Caching. Batch API is ALWAYS wrong for live support."

**Context management approach:**
- New `agent/context_manager.py` module with `ContextSummary` class
- Fixed-field JSON summary: customer_id, issue_type, tools_called (names only), decisions_made (short bullets), pending_actions, turn_count, token_estimate
- `update(tool_name, result_summary)` method — called after each tool dispatch
- `to_system_context()` method — returns structured text for injection into system message
- Self-tracking token estimate — compacts if over budget
- Stays under a fixed token budget while raw transcript grows unbounded

**Context anti-pattern (raw_transcript.py):**
- Anti-pattern: append every user message, assistant response, and tool result as raw text. Pass full transcript as context.
- Observable failure: token count grows linearly per turn. After 5-6 turns, important early facts get buried (lost-in-middle effect).
- Correct: ContextSummary stays bounded, key facts preserved in structured fields.

**Notebook demo scenarios:**
- NB04 (Cost Optimization): Normal multi-turn refund case with deliberately long static policy block
- NB05 (Context Management): 5-6 turn conversation where one important fact appears early and gets buried later. Use C001 (regular happy path)

**Verification rules:**
- Test the ACTUAL token accounting, not just that print_usage was called
- Verify cache_read_input_tokens > 0 on second call (behavioral proof)
- Verify ContextSummary token_estimate stays under budget after N updates (behavioral proof)

### Claude's Discretion
- Exact policy document content (~2000 tokens of refund/compliance policy text)
- ContextSummary compaction strategy when over budget
- Multi-turn scenario message sequence for NB05
- Notebook markdown wording and CCA exam tip text
- Whether to use a helper for multi-turn simulation or manual cell-by-cell

### Deferred Ideas (OUT OF SCOPE)
- Structured escalation handoff with tool_choice enforcement — Phase 5
- Coordinator-subagent pattern — Phase 5
- Streamlit UI — still TBD
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OPTIM-01 | Prompt caching with `cache_control` markers on static policy context and token accounting | SDK verified: `TextBlockParam.cache_control` field confirmed in anthropic 0.86.0; `Usage` fields `cache_creation_input_tokens` and `cache_read_input_tokens` confirmed present in project SDK |
| OPTIM-02 | Context management with structured JSON summaries | Pattern: fixed-field Pydantic model or dataclass; `to_system_context()` renders structured text; compaction when over budget |
| ANTI-04 | Raw transcript context anti-pattern (no structured summaries) | New `anti_patterns/raw_transcript.py` demonstrating growing transcript + lost-in-middle effect |
| NB-05 | Notebook 04 — Cost optimization pattern (prompt caching vs Batch API misuse) | Single notebook: Batch API explanation (markdown only) + cached vs uncached comparison with real token accounting |
| NB-06 | Notebook 05 — Context management pattern (structured summaries vs raw transcript) | 5-6 turn C001 happy path conversation; anti-pattern shows token growth; correct shows bounded summary |
</phase_requirements>

---

## Summary

Phase 4 builds on the complete Phase 2 agent loop to add two CCA-critical capabilities: prompt caching for cost optimization and structured context management to prevent lost-in-middle degradation. The Anthropic SDK (version 0.86.0, required `>=0.42.0`) fully supports both patterns via native types without beta headers.

The key SDK facts are: (1) `messages.create(system=...)` accepts `Union[str, Iterable[TextBlockParam]]`, where each `TextBlockParam` can carry `cache_control: {"type": "ephemeral"}`; (2) the `Usage` object in 0.86.0 has `cache_creation_input_tokens` and `cache_read_input_tokens` as first-class optional fields — these match the fields already tracked in `UsageSummary` and displayed by `print_usage`; (3) **the minimum cacheable token threshold for `claude-sonnet-4-6` is 2048 tokens** — the CONTEXT.md target of "~2000 tokens" is at risk of falling below the threshold and failing silently.

The `ContextSummary` class is a pure Python addition with no new library dependencies. Token estimation is lightweight: the `len(text) // 4` heuristic is sufficient for budget-gating; no tiktoken or SDK counting call is needed for the demo. Both notebooks follow the established template (Setup > Anti-Pattern > Correct > Compare) and reuse `print_usage`, `compare_results`, and seed customer C001.

**Primary recommendation:** Size POLICY_DOCUMENT to at least 2200 tokens (approximately 8800 characters / 1600 words) to guarantee the minimum caching threshold for `claude-sonnet-4-6`, with a margin of ~150 tokens above the 2048 limit.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.42.0 (project has 0.86.0) | Prompt caching API, Usage fields | Native `TextBlockParam.cache_control` + first-class `Usage.cache_creation_input_tokens` |
| pydantic | >=2.0 | ContextSummary data model (or dataclass) | Existing project standard; all data models use pydantic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tabulate | >=0.9 | compare_results table output | Already used in helpers.py |
| python-dotenv | >=1.0 | Load ANTHROPIC_API_KEY in notebooks | Already used in all notebooks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `len(text) // 4` token estimate | tiktoken / `client.count_tokens()` | tiktoken adds a dependency; SDK counting costs an API call. For a budget gate in a teaching demo, the character heuristic is accurate enough (~10% error acceptable) |
| Pydantic model for ContextSummary | Plain dataclass | Pydantic adds validation; plain dataclass is simpler and sufficient since no external input parsing needed |

**Installation:** No new dependencies needed. All required packages are already in pyproject.toml.

**Version verification (confirmed 2026-03-26):**
```bash
# In project venv:
poetry run python -c "import anthropic; print(anthropic.__version__)"
# Output: 0.86.0
```

---

## Architecture Patterns

### Recommended Project Structure (Phase 4 additions)

```
src/customer_service/
├── agent/
│   ├── system_prompts.py       # ADD: get_system_prompt_with_caching(), POLICY_DOCUMENT
│   └── context_manager.py      # NEW: ContextSummary class
├── anti_patterns/
│   ├── raw_transcript.py       # NEW: raw transcript accumulator anti-pattern
│   └── batch_api_live.py       # NEW: conceptual explanation (no live calls)
notebooks/
├── 04_cost_optimization.ipynb  # NEW: NB-05
└── 05_context_management.ipynb # NEW: NB-06
tests/
└── test_caching.py             # NEW: OPTIM-01, OPTIM-02 behavioral tests
```

### Pattern 1: System Prompt as List of Content Blocks with Cache Control

**What:** Pass `system` as a list of `TextBlockParam` dicts rather than a plain string. Place `cache_control: {"type": "ephemeral"}` on the LAST static block to create a cache breakpoint.

**When to use:** Whenever a large static section (policy docs, tool docs, reference data) is sent on every request.

**Example:**
```python
# Source: anthropic-sdk-python/src/anthropic/types/text_block_param.py (confirmed 0.86.0)
# Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

POLICY_DOCUMENT = """[2200+ token policy text here]"""

def get_system_prompt_with_caching() -> list[dict]:
    """Return system prompt as list-of-blocks with cache_control on static policy.

    Block 0: AGENT_INSTRUCTIONS — not cached (small, may vary per agent variant)
    Block 1: POLICY_DOCUMENT — cached (large, static across all requests)
    """
    return [
        {
            "type": "text",
            "text": get_system_prompt(),  # existing 31-line instructions
        },
        {
            "type": "text",
            "text": POLICY_DOCUMENT,
            "cache_control": {"type": "ephemeral"},  # "ephemeral" is only supported type
        },
    ]
```

**Integration with agent_loop.py:**

The `run_agent_loop` signature already accepts `system_prompt: str`. To support both string and list-of-blocks, either:
- Option A: Widen type hint to `system_prompt: str | list[dict]` (no logic change needed — SDK handles both)
- Option B: Add separate `run_agent_loop_with_caching()` wrapper for notebook clarity

Option A is preferred — `client.messages.create(system=...)` natively accepts `Union[str, Iterable[TextBlockParam]]`.

### Pattern 2: Reading Cache Token Fields from Usage

**What:** The `Usage` object in anthropic 0.86.0 has `cache_creation_input_tokens` and `cache_read_input_tokens` as `Optional[int]`. The existing `agent_loop.py` already reads these with `getattr(..., 0) or 0` defensive access — this is correct and will work with both 0.40.x (no fields) and 0.86.0 (fields present).

**Key insight on input_tokens accounting:**

```
# Total tokens sent in a request =
total = input_tokens + cache_read_input_tokens + cache_creation_input_tokens

# input_tokens = ONLY tokens after the last cache breakpoint (not cached portion)
# cache_creation_input_tokens = tokens being written to cache (first call)
# cache_read_input_tokens = tokens served from cache (subsequent calls)

# print_usage in helpers.py already implements this correctly:
total = inp + out + cr + cw   # inp = uncached input only
```

**Cost accounting already correct in helpers.py** — verified against official docs.

### Pattern 3: ContextSummary Class

**What:** A fixed-schema summary that grows at O(1) not O(n) per turn. Updated after each tool dispatch, injected into system message at turn start.

**When to use:** Multi-turn conversations (3+ turns) where critical early facts must survive attention dilution.

**Example:**
```python
# Source: CCA-RULES.md + 04-CONTEXT.md decisions

from dataclasses import dataclass, field

TOKEN_BUDGET = 300  # characters heuristic / 4 ≈ 75 tokens — fits in system block

@dataclass
class ContextSummary:
    """Structured session context for multi-turn agent conversations.

    CCA Rule: structured summaries beat raw transcripts for context preservation.
    Fixed fields prevent unbounded growth; token_estimate enables budget gating.
    """
    customer_id: str = ""
    issue_type: str = ""
    tools_called: list[str] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)
    turn_count: int = 0
    token_estimate: int = 0

    def update(self, tool_name: str, result_summary: str) -> None:
        """Record one tool dispatch. Compacts decisions_made if over budget."""
        self.tools_called.append(tool_name)
        self.decisions_made.append(result_summary)
        self.turn_count += 1
        self._update_token_estimate()
        if self.token_estimate > TOKEN_BUDGET:
            self._compact()

    def to_system_context(self) -> str:
        """Render structured text for injection into system message."""
        return (
            f"SESSION CONTEXT:\n"
            f"Customer: {self.customer_id} | Issue: {self.issue_type}\n"
            f"Turn: {self.turn_count} | Tools used: {', '.join(self.tools_called[-5:])}\n"
            f"Decisions: {'; '.join(self.decisions_made[-3:])}\n"
            f"Pending: {'; '.join(self.pending_actions)}"
        )

    def _update_token_estimate(self) -> None:
        self.token_estimate = len(self.to_system_context()) // 4

    def _compact(self) -> None:
        """Keep only most recent decisions when over budget."""
        self.decisions_made = self.decisions_made[-2:]
        self._update_token_estimate()
```

### Pattern 4: Raw Transcript Anti-Pattern (ANTI-04)

**What:** Append every message + tool result as raw text. Pass as `context` string.

```python
# src/customer_service/anti_patterns/raw_transcript.py
class RawTranscriptContext:
    """Anti-pattern: unbounded raw transcript accumulator.

    Demonstrates: O(n) token growth per turn, lost-in-middle effect.
    CCA Exam: bigger context window makes degradation WORSE, not better.
    """
    def __init__(self):
        self.transcript: str = ""

    def append(self, role: str, content: str) -> None:
        self.transcript += f"\n[{role.upper()}]: {content}"

    def to_context_string(self) -> str:
        return f"CONVERSATION HISTORY:\n{self.transcript}"

    def token_estimate(self) -> int:
        return len(self.transcript) // 4
```

### Anti-Patterns to Avoid

- **cache_control on the first block only:** The cache breakpoint marks the LAST cacheable block. Putting `cache_control` on the AGENT_INSTRUCTIONS block (block 0) and not on POLICY_DOCUMENT (block 1) means the shorter instructions block gets cached, not the large policy — defeating the purpose.
- **POLICY_DOCUMENT below 2048 tokens for claude-sonnet-4-6:** Caching silently does not activate. `cache_creation_input_tokens` will be 0 even though `cache_control` is set. No error is raised.
- **Checking `cache_creation_input_tokens` on the same request where the cache is read:** A single request either writes OR reads from cache, not both for the same breakpoint.
- **Passing `system` as a list on the anti-pattern path:** The uncached comparison in NB04 must use the plain string form to demonstrate the cost difference.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cache token display | Custom formatter | `print_usage` in helpers.py | Already handles cr/cw conditional display |
| Side-by-side comparison | Custom table | `compare_results` in helpers.py | Already handles numeric % delta |
| Token counting | tiktoken integration | `len(text) // 4` heuristic | Sufficient for budget-gating; adding tiktoken adds a new dependency |
| Multi-turn message loop | Hand-rolled recursion | Simple `for msg in messages:` loop with `run_agent_loop` | The loop already handles iterative tool calls per turn |

**Key insight:** The entire caching infrastructure (usage tracking, display, comparison) already exists in Phase 2 outputs. Phase 4 only adds the `cache_control` marker on the system prompt block.

---

## Common Pitfalls

### Pitfall 1: POLICY_DOCUMENT Below Minimum Token Threshold

**What goes wrong:** `cache_control` is set correctly in code, but `cache_creation_input_tokens` remains 0 on every call. The demo appears broken — students see no caching savings.

**Why it happens:** `claude-sonnet-4-6` requires **2048 tokens minimum** in the cached block. A document under this threshold is silently not cached. No API error is raised.

**How to avoid:** Target 2200+ tokens (approximately 8800 characters / 1600 words of prose) to ensure a safe margin. The `POLICY_DOCUMENT` should include: tier definitions, per-tier refund limits, return windows, damage categories, compliance requirements, edge cases. This content is naturally substantial when fully detailed.

**Warning signs:** `cache_creation_input_tokens == 0` on the first API call despite correct `cache_control` syntax.

### Pitfall 2: Double-Counting Input Tokens

**What goes wrong:** Student or code sums `input_tokens + cache_read_input_tokens + cache_creation_input_tokens + output_tokens` and gets the wrong total cost.

**Why it happens:** `input_tokens` in the API response is ONLY the tokens after the last cache breakpoint (the uncached portion). It does NOT include cached tokens. `cache_read_input_tokens` and `cache_creation_input_tokens` count the cached portion separately.

**How to avoid:** Total cost = `(input_tokens * INPUT_PRICE) + (cache_read * READ_PRICE) + (cache_creation * WRITE_PRICE) + (output * OUTPUT_PRICE)`. The existing `helpers.py` already does this correctly.

**Warning signs:** Total cost appears lower than uncached on turn 1 (cache write is 1.25x, not cheaper).

### Pitfall 3: Cache Expires Between NB04 Demo Turns

**What goes wrong:** The demo runs cached and uncached scenarios, but the 5-minute TTL expires before the second call, so `cache_read_input_tokens` shows 0 unexpectedly.

**Why it happens:** Default cache TTL is 5 minutes for `{"type": "ephemeral"}`. A slow notebook execution can let it expire.

**How to avoid:** Run the cached scenario turn 1 and turn 2 in rapid succession within the same kernel session. The demo comparison should run both calls within seconds.

**Warning signs:** `cache_read_input_tokens == 0` on what should be the cached second call.

### Pitfall 4: System Parameter Type Mismatch in Tests

**What goes wrong:** Existing tests pass `system_prompt: str` but new caching tests pass `list[dict]`. If the test helper enforces the string type, tests fail unexpectedly.

**Why it happens:** `run_agent_loop` currently type-hints `system_prompt: str`. The SDK accepts `Union[str, Iterable[TextBlockParam]]` but the Python type checker flags the mismatch.

**How to avoid:** Update the `system_prompt` parameter type hint to `str | list[dict]` in `run_agent_loop`. No logic change needed — just the annotation. Add a test that passes the list-of-blocks form and verifies `client.messages.create` received it correctly.

### Pitfall 5: ContextSummary Token Estimate Drift

**What goes wrong:** `token_estimate` drifts out of sync with actual `to_system_context()` output because a field is updated without calling `_update_token_estimate()`.

**Why it happens:** If `customer_id` or `issue_type` is set directly (bypassing `update()`), the estimate won't refresh.

**How to avoid:** Call `_update_token_estimate()` in every mutating method. Test specifically: assert `token_estimate == len(summary.to_system_context()) // 4` after every operation in test suite.

---

## Code Examples

Verified patterns from official sources and installed SDK:

### Correct: System as List-of-Blocks with Cache Control

```python
# Source: anthropic SDK 0.86.0 TextBlockParam definition + official docs
# system= accepts Union[str, Iterable[TextBlockParam]]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": "You are a customer support agent...",
            # No cache_control — small block, not worth caching
        },
        {
            "type": "text",
            "text": POLICY_DOCUMENT,  # must be >= 2048 tokens for claude-sonnet-4-6
            "cache_control": {"type": "ephemeral"},
            # Optional ttl: "5m" (default) or "1h"
        },
    ],
    tools=TOOLS,
    messages=messages,
)
```

### Reading Cache Usage Fields

```python
# Source: anthropic SDK 0.86.0 Usage class
# Fields: input_tokens (int), output_tokens (int),
#         cache_creation_input_tokens (Optional[int]),
#         cache_read_input_tokens (Optional[int])

# Defensive access (works for both 0.40.x and 0.86.0):
cr = getattr(response.usage, "cache_read_input_tokens", 0) or 0
cw = getattr(response.usage, "cache_creation_input_tokens", 0) or 0

# In 0.86.0, both fields are present directly:
cr = response.usage.cache_read_input_tokens or 0
cw = response.usage.cache_creation_input_tokens or 0
```

### Uncached Baseline (Anti-Pattern Path for NB04)

```python
# Pass system as plain string — no caching
response_uncached = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=get_system_prompt(),  # returns str, not list
    tools=TOOLS,
    messages=messages,
)
# cache_read_input_tokens will be 0 or None
# All tokens charged at full input rate
```

### NB04 Comparison Pattern

```python
# Run same scenario twice, show token accounting difference
from notebooks.helpers import compare_results

uncached_result = run_agent_loop(client, services, msg, get_system_prompt(), ...)
cached_result_turn1 = run_agent_loop(client, services, msg, get_system_prompt_with_caching(), ...)
cached_result_turn2 = run_agent_loop(client, services, msg, get_system_prompt_with_caching(), ...)

compare_results(
    {
        "input_tokens": uncached_result.usage.input_tokens,
        "cache_creation": uncached_result.usage.cache_creation_input_tokens,
        "cache_read": uncached_result.usage.cache_read_input_tokens,
    },
    {
        "input_tokens": cached_result_turn2.usage.input_tokens,
        "cache_creation": cached_result_turn2.usage.cache_creation_input_tokens,
        "cache_read": cached_result_turn2.usage.cache_read_input_tokens,
    },
)
```

### Mock for Caching Tests (extends existing _make_usage pattern)

```python
# Source: tests/test_agent_loop.py — _make_usage pattern (extend for caching)
from types import SimpleNamespace

def _make_usage_with_cache(inp=100, out=50, cr=500, cw=0):
    """Mock usage object with cache fields populated."""
    return SimpleNamespace(
        input_tokens=inp,
        output_tokens=out,
        cache_read_input_tokens=cr,
        cache_creation_input_tokens=cw,
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Beta header required for caching (`anthropic-beta: prompt-caching-2024-07-31`) | Native `cache_control` field in `TextBlockParam` (no beta header needed) | SDK 0.42+ / late 2024 | No beta flag needed — use `TextBlockParam.cache_control` directly |
| `Usage` cache fields only in beta types (`PromptCachingBetaUsage`) | `Usage` has `cache_creation_input_tokens` and `cache_read_input_tokens` as first-class optional fields | SDK 0.42+ | Existing `UsageSummary` in `agent_loop.py` already reads them correctly |
| Only 5-minute cache TTL | `ttl: "5m"` or `ttl: "1h"` supported | Added post-launch | 1h TTL useful for longer sessions; 5m default is fine for notebook demos |

**Deprecated/outdated:**
- Beta header `anthropic-beta: prompt-caching-2024-07-31`: no longer required. The installed SDK (0.86.0) does not need it. Do NOT add it.
- `PromptCachingBetaUsage` / `PromptCachingBetaMessageParam`: these beta types still exist in the SDK for backward compat but are not needed for new code.

---

## Open Questions

1. **POLICY_DOCUMENT token target: "~2000" vs 2048 minimum**
   - What we know: `claude-sonnet-4-6` requires minimum 2048 tokens. CONTEXT.md says "~2000 tokens."
   - What's unclear: This is ambiguous — 2000 < 2048, so "~2000" may silently fail.
   - Recommendation: **Target 2200 tokens (approximately 8800 characters)**. Document this as a teaching point in the notebook: "We size this deliberately above the 2048-token minimum required for caching to activate on claude-sonnet-4-6."

2. **run_agent_loop system_prompt type signature**
   - What we know: Currently `system_prompt: str`. The SDK accepts `Union[str, Iterable[TextBlockParam]]`.
   - What's unclear: Whether to widen the type or add a separate function.
   - Recommendation: Widen to `str | list[dict]` — minimal change, preserves all existing callers. The type hint update is the only code change; SDK already handles both.

3. **NB05 multi-turn helper vs manual cells**
   - What we know: CONTEXT.md leaves this to Claude's discretion.
   - What's unclear: Whether a `simulate_conversation(client, services, messages)` helper aids or obscures teaching.
   - Recommendation: Manual cell-by-cell — more explicit for teaching. Each turn in its own cell with `print_usage` output makes the token growth visible step by step. A helper can be in a setup cell but the per-turn loop should be visible.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `poetry run pytest tests/test_caching.py -x` |
| Full suite command | `poetry run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPTIM-01 | `get_system_prompt_with_caching()` returns list with 2 blocks, second has `cache_control` | unit | `poetry run pytest tests/test_caching.py::TestSystemPromptCaching -x` | ❌ Wave 0 |
| OPTIM-01 | Mock client: `cache_creation_input_tokens > 0` when caching system used (first call) | unit | `poetry run pytest tests/test_caching.py::TestCacheTokenAccounting::test_cache_write_on_first_call -x` | ❌ Wave 0 |
| OPTIM-01 | Mock client: `cache_read_input_tokens > 0` when same system used (second call) | unit | `poetry run pytest tests/test_caching.py::TestCacheTokenAccounting::test_cache_read_on_second_call -x` | ❌ Wave 0 |
| OPTIM-01 | `UsageSummary` accumulates `cache_read_input_tokens` across iterations correctly | unit | `poetry run pytest tests/test_caching.py::TestUsageAccumulation -x` | ❌ Wave 0 |
| OPTIM-02 | `ContextSummary.update()` increments `turn_count` and appends to `tools_called` | unit | `poetry run pytest tests/test_caching.py::TestContextSummary::test_update -x` | ❌ Wave 0 |
| OPTIM-02 | `ContextSummary.token_estimate` stays under TOKEN_BUDGET after N updates | unit | `poetry run pytest tests/test_caching.py::TestContextSummary::test_budget_enforcement -x` | ❌ Wave 0 |
| OPTIM-02 | `ContextSummary.token_estimate == len(summary.to_system_context()) // 4` (estimate is accurate) | unit | `poetry run pytest tests/test_caching.py::TestContextSummary::test_estimate_accuracy -x` | ❌ Wave 0 |
| ANTI-04 | `RawTranscriptContext.token_estimate()` grows with each append (demonstrates O(n)) | unit | `poetry run pytest tests/test_caching.py::TestRawTranscriptAntiPattern -x` | ❌ Wave 0 |
| NB-05, NB-06 | Notebooks execute without raising errors (smoke test) | smoke | `poetry run pytest tests/test_notebooks.py -x` (already exists, extend it) | ✅ (extend) |

### Sampling Rate
- **Per task commit:** `poetry run pytest tests/test_caching.py -x`
- **Per wave merge:** `poetry run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_caching.py` — covers OPTIM-01, OPTIM-02, ANTI-04 (all tests listed above)
- [ ] `src/customer_service/agent/context_manager.py` — implementation needed before tests pass
- [ ] `src/customer_service/agent/system_prompts.py` — `get_system_prompt_with_caching()` function
- [ ] `src/customer_service/anti_patterns/raw_transcript.py` — `RawTranscriptContext` class

Note: `conftest.py` already provides `services` fixture; `_make_usage` pattern from `test_agent_loop.py` covers mock client setup. No new fixture infrastructure needed.

---

## Sources

### Primary (HIGH confidence)
- anthropic SDK 0.86.0 installed in project venv — `TextBlockParam`, `CacheControlEphemeralParam`, `Usage` source files read directly
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching — minimum token thresholds, cache_control format, Usage fields, pricing multipliers
- anthropic-sdk-python GitHub `src/anthropic/types/message_create_params.py` — `system: Union[str, Iterable[TextBlockParam]]` type confirmed

### Secondary (MEDIUM confidence)
- https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/types/text_block_param.py — `cache_control: Optional[CacheControlEphemeralParam]` field confirmed in latest SDK main branch

### Tertiary (LOW confidence — not needed, all critical facts verified from primary sources)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — SDK version confirmed (0.86.0), types read from installed package, official docs consulted
- Architecture: HIGH — patterns derived from verified SDK types + existing code patterns + CONTEXT.md locked decisions
- Pitfalls: HIGH for token threshold (verified against official docs); MEDIUM for cache expiry TTL behavior (single source)

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (SDK types are stable; prompt caching is GA; pricing may change)
