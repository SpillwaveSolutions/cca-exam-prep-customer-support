# CCA Customer Support Resolution Agent — Project Standards

This project is a hands-on coding example for the CCA Exam Prep course.
It demonstrates all 6 architectural patterns from the Customer Support scenario article.

## Code Style
- Python 3.13+, type annotations on all public functions
- Pydantic BaseModel for all data structures
- No `Any` types except in `anti_patterns/` directory (anti-patterns are deliberately wrong)
- Imports: stdlib, third-party, local (isort compatible)
- Line length: 100 characters max

## Architecture Rules
- All tool handlers return JSON strings (matching Claude API tool_result format)
- Business rules enforced in `callbacks.py`, NEVER in system prompts alone
- Services are injected via `ServiceContainer`, never imported directly in tools
- Anti-pattern code lives ONLY in `src/customer_service/anti_patterns/`
- The 5 tools per agent: `lookup_customer`, `check_policy`, `process_refund`, `escalate_to_human`, `log_interaction`

## CCA Patterns Enforced
- Escalation: deterministic business rules (amount > $500, account closure, VIP, legal)
- Compliance: programmatic hooks in callbacks, not prompt instructions
- Tool count: 4-5 focused tools per agent; use coordinator-subagent for more
- Context: structured JSON summaries, not raw transcripts
- Cost: prompt caching for repeated context, real-time API for live support
- Handoffs: structured EscalationRecord JSON, not raw conversation dumps

## Testing
- Every callback rule needs a test in `test_callbacks.py`
- Tests use simulated services, never real API calls
- Run: `poetry run pytest`

## Verification Rules (Behavior-First)
- **Test the store, not the API response** — For side-effecting paths (AuditLog, EscalationQueue, FinancialSystem), verify the persistent state, not just returned JSON
- **Every completion claim needs executable proof** — Format: "Claim" → "test name / command". No proof = no claim.
- **Split structure vs behavior** — Structural tests (file exists, cell count) are necessary but not sufficient. Behavioral tests (PII never in audit log, refund blocked leaves FinancialSystem empty) prove correctness.
- **Regression checklist** — Before marking work complete, verify: (1) persistent state tested, (2) actual runtime path tested, (3) failing test added before fix, (4) notebook/example calls real APIs that exist

## Commands
- `poetry run pytest` — run all tests
- `poetry run jupyter lab` — launch notebooks
- `poetry run ruff check src/` — lint
- `poetry run ruff format src/` — format
