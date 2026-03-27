---
phase: 4
slug: caching-and-context-notebooks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 4 — Validation Strategy

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 |
| **Quick run command** | `poetry run pytest tests/test_caching.py tests/test_context_manager.py -x -q` |
| **Full suite command** | `poetry run pytest -m "not integration"` |
| **Estimated runtime** | ~3 seconds |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | OPTIM-01 | unit | `poetry run pytest tests/test_caching.py -x` | ❌ W0 | ⬜ |
| 04-01-02 | 01 | 1 | OPTIM-02 | unit | `poetry run pytest tests/test_context_manager.py -x` | ❌ W0 | ⬜ |
| 04-01-03 | 01 | 1 | ANTI-04 | unit | `poetry run pytest tests/test_caching.py -x` | ❌ W0 | ⬜ |
| 04-02-01 | 02 | 2 | NB-05, NB-06 | smoke | `poetry run pytest tests/test_notebooks.py -x` | ❌ W0 | ⬜ |

---

## Wave 0 Requirements

- [ ] `tests/test_caching.py` — OPTIM-01: cache_control format, POLICY_DOCUMENT > 2048 tokens, system prompt list-of-blocks
- [ ] `tests/test_context_manager.py` — OPTIM-02: ContextSummary update, token budget, to_system_context
- [ ] Updated `tests/test_anti_patterns.py` — ANTI-04: batch_api_live.py and raw_transcript.py structural tests
- [ ] Updated `tests/test_notebooks.py` — NB-05/06: notebook existence and section structure

---

## Behavioral Tests Required

- [ ] POLICY_DOCUMENT exceeds 2048 tokens (caching threshold)
- [ ] ContextSummary token_estimate stays under budget after 10 updates
- [ ] ContextSummary preserves key facts from early turns
- [ ] system prompt with caching returns list-of-blocks format (not string)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual |
|----------|-------------|------------|
| cache_read_input_tokens > 0 on second API call | OPTIM-01 | Requires live API |
| NB04 shows cost difference between cached/uncached | NB-05 | Requires live API |
| NB05 shows transcript growth vs summary stability | NB-06 | Requires live API |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify
- [ ] Behavioral tests cover stores/state, not just returned values
- [ ] Every claim maps to a test
- [ ] `nyquist_compliant: true` set

**Approval:** pending
