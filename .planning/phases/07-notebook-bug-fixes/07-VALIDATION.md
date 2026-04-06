---
phase: 7
slug: notebook-bug-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-06
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Poetry-managed) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `poetry run pytest tests/test_callbacks.py -x` |
| **Full suite command** | `poetry run pytest` |
| **Estimated runtime** | ~0.10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `poetry run pytest tests/test_callbacks.py -x`
- **After every plan wave:** Run `poetry run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green + all 3 notebooks execute without error
- **Max feedback latency:** 1 second (pytest), ~60 seconds (notebook execution)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | NBFIX-01 | notebook execution | `jupyter nbconvert --to notebook --execute notebooks/04_cost_optimization.ipynb` | ✅ | ⬜ pending |
| 07-01-02 | 01 | 1 | NBFIX-02 | notebook execution | `jupyter nbconvert --to notebook --execute notebooks/05_context-management.ipynb` | ✅ | ⬜ pending |
| 07-01-03 | 01 | 1 | NBFIX-03 | notebook execution | `jupyter nbconvert --to notebook --execute notebooks/01_escalation.ipynb` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — existing test infrastructure covers callback logic. Notebook execution is validated manually or via `nbconvert --execute`. No new test files needed for Phase 7.

---

## Phase Gate

All three conditions must be true before `/gsd:verify-work`:
1. `poetry run pytest` exits 0 (no regressions)
2. NB04, NB05 make_services() cells execute without TypeError
3. NB01 correct-pattern escalation cell shows non-empty escalation queue
