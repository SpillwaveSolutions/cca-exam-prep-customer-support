---
phase: 8
slug: notebook-completion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-06
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Poetry-managed) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `poetry run pytest tests/test_notebook_execution.py -x` |
| **Full suite command** | `poetry run pytest` |
| **Estimated runtime** | ~5 seconds (includes notebook cell execution) |

---

## Sampling Rate

- **After every task commit:** Run `poetry run pytest tests/test_notebooks.py tests/test_notebook_execution.py -x`
- **After every plan wave:** Run `poetry run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | NBCOMP-01 | structural | `poetry run pytest tests/test_notebooks.py::test_notebook_06_sections -x` | ✅ | ⬜ pending |
| 08-01-02 | 01 | 1 | NBCOMP-02 | structural | `poetry run pytest tests/test_notebooks.py::test_notebook_07_has_six_cca_exam_tips -x` | ✅ | ⬜ pending |
| 08-01-03 | 01 | 1 | NBCOMP-01/02 | execution | `poetry run pytest tests/test_notebook_execution.py -x` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_notebook_execution.py` — headless execution tests for NB06/NB07 non-API cells

---

## Phase Gate

All conditions must be true before `/gsd:verify-work`:
1. `poetry run pytest` exits 0 (no regressions)
2. NB06 has no developer TODOs and comparison output verified correct
3. NB07 has all 6 CCA pattern sections complete
4. Non-API cells in both notebooks execute without error in headless test
