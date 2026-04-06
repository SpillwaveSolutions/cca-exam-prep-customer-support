# Phase 7: Notebook Bug Fixes - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning
**Source:** Conversation + Todo analysis

<domain>
## Phase Boundary

Fix 3 bugs in shipped notebooks (NB01, NB04, NB05) so all cells execute without error and produce correct observable output. These are runtime failures found during notebook review — the package code may need minor fixes but the primary work is in notebook cells.

Two root causes:
1. **`make_services()` missing seed data** — NB04 and NB05 construct `CustomerDatabase()` with no arguments but the constructor requires a `customers` dict. This is a shared root cause affecting both notebooks.
2. **Escalation callback not firing** — NB01's correct-pattern cell produces an empty escalation queue for a $600 refund, but the >$500 rule should trigger mandatory human escalation via `callbacks.py`.

</domain>

<decisions>
## Implementation Decisions

### make_services() Fix (NBFIX-01, NBFIX-02)
- Fix must mirror how working notebooks (NB00-NB03) construct `ServiceContainer` — use seed data from `src/customer_service/data/`
- Do NOT give `CustomerDatabase.__init__` a default empty dict — the explicit data requirement is correct production pattern
- Both NB04 and NB05 have their own `make_services()` helper defined in a code cell — fix both consistently

### Escalation Callback Fix (NBFIX-03)
- The >$500 escalation rule is enforced in `callbacks.py` as a PostToolUse hook — this is the CCA-correct pattern
- The bug could be: (a) callback not wired into agent loop in notebook cell, (b) threshold check bug in callbacks.py, (c) agent never calls `process_refund` tool, or (d) agent resolves via different path
- Must trace the actual tool call sequence before fixing — don't assume the cause
- The fix must result in `escalation_queue.get_escalations()` returning at least one entry for the $600 scenario

### Claude's Discretion
- How to structure the `make_services()` helper (inline seed data vs import from data module)
- Whether to add defensive output in notebook cells to help students debug if API behavior varies
- How verbose the verification output should be in each cell

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Working notebook pattern (reference for make_services)
- `notebooks/00_setup.ipynb` — Setup notebook with working ServiceContainer construction
- `notebooks/01_escalation.ipynb` — The broken escalation notebook (NBFIX-03)

### Package code (may need fixes)
- `src/customer_service/agent/callbacks.py` — Escalation and compliance callback implementations
- `src/customer_service/agent/agent_loop.py` — Agent loop that accepts callbacks parameter
- `src/customer_service/services/__init__.py` — ServiceContainer and service classes
- `src/customer_service/data/customers.py` — Seed customer data
- `src/customer_service/data/scenarios.py` — Seed scenarios including $600 refund

### Broken notebooks
- `notebooks/04_cost_optimization.ipynb` — TypeError on make_services() (NBFIX-01)
- `notebooks/05_context-management.ipynb` — TypeError on make_services() + verify RawTranscript API (NBFIX-02)

### Anti-pattern code (verify API matches notebook usage)
- `src/customer_service/anti_patterns/raw_transcript.py` — RawTranscript class used by NB05

</canonical_refs>

<specifics>
## Specific Ideas

- NB05 uses `raw_transcript.append("user", msg1)`, `raw_transcript.token_estimate()`, and `raw_transcript.to_context_string()` — verify these methods exist on `RawTranscript`
- NB05 checks for `'birthday'` substring in context string — verify seed scenario messages reference "birthday"
- NB01 verification cell checks `correct_services.escalation_queue.get_escalations()` — must return non-empty list
- The observed NB01 output was: `Escalation queue length: 0` / `UNEXPECTED: Correct pattern did not escalate`

</specifics>

<deferred>
## Deferred Ideas

- NB06 and NB07 completion (Phase 8)
- Any new notebook content or restructuring

</deferred>

---

*Phase: 07-notebook-bug-fixes*
*Context gathered: 2026-04-06 from conversation and todo analysis*
