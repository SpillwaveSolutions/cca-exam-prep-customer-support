# Phase 2: Models, Services, and Core Loop - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

The 5-tool customer support agent can process a customer message through a complete agentic loop using simulated services. Pydantic models define all data structures. Simulated services are input-sensitive (deterministic, rule-based). Seed data includes customers and scenarios that trigger specific escalation thresholds. The dispatch registry routes tool_use blocks to correct handlers.

No notebooks in this phase. No callbacks/enforcement (Phase 3). No prompt caching (Phase 4). No handoff patterns (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Seed data & scenario design
- 5-6 targeted customer profiles, each designed to trigger a specific escalation rule:
  - C001: regular tier, $50 refund (happy path)
  - C002: VIP tier, $200 refund (VIP escalation rule)
  - C003: regular tier, $600 refund (amount > $500 rule)
  - C004: closure flag set (account closure rule)
  - C005: mentions lawsuit in message (legal keyword rule)
  - C006: VIP + $600 + closure (multi-trigger edge case)
- Seed data includes pre-built scenarios (customer + message + expected outcome):
  - Each scenario: customer_id, message text, expected_tools list, expected_outcome
  - Notebooks can run scenarios directly without constructing messages
- Seed data stored as Python dicts in `data/` sub-package (Claude's discretion on exact format)

### Service behavior rules
- Rule-based lookup tables — fully deterministic, no randomness
- CustomerDatabase: returns different tiers/flags per customer ID from seed data
- PolicyEngine: returns different refund limits per tier (basic=$100, premium=$500, VIP=$5000), flags amounts > $500 as requires_review
- FinancialSystem: succeeds/fails based on amount vs policy result, tracks refund state
- EscalationQueue: accepts structured EscalationRecord, stores in memory
- AuditLog: appends all interactions for compliance verification
- ServiceContainer: frozen dataclass holding all 5 services, created once, passed to handlers

### Agent loop termination & error handling
- AgentResult dataclass returned from every run: stop_reason, messages, tool_calls, final_text, usage
- Graceful exit with status — never raises exceptions for expected API responses
- Loop terminates on stop_reason == "end_turn" (NEVER content-type checking — CCA rule)
- stop_reason == "tool_use" → dispatch tools, continue loop
- All other stop_reasons (max_tokens, refusal, etc.) → return AgentResult with that stop_reason
- Max 10 iterations safety limit — returns AgentResult with stop_reason="max_iterations"
- Token usage accumulated across all iterations for print_usage reporting

### Tool schema design
- Pydantic model_json_schema() for all tool input schemas (single source of truth — CCA rule)
- 5 focused tools (CCA 4-5 tool rule): lookup_customer, check_policy, process_refund, escalate_to_human, log_interaction
- Tool descriptions must include negative bounds (CCA rule):
  - "Look up customer profile by ID; does NOT modify customer data"
  - "Check refund policy eligibility; does NOT process the refund"
  - etc.
- Simple dict registry for dispatch: tool name string → handler callable
- Each handler signature: (input_dict: dict, services: ServiceContainer) → str
- All handlers return JSON strings (CCA rule: matching Claude API tool_result format)

### CCA compliance rules (MANDATORY — from source articles)
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CCA certification rules (HIGHEST PRIORITY)
- `.planning/CCA-RULES.md` — Authoritative CCA exam patterns, anti-patterns, and rules extracted from all 8 source articles. ALL code must comply. Never contradict.

### Source articles (for verification)
- `/Users/richardhightower/articles/articles/cca-customer-support/work/final/article_publication_ready.md` — Customer Support Resolution Agent scenario (primary)
- `/Users/richardhightower/articles/articles/cca-multi-agent/work/final/article_publication_ready.md` — Multi-agent patterns, coordinator-subagent, context isolation
- `/Users/richardhightower/articles/articles/cca-data-extraction/work/final/article_publication_ready.md` — Three-layer reliability, schema enforcement, validation-retry
- `/Users/richardhightower/articles/articles/cca-intro/work/final/article_publication_ready.md` — 5 core principles, decision frameworks

### Project standards
- `.claude/CLAUDE.md` — Code style rules, architecture rules, CCA patterns enforced
- `CLAUDE.md` (root) — Project overview, build commands, architecture description, data flow diagram

### Package configuration
- `pyproject.toml` — Poetry config, dependencies, ruff settings

### Phase 1 context
- `.planning/phases/01-project-foundation/01-CONTEXT.md` — Package init exports decision (re-export key items), print_usage/compare_results helpers already built

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `notebooks/helpers.py` — print_usage (token breakdown + cost) and compare_results (side-by-side table) already built and tested
- `src/customer_service/__init__.py` — Has __version__, needs re-exports after Phase 2 builds models/services
- `src/customer_service/__main__.py` — Skeleton ready, needs agent loop wiring after Phase 2

### Established Patterns
- `pyproject.toml`: Python 3.13+, ruff (E/F/I/N/W/UP), 100-char lines, anthropic >= 0.42.0, pydantic >= 2.0
- Package layout: src/customer_service/ with sub-packages: agent, anti_patterns, data, models, services, tools
- All sub-packages have stub __init__.py files ready for content
- 24 tests passing (imports + config + helpers)
- Model: claude-sonnet-4-6 (verified working in setup notebook)

### Integration Points
- `__init__.py` re-exports: After Phase 2, update to export ServiceContainer, run_agent_loop, Pydantic models
- `__main__.py`: After Phase 2, wire to run a single scenario end-to-end
- `notebooks/helpers.py`: print_usage expects response.usage object — agent loop must return compatible usage data
- tests/: Add tests for models, services, tool dispatch, agent loop

</code_context>

<specifics>
## Specific Ideas

- Seed data scenarios should be reusable across notebooks — same scenario used in both anti-pattern and correct pattern runs for fair comparison
- ServiceContainer is frozen (immutable) — prevents accidental state mutation between notebook runs
- The $500 escalation threshold is from the CCA source article — use exactly $500, not a different number
- Tool descriptions with negative bounds are a CCA exam topic — make them exemplary
- AgentResult should carry enough info for print_usage (usage field) and compare_results (tool_calls, stop_reason)

</specifics>

<deferred>
## Deferred Ideas

- PostToolUse callbacks — Phase 3 (enforcement layer)
- Prompt caching with cache_control markers — Phase 4 (cost optimization)
- Structured escalation handoff with tool_choice enforcement — Phase 5 (handoff pattern)
- Coordinator-subagent pattern — Phase 5 (multi-agent)
- Streamlit UI — deferred from Phase 1, still TBD

</deferred>

---

*Phase: 02-models-services-and-core-loop*
*Context gathered: 2026-03-25*
