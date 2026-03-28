# Skill: review-cca-compliance

Review any Python code, notebook, or workflow file for compliance with CCA (Claude Certification for Agentic systems) architectural patterns.

## Usage

Invoke this skill when you need to audit code for CCA exam anti-patterns:

```
Use the review-cca-compliance skill to check this file: src/customer_service/agent/agent_loop.py
```

Or to review a directory:

```
Use the review-cca-compliance skill to audit the entire src/customer_service/agent/ directory.
```

---

## CCA Compliance Checklist

Work through each section. For every check, report one of:
- **PASS** — requirement met, brief explanation
- **WARN** — marginal or unclear, flag for human review
- **FAIL** — clear CCA anti-pattern violation, explain why and how to fix

---

### 1. Tool Count (CCA Rule: 4-5 tools per agent)

- [ ] Count tools in each `TOOLS` list or tool definition. Report total.
- [ ] If count > 5: **FAIL** — list the tools and recommend splitting to coordinator-subagent pattern
- [ ] If count == 5: **PASS**
- [ ] If count 4-5: **PASS**
- [ ] Check: Does any tool list include HR, marketing, shipping, or other domain-crossing tools? → **FAIL** (Swiss Army anti-pattern)

**Anti-pattern signal:** `SWISS_ARMY_TOOLS`, tool lists > 5 entries, tool names like `send_marketing_email`, `update_hr_record`

---

### 2. Tool Descriptions — Negative Bounds (CCA Rule: descriptions drive routing)

- [ ] Read every tool description string
- [ ] Does each description contain "does NOT" or "does not"? If missing: **WARN**
- [ ] Is the description specific enough to prevent misrouting? Vague = **WARN**, e.g., "Get customer info" (bad) vs "Look up customer profile by ID; does NOT modify customer data" (good)
- [ ] Are parameter descriptions present and meaningful?

**Anti-pattern signal:** Descriptions under 20 words with no negative bounds

---

### 3. Escalation Logic (CCA Rule: deterministic code, NOT LLM confidence)

- [ ] Find where escalation routing decisions are made
- [ ] Is it a programmatic check (Python `if` on a flag, amount, or tier)? → **PASS**
- [ ] Is it based on a confidence score or LLM self-assessment? → **FAIL**
- [ ] Is escalation enforced in a callback/hook BEFORE the tool executes? → **PASS**
- [ ] Is escalation guidance only in the system prompt (not in code)? → **FAIL**

**Anti-pattern signal:** `confidence > 0.7`, `if response.confidence`, system prompt phrases like "escalate when unsure"

**Correct pattern signal:** `callbacks.py`, `PostToolUse`, `if context.get("requires_review")`, `if context.get("vip")`

**Thresholds to verify:** amount > $500, account closure flag, VIP tier, legal complaint keywords

---

### 4. Compliance Enforcement (CCA Rule: programmatic hooks, not prompt instructions)

- [ ] Is PII/PCI redaction done in code (regex, callback)? → **PASS**
- [ ] Is redaction instruction only in the system prompt ("never log credit card numbers")? → **FAIL**
- [ ] Is audit logging performed programmatically for every tool call? → **PASS**
- [ ] Does the callback execute BEFORE the tool result is written to storage? → **PASS** (critical: redaction must precede the write)

**Anti-pattern signal:** System prompt phrases like "never include credit card", "ensure PCI compliance", "do not log sensitive"

**Correct pattern signal:** `compliance_callback`, `re.sub(r'\b\d{4}[- ]\d{4}...`, `AuditLog.add_entry()`

---

### 5. Context Management (CCA Rule: structured JSON summaries, not raw transcripts)

- [ ] Find where conversation context is stored between turns
- [ ] Is it a structured object with named fields (customer_id, issue_type, turn_count)? → **PASS**
- [ ] Is it a raw list of messages or string concatenation? → **FAIL** (lost-in-middle risk)
- [ ] Does the context object have a token budget and compaction logic? → **PASS**
- [ ] Does `to_system_context()` or equivalent produce a compact string, not full history?

**Anti-pattern signal:** `transcript.append(message)`, `"\n".join(messages)`, O(n) growth patterns

**Correct pattern signal:** `ContextSummary`, `update(tool_name, result_summary)`, `token_estimate < TOKEN_BUDGET`

---

### 6. Cost Optimization (CCA Rule: Prompt Caching for repeated context, NOT Batch API for live support)

- [ ] Is Batch API (`client.beta.messages.batches`) used anywhere in live agent paths? → **FAIL**
- [ ] Is `cache_control: {"type": "ephemeral"}` applied to repeated policy documents? → **PASS**
- [ ] Is the cached block >= 2048 tokens (minimum threshold for claude-sonnet-4-6)? → check content size
- [ ] Is `cache_control` placed on the LAST static block (before dynamic content)? → **PASS**

