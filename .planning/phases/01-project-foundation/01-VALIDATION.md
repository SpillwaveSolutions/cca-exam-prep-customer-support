---
phase: 1
slug: project-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| **Quick run command** | `poetry run pytest tests/ -x -q` |
| **Full suite command** | `poetry run pytest tests/` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `poetry run pytest tests/ -x -q`
- **After every plan wave:** Run `poetry run pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | SETUP-01 | smoke | `poetry run pytest tests/test_imports.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | SETUP-01 | smoke | `poetry run pytest tests/test_imports.py -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | SETUP-02 | unit | `poetry run pytest tests/test_helpers.py::test_print_usage -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | SETUP-02 | unit | `poetry run pytest tests/test_helpers.py::test_compare_results -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 01 | 1 | SETUP-03 | smoke | `poetry run pytest tests/test_config.py::test_precommit_config -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 02 | 2 | NB-01 | smoke | `poetry run pytest tests/test_config.py::test_setup_notebook_exists -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — makes tests/ a package
- [ ] `tests/test_imports.py` — covers SETUP-01 import smoke tests
- [ ] `tests/test_helpers.py` — covers SETUP-02 helper function unit tests
- [ ] `tests/test_config.py` — covers SETUP-03 config file existence, NB-01 notebook existence

*Framework already installed via `poetry install` — no gap*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notebook 00 runs end-to-end with live API call | NB-01 | Requires ANTHROPIC_API_KEY and live API | Run `jupyter lab`, open `notebooks/00_setup.ipynb`, execute all cells, verify 4 green checkmarks |
| Pre-commit hooks reject unstripped notebook | SETUP-03 | Requires git commit attempt | `git add notebooks/00_setup.ipynb && git commit -m "test"` — should fail if outputs present |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
