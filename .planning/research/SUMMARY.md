# Project Research Summary

**Project:** CCA Exam Prep -- Customer Support Resolution Agent
**Domain:** Claude API teaching example (Jupyter notebooks + Python package)
**Researched:** 2026-03-25
**Confidence:** HIGH

## Executive Summary

This project is a hands-on coding example for the CCA Exam Prep course that teaches 6 architectural patterns through side-by-side anti-pattern vs correct-pattern demonstrations. The expert approach for this type of project is a two-layer architecture: a production Python package (`customer_service/`) providing models, services, tools, callbacks, and agent loop implementations, with Jupyter notebooks as the teaching layer that imports from the package. The raw Anthropic Python SDK (not the Agent SDK, not LangChain) is the correct choice because the CCA exam tests understanding of the tool-use loop internals, `stop_reason` dispatch, `tool_choice` enforcement, and prompt caching -- all of which are hidden by higher-level abstractions.

The recommended approach is to build bottom-up following the architecture dependency graph: Pydantic models first, then in-memory simulated services with input-sensitive behavior, then tool schemas and dispatch, then the PostToolUse callback enforcement layer, then the agentic loop, and finally notebooks that compose these components into teaching demonstrations. The critical design decision is that simulated services must return different results based on customer tier, refund amount, and account flags -- otherwise anti-pattern demos produce identical output to correct-pattern demos and the teaching value collapses.

