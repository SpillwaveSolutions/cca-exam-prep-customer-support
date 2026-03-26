---
phase: 2
slug: models-services-and-core-loop
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| **Quick run command** | `poetry run pytest tests/test_models.py tests/test_services.py tests/test_tools.py tests/test_data.py -x -q` |
| **Full suite command** | `poetry run pytest -m "not integration"` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CORE-01 | unit | `poetry run pytest tests/test_models.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | CORE-02, CORE-03 | unit | `poetry run pytest tests/test_services.py -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | STUDENT-02 | unit | `poetry run pytest tests/test_data.py -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | CORE-04 | unit | `poetry run pytest tests/test_tools.py -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | CORE-05 | unit | `poetry run pytest tests/test_tools.py::test_dispatch_routing -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | CORE-06 | unit+integration | `poetry run pytest tests/test_agent_loop.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_models.py` — CORE-01 model validation, JSON schema generation
- [ ] `tests/test_services.py` — CORE-02 service behavior, CORE-03 ServiceContainer frozen
- [ ] `tests/test_tools.py` — CORE-04 schema structure, CORE-05 dispatch routing
- [ ] `tests/test_agent_loop.py` — CORE-06 loop control, usage accumulation
- [ ] `tests/test_data.py` — STUDENT-02 seed data structure
- [ ] `tests/conftest.py` — shared fixtures: make_services(), mock_anthropic_client()

*Framework already installed — no gap*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Agent loop completes with live API | CORE-06 | Requires ANTHROPIC_API_KEY | Run `poetry run pytest tests/test_agent_loop.py -m integration` with key set |
| __main__.py runs full scenario | N/A | Requires live API | Run `poetry run python -m customer_service` and verify output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
