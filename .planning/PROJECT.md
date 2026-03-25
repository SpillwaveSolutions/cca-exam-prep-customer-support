# CCA Exam Prep: Customer Support Resolution Agent

## What This Is

A hands-on coding example for the CCA Exam Prep course that demonstrates all 6 architectural patterns from the Customer Support Resolution Agent scenario article. Students learn by running anti-patterns (the wrong way) side-by-side with correct patterns (the right way) through Jupyter notebooks, backed by a production-quality Python package using the Claude API.

## Core Value

Students can run code that demonstrates every CCA Customer Support anti-pattern failure and its correct architectural fix, so they internalize the patterns before exam day.

## Requirements

### Validated

- [x] Importable Python package skeleton with 6 sub-packages — Validated in Phase 1: Project Foundation
- [x] Notebook template with anti-pattern vs correct-pattern visual differentiation (red/green HTML boxes) — Validated in Phase 1
- [x] Setup notebook (00) with 4 environment verification checks — Validated in Phase 1
- [x] Pre-commit hooks (nbstripout + ruff) — Validated in Phase 1
- [x] print_usage and compare_results helpers for token accounting — Validated in Phase 1
- [x] Taskfile.yml for automated project setup and verification — Validated in Phase 1

### Active

- [ ] Notebooks (00-07) covering all 6 CCA patterns with anti-pattern vs correct pattern contrast
- [ ] Production Python package with Pydantic models, simulated services, Claude API tools, callbacks
- [ ] Deterministic escalation logic via PostToolUse callbacks (amount > $500, account closure, VIP, legal)
- [ ] Programmatic compliance enforcement in application layer, not prompt instructions
- [ ] 5 focused tools per agent (lookup_customer, check_policy, process_refund, escalate_to_human, log_interaction)
- [ ] 15-tool Swiss Army anti-pattern for tool design comparison
- [ ] Prompt caching demonstration with cache_control markers on static policy context
- [ ] Structured JSON escalation handoffs via tool_choice enforcement
- [ ] Context management with structured summaries vs raw transcript comparison
- [ ] Coordinator-subagent pattern for when tools exceed 4-5 per agent
- [ ] GitHub Actions CI/CD with `claude -p --bare` (PR review, nightly cron, weekly docs)
- [ ] Project-level `.claude/CLAUDE.md` and custom skills as living CCA best-practice examples
- [ ] Simulated in-memory services (students only need ANTHROPIC_API_KEY)
- [ ] Student contribution opportunities (TODO placeholders for hands-on learning)

### Out of Scope

- Real database or external service integrations — simulated only, zero infrastructure setup
- Firebase backend — was considered, decided against for student simplicity
- Claude Agent SDK — using raw Anthropic Python SDK to teach fundamentals
- Async/streaming — synchronous calls keep the teaching code readable
- Deployment or production hosting — this is a learning project

## Context

This is the first coding example in a CCA Exam Prep course series by Rick Hightower at Spillwave. The companion article (published at /Users/richardhightower/articles/articles/cca-customer-support/work/final/article_publication_ready.md) covers the Customer Support Resolution Agent scenario — the hardest of the 6 CCA exam scenarios. The article identifies 6 decision patterns where candidates pick the plausible-sounding wrong answer.

The project itself serves as a meta-teaching tool: the `.claude/CLAUDE.md`, custom skills, and GitHub Actions CI/CD demonstrate the CCA best practices that Article 2 (Code Generation with Claude Code) covers — CLAUDE.md hierarchy, `-p` flag for CI/CD, custom skills.

Rick has completed the Claude API course on Anthropic Academy and works in Python 3.13+ with Poetry, Pydantic, and multiple LLM integrations.

## Constraints

- **Python**: 3.13+ with Poetry for dependency management
- **API**: Anthropic Python SDK (anthropic >= 0.42.0), Pydantic >= 2.0
- **Format**: Both Jupyter notebooks (teaching) AND Python package (production)
- **Dependencies**: Students need only `ANTHROPIC_API_KEY` — no other services
- **Teaching**: Each notebook must show WRONG way first, then CORRECT way
- **CCA Accuracy**: All patterns must match Anthropic's recommended architectural patterns exactly

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Simulated services over Firebase | Students need zero infrastructure setup | — Pending |
| Both notebooks AND package | Notebooks for learning, package for production reference | — Pending |
| Side-by-side anti-pattern contrast | Mirrors exam format — wrong answers look right | — Pending |
| 5 focused tools matching article spec | Direct mapping to CCA exam tool count guidance (4-5) | — Pending |
| PostToolUse callbacks for enforcement | Matches Claude Agent SDK pattern; programmatic > prompt-based | — Pending |
| claude -p --bare for CI/CD | Demonstrates CCA Article 2 best practices in the project itself | — Pending |

---
*Last updated: 2026-03-25 after Phase 1 completion*
