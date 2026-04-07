# Phase 8: Notebook Completion - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning
**Source:** Conversation + Todo analysis + user request for Papermill automation

<domain>
## Phase Boundary

Complete NB06 (handoffs) and NB07 (integration) by implementing all remaining TODO markers, verifying output correctness, and adding Papermill-based automated notebook execution tests so notebooks never regress silently.

Three deliverables:
1. **NB06 completion** — Remove all TODOs, fix duplicate cells, verify handoff comparison output
2. **NB07 completion** — Remove all TODOs, implement all 6 pattern sections fully
3. **Automated notebook testing** — Add Papermill-based execution tests that run notebooks headlessly and catch errors without live API calls (using mock/stub approach or cell-level validation)

</domain>

<decisions>
## Implementation Decisions

### NB06 Handoffs (NBCOMP-01)
- Read NB06 end-to-end, inventory all TODO markers
- Verify the handoff comparison output: raw dump should be ~5-10x larger than structured EscalationRecord
- Remove any duplicate code cells (user reported comparison block appeared twice)
- Ensure the notebook follows the project pattern: anti-pattern first → correct pattern → compare → CCA Exam Tip
- Student TODO placeholders (with try/except or conditional guards) should remain — only remove developer TODOs

### NB07 Integration (NBCOMP-02)
- Read NB07 end-to-end, inventory all TODO markers
- Implement each incomplete section for all 6 CCA patterns
- The notebook uses shared services/result across all 6 pattern sections (one scenario exercises all patterns)
- Ensure imports from both `customer_service` (correct) and `customer_service.anti_patterns` (wrong)
- Must have at least 6 CCA Exam Tip boxes (one per pattern)

### Automated Notebook Testing (user request)
- Use Papermill (`papermill`) to execute notebooks headlessly in pytest
- Since notebooks call the Anthropic API, the test should either:
  - (a) Run with a mock/stub client (preferred — no API key needed in CI)
  - (b) Use `nbconvert --execute` with a timeout and check for cell errors in output
  - (c) Parse notebook JSON to validate cell structure without execution
- Add to `tests/test_notebook_execution.py`
- The goal is: if a notebook cell has a bug (wrong import, wrong attribute, missing data), the CI catches it
- For cells that call the API, validate the setup cells (imports, make_services, scenario loading) execute without error — skip API-calling cells

### Claude's Discretion
- How to mock/stub API calls for notebook execution testing
- Whether to use Papermill or nbconvert for headless execution
- How to handle cells that require ANTHROPIC_API_KEY (skip, mock, or tag-based filtering)
- How much notebook restructuring is acceptable vs just filling TODOs

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Notebooks to complete
- `notebooks/06_handoffs.ipynb` — Handoffs notebook (NBCOMP-01)
- `notebooks/07_integration.ipynb` — Integration notebook (NBCOMP-02)

### Package code (reference, not to modify)
- `src/customer_service/agent/agent_loop.py` — AgentResult, run_agent_loop
- `src/customer_service/agent/callbacks.py` — build_callbacks
- `src/customer_service/agent/context_manager.py` — ContextSummary
- `src/customer_service/agent/system_prompts.py` — get_system_prompt, get_system_prompt_with_caching
- `src/customer_service/agent/coordinator.py` — Coordinator pattern
- `src/customer_service/anti_patterns/raw_handoff.py` — format_raw_handoff
- `src/customer_service/models/escalation.py` — EscalationRecord

### Working notebooks (reference patterns)
- `notebooks/01_escalation.ipynb` — Recently fixed, good reference for correct pattern
- `notebooks/04_cost_optimization.ipynb` — Recently fixed, good reference for make_services pattern
- `notebooks/05_context_management.ipynb` — Recently fixed, good reference for anti-pattern demos

### Existing tests (patterns to follow)
- `tests/test_notebooks.py` — Structural notebook tests (existence, sections, imports)
- `tests/test_notebook_fixes.py` — Phase 7 fix verification tests

</canonical_refs>

<specifics>
## Specific Ideas

- User wants Papermill-based automated notebook testing to prevent regression
- The test should validate that non-API cells execute without error
- Consider tagging API-calling cells so Papermill can skip them
- NB07 must reference all 6 patterns: escalation, compliance, tool design, context, cost, handoffs
- Student TODOs (with guards) must be preserved — they're a teaching feature
- The existing `test_notebooks_have_todo_placeholders` test expects >= 3 TODOs across NB06+NB07

</specifics>

<deferred>
## Deferred Ideas

- Full end-to-end notebook execution with live API (requires ANTHROPIC_API_KEY)
- AI-powered auto-fix loop (Papermill + Claude for self-healing notebooks) — interesting idea from user but out of scope for v1.1

</deferred>

---

*Phase: 08-notebook-completion*
*Context gathered: 2026-04-06 from conversation and todo analysis*
