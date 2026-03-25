# Feature Research

**Domain:** CCA Exam Prep Coding Example — Customer Support Resolution Agent
**Researched:** 2026-03-25
**Confidence:** HIGH (domain is well-defined by PROJECT.md, companion article, and Anthropic's published CCA exam framework)

---

## Feature Landscape

### Table Stakes (Students Expect These)

Features that must exist or the teaching example fails to serve its purpose. Missing any of these means the student cannot internalize the targeted CCA patterns.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Anti-pattern vs correct pattern side-by-side in notebooks | Mirrors CCA exam format: wrong answers look right. Students need to _see_ the failure before the fix lands | MEDIUM | Each notebook shows wrong way first, then correct way. Order matters for learning retention. |
| Real Claude API calls using `anthropic` Python SDK | Students need to see actual API responses, tool use payloads, and token usage — not mocked output | LOW | Requires `ANTHROPIC_API_KEY` only. Synchronous calls keep output readable. |
| Deterministic escalation via PostToolUse callbacks | Pattern 1 of 6. Single most tested concept per the article. Must be runnable, not just described | HIGH | Callbacks intercept after agent proposes action; business rules fire unconditionally regardless of model confidence |
| Programmatic compliance enforcement (not prompt-based) | Pattern 2. Exam consistently tests "prompt vs code" for hard rules. Students must see both fail and succeed | MEDIUM | Application-layer enforcement: redaction, authorization checks, audit logging all in Python |
| Focused 5-tool agent (lookup_customer, check_policy, process_refund, escalate_to_human, log_interaction) | Pattern 3. 4-5 tools is Anthropic's explicit guidance. Students need the canonical tool set running | LOW | Tool descriptions must be precise — descriptions ARE the routing mechanism |
| 15-tool Swiss Army anti-pattern agent | Pattern 3 inverse. Without seeing the bloated agent, the "reduce tool count" lesson is abstract | MEDIUM | Deliberately includes HR, marketing, inventory, shipping tools on a support agent to demonstrate scope creep + selection accuracy degradation |
| Prompt caching demonstration with `cache_control` markers | Pattern 4 / cost optimization. 90% savings on repeated tokens vs the Batch API trap | MEDIUM | Marks policy document as `cache_control: {"type": "ephemeral"}`. Shows token accounting before and after. |
| Structured JSON escalation handoff via `tool_choice` enforcement | Pattern 5. Exam tests "full transcript vs structured summary" — students need to run both | MEDIUM | `tool_choice: {"type": "tool", "name": "escalate_to_human"}` forces structured output; contrasts with raw transcript pass-through |
| Context management: structured summaries vs raw transcript | Pattern 6. "Lost in the middle" is real; students need to observe degraded behavior before the fix | HIGH | Side-by-side demo: raw conversation grows unbounded vs periodic structured summary injection |
| Simulated in-memory services (no real database) | Students need zero infrastructure. Any required external service is a barrier to running the example | LOW | In-memory dicts simulate CRM, policy engine, financial system, escalation queue, audit log |
| Numbered notebooks (00-07) with logical progression | Standard Jupyter course format. Students expect linear walkthrough from setup to advanced patterns | LOW | 00: setup/intro, 01-06: one pattern each, 07: integrated full scenario |
| Student TODO placeholders | Active learning. Passive reading of notebooks teaches less than completing structured exercises | LOW | `# TODO: ...` comments at key decision points with clear instructions |
| Production Python package alongside notebooks | Notebooks are for learning; package is the reference implementation. Students need both to understand the gap | MEDIUM | Package uses same code but without teaching scaffolding — Poetry, Pydantic models, proper module structure |

### Differentiators (Competitive Advantage)

Features that set this coding example apart from other CCA prep materials (typically text-only articles, flashcard decks, or abstract pseudocode).

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Coordinator-subagent pattern demonstration | No other CCA prep material shows this running. Students who only read the exam guide often miss the "when to split" decision logic | HIGH | Coordinator agent routes to billing-subagent and shipping-subagent, each with their own 4-5 tools. Directly answers exam Question 3 pattern. |
| Live token accounting output (prompt cache hit/miss) | Makes abstract "90% savings" concrete. Students see `cache_creation_input_tokens` vs `cache_read_input_tokens` in real API response | LOW | Print token usage from `response.usage` after each call. Before/after comparison makes the lesson land. |
| Exam question patterns mapped to runnable code | Each notebook section maps to a specific CCA exam question type from the article. Students see the exam question, then run the code that answers it | MEDIUM | Headers like "This demonstrates CCA Question Pattern: Escalation Routing" tie notebook cells to exam outcomes |
| PostToolUse callback implementation | This is the Claude Agent SDK pattern but implemented in raw SDK to teach fundamentals. Shows the interception point that makes escalation deterministic | HIGH | Wrapping tool execution with pre/post hooks in pure Python using the Anthropic SDK demonstrates what the Agent SDK abstracts |
| Project itself as CCA meta-example (CLAUDE.md + CI/CD) | `.claude/CLAUDE.md`, custom skills, and GitHub Actions `claude -p --bare` are live examples of the patterns in Article 2. The project teaches Article 2 while demonstrating Article 1 | HIGH | Meta-teaching layer: reading the project files teaches CCA Article 2 content without a separate tutorial |
| Anti-pattern failure modes are observable, not just described | The 15-tool agent actually produces wrong tool selections students can observe. The confidence-score escalation actually routes incorrectly at times. Failures are real, not simulated as examples | HIGH | Requires careful prompt and scenario design so anti-patterns fail predictably enough to demonstrate without being so broken they're useless |
| Pydantic v2 models for all data structures | Shows correct structured output handling. Exam tests structured output domain (20% weight). Students see Pydantic as enforcement, not just annotation | MEDIUM | `EscalationHandoff`, `CustomerProfile`, `PolicyResult` are all Pydantic models — validates the structured handoff pattern |

### Anti-Features (Commonly Requested, Often Problematic)

Things to explicitly NOT build, with rationale.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real database / Firebase backend | "More realistic" — students want production-like infrastructure | Adds infrastructure setup friction that blocks 80% of students from running the example. Firebase setup alone is 30-minute barrier. Kills adoption. | In-memory Python dicts that implement the same interface. Students can swap in real backends after understanding the patterns. |
| Async / streaming API calls | "More realistic" — real production agents use streaming | Async code obscures the teaching signal. Students spend time understanding asyncio, not the CCA patterns. `await` keywords in every cell distract from tool use payloads. | Synchronous calls. Add async note in comments pointing to Anthropic async docs for production adaptation. |
| Claude Agent SDK | "Why not use the abstraction?" — students familiar with higher-level SDKs | This is specifically a CCA fundamentals prep example. Using the Agent SDK hides the patterns being tested. Students must see the raw PostToolUse hook implementation, not `agent.run()`. | Implement callback patterns in raw `anthropic` SDK. Document clearly: "In production, use Agent SDK — this shows what it abstracts." |
| Confidence score-based escalation (even as a working implementation) | "Show a working version of the anti-pattern" — tempting for completeness | A working confidence-based escalation creates false legitimacy. Students may think "well it works for simple cases." The lesson must be that it is categorically wrong, not conditionally wrong. | Show it in code, make it fail on the specific $600 refund scenario from the article exam walkthrough. The failure is the lesson. |
| Batch API integration | "Show the cost optimization trap running" | The Batch API requires async polling, webhooks, or result storage. Adding it for anti-pattern demonstration creates a disproportionate amount of infrastructure complexity for a secondary lesson. | Describe the Batch API trap in a dedicated notebook cell with the exam question walkthrough. Point to official Batch API docs. The concept is architectural, not implementation-dependent. |
| Deployment / hosting (Docker, cloud functions, etc.) | "Show how to deploy the agent" | Deployment is out of scope for CCA exam content. Adding it bloats the project and blurs the teaching focus. | README note: "deployment is left as an exercise; focus here is the architectural patterns." |
| Multi-tenant / production auth | "Make it more like a real system" | Auth and multi-tenancy complexity dwarfs the teaching value. Students would read auth code, not CCA patterns. | Single-user in-memory session per notebook run. Clean slate each execution. |
| Web UI / chat frontend | "Students want a visual demo" | Frontend work consumes build time that adds zero CCA exam prep value. The exam tests backend architecture, not UI. | Jupyter widgets for interactive demos if needed. CLI output is sufficient for demonstrating API responses. |

---

## Feature Dependencies

```
[Production Python Package]
    └──required by──> [Notebooks import from package]
                          └──required by──> [All 6 pattern demonstrations]

[Simulated In-Memory Services]
    └──required by──> [Deterministic Escalation Demo]
    └──required by──> [Programmatic Compliance Demo]
    └──required by──> [Structured Handoff Demo]
    └──required by──> [Context Management Demo]

[5-Tool Focused Agent]
    └──required by──> [15-Tool Swiss Army Comparison]
    └──required by──> [Coordinator-Subagent Pattern]
    (baseline must exist before contrast and extension)

[Pydantic Models for Data Structures]
    └──required by──> [Structured JSON Escalation Handoff]
    └──required by──> [tool_choice Enforcement Demo]

[PostToolUse Callback Implementation]
    └──required by──> [Deterministic Escalation Demo]
    └──required by──> [Programmatic Compliance Demo]
    (callbacks are the enforcement mechanism for both patterns)

[cache_control Markers on Policy Context]
    └──required by──> [Prompt Caching Demo]
    └──required by──> [Token Accounting Output]

[Coordinator-Subagent Pattern]
    └──requires──> [5-Tool Focused Agent] (subagent must exist first)
    └──requires──> [Simulated In-Memory Services]

[Exam Question Mapping Headers]
    └──enhances──> [All Pattern Demonstration Notebooks]
    (adds exam context without blocking execution)

[Student TODO Placeholders]
    └──enhances──> [All Notebooks]
    └──conflicts with──> [Complete Working Implementation]
    (TODOs are deliberately incomplete sections — balance needed)

[CLAUDE.md + CI/CD Meta-Teaching Layer]
    └──enhances──> [Production Python Package]
    └──independent of──> [Notebook Pattern Demonstrations]
    (meta-layer teaches Article 2 content; does not affect Article 1 notebook functionality)
```

### Dependency Notes

- **Production Python Package required by Notebooks**: Notebooks use `from customer_service import ...` imports. The package must be installable via `pip install -e .` before any notebook runs. Failure here blocks 100% of students.
- **5-Tool Focused Agent required by 15-Tool Comparison**: The contrast requires both to exist. Build the correct pattern first; the anti-pattern is a modified derivative.
- **Pydantic Models required by Structured Handoff**: `tool_choice` enforcement produces a Pydantic-validated `EscalationHandoff` — validation is part of the pattern demonstration.
- **PostToolUse Callbacks required by both Escalation and Compliance**: The same callback architecture enforces escalation business rules AND compliance (redaction, authorization). Implement once, demonstrate in two contexts.
- **Student TODOs conflict with Complete Working Implementation**: Each TODO must be scoped to an isolated function so the rest of the notebook still runs. TODOs that break execution kill the learning loop. Strategy: provide stub function with `raise NotImplementedError` that only affects the exercise cell.
- **Coordinator-Subagent requires 5-Tool Agent**: The coordinator routes to subagents. Each subagent IS a focused agent. The 5-tool agent implementation is reused as the subagent template.

---

## MVP Definition

### Launch With (v1)

Minimum viable content to deliver the stated value: students can run code demonstrating every CCA Customer Support anti-pattern failure and its correct fix.

- [ ] **00-setup.ipynb** — environment check, API key validation, package install verification. Students cannot proceed without this working.
- [ ] **Production Python package installable via `pip install -e .`** — all notebooks depend on this. Must be first artifact built.
- [ ] **Pydantic models for all domain types** — `CustomerProfile`, `PolicyResult`, `EscalationHandoff`, `InteractionLog`. Foundation for all structured output demos.
- [ ] **Simulated in-memory services** — `CustomerService`, `PolicyEngine`, `FinancialService`, `EscalationQueue`, `AuditLog`. Required by every pattern demonstration.
- [ ] **01-escalation-logic.ipynb** — Pattern 1 (highest exam impact). Anti-pattern: confidence score routing. Correct: PostToolUse callback with deterministic business rules.
- [ ] **02-compliance.ipynb** — Pattern 2. Anti-pattern: prompt-based PCI guidance. Correct: programmatic redaction + audit logging.
- [ ] **03-tool-design.ipynb** — Pattern 3. Anti-pattern: 15-tool Swiss Army agent. Correct: 5-tool focused agent. Coordinator-subagent for overflow.
- [ ] **04-cost-optimization.ipynb** — Pattern 4. Anti-pattern: Batch API for live support. Correct: Prompt Caching with token accounting.
- [ ] **05-context-management.ipynb** — Pattern 5. Anti-pattern: raw unbounded transcript. Correct: structured summaries at context boundaries.
- [ ] **06-structured-handoffs.ipynb** — Pattern 6. Anti-pattern: full transcript dump on escalation. Correct: structured JSON handoff via `tool_choice`.
- [ ] **Student TODO placeholders in each notebook** — minimum one exercise per pattern. Stubs must not break notebook execution.

### Add After Validation (v1.x)

Add once core notebooks are running and student feedback is collected.

- [ ] **07-full-scenario.ipynb** — Integrated scenario combining all 6 patterns in a single realistic support interaction. Add after individual pattern notebooks are validated.
- [ ] **Coordinator-subagent pattern** — High complexity, high value differentiator. Add after tool design notebook (03) is solid. Requires subagent implementation to be stable.
- [ ] **Exam question mapping headers** — Low effort enhancement. Add to all notebooks once content is stable to avoid rework.
- [ ] **Token accounting comparison output** — Adds specificity to the Prompt Caching demo. Add after 04-cost-optimization baseline works.

### Future Consideration (v2+)

Defer until the v1 course receives student feedback.

- [ ] **GitHub Actions CI/CD (`claude -p --bare`)** — High value meta-teaching for Article 2 but zero value for Article 1 exam prep. Defer until Article 2 content exists to contextualize it.
- [ ] **CLAUDE.md + custom skills meta-layer** — Same rationale as CI/CD. Teaches Article 2 patterns. Defer.
- [ ] **Additional student exercise variations** — More TODO exercises per pattern. Defer until feedback indicates which patterns students find hardest.
- [ ] **Video walkthrough companion** — Outside scope of this coding project.

---

## Feature Prioritization Matrix

| Feature | Student Value | Implementation Cost | Priority |
|---------|--------------|---------------------|----------|
| Production Python package (installable) | HIGH | MEDIUM | P1 |
| Simulated in-memory services | HIGH | LOW | P1 |
| Pydantic domain models | HIGH | LOW | P1 |
| PostToolUse callback for escalation (Pattern 1) | HIGH | HIGH | P1 |
| Programmatic compliance enforcement (Pattern 2) | HIGH | MEDIUM | P1 |
| 5-tool focused agent (Pattern 3 correct) | HIGH | LOW | P1 |
| 15-tool Swiss Army agent (Pattern 3 anti) | HIGH | MEDIUM | P1 |
| Prompt caching with `cache_control` markers (Pattern 4) | HIGH | MEDIUM | P1 |
| Structured summaries vs raw transcript (Pattern 5) | HIGH | HIGH | P1 |
| Structured JSON handoff via `tool_choice` (Pattern 6) | HIGH | MEDIUM | P1 |
| Student TODO placeholders | MEDIUM | LOW | P1 |
| Setup notebook (00) | HIGH | LOW | P1 |
| Coordinator-subagent pattern | HIGH | HIGH | P2 |
| Token accounting output (cache hit/miss) | MEDIUM | LOW | P2 |
| Integrated full-scenario notebook (07) | MEDIUM | MEDIUM | P2 |
| Exam question mapping headers | MEDIUM | LOW | P2 |
| GitHub Actions CI/CD | MEDIUM | HIGH | P3 |
| CLAUDE.md + custom skills meta-layer | MEDIUM | MEDIUM | P3 |
| Additional student exercises (v2) | MEDIUM | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch — teaching value fails without it
- P2: Should have — adds clarity and differentiation, add after P1 validation
- P3: Nice to have — meta-teaching layer for Article 2 content

---

## Competitor Feature Analysis

The "competitors" in this context are other CCA exam prep materials: the Anthropic documentation, text-only articles, flashcard decks, and abstract pseudocode examples.

| Feature | Text Articles / Docs | Flashcard Decks | This Project |
|---------|---------------------|-----------------|--------------|
| Runnable anti-pattern demonstration | No — described only | No | Yes — observable failure |
| Real API responses visible | No | No | Yes — printed token usage, tool call payloads |
| Side-by-side pattern contrast | Sometimes | No | Yes — wrong way then right way in same notebook |
| Coordinator-subagent running example | No | No | Yes (P2) |
| PostToolUse callback implementation | No | No | Yes — raw SDK shows what Agent SDK abstracts |
| Exam question → code mapping | Partial | Yes (question only) | Yes — question header + runnable answer |
| Student exercises | No | Passive recall only | Yes — TODO stubs in notebooks |
| Production-quality reference implementation | No | No | Yes — Poetry package alongside notebooks |
| Zero infrastructure setup | N/A | N/A | Yes — ANTHROPIC_API_KEY only |
| Prompt caching with measurable token savings | No | No | Yes — before/after token accounting |

---

## Sources

- `PROJECT.md` at `/Users/richardhightower/clients/spillwave/src/cca_exam/customer_service/.planning/PROJECT.md` — project requirements, constraints, out-of-scope decisions (HIGH confidence — primary source)
- Companion article: `/Users/richardhightower/articles/articles/cca-customer-support/work/final/article_publication_ready.md` — CCA exam patterns, anti-pattern taxonomy, exam question walkthroughs (HIGH confidence — authoritative source for CCA content)
- Anthropic CCA Exam Framework (as described in article) — 6 exam domains, weights, scenario structure (MEDIUM confidence — described in article, not directly verified against Anthropic's current exam guide)
- Anthropic Python SDK documentation — `cache_control`, `tool_choice`, `PostToolUse` patterns (MEDIUM confidence — based on training data; recommend Context7 verification during implementation)

---

*Feature research for: CCA Exam Prep Coding Example — Customer Support Resolution Agent*
*Researched: 2026-03-25*
