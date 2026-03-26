# Phase 4: Caching and Context Notebooks - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Students observe prompt caching savings with concrete token numbers and compare structured context summaries against raw transcript bloat. Two notebooks (04, 05) demonstrate CCA cost optimization and context management patterns. Anti-pattern: Batch API for live support + no caching baseline. Correct: Prompt Caching with cache_control on static policy context.

Independent of Phase 3 (callbacks/enforcement). Both depend on Phase 2's core loop.

No handoff patterns (Phase 5). No coordinator-subagent (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Prompt caching strategy
- Add a large static POLICY_DOCUMENT (~2000 tokens) as a separate system message block with `cache_control: {"type": "ephemeral"}`
- System message becomes a list of content blocks: [AGENT_INSTRUCTIONS, POLICY_DOCUMENT(cached)]
- AGENT_INSTRUCTIONS: existing 31-line prompt (not cached — small, changes per agent variant)
- POLICY_DOCUMENT: detailed refund policies, tier limits, compliance rules (static — the cacheable content)
- `system_prompts.py` updated to support `get_system_prompt_with_caching()` returning the list-of-blocks format
- First call: `cache_creation_input_tokens > 0`, second call: `cache_read_input_tokens > 0`
- Students see the cost difference in print_usage between cached and uncached runs

### Cost anti-pattern (Notebook 04)
- Both demos in one notebook:
  1. Batch API trap: markdown explanation of why Batch API is wrong for live support (24h latency, NOT ZDR-eligible). CCA Exam Tip box. No code execution needed — this is a conceptual lesson.
  2. Cached vs uncached comparison: run the same scenario twice — once with plain string system prompt (no caching), once with cache_control blocks. Show token accounting difference with print_usage and compare_results.
- CCA exam lesson: "Someone waiting? → Real-Time API + Prompt Caching. Batch API is ALWAYS wrong for live support."

### Context management approach
- New `agent/context_manager.py` module with `ContextSummary` class
- Fixed-field JSON summary: customer_id, issue_type, tools_called (names only), decisions_made (short bullets), pending_actions, turn_count, token_estimate
- `update(tool_name, result_summary)` method — called after each tool dispatch
- `to_system_context()` method — returns structured text for injection into system message
- Self-tracking token estimate — compacts if over budget
- Stays under a fixed token budget while raw transcript grows unbounded

### Context anti-pattern (raw_transcript.py)
- Anti-pattern: append every user message, assistant response, and tool result as raw text. Pass full transcript as context.
- Observable failure: token count grows linearly per turn. After 5-6 turns, important early facts get buried (lost-in-middle effect).
- Correct: ContextSummary stays bounded, key facts preserved in structured fields.
- CCA exam lesson: bigger context window makes degradation worse, not better. Structured summaries beat raw transcripts.

### Notebook demo scenarios
- **NB04 (Cost Optimization)**: Normal multi-turn refund case with deliberately long static policy block. NOT a tricky business-rule case. Students see:
  - Turn 1: cache write (cache_creation_input_tokens > 0)
  - Turn 2+: cache read (cache_read_input_tokens > 0)
  - Cumulative cost comparison: cached vs uncached
  - Relative outcomes, not magic constants
- **NB05 (Context Management)**: 5-6 turn conversation where one important fact appears early and gets buried later.
  - Avoid VIP/legal/closure triggers — don't let callbacks distract from the context lesson
  - Use C001 (regular happy path) with a multi-turn scenario
  - Students see: transcript tokens grow each turn, summary stays bounded, key facts remain preserved
  - Anti-pattern (raw): early fact lost by turn 5-6
  - Correct (summary): early fact preserved in structured fields

### Verification rules (behavior-first)
- Test the ACTUAL token accounting, not just that print_usage was called
- Verify cache_read_input_tokens > 0 on second call (behavioral proof)
- Verify ContextSummary token_estimate stays under budget after N updates (behavioral proof)
- Every completion claim maps to a test: "Claim" → "test name"

### Claude's Discretion
- Exact policy document content (~2000 tokens of refund/compliance policy text)
- ContextSummary compaction strategy when over budget
- Multi-turn scenario message sequence for NB05
- Notebook markdown wording and CCA exam tip text
- Whether to use a helper for multi-turn simulation or manual cell-by-cell

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CCA certification rules (HIGHEST PRIORITY)
- `.planning/CCA-RULES.md` — Token economics table, Batch API vs Real-Time decision framework, prompt caching rules, lost-in-middle effect, context degradation

### Source articles
- `/Users/richardhightower/articles/articles/cca-customer-support/work/final/article_publication_ready.md` — Cost optimization patterns, prompt caching vs Batch API
- `/Users/richardhightower/articles/articles/cca-code-generation/work/final/article_publication_ready.md` — Context degradation, per-file focused passes, lost-in-middle

### Project standards
- `.claude/CLAUDE.md` — Verification rules: test stores not responses, behavior-first
- `CLAUDE.md` (root) — Architecture, data flow

### Phase 2 outputs (build on these)
- `src/customer_service/agent/system_prompts.py` — Current system prompt to extend with caching
- `src/customer_service/agent/agent_loop.py` — UsageSummary already tracks cache tokens
- `notebooks/helpers.py` — print_usage already shows cache tokens + cost

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `system_prompts.py` (31 lines) — `get_system_prompt()` returns plain string. Needs new `get_system_prompt_with_caching()` returning list-of-blocks format
- `agent_loop.py` — passes `system=system_prompt` to `client.messages.create()`. Accepts string or list — Anthropic SDK handles both
- `UsageSummary` — already tracks `cache_read_input_tokens`, `cache_creation_input_tokens`
- `print_usage` in helpers.py — already displays cache tokens and cost estimate
- `compare_results` — ready for cached vs uncached comparison
- 6 seed scenarios in `data/scenarios.py` — C001 happy path available for NB05

### Established Patterns
- Notebook template: Setup > Anti-Pattern (red) > Correct (green) > Compare
- CCA Exam Tip boxes as highlighted blockquotes
- Anti-patterns in `anti_patterns/` directory only

### Integration Points
- `system_prompts.py` — add `get_system_prompt_with_caching()` and `POLICY_DOCUMENT` constant
- `agent/context_manager.py` — new module
- `anti_patterns/raw_transcript.py` — new anti-pattern (Batch API explanation + raw transcript demo)
- `anti_patterns/batch_api_live.py` — new anti-pattern (conceptual, no live Batch API call needed)
- `notebooks/` — add 04_cost_optimization.ipynb, 05_context_management.ipynb

</code_context>

<specifics>
## Specific Ideas

- The POLICY_DOCUMENT should be substantial (~2000 tokens) to ensure it crosses the minimum caching threshold. If it's too short, caching won't activate and the demo fails silently.
- Multi-turn simulation for NB05 can be a simple loop: predefined list of user messages, each processed through the agent loop, with token accounting displayed after each turn.
- The "important early fact" in NB05 should be something concrete that Claude needs to reference later — e.g., "customer mentioned their order was a gift for their mother's birthday" and then 5 turns later the resolution should reference this.

</specifics>

<deferred>
## Deferred Ideas

- Structured escalation handoff with tool_choice enforcement — Phase 5
- Coordinator-subagent pattern — Phase 5
- Streamlit UI — still TBD

</deferred>

---

*Phase: 04-caching-and-context-notebooks*
*Context gathered: 2026-03-26*