**Anti-pattern signal:** `batches.create()` in any live support path, no `cache_control` on large policy documents

**Correct pattern signal:** `get_system_prompt_with_caching()`, `{"type": "text", "text": POLICY_DOCUMENT, "cache_control": {"type": "ephemeral"}}`

---

### 7. Handoff Pattern (CCA Rule: structured EscalationRecord JSON via tool_choice)

- [ ] Is the escalation output a structured JSON object with all required fields? → **PASS**
  - Required: `customer_id`, `customer_tier`, `issue_type`, `disputed_amount`, `escalation_reason`, `recommended_action`, `conversation_summary`, `turns_elapsed`
- [ ] Is the full conversation transcript passed to the human agent? → **FAIL**
- [ ] Is `tool_choice={"type": "tool", "name": "escalate_to_human"}` used to force structured output? → **PASS**

**Anti-pattern signal:** Passing `messages` list directly to human agent, raw conversation dumps, `format_raw_handoff()`

**Correct pattern signal:** `EscalationRecord`, `tool_choice`, `_has_escalation_required()`, `stop_reason == "escalated"`

---

### 8. Agentic Loop (CCA Rule: terminate on stop_reason, not content-type)

- [ ] Find the main agentic loop (`while True` or equivalent)
- [ ] Does it terminate based on `stop_reason != "tool_use"` or `stop_reason == "end_turn"`? → **PASS**
- [ ] Does it check `response.content[0].type == "text"` to decide whether to stop? → **WARN** (fragile)
- [ ] Does the loop dispatch ALL tool_use blocks before continuing? → **PASS**

**Anti-pattern signal:** `if response.content[0].type == "text": break`, `if "end_turn" in str(response):`

**Correct pattern signal:** `while response.stop_reason != "end_turn":` or `while True:` with `if stop_reason != "tool_use": break`

---

### 9. Coordinator-Subagent Pattern (CCA Rule: explicit context passing, no inheritance)

- [ ] Do subagents receive all required context as explicit arguments? → **PASS**
- [ ] Do subagents share the coordinator's `messages` list or `system_prompt`? → **FAIL**
- [ ] Does each subagent have 4-5 focused tools (not the coordinator's full set)? → **PASS**
- [ ] Do subagents communicate directly with each other? → **FAIL** (must go through coordinator)

**Anti-pattern signal:** `subagent_messages = coordinator_messages`, passing `system_prompt=coordinator_system_prompt` to subagents

**Correct pattern signal:** `context_string = f"Customer ID: {customer_id}\nTask: {task}"`, subagent initialized with only task-specific data

---

### 10. CLAUDE.md Hierarchy (CCA Rule: project standards in .claude/CLAUDE.md)

- [ ] Does `.claude/CLAUDE.md` exist in the repo root? → **PASS**
- [ ] Is it committed to version control (not gitignored)? → **PASS**
- [ ] Does it contain team coding standards? → **PASS**
- [ ] Are secrets or personal preferences in `.claude/CLAUDE.md`? → **FAIL** (belongs in `~/.claude/CLAUDE.md`)

**Level reference:**
- System directory = org-managed, non-overridable
- `.claude/CLAUDE.md` = project, VCS, team standards ← correct for team rules
- `~/.claude/CLAUDE.md` = user, personal preferences
- `CLAUDE.local.md` = personal override, gitignored

---

### 11. CI/CD Flags (CCA Rule: -p mandatory, --bare recommended)

- [ ] Does any CI workflow use `claude` without `-p`? → **FAIL** (pipeline will hang)
- [ ] Is `--bare` present for reproducibility? → **PASS** if yes, **WARN** if absent
- [ ] Is `--output-format json` used when output is parsed programmatically? → **PASS**
- [ ] Is `jq -r '.result'` (or equivalent) used to extract text from JSON envelope? → **PASS**
- [ ] Is `--allowedTools` scoped to minimum required tools (Read, Grep, Glob)? → **PASS**
- [ ] Is `ANTHROPIC_API_KEY` stored as a secret, never hardcoded? → check workflow env blocks

---

## Output Format

For each check, report findings in this format:

```
### [Section Name]

- [PASS/WARN/FAIL] [Check description]
  - File: <file path>
  - Line: <line number or range, if applicable>
  - Detail: <specific evidence from the code>
  - Fix: <what to change, if WARN or FAIL>
```

End with a summary table:

```
## Summary

| Section | Status | Issues |
|---------|--------|--------|
| Tool Count | PASS | 5 tools |
| Tool Descriptions | WARN | 2 tools missing negative bounds |
| Escalation Logic | PASS | deterministic callbacks |
| ... | ... | ... |

**Overall: PASS / REVIEW NEEDED (N issues)**
```

A result of PASS means the code follows CCA architectural patterns and would score well on the CCA exam.
A result of REVIEW NEEDED means at least one anti-pattern was detected that could cost points on the exam.
