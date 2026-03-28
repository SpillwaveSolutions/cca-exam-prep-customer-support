---
phase: 5
slug: handoffs-integration-and-student-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 5 — Validation Strategy

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 |
| **Quick run command** | `poetry run pytest tests/test_handoffs.py tests/test_coordinator.py -x -q` |
| **Full suite command** | `poetry run pytest -m "not integration"` |
| **Estimated runtime** | ~3 seconds |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | HANDOFF-01, ANTI-05 | unit | `poetry run pytest tests/test_handoffs.py -x` | ❌ W0 | ⬜ |
| 05-01-02 | 01 | 1 | HANDOFF-02 | unit | `poetry run pytest tests/test_coordinator.py -x` | ❌ W0 | ⬜ |
| 05-02-01 | 02 | 2 | NB-07, NB-08, STUDENT-01 | smoke | `poetry run pytest tests/test_notebooks.py -x` | exists | ⬜ |

---

## Behavioral Tests Required

- [ ] tool_choice produces EscalationRecord in escalation_queue (test store, not just return)
- [ ] Subagent messages list does NOT contain coordinator history (context isolation proof)
- [ ] Raw handoff output contains tool_use/tool_result blocks (observable noise)
- [ ] Student TODOs don't break notebook execution when unfilled
- [ ] Integration notebook references all 6 CCA patterns

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual |
|----------|-------------|------------|
| NB06 shows tool_choice forcing structured handoff | NB-07 | Requires live API |
| NB07 integration touches all 6 patterns | NB-08 | Requires live API |
| TODOs are pedagogically valuable | STUDENT-01 | Subjective quality |

**Approval:** pending
