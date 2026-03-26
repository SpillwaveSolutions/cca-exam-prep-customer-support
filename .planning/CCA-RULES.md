# CCA Certification Rules — Authoritative Reference

> Extracted from all 8 CCA exam prep articles. This is the source of truth.
> All code in this project MUST comply with these rules. Never contradict them.

## 5 Core Principles (Apply Across ALL Scenarios)

1. **Programmatic Enforcement Beats Prompt-Based Guidance**
   - Business rules, JSON compliance, escalation: code is law, prompts are guidance
   - Validation hooks execute deterministically; system prompts execute probabilistically
   - Any "add to system prompt" for hard requirements is WRONG

2. **Subagents Do NOT Inherit Context**
   - Subagents start with blank slate
   - Everything needed must be explicitly passed
   - Counterintuitive and heavily tested on exam

3. **Tool Descriptions Drive Routing**
   - Claude selects tools based on descriptions, not names
   - Vague descriptions cause misrouting
   - Negative bounds ("does NOT...") prevent misuse

4. **The "Lost in the Middle" Effect Is Real**
   - Applies regardless of total context size
   - Bigger context window makes it WORSE, not better
   - Mitigation: critical info at start/end, structured summaries, chunk documents

5. **Match API to Latency Requirements**
   - Someone waiting → Real-Time API (always)
   - No one waiting + no ZDR → Batch API acceptable
   - Repeated context → Prompt Caching (90% savings on reads)

---

## Customer Support Scenario Rules

### Escalation Logic (THE #1 TRAP)
- WRONG: Self-reported confidence scores for routing
- RIGHT: Deterministic business rules in code (PostToolUse callbacks)
- Thresholds: amount > $500, account closure, VIP tier, legal complaint
- Implemented as programmatic hooks, NEVER in prompts alone

### Tool Count
- 4-5 focused tools per agent (architectural best practice)
- Beyond 5: tool selection accuracy degrades measurably
- The 5 tools: `lookup_customer`, `check_policy`, `process_refund`, `escalate_to_human`, `log_interaction`
- Anti-pattern: 12-15+ tools including HR, marketing, shipping

### Compliance Enforcement
- WRONG: "Include PCI compliance requirements in system prompt"
- RIGHT: Programmatic redaction, audit logging, validation hooks
- PostToolUse callbacks enforce; system prompt provides context only

### Cost Optimization
- WRONG: "Use Batch API for live support to save 50%"
- RIGHT: "Use Prompt Caching for repeated policy context (90% savings)"
- Batch API: up to 24-hour latency, NOT for live customer support
- Batch API: NOT eligible for Zero Data Retention (ZDR)

### Handoff Pattern
- WRONG: Pass full conversation transcript to human agent
- RIGHT: Pass structured JSON with key fields at top:
  - customer_id, customer_tier, issue_type, disputed_amount
  - escalation_reason, recommended_action, conversation_summary, turns_elapsed
- Use tool_choice enforcement for structured escalation output

### Context Management
- Structured JSON summaries, NOT raw transcripts
- Raw transcripts → lost-in-middle effect, attention dilution
- Structured summaries stay under token budget while raw grows unbounded

---

## Agentic Architecture Rules

### Agentic Loop
- Cycle: receive input → reason → call tools → evaluate results → decide next step
- Terminate on stop_reason, NEVER content-type checking
- stop_reason == "end_turn" → agent is done
- stop_reason == "tool_use" → dispatch tools, continue loop
- Validation-retry loops for unreliable outputs

### Coordinator-Subagent Pattern
- Single coordinator manages decomposition and delegation
- Subagents execute focused tasks (4-5 tools each)
- Subagents NEVER communicate directly — all through coordinator
- Explicit context passing required (subagents start blank)

### Silent Failure Prevention
- Return structured error context, never swallow errors
- Fields: status, error_type, source, retry_eligible, fallback_available, partial_data
- Coordinator must distinguish "no data" from "failed to retrieve"

---

## Structured Output Rules (Three-Layer Reliability)

| Layer | Approach | Reliability |
|-------|----------|-------------|
| Layer 1 | Prompt guidance ("return JSON") | Unreliable — anti-pattern alone |
| Layer 2 | Schema enforcement (tool-forcing, messages.parse()) | Structurally reliable |
| Layer 3 | Schema + validation gate + retry loop | Production reliable — correct |

### Schema Enforcement Methods (Anthropic SDK)
- Tool-forcing: `tool_choice={"type": "tool", "name": "tool_name"}`
- `client.messages.parse()` with Pydantic models
- NOT `with_structured_output()` — that's LangChain, not Anthropic SDK

### Validation-Retry Loop
- Informed retry with specific error feedback, NOT blind "try again"
- Max 2-3 retries, then escalate to human
- Error feedback: which field failed, current value, expected format, where to look

---

## Tool Design Rules

### Tool Schemas
- Use Pydantic model_json_schema() for single source of truth
- Tool descriptions must be precise with negative bounds
- Good: "Look up customer profile by ID; does NOT modify customer data"
- Bad: "Get customer info"

### Tool Handlers
- All return JSON strings (matching Claude API tool_result format)
- Services injected via ServiceContainer, never imported directly
- Each handler: (input_dict, services) → JSON string

### MCP Configuration
- `.mcp.json` (project, VCS): shared server definitions (no secrets)
- `~/.claude.json` (user): credentials and personal servers

---

## CLAUDE.md Hierarchy

| Level | Path | VCS | Authority |
|-------|------|-----|-----------|
| Managed/Org | System directory | No | Non-overridable |
| Project | `.claude/CLAUDE.md` | Yes | Team standards |
| User | `~/.claude/CLAUDE.md` | No | Personal prefs |
| Local | `CLAUDE.local.md` | No (gitignored) | Personal override |

---

## CI/CD Rules
- `-p` flag MANDATORY for non-interactive mode
- `--bare` flag RECOMMENDED for reproducibility
- `--output-format json` for structured output at CLI level
- `--allowedTools` for sandboxing

---

## Exam Signal → Answer Mapping

| Signal | Answer |
|--------|--------|
| "Pipeline is hanging" | Missing `-p` flag |
| "Output sometimes invalid" | Need schema enforcement (Layer 2) |
| "Quality drops in longer sessions" | Context degradation → decompose |
| "Team standards inconsistent" | Move to project-level CLAUDE.md |
| "Subagent unexpected output" | Instructions not explicitly passed |
| "Retries don't fix extraction" | Need specific error feedback |
| "Confidence threshold for escalation" | TRAP — use deterministic rules |
| "Batch API for live support" | WRONG — use Prompt Caching |
| "12 tools, wrong one selected" | Reduce to 4-5, split to subagents |

---

*Extracted from: cca-intro, cca-customer-support, cca-code-generation, cca-data-extraction, cca-developer-productivity, cca-multi-agent, cca-cicd, cca-practice-exam*
*Date: 2026-03-25*
