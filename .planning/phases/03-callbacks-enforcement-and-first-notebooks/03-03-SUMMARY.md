---
phase: 03-callbacks-enforcement-and-first-notebooks
plan: 03
subsystem: notebooks
tags: [notebooks, cca-patterns, escalation, compliance, tool-design, teaching-artifacts, nbformat]
dependency_graph:
  requires: [03-01, 03-02]
  provides: [NB-02, NB-03, NB-04]
  affects:
    - notebooks/ (three new teaching notebooks)
    - tests/test_notebooks.py (smoke test coverage for all notebooks)
tech_stack:
  added: []
  patterns:
    - nbformat.v4 notebook generation (programmatic .ipynb creation via Python script)
    - Notebook template: Setup > Anti-Pattern (red box) > Correct Pattern (green box) > Compare > CCA Exam Tip
    - _UsageWrapper adapter for UsageSummary -> print_usage compatibility
    - ServiceContainer construction helper (make_services()) for clean per-run isolation
key_files:
  created:
    - notebooks/01_escalation.ipynb
    - notebooks/02_compliance.ipynb
    - notebooks/03_tool_design.ipynb
    - tests/test_notebooks.py
  modified: []
decisions:
  - Notebook cell import order uses helpers first (local), then customer_service (project) to satisfy isort rule I001 — helpers.py lives in notebooks/ and is treated as first-party
  - make_services() helper defined in each notebook to construct ServiceContainer explicitly (no default constructor exists — frozen dataclass requires all 5 services)
  - _UsageWrapper class defined in NB cells because print_usage expects response.usage; AgentResult.usage is a UsageSummary dataclass not a raw SDK response
  - NB01 checks escalation_queue.get_queue() (NOT financial_system.get_processed) — the CCA teaching point is whether escalation happened, not whether a refund was written
key-decisions:
  - isort notebook imports: helpers (local first-party) before customer_service (project package) to satisfy ruff I001
  - make_services() pattern: explicit ServiceContainer construction in notebooks matches conftest.py pattern, avoids hidden state
  - Smoke tests parse .ipynb JSON via nbformat (not subprocess/nbconvert) — deterministic, fast, no API calls needed
metrics:
  duration_seconds: 292
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 4
  files_modified: 0
  tests_added: 13
---

# Phase 03 Plan 03: First Notebooks (Escalation, Compliance, Tool Design) Summary

**One-liner:** Three CCA teaching notebooks using nbformat, each showing anti-pattern failure followed by correct-pattern success with escalation_queue/audit_log/tool-count comparison and CCA Exam Tip boxes.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Notebook 01 (Escalation) and notebook smoke tests | e353b5b | notebooks/01_escalation.ipynb, tests/test_notebooks.py |
| 2 | Notebooks 02 (Compliance) and 03 (Tool Design) | f8c96c4 | notebooks/02_compliance.ipynb, notebooks/03_tool_design.ipynb |

## What Was Built

### Notebook 01: Escalation Pattern (`01_escalation.ipynb`)

Template: Setup > Anti-Pattern (red box) > Correct Pattern (green box) > Compare > CCA Exam Tip > Summary

**Anti-pattern section:** Imports `run_confidence_agent` from `anti_patterns.confidence_escalation`. Runs on C003 `$600 refund` scenario. Checks `anti_services.escalation_queue.get_queue()` — typically returns empty (agent skips escalation because confidence-based routing lets Claude self-report high confidence and handle the case directly).

**Correct pattern section:** Imports `build_callbacks, get_system_prompt, run_agent_loop`. Runs with `callbacks=build_callbacks()`. Checks `correct_services.escalation_queue.get_queue()` — deterministically non-empty because the `escalation_callback` blocks `process_refund` when amount > $500.

**Key CCA enforcement:** NB01 checks `escalation_queue` (NOT `financial_system.get_processed`) — the teaching point is whether escalation happened, not whether a refund was processed.

**CCA Exam Tip:** Confidence threshold / self-assessment answers are ALWAYS wrong. Escalation routing must use deterministic business rules in code.

### Notebook 02: Compliance Pattern (`02_compliance.ipynb`)

Template: Setup > Anti-Pattern (red box) > Correct Pattern (green box) > Compare > CCA Exam Tip > Summary

**Anti-pattern section:** Imports `run_prompt_compliance_agent`. Uses `SCENARIOS["happy_path"]` (C001) with injected PII: `pii_message = scenario["message"] + " My card is 4111-1111-1111-1111."`. Checks `anti_services.audit_log.get_entries()` for raw card number presence.