The top risks are: (1) compliance enforcement living in prompts instead of application code (directly contradicts the CCA exam's central principle), (2) anti-pattern demonstrations that fail to produce observable failures due to deterministic/oversimplified service data, and (3) prompt cache breakpoints placed on dynamic content, causing cost increases rather than savings. All three are preventable with the callback architecture and input-sensitive service design established in early phases.

## Key Findings

### Recommended Stack

The stack is well-defined by project constraints and verified against current releases. Python 3.13+ with Poetry 2.x for dependency management. The `anthropic` SDK (>=0.77.0, current 0.86.0) provides the raw `client.messages.create()` loop that students must understand. Pydantic v2 (2.12.x) generates JSON Schema for tool `input_schema` via `model_json_schema()` and powers structured outputs via `client.messages.parse()`. JupyterLab 4.x with ipykernel for teaching.

**Core technologies:**
- **anthropic SDK (>=0.77.0):** Raw Claude API client -- explicit agentic loop, no abstraction hiding the patterns the exam tests
- **Pydantic v2 (2.12.x):** Data models and tool schema generation -- `model_json_schema()` eliminates manual JSON Schema authoring
- **Poetry 2.x:** Dependency management with PEP 621 `[project]` table -- editable install makes `from customer_service import ...` work in notebooks
- **JupyterLab 4.x:** Teaching environment -- self-contained, no IDE config needed for student onboarding
- **pytest + pytest-mock + pytest-recording:** Unit tests mock the client, integration tests use VCR cassettes, `nbval` smoke-tests notebooks in CI

**Critical exclusions:** No Agent SDK (hides loop internals), no async (obscures teaching signal), no LangChain (hides Claude-specific features), no external databases (zero infrastructure requirement).

### Expected Features

**Must have (table stakes):**
- Anti-pattern vs correct pattern side-by-side in each notebook (mirrors CCA exam format)
- Real Claude API calls with visible tool_use payloads and token usage
- Deterministic escalation via PostToolUse callbacks (Pattern 1 -- highest exam impact)
- Programmatic compliance enforcement in application layer (Pattern 2)
- 5-tool focused agent and 15-tool Swiss Army anti-pattern (Pattern 3)
- Prompt caching with `cache_control` markers and token accounting (Pattern 4)
- Context management: structured summaries vs raw transcript (Pattern 5)
- Structured JSON escalation handoff via `tool_choice` enforcement (Pattern 6)
- Simulated in-memory services with input-sensitive behavior
- Numbered notebooks 00-06 with logical progression
- Student TODO placeholders that do not break notebook execution
- Production Python package installable via `pip install -e .`

**Should have (differentiators):**
- Coordinator-subagent pattern demonstration (no other CCA prep shows this running)
- Live token accounting output making "90% cache savings" concrete
- Exam question pattern headers mapping notebook cells to CCA question types
- Integrated full-scenario notebook (07) combining all 6 patterns
- PostToolUse callback as raw SDK implementation of what Agent SDK abstracts

**Defer (v2+):**
- GitHub Actions CI/CD with `claude -p --bare` (Article 2 content, not Article 1)
- CLAUDE.md + custom skills meta-teaching layer (same rationale)
- Additional student exercise variations (wait for feedback on difficulty)

### Architecture Approach

Two-layer architecture: production package (`src/customer_service/`) with `agents/`, `tools/`, `callbacks/`, `services/`, and `models/` subpackages, consumed by teaching notebooks (`notebooks/`) via standard Python imports. The agentic loop is an explicit `while True` loop checking `response.stop_reason`, not a framework abstraction. PostToolUse callbacks are pure functions `(tool_name, tool_input, tool_result) -> tool_result` that fire unconditionally after every tool execution. Services are injected via a container dataclass, never imported directly in tools.

**Major components:**
1. **`models/`** -- Pydantic v2 data models (CustomerProfile, PolicyResult, EscalationHandoff) providing type safety and JSON Schema generation
2. **`services/`** -- In-memory simulated services (CustomerDB, PolicyEngine, RefundProcessor) with input-sensitive behavior for observable anti-pattern failures
3. **`tools/`** -- JSON tool schemas in `schemas.py`, dispatch registry in `dispatch.py`, handler implementations -- the 5 focused tools plus 15-tool anti-pattern set
4. **`callbacks/`** -- PostToolUse enforcement hooks for escalation rules ($500 threshold, VIP, legal, account closure) and compliance (redaction, audit logging)
5. **`agents/`** -- Base agentic loop (`base_agent.py`), 5-tool customer agent, 15-tool anti-pattern agent, coordinator-subagent orchestrator

### Critical Pitfalls

1. **Agentic loop checks content type instead of stop_reason** -- Claude returns text narration before tool_use blocks in the same response; checking `content[0].type == "text"` exits early and drops tool calls. Fix: always use `response.stop_reason == "end_turn"` as the only termination signal.

2. **Compliance enforcement in prompt instead of application code** -- Prompt-based rules are probabilistic and bypassable. This is the CCA exam's #1 wrong-answer trap. Fix: PostToolUse callbacks enforce business rules unconditionally in Python; prompts provide context only.

3. **Simulated services too deterministic for anti-pattern visibility** -- If all services return identical results regardless of input, the 15-tool agent and 5-tool agent produce the same output. Fix: design services with input-sensitive behavior (VIP triggers escalation, $600 triggers threshold, account closure triggers hold) before building notebooks.

4. **Prompt cache breakpoint on dynamic content** -- Placing `cache_control` on user messages (which change every turn) causes 100% cache misses with 25% write premium. Fix: mark only the static policy document in system blocks; verify `cache_read_input_tokens > 0` on second request.

5. **Anti-pattern shown before correct pattern is established** -- Cognitive load research shows students internalize the first pattern they see. Fix: each notebook explains the correct pattern first, runs it, then shows and runs the anti-pattern, then compares.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 0: Project Foundation and Notebook Template
**Rationale:** All notebooks share structural conventions (correct-before-anti-pattern ordering, `print_usage` helper, visual differentiation of anti-pattern cells). Establishing the template first prevents rework across 8 notebooks.
**Delivers:** pyproject.toml, project skeleton with `src/` layout, `.env.example`, `.gitignore`, pre-commit hooks (nbstripout + ruff), notebook section template, `print_usage` helper utility.
**Addresses:** Setup notebook (00), notebook structure conventions.
**Avoids:** Pitfall 6 (anti-pattern shown before pattern), Pitfall 10 (API costs not visible).

### Phase 1: Models, Services, and Core Agentic Loop
**Rationale:** Everything depends on the data models and service layer. The agentic loop is the foundation that all subsequent notebooks inherit. Services must be input-sensitive from the start to support observable anti-pattern failures.
**Delivers:** Pydantic models, in-memory services with input-sensitive behavior, tool schemas, dispatch registry, base agentic loop with `stop_reason` control.
**Addresses:** Pydantic domain models, simulated services, 5-tool focused agent, agentic loop.
**Avoids:** Pitfall 1 (content-type loop termination), Pitfall 2 (tool_result format), Pitfall 9 (deterministic services).

### Phase 2: Callbacks, Enforcement, and Tool Design Notebooks
**Rationale:** With the loop working, add the enforcement layer and build the first teaching notebooks. PostToolUse callbacks are required by both the escalation and compliance demonstrations. The Swiss Army anti-pattern needs the focused agent as its baseline.
**Delivers:** PostToolUse callback framework, escalation rules ($500, VIP, legal, closure), compliance hooks (redaction, audit), 15-tool anti-pattern agent, notebooks 01-03 (escalation, compliance, tool design).
**Addresses:** Deterministic escalation (Pattern 1), programmatic compliance (Pattern 2), tool count contrast (Pattern 3), structured escalation handoff (Pattern 6).
**Avoids:** Pitfall 4 (prompt-only compliance), Pitfall 5 (unobservable Swiss Army failure), Pitfall 7 (raw transcript handoff), Pitfall 8 (overused forced tool_choice).

### Phase 3: Prompt Caching and Context Management Notebooks
**Rationale:** Cost optimization and context management are independent of the enforcement layer but depend on a working agentic loop. Prompt caching requires careful `cache_control` placement -- the pitfall research flags this as a common and costly mistake.
**Delivers:** Prompt caching with `cache_control` markers and token accounting, structured context summaries vs raw transcript comparison, notebooks 04-05 (cost optimization, context management).
**Addresses:** Prompt caching demonstration (Pattern 4), context management (Pattern 5), live token accounting output.
**Avoids:** Pitfall 3 (cache breakpoint on dynamic content), Pitfall 10 (costs not visible).

### Phase 4: Structured Handoffs and Integration
**Rationale:** Structured handoffs combine Pydantic models, `tool_choice` enforcement, and the callback layer -- all must be stable before this notebook. The integration notebook (07) requires all 6 patterns working together.
**Delivers:** Structured JSON escalation handoff notebook (06), exam question mapping headers across all notebooks, student TODO verification pass, integration notebook (07).
**Addresses:** Structured handoffs (Pattern 6), coordinator-subagent pattern, integrated full-scenario, exam question mapping.
**Avoids:** Pitfall 7 (raw transcript handoff), Pitfall 8 (forced tool_choice misuse).

### Phase 5: Testing, CI/CD, and Polish
**Rationale:** Tests and CI codify the patterns. GitHub Actions CI/CD (`claude -p --bare`) is a meta-teaching layer for Article 2 content and should come last.
**Delivers:** pytest suite for callbacks and tool routing, VCR cassettes for integration tests, nbval notebook smoke tests, GitHub Actions workflows, CLAUDE.md meta-teaching layer.
**Addresses:** CI/CD meta-example, test coverage, production polish.

### Phase Ordering Rationale

- The dependency graph is strict: models -> services -> tools -> callbacks -> agents -> notebooks. Phases follow this order.
- PostToolUse callbacks must exist before any enforcement notebook can be written, so callbacks land in Phase 2 alongside the first notebooks rather than later.
- Prompt caching and context management (Phase 3) are architecturally independent from enforcement (Phase 2) but both require the Phase 1 agentic loop.
- The coordinator-subagent pattern lands in Phase 4 because it requires stable subagent implementations from Phases 1-2.
- Testing and CI come last because they codify behavior that must be stable first; writing tests against a changing API would create churn.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Callbacks and Enforcement):** The PostToolUse callback pattern in raw SDK (not Agent SDK) needs careful design. The exact interception point and how forced escalation interacts with the message history requires API-level verification.
- **Phase 3 (Prompt Caching):** Minimum token thresholds vary by model (1024 for Sonnet 4.5+, 2048 for Haiku 4.5). The policy document size must be verified against the chosen model's threshold. Cost accounting display needs exact field names from current SDK version.
- **Phase 4 (Coordinator-Subagent):** Multi-agent coordination patterns are less documented than single-agent loops. Subagent instantiation, result passing via Pydantic, and coordinator message history management need design research.

