---
phase: 05-handoffs-integration-and-student-polish
plan: 02
subsystem: notebooks
tags: [handoffs, integration, student-todos, notebooks, tdd, cca-patterns]
dependency_graph:
  requires: [agent_loop, callbacks, coordinator, raw_handoff, context_manager, system_prompts]
  provides: [NB06_handoffs, NB07_integration, nb_smoke_tests_06_07]
  affects: [tests/test_notebooks.py]
tech_stack:
  added: []
  patterns:
    - anti-pattern vs correct pattern template (NB06)
    - capstone integration notebook covering all 6 CCA patterns (NB07)
    - try/except guarded TODO placeholders (STUDENT-01)
key_files:
  created:
    - notebooks/06_handoffs.ipynb
    - notebooks/07_integration.ipynb
  modified:
    - tests/test_notebooks.py
decisions:
  - "NB06 reuses single agent loop run for both anti-pattern and correct pattern sections — avoids double API call, cleaner pedagogy"
  - "NB07 uses shared services/result across all 6 pattern sections — one scenario exercises all patterns"
  - "TODO-2 in NB07 uses student_customer = None conditional guard (not try/except) — more Pythonic for data setup TODOs"
metrics:
  duration: 20min
  completed: "2026-03-27"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
  tests_added: 11
---

# Phase 05 Plan 02: Integration Notebooks and Student Polish Summary

**One-liner:** Created NB06 (raw dump vs structured EscalationRecord via tool_choice) and NB07 (capstone covering all 6 CCA patterns) with 11 new smoke tests and 3 guarded TODO placeholders.

## What Was Built

### Task 1: NB06 Handoffs + NB07 Integration Capstone

**`notebooks/06_handoffs.ipynb`** — Handoff pattern notebook (NB-07 requirement):
- Setup: imports, `make_services()`, C003 $600 scenario setup
- Anti-Pattern: runs `run_agent_loop` with callbacks, calls `format_raw_handoff(result.messages)`, shows raw_len chars of JSON noise including `tool_use` blocks
- Correct Pattern: retrieves `EscalationRecord` from `services.escalation_queue.get_all_escalations()`, prints structured JSON (8 clean fields)
- Compare: side-by-side table showing raw vs structured size, ratio, field visibility
- CCA Exam Tip: `tool_choice` enforcement for deterministic structured output
- TODO-3: student sentiment callback with `try/except NotImplementedError` guard

**`notebooks/07_integration.ipynb`** — Integration capstone (NB-08 requirement):
- One scenario (C003 $600 refund + PII credit card) exercises all 6 patterns
- Pattern 1 (Escalation): `run_agent_loop` → `stop_reason == "escalated"`, shows forced escalation tool call
- Pattern 2 (Compliance): inspects `audit_log` for redacted card pattern `****-****-****-1234`
- Pattern 3 (Tool Design): shows `len(TOOLS) <= 5` assertion, lists tools called in scenario
- Pattern 4 (Context): creates `ContextSummary`, shows `token_estimate <= TOKEN_BUDGET`, compares vs raw messages dump
- Pattern 5 (Cost): shows `usage.cache_read_input_tokens`, demonstrates `get_system_prompt_with_caching()` structure
- Pattern 6 (Handoffs): prints `EscalationRecord` JSON vs `format_raw_handoff()` size comparison
- 6 per-pattern CCA Exam Tip blockquotes
- TODO-1: frequency-based escalation rule (`try/except NotImplementedError` guard)
- TODO-2: premium-tier customer (`student_customer = None` conditional guard)

### Task 2: Extended test_notebooks.py Smoke Tests (TDD)

**`tests/test_notebooks.py`** — 11 new tests appended after NB05 section:

NB06 tests (5):
- `test_notebook_06_exists`: file existence check
- `test_notebook_06_sections`: Anti-Pattern, Correct Pattern, Compare, CCA Exam Tip in markdown
- `test_notebook_06_imports_raw_handoff`: `format_raw_handoff` in code
- `test_notebook_06_references_tool_choice`: `tool_choice` in code or markdown
- `test_notebook_06_checks_escalation_queue`: `escalation_queue` in code

NB07 tests (4):
- `test_notebook_07_exists`: file existence check
- `test_notebook_07_has_six_cca_exam_tips`: `md.count("CCA Exam Tip") >= 6`
- `test_notebook_07_imports_key_modules`: `run_agent_loop`, `build_callbacks`, `ContextSummary` in code
- `test_notebook_07_references_all_patterns`: all 6 patterns mentioned in markdown

TODO safety tests (2):
- `test_notebooks_have_todo_placeholders`: `>=3` `# TODO:` comments across NB06+NB07
- `test_todo_guards_use_try_except`: each TODO cell has `try:`, `except`, or `if/None` guard

## Success Criteria Verification

| Criterion | Status |
|-----------|--------|
| NB06 shows raw dump vs structured EscalationRecord | PASS |
| NB06 compares token counts: raw > structured | PASS — side-by-side table with ratio |
| NB07 covers all 6 CCA patterns | PASS — 6 sections + 6 CCA Exam Tips |
| At least 3 TODO placeholders, non-breaking | PASS — 3 TODOs (1 NB06, 2 NB07) |
| All notebook smoke tests pass | PASS — 33/33 |
| Full test suite passes | PASS — 234/234 |
| Ruff clean | PASS |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Duplicate import `get_system_prompt_with_caching` in NB07 cell 18**
- **Found during:** Task 1, pre-commit ruff check (F811 redefinition + E402 module-level import)
- **Issue:** Pattern 5 code cell had a redundant `from customer_service.agent.system_prompts import get_system_prompt_with_caching` — already imported in the top-level imports cell. Ruff flagged F811 (redefinition) and E402 (not at top of cell).
- **Fix:** Removed the duplicate import from the Pattern 5 cell; used the already-imported name directly.
- **Files modified:** `notebooks/07_integration.ipynb`

**2. [Rule 1 - Lint] Line-too-long (E501) in NB07 cells 18 and 25**
- **Found during:** Task 1, pre-commit ruff check
- **Issue:** Two lines exceeded 100-char limit: `block_type = block.get(...) if isinstance(...) else getattr(...)` and the TODO-2 hint comment about `CustomerProfile(...)`.
- **Fix:** Broke long ternary into if/else block; wrapped long comment hint across multiple lines.
- **Files modified:** `notebooks/07_integration.ipynb`

**3. [Rule 1 - Format] ruff format reformatted test_notebooks.py**
- **Found during:** Task 2, pre-commit ruff-format hook
- **Issue:** `has_guard` boolean expression in `test_todo_guards_use_try_except` needed reformatting — parenthesized compound `or` expression.
- **Fix:** Applied ruff format output (pre-commit auto-applies), re-staged, re-committed.
- **Files modified:** `tests/test_notebooks.py`

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| `notebooks/06_handoffs.ipynb` | FOUND |
| `notebooks/07_integration.ipynb` | FOUND |
| `tests/test_notebooks.py` (modified) | FOUND |
| commit d4aafbe (Task 1 — notebooks) | FOUND |
| commit 8596fc8 (Task 2 — tests) | FOUND |
| 33 notebook smoke tests pass | PASS |
| 234 total tests pass | PASS |
| Ruff clean | PASS |