**Correct pattern section:** Runs `run_agent_loop` with `callbacks=build_callbacks()`. Checks `correct_services.audit_log.get_entries()` to verify `4111-1111-1111-1111` never appears (replaced by `****-****-****-1111`).

**CCA Exam Tip:** Adding PCI rules to system prompt is WRONG. Compliance enforcement must be programmatic (callbacks), not prompt-based.

### Notebook 03: Tool Design Pattern (`03_tool_design.ipynb`)

Template: Setup > Anti-Pattern (red box) > Correct Pattern (green box) > Compare > CCA Exam Tip > Summary

**Setup section:** Imports both `SWISS_ARMY_TOOLS` (15 tools) and `TOOLS` (5 tools). Shows tool counts and marks distractor tool names.

**Anti-pattern section:** Imports `run_swiss_army_agent`. Runs on C003 `$600` scenario. Measures whether any distractor tools (`file_billing_dispute`, `create_support_ticket`, etc.) were called instead of the correct tools.

**Correct pattern section:** Runs `run_agent_loop` with default 5-tool set. All tool calls stay within `correct_tool_names` set.

**CCA Exam Tip:** Beyond 4–5 tools, selection accuracy degrades. When > 5 tools needed, use coordinator-subagent pattern — never cram more tools into one agent.

### tests/test_notebooks.py (13 smoke tests)

Deterministic tests that parse .ipynb JSON via `nbformat` — no API calls, no mocking.

- **Existence tests (3):** `test_notebook_01_exists`, `test_notebook_02_exists`, `test_notebook_03_exists`
- **Section structure tests (3):** Each notebook must contain "Anti-Pattern", "Correct Pattern", "Compare", "CCA Exam Tip" in markdown cells
- **CCA pattern-specific checks (3):** NB01 checks `escalation_queue` (not `financial_system.get_processed`); NB02 checks `audit_log`; NB03 checks `SWISS_ARMY_TOOLS` and tool count
- **Import checks (4):** NB01 imports `run_confidence_agent` and `build_callbacks`; NB02 imports `run_prompt_compliance_agent`; NB03 imports `run_swiss_army_agent`

## CCA Pattern Compliance Verification

| Pattern | Anti-pattern shown | Correct pattern shown | Key observable difference |
|---------|--------------------|----------------------|--------------------------|
| Escalation | Confidence routing: agent skips escalation | Callback enforcement: escalation_queue non-empty | `len(escalation_queue)` 0 vs 1+ |
| Compliance | Prompt-only: PII may reach audit_log | Callback redaction: regex replaces card number | `"4111"` in audit_log entries |
| Tool design | 15-tool Swiss Army: distractor calls | 5-tool focused: all calls from correct set | distractor tool names in call list |

## Test Coverage

- 13 new smoke tests in `tests/test_notebooks.py`
- Total passing: 156 (143 prior + 13 new)
- ruff lint: all checks passed (notebooks/ + tests/test_notebooks.py)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] isort I001: import order in NB02 and NB03**
- **Found during:** Task 2 lint check (`poetry run ruff check notebooks/`)
- **Issue:** NB02 and NB03 import cells had `anthropic` first, then `from helpers ...` at end. ruff's isort rule I001 requires local/first-party imports (`helpers`) to come before third-party project imports (`customer_service.*`) because `helpers` is in the notebooks directory (treated as first-party).
- **Fix:** Reordered import cells in gen_nb02.py and gen_nb03.py: `import anthropic`, then `from helpers import ...`, then blank line, then `from customer_service...` imports. Regenerated notebooks.
- **Files modified:** scripts/gen_nb02.py, scripts/gen_nb03.py, notebooks/02_compliance.ipynb, notebooks/03_tool_design.ipynb

**2. [Rule 1 - Bug] F541: spurious f-string without placeholders in NB03**
- **Found during:** Task 2 lint check
- **Issue:** Three `print(f'\n...')` calls with no format placeholders in gen_nb03.py setup cell.
- **Fix:** Changed to plain `print('\n...')` in gen_nb03.py, regenerated notebook.
- **Files modified:** scripts/gen_nb03.py, notebooks/03_tool_design.ipynb

## Self-Check: PASSED

Files exist:
- notebooks/01_escalation.ipynb: FOUND
- notebooks/02_compliance.ipynb: FOUND
- notebooks/03_tool_design.ipynb: FOUND
- tests/test_notebooks.py: FOUND

Commits:
- e353b5b: feat(03-03): notebook 01 (escalation) and notebook smoke tests — FOUND
- f8c96c4: feat(03-03): notebooks 02 (compliance) and 03 (tool design) — FOUND

All 156 tests pass. ruff lint clean on notebooks/ and tests/test_notebooks.py.
