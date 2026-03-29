# CCA Customer Support Resolution Agent

> Hands-on coding example for the **Claude Certified Architect -- Foundations (CCA-F)** exam prep course.

The **Customer Support Resolution Agent** is a key scenario in the CCA-F exam, designed to test real-world AI agent architecture for high-stakes customer service. This project demonstrates all 6 architectural patterns from the scenario through 9 Jupyter notebooks, pairing anti-patterns (the wrong way) with correct patterns (the right way) so students internalize the distinctions before exam day.

## The CCA Customer Support Scenario

### Core Architecture

This scenario involves a **single-agent loop** using the Anthropic Python SDK, integrated with **5 focused tools**:

| Tool | Type | Purpose |
|------|------|---------|
| `lookup_customer` | Read | Retrieves verified customer profiles (must be called first) |
| `check_policy` | Read | Checks refund eligibility against tier-based policy limits |
| `process_refund` | Write | Executes refund actions (two-step vetoable -- callbacks can block) |
| `escalate_to_human` | Write | Transfers conversation with structured EscalationRecord JSON |
| `log_interaction` | Write | Records interaction for compliance audit (PII redacted before write) |

The agent follows a strict sequence: **Intake -> Verify Identity -> Context Lookup -> Classify -> Act**.

### Key Exam Concepts

The scenario tests critical architectural tradeoffs:

1. **Programmatic Enforcement** -- The exam emphasizes using code (PostToolUse callbacks) over relying on prompts to prevent costly errors. In this project, `callbacks.py` enforces escalation rules deterministically -- amount > $500, VIP tier, account closure, legal keywords.

2. **Tool Description Quality** -- Clear, detailed tool descriptions with negative bounds ("does NOT modify customer data") prevent the agent from misrouting. The 15-tool Swiss Army anti-pattern demonstrates how tool overload degrades selection accuracy.

3. **Explicit Escalation Criteria** -- The agent escalates based on deterministic business rules, NOT self-reported confidence scores. The confidence escalation anti-pattern shows how Claude reports high confidence (>80%) and processes a $600 refund instead of escalating.

4. **Structured Handoffs** -- The `escalate_to_human` tool provides a comprehensive EscalationRecord JSON (customer ID, tier, issue type, escalation reason, recommended action, conversation summary) enforced via `tool_choice`. The raw handoff anti-pattern dumps the entire conversation as unstructured text.

5. **Context Management** -- The agent efficiently manages context through structured JSON summaries that stay under a token budget, while the raw transcript anti-pattern demonstrates unbounded growth and the lost-in-middle effect.

6. **Cost Optimization** -- Prompt caching with `cache_control` on static policy context (90% savings on reads). The Batch API anti-pattern shows why 50% savings with 24-hour latency is always wrong for live customer support.

## Quick Start

```bash
# Install Task runner (if not already installed)
brew install go-task

# One-command setup (installs deps, checks API key, opens setup notebook)
task setup

# Or manually:
poetry install --with notebooks
cp .env.example .env  # Add your ANTHROPIC_API_KEY
poetry run jupyter lab
```

### Available Commands

```bash
task setup      # Install deps + check API key + open setup notebook
task test       # Run all 234 tests
task lint       # Run ruff linter
task verify     # Full verification: tests + lint + import check
task notebook   # Launch Jupyter Lab
```

## Notebooks

| # | Notebook | CCA Pattern | Anti-Pattern |
|---|----------|-------------|--------------|
| 00 | Setup | Environment verification | -- |
| 01 | Escalation | Deterministic callbacks | LLM confidence routing |
| 02 | Compliance | Programmatic PII redaction | Prompt-only rules |
| 03 | Tool Design | 5 focused tools | 15-tool Swiss Army |
| 04 | Cost Optimization | Prompt caching | Batch API for live support |
| 05 | Context Management | Structured summaries | Raw transcript bloat |
| 06 | Handoffs | tool_choice + EscalationRecord | Raw conversation dump |
| 07 | Integration | All 6 patterns in one scenario | -- |
| 08 | Meta-Teaching | Project as CCA example | -- |

Each notebook follows: **Setup -> Anti-Pattern (red box) -> Correct Pattern (green box) -> Compare**

Student TODO placeholders in notebooks 06 and 07 provide hands-on learning opportunities.

## Architecture

```
src/customer_service/
  models/        # Pydantic data models (CustomerProfile, EscalationRecord, etc.)
  services/      # 5 simulated in-memory services + frozen ServiceContainer
  tools/         # Tool schemas (from model_json_schema()), handlers, dispatch registry
  agent/         # Agentic loop, PostToolUse callbacks, context manager, coordinator
  anti_patterns/ # 6 deliberately wrong implementations (imported by notebooks only)
  data/          # Seed customers (C001-C006) and scenarios
```

### Critical Data Flow

```
Customer message
  -> agent_loop.py calls client.messages.create()
  -> Claude returns tool_use blocks
  -> callbacks.py validates each tool call against business rules (BEFORE execution)
  -> if approved: handlers.py dispatches to the correct tool handler -> service call
  -> if blocked: error returned as tool_result, agent retries or escalates
  -> loop continues until end_turn stop reason
```

## CCA Meta-Patterns in This Project

This project doesn't just *teach* CCA patterns -- it *uses* them:

### CLAUDE.md Hierarchy (Level 2: Project)

- `.claude/CLAUDE.md` -- Team standards enforced project-wide (CCA exam: project-level is VCS-tracked, shared across team)
- `CLAUDE.md` (root) -- Architecture docs and build commands

### CI/CD Pipeline Flags

- `.github/workflows/ci.yml` -- Uses `claude -p --bare --output-format json --allowedTools Read,Grep,Glob`
- `-p`: mandatory for non-interactive CI (without it, pipeline hangs)
- `--bare`: reproducibility (no auto-discovery in CI)
- `--allowedTools`: principle of least privilege for CI agents
- Nightly cron runs full test suite

### Custom Skill

- `.claude/skills/review-cca-compliance.md` -- Invoke to review any code for CCA compliance
- Demonstrates custom skills as reusable, on-demand workflows

### Programmatic Enforcement

- `.pre-commit-config.yaml` -- nbstripout + ruff enforced on every commit
- Same principle as callbacks: code enforces rules, not human memory

## Testing

```bash
poetry run pytest              # 234 tests, ~1.3s
poetry run pytest -m integration  # Live API tests (needs ANTHROPIC_API_KEY)
```

Tests follow **behavior-first** verification:
- Test persistent stores (AuditLog, EscalationQueue, FinancialSystem), not just returned JSON
- Every completion claim maps to a specific test
- The PII redaction test checks the actual audit log, not the API response

## CCA Rules Reference

`.planning/CCA-RULES.md` contains the authoritative CCA exam patterns extracted from all 8 source articles. Every line of code in this project complies with these rules.

## Requirements

- Python 3.13+
- Poetry
- `ANTHROPIC_API_KEY` (that's it -- no other services needed)

## License

This project is part of the CCA Exam Prep course by Rick Hightower at Spillwave.