Phases with standard patterns (skip research-phase):
- **Phase 0 (Project Foundation):** Standard Poetry + JupyterLab setup; well-documented.
- **Phase 1 (Models, Services, Loop):** The agentic loop is thoroughly documented in Anthropic's official docs. Pydantic model creation is standard.
- **Phase 5 (Testing and CI):** pytest, VCR, nbval are well-established patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI and official releases; SDK compatibility confirmed |
| Features | HIGH | Domain fully defined by PROJECT.md and companion article; CCA exam patterns are specific and documented |
| Architecture | HIGH | Official Anthropic docs cover agentic loop, tool use, prompt caching; patterns verified against SDK reference |
| Pitfalls | HIGH | Primary sources are Anthropic official docs; pitfalls verified against known API behavior and error messages |

**Overall confidence:** HIGH

### Gaps to Address

- **Prompt caching minimum token thresholds:** The exact threshold for the chosen model needs verification at implementation time. If the policy document is under 1024 tokens, caching will silently fail. Size the policy document during Phase 3 planning.
- **Swiss Army anti-pattern reproducibility:** Tool selection degradation with 15 tools is probabilistic. The test query set must be designed to trigger observable failures reliably. May require iteration during Phase 2 to find queries that expose the anti-pattern consistently.
- **PostToolUse callback in raw SDK vs Agent SDK:** The Agent SDK defines a formal `PostToolUse` hook interface. The raw SDK implementation is a custom Python pattern. Verify during Phase 2 that the raw implementation faithfully represents what the Agent SDK abstracts.
- **Coordinator-subagent message isolation:** How the coordinator's message history and the subagent's message history interact (shared vs isolated) needs design validation during Phase 4.

