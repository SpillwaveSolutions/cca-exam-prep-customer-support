# CCA Exam Prep: Customer Support Resolution Agent

## What This Is

A hands-on coding example for the CCA Exam Prep course that demonstrates all 6 architectural patterns from the Customer Support Resolution Agent scenario article. Students learn by running anti-patterns (the wrong way) side-by-side with correct patterns (the right way) through 9 Jupyter notebooks, backed by a production-quality Python package using the Claude API. The project itself demonstrates CCA meta-patterns: `.claude/CLAUDE.md` hierarchy, CI/CD with `-p --bare`, and custom skills.

## Core Value

Students can run code that demonstrates every CCA Customer Support anti-pattern failure and its correct architectural fix, so they internalize the patterns before exam day.

## Current State

**Shipped:** v1.0 — 2026-03-28
**Stack:** Python 3.13+, Poetry, Pydantic v2, Anthropic SDK 0.86.0
**Code:** 2,872 LOC production + 3,841 LOC tests = 6,713 total
**Tests:** 234 passing (0.10s)
**Notebooks:** 9 (00-08) covering all 6 CCA patterns + setup + integration + meta-teaching

## Requirements

### Validated (v1.0)

- ✓ Importable Python package with 6 sub-packages — v1.0
- ✓ 6 Pydantic models, 5 deterministic services, frozen ServiceContainer — v1.0
- ✓ 5 focused tool schemas with negative-bound descriptions — v1.0
- ✓ stop_reason-controlled agentic loop with UsageSummary — v1.0
- ✓ Per-tool callback registry with two-step vetoable process_refund — v1.0
- ✓ Programmatic PII redaction before audit log write — v1.0
- ✓ 3 anti-pattern modules (confidence, prompt compliance, Swiss Army) — v1.0
- ✓ Prompt caching with POLICY_DOCUMENT (4079 tokens) + cache_control — v1.0
- ✓ ContextSummary with budget compaction — v1.0
- ✓ tool_choice forced structured escalation handoffs — v1.0
- ✓ Coordinator-subagent with context isolation — v1.0
- ✓ 9 notebooks (00-08) with CCA Exam Tip boxes — v1.0
- ✓ Seed data: 6 customers + 6 scenarios targeting all escalation rules — v1.0
- ✓ GitHub Actions CI/CD with `-p --bare --output-format json` — v1.0
- ✓ Custom CCA compliance review skill — v1.0
- ✓ 3+ student TODO placeholders with try/except guards — v1.0
- ✓ Behavior-first testing: test stores not API responses — v1.0

### Active (v1.1 — Notebook Fixes)

- ✓ Fix `make_services()` seed data initialization in NB04 and NB05 — Phase 7
- ✓ Fix $600 refund escalation callback not triggering in NB01 — Phase 7
- ✓ Fix context management anti-pattern demo in NB05 — Phase 7
- [ ] Review and complete handoffs notebook (NB06) — verify output, complete TODOs
- [ ] Complete integration notebook (NB07) — implement all remaining TODOs

### Out of Scope

- Real database or external service integrations — simulated only, zero infrastructure setup
- Claude Agent SDK — using raw Anthropic Python SDK to teach fundamentals
- Async/streaming — synchronous calls keep teaching code readable
- Deployment or production hosting — this is a learning project
- Streamlit UI — considered but deferred

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Simulated services over Firebase | Students need zero infrastructure setup | ✓ Good |
| Both notebooks AND package | Notebooks for learning, package for production reference | ✓ Good |
| Anti-pattern-first ordering | "Productive failure" — feel the pain before the fix | ✓ Good |
| 5 focused tools matching article spec | Direct mapping to CCA exam tool count guidance (4-5) | ✓ Good |
| Per-tool callback registry | Each callback fires only for its registered tool, no cross-tool bugs | ✓ Good |
| Block-not-bypass escalation | Claude calls escalate_to_human naturally, preserving expected tool trace | ✓ Good |
| Pre-handler redaction for log_interaction | PII must never reach audit log — redact before write, not after | ✓ Good |
| claude -p --bare for CI/CD | Demonstrates CCA Article 2 best practices in the project itself | ✓ Good |
| Behavior-first testing rules | Emerged from PII audit log bug — test stores, not API responses | ✓ Good |
| CCA-RULES.md as authoritative reference | Extracted from all 8 source articles, prevents contradicting exam material | ✓ Good |

## Context

This is the first coding example in a CCA Exam Prep course series by Rick Hightower at Spillwave. The companion article covers the Customer Support Resolution Agent scenario — the hardest of the 6 CCA exam scenarios. The article identifies 6 decision patterns where candidates pick the plausible-sounding wrong answer.

Known tech debt: VALIDATION.md `nyquist_compliant` frontmatter never flipped to `true` (cosmetic), notebook smoke tests are structural only. See `.planning/v1.0-MILESTONE-AUDIT.md` for full audit.

## Constraints

- **Python**: 3.13+ with Poetry for dependency management
- **API**: Anthropic Python SDK (anthropic >= 0.42.0), Pydantic >= 2.0
- **Format**: Both Jupyter notebooks (teaching) AND Python package (production)
- **Dependencies**: Students need only `ANTHROPIC_API_KEY` — no other services
- **Teaching**: Each notebook shows WRONG way first, then CORRECT way
- **CCA Accuracy**: All patterns must match Anthropic's recommended architectural patterns exactly

---
## Current Milestone: v1.1 Notebook Fixes

**Goal:** Fix broken notebook cells and complete unfinished notebook sections so all 9 notebooks run end-to-end correctly.

**Target fixes:**
- `make_services()` missing seed data (blocks NB04, NB05)
- Escalation callback not firing for $600 refund (NB01)
- Context management anti-pattern demo broken (NB05)
- Handoffs notebook incomplete/suspect output (NB06)
- Integration notebook has remaining TODOs (NB07)

---
*Last updated: 2026-04-06 after Phase 7 completion*
