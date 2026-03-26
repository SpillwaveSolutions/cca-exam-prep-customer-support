---
phase: 3
slug: callbacks-enforcement-and-first-notebooks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `poetry run pytest tests/test_callbacks.py -x -q` |
| **Full suite command** | `poetry run pytest -m "not integration"` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run `poetry run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ENFORCE-01, ENFORCE-02, ENFORCE-03 | unit | `poetry run pytest tests/test_callbacks.py -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | ANTI-01, ANTI-02, ANTI-03 | unit | `poetry run pytest tests/test_anti_patterns.py -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 3 | NB-02, NB-03, NB-04 | smoke | `poetry run pytest tests/test_notebooks.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_callbacks.py` — ENFORCE-01/02/03 callback dispatch, escalation rules, compliance redaction
- [ ] `tests/test_anti_patterns.py` — ANTI-01/02/03 Swiss Army tool count, prompt compliance, confidence prompt
- [ ] `tests/test_notebooks.py` — NB-02/03/04 notebook existence and section structure

*No new framework needed*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notebook 01 end-to-end with live API | NB-02 | Requires ANTHROPIC_API_KEY | Run all cells, verify anti-pattern approves $600, correct pattern escalates |
| Notebook 02 PII redaction demo | NB-03 | Requires live API | Run all cells, verify anti-pattern logs raw card, correct pattern redacts |
| Notebook 03 tool selection contrast | NB-04 | Requires live API + probabilistic | Run all cells, verify 15-tool agent misroutes (note: ~70% reliable) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