## Sources

### Primary (HIGH confidence)
- [Anthropic Python SDK releases (PyPI)](https://pypi.org/project/anthropic/) -- v0.86.0 confirmed, Python 3.9+ support
- [Claude API tool use implementation docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) -- agentic loop, tool_result format, parallel tool calls
- [Claude API prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) -- cache_control placement, TTL, minimum token thresholds, verification fields
- [Claude API structured outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) -- output_config, client.messages.parse(), strict tool use
- [Claude API agent loop docs](https://platform.claude.com/docs/en/agent-sdk/agent-loop) -- stop_reason as loop control signal
- [Claude API hooks docs](https://platform.claude.com/docs/en/agent-sdk/hooks) -- PostToolUse, PreToolUse callback patterns
- [Building effective AI agents (Anthropic Research)](https://www.anthropic.com/research/building-effective-agents) -- multi-agent patterns
- [Writing tools for agents (Anthropic Engineering)](https://www.anthropic.com/engineering/writing-tools-for-agents) -- tool design guidance

### Secondary (MEDIUM confidence)
- [pytest-recording (GitHub)](https://github.com/kiwicom/pytest-recording) -- VCR integration for API testing
- [Poetry 2.0 pyproject.toml docs](https://python-poetry.org/docs/pyproject/) -- PEP 621 table migration
- [Anti-pattern pedagogy research (ScienceDirect, Cagiltay 2006)](https://www.sciencedirect.com/science/article/abs/pii/S0360131506001485) -- cognitive load in anti-pattern teaching

### Tertiary (LOW confidence)
- [Agentic Workflows with Claude (Medium)](https://medium.com/@reliabledataengineering/agentic-workflows-with-claude-architecture-patterns-design-principles-production-patterns-72bbe4f7e85a) -- community patterns, verified against official docs

---
*Research completed: 2026-03-25*
*Ready for roadmap: yes*
