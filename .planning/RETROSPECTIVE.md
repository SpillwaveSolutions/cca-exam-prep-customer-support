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

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 6 |
| Plans | 13 |
| Tests | 234 |
| LOC (prod) | 2,872 |
| LOC (test) | 3,841 |
| Notebooks | 9 |
| Requirements | 34 |
| Timeline | 4 days |
| Replan cycles | 2 (Phase 3, Phase 4) |
| Review-found bugs | 5 (PII leak, method names, spec drift, structured errors, cache threshold) |
