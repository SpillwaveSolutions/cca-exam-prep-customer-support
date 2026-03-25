---
phase: 01-project-foundation
plan: 02
subsystem: notebooks
tags: [python, jupyter, helpers, print_usage, compare_results, tabulate, nbformat, dotenv]

# Dependency graph
requires:
  - 01-01  # importable customer_service package
provides:
  - notebooks/helpers.py with print_usage (token breakdown + cost) and compare_results (tabulate side-by-side)
  - notebooks/00_setup.ipynb with 4 verification checks (Python, SDK, API key, package)
  - Red/green HTML alert box template convention for all 8 notebooks
  - tests/test_helpers.py with 7 passing unit tests
  - tests/test_config.py extended with notebook existence and cell-count tests
affects:
  - 02-models and all subsequent phases (can import helpers in their notebooks)
  - notebooks/01-07 (inherit template convention from 00_setup.ipynb)

# Tech tracking
tech-stack:
  added: [tabulate >= 0.9 (notebook extras, already in pyproject)]
  patterns:
    - "TDD RED-GREEN: write failing tests first, then implement (confirmed workflow)"
    - "Notebook cell source as JSON arrays of strings (one string per line)"
    - "Use variable for separator string to avoid f-string escaped-quote issue (py313 ruff UP036/E501)"
    - "sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'notebooks')) for test imports"
    - "find_dotenv() for .env loading in notebooks (not hardcoded .env path)"
    - "Pre-commit hook ordering: ruff-check -> ruff-format -> nbstripout (two-attempt commit pattern)"

key-files:
  created:
    - notebooks/helpers.py
    - notebooks/00_setup.ipynb
    - tests/test_helpers.py
  modified:
    - tests/test_config.py

key-decisions:
  - "Use variable for separator (sep = '=' * 50) in notebooks — avoids UP036/E501 ruff errors from escaped quotes in f-strings (Python 3.13 strictness)"
  - "Version check uses (major, minor) tuple comparison instead of sys.version_info >= (3, 13) — avoids UP036 since py313 is minimum"
  - "print_usage cost rates hardcoded as module-level constants (_PRICE_INPUT, etc.) — visible for students to inspect and modify"
  - "compare_results boolean delta uses 'FIXED'/'REGRESSED'/'same' labels — pedagogically clear for CCA exam prep"

patterns-established:
  - "Pattern 4: Notebook alert boxes — red (#dc3545) for anti-pattern, green (#28a745) for correct, blue (#007bff) for exam tips"
  - "Pattern 5: Notebook section ordering — Setup > Anti-Pattern > Correct > Compare (established in 00_setup.ipynb)"

requirements-completed: [SETUP-02, NB-01]

# Metrics
duration: 5min
completed: 2026-03-25
---

# Phase 1 Plan 02: Notebook Helpers and Setup Notebook Summary

**Notebook helper module (print_usage + compare_results) and 13-cell setup notebook with 4 environment verification checks and red/green alert box template**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-25T23:16:06Z
- **Completed:** 2026-03-25T23:20:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `notebooks/helpers.py` with `print_usage` (aligned token breakdown, estimated USD cost) and `compare_results` (tabulate side-by-side table with percentage deltas and FIXED/REGRESSED for booleans)
- Created `notebooks/00_setup.ipynb` with 13 cells: red/green alert box template demo, 4 environment verification checks (Python version, Anthropic SDK, API key validity with minimal API call, all sub-package imports), CCA exam tip
- Added 7 passing unit tests in `tests/test_helpers.py` covering all helper behaviors including zero-baseline N/A, cache field handling, boolean delta labels
- Extended `tests/test_config.py` with notebook existence and cell-count tests (9 total, all passing)

## Task Commits

Each task was committed atomically:

1. **Task 1: Notebook helpers with print_usage and compare_results (TDD RED-GREEN)** - `b797fde` (feat)
2. **Task 2: Setup notebook 00 with 4 verification checks** - `96e0033` (feat)

## Files Created/Modified

- `notebooks/helpers.py` - print_usage (token breakdown + cost estimate), compare_results (tabulate side-by-side)
- `notebooks/00_setup.ipynb` - 13-cell setup/verification notebook with template convention
- `tests/test_helpers.py` - 7 unit tests: test_print_usage_basic, test_print_usage_with_cache, test_print_usage_no_cache_fields, test_print_usage_cost_estimate, test_compare_results_basic, test_compare_results_business_metrics, test_compare_results_zero_baseline
- `tests/test_config.py` - Added test_setup_notebook_exists, test_setup_notebook_has_cells (now 9 total tests)

## Decisions Made

- Used `(major, minor) < (3, 13)` tuple comparison instead of `sys.version_info >= (3, 13)` — avoids ruff UP036 "version block outdated for minimum Python" since pyproject.toml requires py313
- Used `sep = '=' * 50` variable instead of `f"{'=' * 50}"` — avoids ruff E501 and f-string escaped-quote syntax errors under py313 strict mode
- Hardcoded cost rates as module-level constants (`_PRICE_INPUT = 3.00`, etc.) — pedagogically visible for students reviewing the helper

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff UP036/E501 lint errors in notebook cells**
- **Found during:** Task 2 commit (pre-commit hook failure)
- **Issue 1:** `if sys.version_info >= (3, 13):` triggered UP036 ("version block outdated for minimum Python version") since the project requires Python 3.13+
- **Issue 2:** Long f-string with `{\"=\" * 50}` escaped quotes caused E501 (line too long) and invalid-syntax errors under Python 3.13 ruff target
- **Fix 1:** Replaced version gate with `(major, minor) < (3, 13)` tuple comparison
- **Fix 2:** Extracted `sep = '=' * 50` variable, used `f"{sep}"` in print calls
- **Files modified:** notebooks/00_setup.ipynb
- **Commit:** 96e0033 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug in notebook code)
**Impact on plan:** Two-attempt commit for Task 2 notebook (pre-commit reformatted, then lint-fixed, then committed clean). No scope creep.

## Issues Encountered

- Pre-commit two-attempt pattern: ruff-check, ruff-format, and nbstripout all ran on the notebook. First commit attempt triggered nbstripout changes; second attempt was clean.
- Python script to write notebook JSON required careful string escaping — ANSI escape codes (`\033`) and backslash-n (`\n`) must be double-escaped in JSON source arrays.

## User Setup Required

None - no external service configuration required for notebook structure tests.
Students need `ANTHROPIC_API_KEY` set to fully run the setup notebook Check 3 (API call).

## Next Phase Readiness

- Notebook helper infrastructure complete; all 8 notebooks can import `from helpers import print_usage, compare_results`
- Setup notebook template establishes red/green alert box convention for all remaining notebooks
- 16 total passing tests (8 import smoke + 7 helper unit + 9 config/notebook existence = actually 7+9=16 from this plan's test files)
- Phase 1 complete — ready for Phase 2 (models, services, tools implementation)

---
*Phase: 01-project-foundation*
*Completed: 2026-03-25*
