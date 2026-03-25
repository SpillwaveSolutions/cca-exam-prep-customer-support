---
phase: 01-project-foundation
plan: 01
subsystem: infra
tags: [python, poetry, pre-commit, ruff, nbstripout, pytest, package-skeleton]

# Dependency graph
requires: []
provides:
  - Importable customer_service package with __version__ = "0.1.0"
  - Six importable sub-packages: agent, anti_patterns, data, models, services, tools
  - python -m customer_service entry point skeleton returning 0
  - .pre-commit-config.yaml with ruff (check + format, jupyter support) and nbstripout hooks
  - pre-commit and nbstripout in pyproject.toml dev dependencies
  - tests/test_imports.py (8 passing smoke tests)
  - tests/test_config.py (7 passing config tests)
affects:
  - 01-02 (notebooks phase - needs importable package)
  - 02-models (needs sub-packages as stubs)
  - all subsequent phases

# Tech tracking
tech-stack:
  added: [pre-commit >= 3.0, nbstripout >= 0.7]
  patterns:
    - "src/ layout with packages = [{include = 'customer_service', from = 'src'}]"
    - "TDD: write failing tests first (RED), create implementation (GREEN)"
    - "Sub-package __init__.py with docstring-only stubs for Phase 1"
    - "Pre-commit hooks using types_or: [python, pyi, jupyter] for ruff"

key-files:
  created:
    - src/customer_service/__init__.py
    - src/customer_service/__main__.py
    - src/customer_service/agent/__init__.py
    - src/customer_service/anti_patterns/__init__.py
    - src/customer_service/data/__init__.py
    - src/customer_service/models/__init__.py
    - src/customer_service/services/__init__.py
    - src/customer_service/tools/__init__.py
    - .pre-commit-config.yaml
    - tests/__init__.py
    - tests/test_imports.py
    - tests/test_config.py
    - README.md
  modified:
    - pyproject.toml
    - poetry.lock

key-decisions:
  - "Keep Phase 1 __init__.py minimal (version + docstring only) — no re-exports until Phase 2 modules exist (avoids ImportError)"
  - "Use pre-commit hook mode for nbstripout (not git filter mode) — explicit and auditable"
  - "ruff types_or: [python, pyi, jupyter] required for notebook linting — types: [python] alone misses .ipynb files"
  - "Created README.md as deviation fix — pyproject.toml readme field required it for poetry install to succeed"

patterns-established:
  - "Pattern 1: TDD RED-GREEN — write failing tests before creating implementation files"
  - "Pattern 2: Sub-package stubs — minimal __init__.py with docstring only; populate in the phase that adds modules"
  - "Pattern 3: Pre-commit hook ordering — ruff-check (--fix) before ruff-format, both with types_or jupyter"

requirements-completed: [SETUP-01, SETUP-03]

# Metrics
duration: 2min
completed: 2026-03-25
---

# Phase 1 Plan 01: Package Skeleton and Pre-commit Configuration Summary

**Importable 6-subpackage Python skeleton with ruff+nbstripout pre-commit hooks and 15 passing smoke tests**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T23:10:55Z
- **Completed:** 2026-03-25T23:12:58Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments

- Established importable customer_service package with all 6 sub-packages (agent, anti_patterns, data, models, services, tools)
- Created __main__.py entry point skeleton that prints setup instructions and returns 0
- Configured pre-commit hooks for ruff (check + format with jupyter support) and nbstripout notebook output stripping
- Added 15 automated smoke tests covering imports and config file validity

## Task Commits

Each task was committed atomically:

1. **Task 1: Create package __init__.py files, __main__.py, and Wave 0 import tests** - `8de4deb` (feat)
2. **Task 2: Configure pre-commit hooks and add dev dependencies** - `975b1f8` (feat)

## Files Created/Modified

- `src/customer_service/__init__.py` - Package root with `__version__ = "0.1.0"`
- `src/customer_service/__main__.py` - CLI entry point skeleton with `main() -> int`
- `src/customer_service/agent/__init__.py` - Agent sub-package stub
- `src/customer_service/anti_patterns/__init__.py` - Anti-patterns sub-package stub
- `src/customer_service/data/__init__.py` - Data sub-package stub
- `src/customer_service/models/__init__.py` - Models sub-package stub
- `src/customer_service/services/__init__.py` - Services sub-package stub
- `src/customer_service/tools/__init__.py` - Tools sub-package stub
- `.pre-commit-config.yaml` - ruff-check (--fix), ruff-format (both with jupyter), nbstripout
- `tests/__init__.py` - Empty test package marker
- `tests/test_imports.py` - 8 import smoke tests
- `tests/test_config.py` - 7 config file tests
- `README.md` - Project readme (required by pyproject.toml)
- `pyproject.toml` - Added pre-commit >= 3.0 and nbstripout >= 0.7 to dev dependencies
- `poetry.lock` - Updated lock file with new dependencies

## Decisions Made

- Kept Phase 1 `__init__.py` minimal (version + docstring only) — no re-exports until Phase 2 modules exist per RESEARCH.md Pitfall 5
- Used pre-commit hook mode for nbstripout (not `nbstripout --install` git filter mode) — explicit and auditable per RESEARCH.md Pitfall 2
- Used `types_or: [python, pyi, jupyter]` for ruff hooks to include Jupyter notebook linting — `types: [python]` alone misses `.ipynb` files per RESEARCH.md Pitfall 3

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created README.md for poetry install**
- **Found during:** Task 1 (after creating __init__.py files, first `poetry install` failed)
- **Issue:** `pyproject.toml` references `readme = "README.md"` but file did not exist; `poetry install` exited with error "Readme path does not exist"
- **Fix:** Created minimal README.md with project description and quick-start commands
- **Files modified:** README.md
- **Verification:** `poetry install` succeeded after creation
- **Committed in:** 8de4deb (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking issue)
**Impact on plan:** Required for any user to run `poetry install`. No scope creep.

## Issues Encountered

- Pre-commit reformatted `tests/test_config.py` on first commit attempt (ruff-format added blank line after imports). Re-staged and committed successfully on second attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Package skeleton complete; all 6 sub-packages importable
- Pre-commit hooks installed and validated
- TDD infrastructure in place (pytest + 15 passing tests)
- Ready for Plan 02: notebook infrastructure (notebooks/helpers.py + setup notebook)
- Phase 2 (models, services) can begin immediately after Phase 1 is complete

---
*Phase: 01-project-foundation*
*Completed: 2026-03-25*
