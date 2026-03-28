# Phase 5: Handoffs, Integration, and Student Polish - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Structured escalation handoffs via `tool_choice` enforcement, coordinator-subagent pattern for complex queries, integration notebook (07) touching all 6 CCA patterns in one scenario, and student TODO placeholders for hands-on learning. Two new notebooks (06 handoffs, 07 integration). One new anti-pattern (raw_handoff.py).

No new models/services. No new escalation rules. No CI/CD (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Structured handoff via tool_choice enforcement
- When callback blocks a refund (returns `action_required: escalate_to_human`), the agent loop detects this and re-calls Claude with `tool_choice={"type": "tool", "name": "escalate_to_human"}`
- Claude is FORCED to call `escalate_to_human` with EscalationRecord fields (customer_id, customer_tier, issue_type, escalation_reason, recommended_action, conversation_summary, turns_elapsed)
- This produces structured JSON handoff output — the CCA-correct pattern
- Modify `agent_loop.py` to detect blocked results and issue the forced tool_choice call
- The escalate_to_human handler already returns JSON string matching EscalationRecord format

### Raw handoff anti-pattern (raw_handoff.py)
- Anti-pattern dumps the entire messages array as raw text to the human agent
- Human agent gets 2000+ tokens of raw conversation including tool_use/tool_result blocks
- Observable failure: human has to scroll through turns of API artifacts to find the actual issue
- Correct pattern: clean EscalationRecord JSON with key fields at top
- Scenario: C003 $600 refund (same as NB01, NB03) — consistent teaching scenario

### Coordinator-subagent pattern
- CCA rule: subagents do NOT inherit coordinator context — everything must be explicitly passed
- CCA rule: subagents never communicate directly — all through coordinator
- Implement `agent/coordinator.py` with a coordinator that routes complex multi-topic queries to specialized subagents
- Demo: a customer message that spans refund + shipping + account question — coordinator decomposes and delegates
- Each subagent gets only its relevant context (not full conversation)
- Coordinator assembles results and responds to customer
- This is the CCA answer for "agent has 15+ tools" — split into specialized subagents instead

### Integration notebook (07) scenario
- Single scenario that touches all 6 CCA patterns in sequence:
  1. Escalation: $600 refund triggers callback (Pattern 1)
  2. Compliance: PII in customer message gets redacted (Pattern 2)
  3. Tool design: 5 focused tools used (Pattern 3 — demonstrated by NOT using 15)
  4. Context: ContextSummary tracks key facts across turns (Pattern 4)
  5. Cost: Prompt caching active with cache_read tokens visible (Pattern 5)
  6. Handoffs: tool_choice forces structured EscalationRecord (Pattern 6)
- Use C003 ($600 refund) + PII in message to trigger patterns 1, 2, and 6
- Multi-turn to show pattern 4 (context management)
- Show token accounting throughout for pattern 5
- Each pattern gets its own markdown section with CCA Exam Tip

### Student TODO placeholders
- At least 3 TODOs across notebooks that students can complete without breaking execution
- Good TODOs: implement a new escalation rule, add a new customer profile, write a custom callback
- Bad TODOs: boilerplate, config changes, copy-paste
- Each TODO has: clear description of what to build, expected behavior, hints
- Notebooks must still run if TODOs are left unfilled (use try/except or conditional checks)

### Notebook 06 (Handoffs)
- Template: Setup > Anti-Pattern (raw dump) > Correct (tool_choice structured) > Compare
- Scenario: C003 $600 refund
- Anti-pattern shows raw messages dump with tool_use artifacts
- Correct shows clean EscalationRecord JSON
- Compare: side-by-side token count (raw dump >> structured) + readability
- CCA Exam Tip: "Structured JSON handoffs, not raw conversation dumps"

### Verification rules (behavior-first)
- Test that tool_choice produces actual EscalationRecord fields (test the stored escalation, not just returned JSON)
- Test that coordinator passes explicit context to subagents (subagent does NOT see coordinator's full history)
- Test that raw_handoff anti-pattern includes tool_use blocks in output (observable noise)
- Every claim maps to a test

### Claude's Discretion
- Coordinator routing logic (how to detect multi-topic queries)
- Subagent system prompts
- Integration notebook exact cell structure and turn sequence
- TODO placement and wording
- Raw handoff formatting (how to dump messages as text)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CCA certification rules (HIGHEST PRIORITY)
- `.planning/CCA-RULES.md` — Handoff pattern (structured JSON, not raw dumps), coordinator-subagent (hub-and-spoke, explicit context passing), subagent context isolation, tool_choice enforcement

### Source articles
- `/Users/richardhightower/articles/articles/cca-customer-support/work/final/article_publication_ready.md` — Handoff pattern, EscalationRecord, tool_choice
- `/Users/richardhightower/articles/articles/cca-multi-agent/work/final/article_publication_ready.md` — Coordinator-subagent, context isolation, silent failure prevention

### Project standards
- `.claude/CLAUDE.md` — Behavior-first verification rules, anti-patterns in anti_patterns/ only
- `CLAUDE.md` (root) — Architecture: coordinator.py in agent/

### Phase 3 outputs (handoff integrates with callbacks)
- `src/customer_service/agent/callbacks.py` — Block-not-bypass pattern returns `action_required: escalate_to_human`
- `src/customer_service/tools/handlers.py` — dispatch() with per-tool callback registry
- `src/customer_service/agent/agent_loop.py` — Loop to modify for tool_choice enforcement

### Phase 2 outputs
- `src/customer_service/models/customer.py` — EscalationRecord Pydantic model already defined
- `src/customer_service/tools/escalate_to_human.py` — Handler returns EscalationRecord JSON

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EscalationRecord` model — already has all CCA-specified fields
- `escalate_to_human` handler — already returns structured JSON
- Callback block-not-bypass pattern — returns `action_required: escalate_to_human`
- Notebook template — Setup > Anti-Pattern > Correct > Compare
- `print_usage` / `compare_results` helpers
- All 6 seed customers and scenarios

### Established Patterns
- Per-tool callback registry (`dict[str, Callable]`)
- Two-step vetoable pattern for process_refund
- Anti-patterns in `anti_patterns/` only
- CCA Exam Tip boxes as blockquotes
- Behavior-first tests (test stores, not just returns)

### Integration Points
- `agent_loop.py` — detect blocked result, issue `tool_choice` forced call
- `agent/coordinator.py` — new module
- `anti_patterns/raw_handoff.py` — new anti-pattern
- `notebooks/` — add 06_handoffs.ipynb, 07_integration.ipynb
- Existing notebooks — add TODO placeholders

</code_context>

<specifics>
## Specific Ideas

- C003 $600 refund is the canonical scenario — used in NB01, NB03, NB06, NB07. Consistency helps students track the same case across patterns.
- The integration notebook (07) is the capstone — it should feel like a real customer interaction that happens to demonstrate all 6 patterns naturally, not a forced checklist.
- TODOs should be genuinely educational: "implement a loyalty discount callback" is better than "add a print statement."

</specifics>

<deferred>
## Deferred Ideas

- Streamlit UI — still TBD, could be a separate phase or post-milestone addition

</deferred>

---

*Phase: 05-handoffs-integration-and-student-polish*
*Context gathered: 2026-03-27*
