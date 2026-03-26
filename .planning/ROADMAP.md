# Roadmap: CCA Customer Support Resolution Agent

## Overview

This project builds a hands-on CCA Exam Prep coding example in 6 phases, following the dependency graph: project skeleton and notebook template first, then Pydantic models and simulated services with the core agentic loop, then the PostToolUse callback enforcement layer with the first three teaching notebooks, then prompt caching and context management notebooks, then structured handoffs and the integration notebook, and finally testing and CI/CD polish. Each phase delivers a coherent, verifiable capability that students can run.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Project Foundation** - Skeleton, notebook template, pre-commit hooks, setup notebook (completed 2026-03-25)
- [ ] **Phase 2: Models, Services, and Core Loop** - Pydantic models, input-sensitive services, tool schemas, agentic loop, seed data
- [ ] **Phase 3: Callbacks, Enforcement, and First Notebooks** - PostToolUse callbacks, escalation/compliance rules, anti-patterns, notebooks 01-03
- [ ] **Phase 4: Caching and Context Notebooks** - Prompt caching with token accounting, context management, notebooks 04-05
- [ ] **Phase 5: Handoffs, Integration, and Student Polish** - Structured handoffs, coordinator-subagent, notebooks 06-07, TODO placeholders
- [ ] **Phase 6: Testing and CI/CD** - pytest suite, GitHub Actions, CLAUDE.md meta-teaching layer

## Phase Details

### Phase 1: Project Foundation
**Goal**: Students can clone the repo, install dependencies, and run a setup notebook that verifies their environment
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, NB-01
**Success Criteria** (what must be TRUE):
  1. Running `poetry install` succeeds and `from customer_service import ...` works in a Python shell
  2. Notebook 00 (setup) runs end-to-end, verifying ANTHROPIC_API_KEY and SDK version
  3. Pre-commit hooks (nbstripout, ruff) run on `git commit` and reject unstripped notebooks or lint failures
  4. Notebook template exists with correct-before-anti-pattern section ordering and `print_usage` helper
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Package skeleton, __init__.py files, __main__.py, pre-commit hooks
- [x] 01-02-PLAN.md — Notebook helpers (print_usage, compare_results) and setup notebook (00)

### Phase 2: Models, Services, and Core Loop
**Goal**: The 5-tool customer support agent can process a customer message through a complete agentic loop using simulated services
**Depends on**: Phase 1
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06, STUDENT-02
**Success Criteria** (what must be TRUE):
  1. Pydantic models (CustomerProfile, RefundRequest, EscalationRecord, PolicyResult) validate data and generate JSON Schema via `model_json_schema()`
  2. Simulated services return different results based on customer tier, refund amount, and account flags (input-sensitive behavior verified)
  3. The agentic loop processes a customer message, dispatches tool calls, and terminates on `stop_reason == "end_turn"` (not content-type checking)
  4. All 5 tool schemas are registered and the dispatch registry routes tool_use blocks to correct handlers
  5. Seed data includes customers and scenarios that trigger escalation thresholds ($600 refund, VIP customer, legal mention, account closure)
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Pydantic models, 5 simulated services, ServiceContainer, seed data (C001-C006), and scenarios
- [ ] 02-02-PLAN.md — 5 tool schemas with negative bounds, dispatch registry, agentic loop, system prompt, package re-exports

### Phase 3: Callbacks, Enforcement, and First Notebooks
**Goal**: Students can run notebooks 01-03 and observe how deterministic callbacks catch what prompt-only rules miss, and how 5 focused tools outperform 15
**Depends on**: Phase 2
**Requirements**: ENFORCE-01, ENFORCE-02, ENFORCE-03, ANTI-01, ANTI-02, ANTI-03, NB-02, NB-03, NB-04
**Success Criteria** (what must be TRUE):
  1. PostToolUse callbacks block a $600 refund and force escalation -- the callback fires automatically, not via prompt instruction
  2. The compliance anti-pattern (prompt-only rules) fails to redact sensitive data in at least one scenario where the programmatic callback succeeds
  3. The 15-tool Swiss Army agent produces worse tool selection on the same query where the 5-tool agent succeeds cleanly
  4. Notebooks 01 (escalation), 02 (compliance), and 03 (tool design) each run end-to-end showing anti-pattern failure followed by correct-pattern success
  5. Each notebook displays token usage via `print_usage` helper so students see cost differences
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Caching and Context Notebooks
**Goal**: Students can observe prompt caching savings with concrete token numbers and compare structured context summaries against raw transcript bloat
**Depends on**: Phase 2 (requires working agentic loop; independent of Phase 3 enforcement layer)
**Requirements**: OPTIM-01, OPTIM-02, ANTI-04, NB-05, NB-06
**Success Criteria** (what must be TRUE):
  1. Prompt caching notebook shows `cache_read_input_tokens > 0` on second API call, with token accounting proving cost reduction
  2. The `cache_control` marker is placed on static policy context (not dynamic user messages) -- students can see this in the system message structure
  3. Context management notebook shows structured JSON summary staying under a token budget while raw transcript grows unbounded over multi-turn conversation
  4. Notebooks 04 (cost optimization) and 05 (context management) each run end-to-end with visible before/after comparison
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Handoffs, Integration, and Student Polish
**Goal**: Students can see structured escalation handoffs in action, run the full integration notebook combining all 6 patterns, and find TODO placeholders for hands-on learning
**Depends on**: Phase 3, Phase 4 (requires all 6 patterns working)
**Requirements**: HANDOFF-01, HANDOFF-02, ANTI-05, NB-07, NB-08, STUDENT-01
**Success Criteria** (what must be TRUE):
  1. Structured handoff notebook shows EscalationRecord JSON output via `tool_choice` enforcement, compared to raw conversation dump anti-pattern
  2. Coordinator-subagent pattern routes a complex query to the correct subagent and returns structured results
  3. Integration notebook (07) runs a scenario that touches all 6 CCA patterns in sequence with observable output for each
  4. At least 3 TODO placeholders exist across notebooks that students can complete without breaking notebook execution
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: Testing and CI/CD
**Goal**: The project has automated test coverage and CI/CD that itself demonstrates CCA best practices for code generation with Claude
**Depends on**: Phase 5
**Requirements**: CICD-01, CICD-02, CICD-03
**Success Criteria** (what must be TRUE):
  1. `poetry run pytest` passes with tests covering all escalation rules, compliance hooks, and tool routing
  2. GitHub Actions workflow runs `claude -p --bare` for PR review and linting on push
  3. `.claude/CLAUDE.md` and custom skills files exist and are referenced in a meta-teaching section explaining how the project itself follows CCA best practices
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

Note: Phases 3 and 4 are architecturally independent (both depend on Phase 2). They are numbered sequentially but could be executed in either order.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Foundation | 2/2 | Complete   | 2026-03-25 |
| 2. Models, Services, and Core Loop | 0/2 | Not started | - |
| 3. Callbacks, Enforcement, and First Notebooks | 0/3 | Not started | - |
| 4. Caching and Context Notebooks | 0/2 | Not started | - |
| 5. Handoffs, Integration, and Student Polish | 0/2 | Not started | - |
| 6. Testing and CI/CD | 0/2 | Not started | - |

---
*Created: 2026-03-25*
