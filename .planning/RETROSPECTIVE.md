# Project Retrospective

## Milestone: v1.0 — CCA Customer Support Resolution Agent

**Shipped:** 2026-03-28
**Phases:** 6 | **Plans:** 13 | **Tests:** 234
**Timeline:** 4 days (2026-03-25 → 2026-03-28)

### What Was Built

- Production Python package with 6 Pydantic models, 5 deterministic services, 5-tool agent with callbacks
- 9 Jupyter notebooks (00-08) demonstrating all 6 CCA patterns with anti-pattern vs correct contrast
- Per-tool callback registry with two-step vetoable refund pattern and pre-handler PII redaction
- Coordinator-subagent with context isolation, tool_choice forced structured handoffs
- Prompt caching with 4079-token POLICY_DOCUMENT, ContextSummary with budget compaction
- GitHub Actions CI/CD with annotated CCA exam flags, custom CCA compliance review skill
- CCA-RULES.md authoritative reference extracted from all 8 source articles

### What Worked

- **CCA-RULES.md as spec baseline**: Extracting all patterns from source articles BEFORE building prevented contradicting exam material. Every code review could reference specific rules.
- **Per-tool callback registry**: The dict-based registry eliminated an entire class of cross-tool payload bugs that a shared list would have caused.
- **Block-not-bypass escalation**: Letting Claude call `escalate_to_human` naturally after a blocked refund preserved the expected tool trace — cleaner than injecting fabricated tool calls.
- **Review-driven iteration**: Code reviews caught real bugs that tests missed (PII audit log leak, method name mismatches, spec drift). The behavior-first testing rule emerged from actual failure.

### What Was Inefficient

- **VALIDATION.md frontmatter**: `nyquist_compliant: false` was never flipped to `true` after successful execution. Cosmetic but cluttered the audit.
- **SUMMARY.md frontmatter**: Some plans didn't populate `requirements-completed` in YAML, making 3-source cross-reference partial.
- **Notebook smoke tests**: Structural-only tests missed runtime errors (wrong method names, nonexistent APIs). A deterministic notebook execution harness would have caught these earlier.
- **Phase 3 required 2 plan iterations**: First plan had architectural issues (shared callback list, bypass escalation, wrong NB01 check). Review feedback was critical but cost a replanning cycle.

### Patterns Established

- **Behavior-first testing**: Test persistent stores (AuditLog, EscalationQueue, FinancialSystem), not API responses
- **Every claim needs executable proof**: "Claim" → "test name / command / file line"
- **Pre-handler callbacks for side effects**: PII redaction must happen BEFORE the handler writes, not after
- **CCA-RULES.md as authoritative reference**: All downstream agents read it before planning or implementing

### Key Lessons

1. **Test the store, not the return** — The PII audit log bug taught us that redacting the returned JSON while the audit log contains raw card numbers is a compliance failure. Test what's persisted.
2. **Per-tool registry over shared list** — Callbacks that fire for unrelated tools cause hard-to-diagnose bugs. The dict registry makes this impossible by construction.
3. **Block, don't bypass** — When a callback needs to redirect the agent, return a result that tells Claude what to do next. Don't inject fabricated tool calls or bypass the normal flow.
4. **Perplexity hallucinates model IDs** — Always verify LLM-sourced API identifiers against the actual API. `claude-sonnet-4-6-20260217` doesn't exist.
5. **The 2048-token caching threshold is silent** — Below it, `cache_creation_input_tokens` stays 0 with no error. Target 2200+ tokens for safety margin.

### Cost Observations

- Model mix: ~40% Opus (planning, complex execution), ~55% Sonnet (research, execution, verification), ~5% Haiku (none used directly)
- Parallel execution in Waves saved significant wall-clock time (Phases 3, 5, 6)
- The heaviest token usage was Phase 3 (callbacks + 3 anti-patterns + 3 notebooks in one phase)

---

## Milestone: v1.1 — Notebook Fixes

**Shipped:** 2026-04-07
**Phases:** 2 | **Plans:** 2 | **Tests:** 256 (22 new)
**Timeline:** 2 days (2026-04-06 → 2026-04-07)

### What Was Built

- Fixed 3 notebook runtime bugs: make_services() seed data (NB04/NB05), .final_response→.final_text (NB05), customer ID prefix for escalation (NB01)
- Tagged API-dependent cells with skip-execution metadata in NB06 (6 cells) and NB07 (7 cells)
- Created headless notebook execution tests using exec()-based approach (no Papermill dependency needed)
- 18 behavior-first notebook fix tests + 4 headless execution tests = 22 new tests

### What Worked

- **Behavior-first notebook tests**: Creating tests that read notebook JSON and validate cell content caught bugs without requiring API keys. Tests simulated the full callback chain to prove escalation works.
- **exec()-based headless testing**: Using exec() with nbformat instead of Papermill avoided a new dependency while still validating non-API cells execute without error. Simpler and faster (~2s for both notebooks).
- **Skip-execution cell metadata tagging**: Clean separation of API-dependent vs. testable cells. The tag-based filter pattern is reusable for all future notebooks.
- **Fast milestone execution**: Total execution time ~18 minutes across both phases. Small, focused phases with clear requirements enabled rapid delivery.

### What Was Inefficient

- **Research undercount on NB07 skip cells**: Research identified 5 cells for NB07 but 7 were actually needed (cells 13, 17 also reference API result). The execution test caught this immediately, but better dependency tracing in research would have prevented the deviation.
- **Summary frontmatter still incomplete**: `summary-extract` returned null for one-liner fields, suggesting the YAML frontmatter format doesn't include a dedicated one-liner field.

### Patterns Established

- **make_services() must pass CUSTOMERS**: CustomerDatabase(CUSTOMERS) is the canonical notebook pattern — no empty init
- **AgentResult.final_text (not .final_response)**: Established as the correct attribute name across all notebooks
- **skip-execution metadata tag**: Standard pattern for marking API-dependent cells in notebooks for CI filtering
- **exec()-based headless notebook testing**: _load_executable_cells() + _run_cells() pattern reusable for all notebooks

### Key Lessons

1. **Structural tests miss runtime bugs** — v1.0's structural-only notebook tests didn't catch make_services() args or wrong attribute names. v1.1's exec()-based tests close this gap.
2. **Research skip-cell lists need downstream tracing** — Identifying which cells call the API is necessary but not sufficient. Must also trace all cells that reference variables set by API calls.
3. **Small fix milestones are fast** — A focused 2-phase bugfix milestone completed in 2 days with 18 minutes of execution time. Clear scope enables velocity.

### Cost Observations

- Model mix: ~50% Opus (planning, execution), ~50% Sonnet (research, verification)
- Both phases completed in single sessions — no context resets needed
- Minimal rework: only 2 auto-fixed deviations per phase, all caught by tests

---

## Cross-Milestone Trends

| Metric | v1.0 | v1.1 |
|--------|------|------|
| Phases | 6 | 2 |
| Plans | 13 | 2 |
| Tests | 234 | 256 (+22) |
| LOC (prod) | 2,872 | 2,872 (unchanged) |
| LOC (test) | 3,841 | ~4,654 (+813) |
| Notebooks | 9 | 9 (3 fixed, 2 tagged) |
| Requirements | 34 | 5 |
| Timeline | 4 days | 2 days |
| Replan cycles | 2 (Phase 3, Phase 4) | 0 |
| Auto-fixed deviations | 5 | 4 (skip tags, sys.path, stale output, line length) |
