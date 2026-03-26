# Phase 3: Callbacks, Enforcement, and First Notebooks - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Students run notebooks 01-03 and observe how deterministic callbacks catch what prompt-only rules miss, and how 5 focused tools outperform 15. PostToolUse callbacks enforce business rules in code. Three anti-patterns demonstrate observable failures. Three notebooks follow the established template (Setup > Anti-Pattern > Correct > Compare).

No prompt caching (Phase 4). No handoff patterns (Phase 5). No coordinator-subagent (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Callback architecture
- Hook point: dispatch() in handlers.py — the single place every tool result passes through
- Callback logic: separate `agent/callbacks.py` module (not inline in dispatch or agent_loop)
- Signature: `dispatch(tool_name, input_dict, services, context, callbacks=...)`
- **Per-tool callback registry**: callbacks is a `dict[str, Callable]` mapping tool_name → callback function. Each callback ONLY fires for its registered tool. NOT a shared list that runs all callbacks for every tool.
- Callback input: `(tool_name, input_dict, result_dict, context, services)`
- Callback output: `action="allow" | "replace_result" | "block"` plus replacement payload/reason
- Context parameter must include the current user message or structured conversation summary (needed for legal keyword detection)
- **On block (process_refund)**: return a JSON result telling Claude the refund was blocked and must be escalated. Do NOT directly enqueue escalation or fabricate a tool call. Let Claude naturally call `escalate_to_human` on its next turn. This preserves the expected tool trace (lookup_customer → check_policy → process_refund[blocked] → escalate_to_human).
- **On replace_result (log_interaction)**: return the redacted version as the tool result

### Vetoable tool pattern
- Only process_refund is two-step vetoable (irreversible financial side effect)
  - Step 1: compute proposed refund result (no commit to FinancialSystem)
  - Step 2: dispatch runs the process_refund callback on proposed result
  - Step 3: if callback returns action="allow" → commit refund to FinancialSystem
  - Step 4: if callback returns action="block" → return JSON: {"status": "blocked", "reason": "...", "action_required": "escalate_to_human"} — FinancialSystem is UNTOUCHED
  - **Test requirement**: after a blocked refund, `FinancialSystem.get_processed()` must be empty (this IS the veto guarantee)
- escalate_to_human: single-step (append-only, safe — it IS the fallback action)
- log_interaction: single-step, but callback may redact/replace the details field BEFORE the handler writes to audit log
- lookup_customer and check_policy: pure reads, callbacks set context flags only

### Escalation callback rules (CCA-compliant, deterministic)
- lookup_customer callback: detect VIP tier flag, detect account_closure flag → set context flags for downstream callbacks
- check_policy callback: detect amount > $500 (requires_review) → set context flag
- process_refund callback: BLOCK refund if ANY of: VIP, account_closure, legal_complaint, amount > $500. Returns blocked result with "action_required": "escalate_to_human" so Claude calls escalate_to_human naturally on its next turn.
- log_interaction callback: compliance/redaction enforcement — regex-replace credit card patterns in details before write
- **Each callback guards on tool_name** — per-tool registry means callbacks only fire for their registered tool, never for unrelated tools

### Anti-pattern 1: Confidence escalation (confidence_escalation.py)
- Scenario: C003, $600 refund
- System prompt tells agent: "Rate your confidence 0-100. If below 70, escalate. Otherwise proceed."
- **Observable failure: Claude reports high confidence and does NOT escalate to human** — it tries to handle the case itself (regardless of whether the refund is policy-approved or rejected). The failure is about ROUTING, not refund approval.
- Correct pattern: callback on process_refund detects amount > $500, blocks refund, Claude then calls `escalate_to_human` naturally
- **NB01 checks `escalation_queue`**, NOT `financial_system.get_processed()`. The question is "was the case escalated?" not "was the refund processed?"
  - Anti-pattern: escalation_queue is empty (Claude didn't escalate — WRONG)
  - Correct: escalation_queue has an EscalationRecord (CORRECT)
- Mention inconsistency across runs briefly in markdown as additional risk, but NOT as the core demo
- CCA exam lesson: self-reported confidence is ALWAYS the wrong answer for escalation routing

### Anti-pattern 2: Prompt-only compliance (prompt_compliance.py)
- Scenario: C001 (happy path) with credit card number in customer message ("card 4111-1111-1111-1111")
- System prompt tells agent: "Never log credit card numbers or SSNs. Redact before logging."
- Observable failure: log_interaction writes full card number to audit log
- Correct pattern: callback on log_interaction regex-redacts card patterns (****-****-****-1111) before audit write
- CCA exam lesson: prompts are probabilistic guidance, programmatic hooks are deterministic enforcement

### Anti-pattern 3: Swiss Army 15-tool agent (swiss_army_agent.py)
- 15 tools = 5 correct + 10 cross-domain distractors
- Distractor tools (plausible for support agent, overlapping descriptions):
  1. check_shipping_status
  2. lookup_order_history
  3. check_inventory
  4. update_billing_info
  5. file_billing_dispute (target misroute for $600 refund)
  6. create_support_ticket (target misroute for closure/legal)
  7. reset_password
  8. update_account_settings
  9. search_knowledge_base
  10. send_feedback_survey
- Distractor descriptions must be plausible and overlapping, not absurdly broad
- Failure should look like a reasonable model mistake caused by tool overload, not a rigged demo
- Scenario: C003, $600 refund — Swiss Army picks file_billing_dispute; 5-tool agent picks process_refund
- CCA exam lesson: beyond 4-5 tools, tool selection accuracy degrades measurably

### Notebook content & flow
- Template: Setup > Anti-Pattern (red box) > Correct (green box) > Compare (established in Phase 1)
- Explanatory markdown: CCA exam callouts + concise explanation (2-3 sentences + exam tip box per section)
- CCA Exam Tip boxes: highlighted blockquotes with specific exam guidance
- Each notebook displays token usage via print_usage helper
- Comparison section uses compare_results helper

### Notebook scenario assignments
- Notebook 01 (Escalation): C003 ($600 refund, amount > $500 trigger)
- Notebook 02 (Compliance): C001 (happy path + PII in message)
- Notebook 03 (Tool Design): C003 ($600 refund again — same scenario, different failure mode)
- NB01 and NB03 share C003 intentionally: shows different CCA patterns failing on the same scenario

### Claude's Discretion
- Exact callback dataclass/namedtuple shape for action/payload/reason
- Legal keyword detection implementation (regex vs keyword list)
- Credit card regex pattern specifics
- Distractor tool description wording (must be plausible, not rigged)
- Notebook cell count and exact markdown formatting
- System prompt content for anti-pattern agents

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CCA certification rules (HIGHEST PRIORITY)
- `.planning/CCA-RULES.md` — Authoritative CCA exam rules. ALL code must comply. Especially: Principle #1 (programmatic > prompts), escalation rules, tool count rule, structured error context.

### Source articles
- `/Users/richardhightower/articles/articles/cca-customer-support/work/final/article_publication_ready.md` — Customer Support scenario: escalation, compliance, tool design patterns and anti-patterns
- `/Users/richardhightower/articles/articles/cca-developer-productivity/work/final/article_publication_ready.md` — PostToolUse hooks, programmatic enforcement patterns

### Project standards
- `.claude/CLAUDE.md` — Architecture rules: callbacks.py enforces rules, NEVER system prompts alone; anti-patterns live ONLY in anti_patterns/
- `CLAUDE.md` (root) — Data flow diagram showing callbacks.py position in the pipeline

### Phase 2 outputs (build on these)
- `src/customer_service/tools/handlers.py` — dispatch() is the hook point for callbacks
- `src/customer_service/agent/agent_loop.py` — Agent loop that will call dispatch with callback context
- `src/customer_service/tools/definitions.py` — 5 tool schemas (correct pattern)
- `src/customer_service/data/scenarios.py` — Pre-built scenarios for notebooks
- `src/customer_service/data/customers.py` — C001-C006 seed customers

### Phase 1 outputs
- `notebooks/helpers.py` — print_usage and compare_results helpers for notebook comparison sections

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dispatch()` in handlers.py — current signature is `(tool_name, input_dict, services)`, needs `context` and `callbacks` parameters added
- `agent_loop.py` (131 lines) — needs to pass conversation context and callbacks list to dispatch
- `print_usage` / `compare_results` in notebooks/helpers.py — ready for notebook comparison sections
- 6 seed scenarios in data/scenarios.py — C003 scenario ready for NB01/NB03, C001 for NB02
- Structured error context already in dispatch (status, error_type, source, retry_eligible, etc.)

### Established Patterns
- Tool handlers return JSON strings
- stop_reason-based loop control
- Red/green HTML alert boxes for notebook template
- Setup > Anti-Pattern > Correct > Compare ordering
- TDD: tests written first

### Integration Points
- `dispatch()` signature change: add `context` and `callbacks` parameters (backward compatible with defaults)
- `agent_loop.py`: pass user message / conversation summary as context to dispatch
- `anti_patterns/` directory: stub __init__.py exists, add confidence_escalation.py, prompt_compliance.py, swiss_army_agent.py
- `agent/callbacks.py`: new module for callback rules
- `notebooks/`: add 01_escalation.ipynb, 02_compliance.ipynb, 03_tool_design.ipynb

</code_context>

<specifics>
## Specific Ideas

- The $600 refund on C003 is the canonical demo scenario — it appears in NB01 AND NB03 to show different CCA failures on the same case
- Credit card test number 4111-1111-1111-1111 is the standard Visa test number — students will recognize it
- Swiss Army distractor descriptions should feel like real enterprise support tools, not obviously wrong choices
- CCA Exam Tip boxes should use the exact language students will see on the exam ("If an answer mentions confidence threshold... it is ALWAYS wrong")
- process_refund two-step pattern keeps the vetoable logic localized to that one handler, not generalized across all tools

</specifics>

<deferred>
## Deferred Ideas

- Prompt caching with cache_control markers — Phase 4
- Structured escalation handoff with tool_choice enforcement — Phase 5
- Coordinator-subagent pattern — Phase 5
- Batch API vs Real-Time cost comparison — Phase 4
- Streamlit UI — still TBD

</deferred>

---

*Phase: 03-callbacks-enforcement-and-first-notebooks*
*Context gathered: 2026-03-26*
