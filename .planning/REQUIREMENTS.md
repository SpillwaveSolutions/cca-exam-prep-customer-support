# Requirements: CCA Customer Support Resolution Agent

## v1 Requirements

### Setup (SETUP)

- **SETUP-01**: Project skeleton with `src/` layout, pyproject.toml, Poetry config, `.env.example`, `.gitignore`
- **SETUP-02**: Notebook template with anti-pattern-first ordering (Setup > Anti-Pattern > Correct > Compare), `print_usage` helper, visual differentiation (red/green HTML boxes)
- **SETUP-03**: Pre-commit hooks (nbstripout + ruff) for notebook and code hygiene

### Models and Services (CORE)

- **CORE-01**: Pydantic v2 data models (CustomerProfile, RefundRequest, EscalationRecord, PolicyResult, etc.)
- **CORE-02**: Simulated in-memory services with input-sensitive behavior (CustomerDB, PolicyEngine, RefundProcessor, EscalationQueue, AuditLog)
- **CORE-03**: ServiceContainer dataclass for dependency injection across tools
- **CORE-04**: 5 focused tool schemas (lookup_customer, check_policy, process_refund, escalate_to_human, log_interaction) with JSON Schema via `model_json_schema()`
- **CORE-05**: Tool dispatch registry routing tool_use blocks to correct handler
- **CORE-06**: Base agentic loop with `stop_reason` control (not content-type checking)

### Callbacks and Enforcement (ENFORCE)

- **ENFORCE-01**: PostToolUse callback framework for rule enforcement after every tool execution
- **ENFORCE-02**: Deterministic escalation rules (amount > $500, account closure, VIP, legal keywords)
- **ENFORCE-03**: Programmatic compliance enforcement (redaction, audit logging) in application layer

### Anti-Patterns (ANTI)

- **ANTI-01**: 15-tool Swiss Army anti-pattern agent for tool design comparison
- **ANTI-02**: Prompt-only compliance enforcement anti-pattern (no programmatic hooks)
- **ANTI-03**: LLM confidence-based escalation anti-pattern
- **ANTI-04**: Raw transcript context anti-pattern (no structured summaries)
- **ANTI-05**: Raw conversation dump handoff anti-pattern (unstructured escalation)

### Caching and Context (OPTIM)

- **OPTIM-01**: Prompt caching with `cache_control` markers on static policy context and token accounting
- **OPTIM-02**: Context management with structured JSON summaries

### Handoffs and Coordination (HANDOFF)

- **HANDOFF-01**: Structured JSON escalation handoff via `tool_choice` enforcement (EscalationRecord)
- **HANDOFF-02**: Coordinator-subagent pattern for multi-agent orchestration

### Notebooks (NB)

- **NB-01**: Notebook 00 - Setup and environment verification
- **NB-02**: Notebook 01 - Escalation pattern (deterministic rules vs LLM confidence)
- **NB-03**: Notebook 02 - Compliance pattern (programmatic hooks vs prompt instructions)
- **NB-04**: Notebook 03 - Tool design pattern (5 focused tools vs 15-tool Swiss Army)
- **NB-05**: Notebook 04 - Cost optimization pattern (prompt caching vs Batch API misuse)
- **NB-06**: Notebook 05 - Context management pattern (structured summaries vs raw transcript)
- **NB-07**: Notebook 06 - Handoff pattern (structured JSON vs raw conversation dump)
- **NB-08**: Notebook 07 - Integration notebook combining all 6 patterns

### Testing and CI/CD (CICD)

- **CICD-01**: pytest suite for callbacks and tool routing
- **CICD-02**: GitHub Actions CI/CD with `claude -p --bare` (PR review, nightly cron)
- **CICD-03**: Project-level `.claude/CLAUDE.md` and custom skills as meta-teaching examples

### Student Experience (STUDENT)

- **STUDENT-01**: Student TODO placeholders that do not break notebook execution
- **STUDENT-02**: Seed data (customers, policies, scenarios) designed to trigger specific escalation rules

## Out of Scope (v2+)

- Real database or external service integrations
- Firebase backend
- Claude Agent SDK (using raw SDK)
- Async/streaming
- Deployment or production hosting
- Additional student exercise variations
- nbval notebook smoke tests in CI (wait for notebook stability)
- VCR cassettes for integration tests (wait for API patterns to stabilize)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1 | Complete |
| SETUP-02 | Phase 1 | Complete |
| SETUP-03 | Phase 1 | Complete |
| CORE-01 | Phase 2 | Complete |
| CORE-02 | Phase 2 | Complete |
| CORE-03 | Phase 2 | Complete |
| CORE-04 | Phase 2 | Complete |
| CORE-05 | Phase 2 | Complete |
| CORE-06 | Phase 2 | Complete |
| ENFORCE-01 | Phase 3 | Complete |
| ENFORCE-02 | Phase 3 | Complete |
| ENFORCE-03 | Phase 3 | Complete |
| ANTI-01 | Phase 3 | Complete |
| ANTI-02 | Phase 3 | Complete |
| ANTI-03 | Phase 3 | Complete |
| ANTI-04 | Phase 4 | Pending |
| ANTI-05 | Phase 5 | Pending |
| OPTIM-01 | Phase 4 | Pending |
| OPTIM-02 | Phase 4 | Pending |
| HANDOFF-01 | Phase 5 | Pending |
| HANDOFF-02 | Phase 5 | Pending |
| NB-01 | Phase 1 | Complete |
| NB-02 | Phase 3 | Pending |
| NB-03 | Phase 3 | Pending |
| NB-04 | Phase 3 | Pending |
| NB-05 | Phase 4 | Pending |
| NB-06 | Phase 4 | Pending |
| NB-07 | Phase 5 | Pending |
| NB-08 | Phase 5 | Pending |
| CICD-01 | Phase 6 | Pending |
| CICD-02 | Phase 6 | Pending |
| CICD-03 | Phase 6 | Pending |
| STUDENT-01 | Phase 5 | Pending |
| STUDENT-02 | Phase 2 | Complete |

---
*Created: 2026-03-25*
