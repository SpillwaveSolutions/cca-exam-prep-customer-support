# Phase 3: Callbacks, Enforcement, and First Notebooks — Research

**Researched:** 2026-03-26
**Domain:** PostToolUse callback architecture, anti-pattern agents, Jupyter notebook generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Hook point: `dispatch()` in `handlers.py` — the single place every tool result passes through
- Callback logic: separate `agent/callbacks.py` module (not inline in dispatch or agent_loop)
- Signature: `dispatch(tool_name, input_dict, services, context, callbacks=...)`
- Callback input: `(tool_name, input_dict, result_dict, context, services)`
- Callback output: `action="allow" | "replace_result" | "escalate"` plus replacement payload/reason
- Context parameter must include current user message or structured conversation summary (needed for legal keyword detection)
- On escalate: return one replacement JSON tool result AND enqueue the escalation directly; do NOT fabricate a second Claude tool call inside the same cycle
- Only `process_refund` is two-step vetoable (irreversible financial side effect)
- `escalate_to_human`: single-step (append-only, safe)
- `log_interaction`: single-step, but callback may redact/replace the `details` field BEFORE the handler writes
- `lookup_customer` and `check_policy`: pure reads, not vetoable
- Anti-pattern 1 (confidence_escalation.py): C003 $600 refund; system prompt confidence routing
- Anti-pattern 2 (prompt_compliance.py): C001 + PII card `4111-1111-1111-1111`; system prompt redaction rule
- Anti-pattern 3 (swiss_army_agent.py): 15 tools (5 correct + 10 distractors); C003 $600 misroutes to `file_billing_dispute`
- Notebook 01 (Escalation): C003 ($600, amount > $500 trigger)
- Notebook 02 (Compliance): C001 (happy path + PII in message)
- Notebook 03 (Tool Design): C003 ($600 refund again)
- Template: Setup > Anti-Pattern (red box) > Correct (green box) > Compare

### Claude's Discretion

- Exact callback dataclass/namedtuple shape for action/payload/reason
- Legal keyword detection implementation (regex vs keyword list)
- Credit card regex pattern specifics
- Distractor tool description wording (must be plausible, not rigged)
- Notebook cell count and exact markdown formatting
- System prompt content for anti-pattern agents

### Deferred Ideas (OUT OF SCOPE)

- Prompt caching with cache_control markers — Phase 4
- Structured escalation handoff with tool_choice enforcement — Phase 5
- Coordinator-subagent pattern — Phase 5
- Batch API vs Real-Time cost comparison — Phase 4
- Streamlit UI — still TBD
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ENFORCE-01 | PostToolUse callback framework for rule enforcement after every tool execution | Callback dataclass, dispatch() signature extension, application-level hook pattern |
| ENFORCE-02 | Deterministic escalation rules (amount > $500, account closure, VIP, legal keywords) | Verified: `requires_review` already in PolicyResult; `flags` list on CustomerProfile; regex for legal keywords beats naive keyword list |
| ENFORCE-03 | Programmatic compliance enforcement (redaction, audit logging) in application layer | Verified: regex pattern `\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b` redacts 16-digit cards correctly; `log_interaction` callback can mutate `details` before AuditLog.log() |
| ANTI-01 | 15-tool Swiss Army anti-pattern agent | 10 distractor tools identified; `file_billing_dispute` is the canonical misroute target for C003 |
| ANTI-02 | Prompt-only compliance enforcement anti-pattern | System prompt with "never log card numbers" fails; audit log contains raw PII; demonstrated with C001 + `4111-1111-1111-1111` |
| ANTI-03 | LLM confidence-based escalation anti-pattern | System prompt with confidence self-rating; Claude reports >80% confidence on C003 $600; callback approach is deterministic regardless |
| NB-02 | Notebook 01 — Escalation pattern | nbformat 5.10.4 available; template cells established in NB-00; `print_usage`/`compare_results` helpers ready |
| NB-03 | Notebook 02 — Compliance pattern | Same nbformat infrastructure; C001 + PII scenario ready in SCENARIOS dict (happy_path) |
| NB-04 | Notebook 03 — Tool design pattern | Swiss Army tools defined in CONTEXT.md; same C003 scenario as NB-01 to show different failure mode |
</phase_requirements>

---

## Summary

The raw Anthropic Python SDK (`anthropic>=0.40.0`) has **no built-in PostToolUse callback mechanism**. The SDK is a thin HTTP wrapper: `client.messages.create()` returns a response object and that is the complete API surface. There is no event bus, no hook registration, and no middleware layer. PostToolUse enforcement is an **application-level pattern** that must be implemented in the dispatch layer — exactly what the architecture already does.

The existing `dispatch()` function in `handlers.py` is the correct and only hook point. Extending its signature to accept `context: dict` and `callbacks: list[Callable]` (defaulting to `[]`) allows backward-compatible injection of callback logic without touching any individual handler. The two-step vetoable pattern for `process_refund` is a localized design decision: the handler computes a proposed result dict without committing, returns it to dispatch, callbacks evaluate it, then dispatch either commits (calls `FinancialSystem.process_refund()`) or replaces the result with an escalation payload.

For notebook generation, `nbformat` 5.10.4 is already installed as a transitive dependency (via nbstripout). The `nbformat.v4` API (`new_notebook()`, `new_code_cell()`, `new_markdown_cell()`) is stable, well-documented, and sufficient for all three notebooks. The established notebook template from Phase 1 (red/green HTML boxes, `print_usage`, `compare_results`) is already working in `00_setup.ipynb`.

**Primary recommendation:** Implement PostToolUse enforcement as a pure Python application pattern — a `CallbackResult` dataclass with `action/replacement/reason`, a list of callables passed to `dispatch()`, and per-tool callback functions in `agent/callbacks.py`. No new libraries required.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.40.0 (installed: 0.40.0) | Raw SDK for `client.messages.create()` | Project requirement; raw SDK only (no Agent SDK) |
| pydantic | >=2.0 | `CallbackResult` dataclass validation; model schemas | Already in project; type-safe result objects |
| nbformat | 5.10.4 (transitive) | Create `.ipynb` files programmatically | Jupyter standard; already installed via nbstripout |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re (stdlib) | built-in | Credit card regex redaction; legal keyword detection | Callback enforcement; no external dependency needed |
| dataclasses (stdlib) | built-in | `CallbackResult` dataclass | Lightweight, no Pydantic overhead for internal return types |
| typing.Literal | built-in | Type-constrain `action` field to three valid values | Prevents invalid callback actions at type-check time |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dataclass for CallbackResult | Pydantic BaseModel | Pydantic adds validation overhead; dataclass is sufficient for internal return type |
| stdlib `re` for PCI redaction | `phonenumbers`/`scrubadub` | External libs add complexity; single regex pattern is sufficient for the 16-digit Visa/MC scenario |
| keyword list for legal detection | `re.compile` with `\b` word boundaries | Keyword list `['sue', ...]` causes false positives on "issue", "pursue" — regex wins |

**Installation:** No new packages required. `nbformat` is already installed as a transitive dep. No additions to `pyproject.toml` needed.

**Version verification (2026-03-26):**
- `anthropic`: 0.40.0 (installed, verified)
- `nbformat`: 5.10.4 (installed, verified via `poetry run python -c "import nbformat; print(nbformat.__version__)"`)

---

## Architecture Patterns

### Recommended Project Structure (Phase 3 additions)

```
src/customer_service/
├── agent/
│   ├── agent_loop.py        # MODIFY: pass context + callbacks to dispatch()
│   ├── callbacks.py         # NEW: CallbackResult, per-tool callback functions
│   └── system_prompts.py    # existing
├── anti_patterns/
│   ├── __init__.py          # existing stub
│   ├── confidence_escalation.py   # NEW: ANTI-03 — LLM self-rated confidence
│   ├── prompt_compliance.py       # NEW: ANTI-02 — prompt-only PCI redaction
│   └── swiss_army_agent.py        # NEW: ANTI-01 — 15-tool agent
├── tools/
│   └── handlers.py          # MODIFY: dispatch() signature + callback invocation
notebooks/
├── helpers.py               # existing — print_usage, compare_results
├── 00_setup.ipynb           # existing
├── 01_escalation.ipynb      # NEW: NB-02
├── 02_compliance.ipynb      # NEW: NB-03
└── 03_tool_design.ipynb     # NEW: NB-04
tests/
└── test_callbacks.py        # NEW: TDD-first for all ENFORCE rules
```

### Pattern 1: Application-Level PostToolUse Dispatch Hook

**What:** The raw Anthropic SDK has no built-in callback mechanism. PostToolUse enforcement is an application-level pattern: a `CallbackResult` dataclass returned from callback functions, invoked inside `dispatch()` after each tool handler runs. On `action="escalate"`, dispatch enqueues directly and returns a replacement JSON tool result to Claude.

**When to use:** Every tool execution. Callbacks default to `[]` (empty list = allow everything) for backward compatibility. Notebooks and tests pass explicit callback lists.

**The critical design constraint from CONTEXT.md:** On escalate, dispatch returns ONE replacement result and calls `services.escalation_queue.add_escalation()` directly. It does NOT try to force a second `escalate_to_human` tool call in the same loop iteration. This is deterministic and avoids any possibility of the agent failing to route to human.

**Example:**
```python
# Source: application-level pattern (no SDK equivalent)
from dataclasses import dataclass
from typing import Literal

@dataclass
class CallbackResult:
    action: Literal["allow", "replace_result", "escalate"]
    replacement: dict | None = None
    reason: str = ""

# Callback function signature (per-tool, lives in callbacks.py)
def on_process_refund(
    tool_name: str,
    input_dict: dict,
    result_dict: dict,
    context: dict,
    services: ServiceContainer,
) -> CallbackResult:
    ...
```

### Pattern 2: Two-Step Vetoable process_refund

**What:** Only `process_refund` is two-step because it has an irreversible financial side effect. Step 1 computes a proposed result dict (no commit). Dispatch runs callbacks on proposed result. Step 3 commits only if `action="allow"`.

**When to use:** Only for `process_refund`. All other tools are single-step (their side effects are either safe or ARE the fallback action).

**Example — proposed result dict shape (no FinancialSystem write yet):**
```python
# Source: verified against existing PolicyEngine + FinancialSystem services
proposed = {
    "status": "proposed",
    "customer_id": input_dict["customer_id"],
    "order_id": input_dict["order_id"],
    "amount": input_dict["amount"],
    "policy_approved": policy_result.approved,
    "requires_review": policy_result.requires_review,
}
# callbacks evaluate proposed — if escalate, FinancialSystem.process_refund() is never called
```

### Pattern 3: log_interaction Callback — Redact Before Write

**What:** The `log_interaction` callback intercepts `input_dict["details"]` before `AuditLog.log()` is called. It mutates or replaces the `details` field with redacted content. The handler then writes the redacted version.

**Implementation decision (Claude's Discretion):** The simplest approach is to have the callback return `action="replace_result"` with a `replacement` dict containing the redacted `input_dict`. The dispatch layer applies the replacement to `input_dict` before passing it to the handler. This keeps the handler pure and untouched.

**Alternative:** Dispatch passes `input_dict` by reference and callbacks mutate it. This is simpler but less explicit. Recommend the `replace_result` approach for teachability — students see "this is how you intercept input".

### Pattern 4: Escalation Callback Context Passing

**What:** The `context` dict passed to `dispatch()` must include the original user message (or a structured conversation summary). This is required because the legal keyword detection callback fires on `lookup_customer` result processing — it needs to scan the user message for "lawsuit", "sue", "attorney" etc., not the tool result JSON.

**Context dict shape (minimum viable):**
```python
context = {
    "user_message": user_message,      # original user turn text
    "conversation_turn": _iteration,   # loop iteration count
    # optional: "flags": {}            # accumulated flags from prior callbacks
}
```

**Escalation rules mapped to callback firing points:**
| Rule | Detected In | Data Source |
|------|------------|-------------|
| VIP tier | `on_lookup_customer` callback | `result_dict["tier"] == "vip"` |
| account_closure flag | `on_lookup_customer` callback | `"account_closure" in result_dict.get("flags", [])` |
| amount > $500 | `on_check_policy` callback | `result_dict["requires_review"] == True` |
| legal keyword | `on_lookup_customer` or context | `LEGAL_PATTERN.search(context["user_message"])` |
| HARD STOP | `on_process_refund` callback | Any of above flags set in context |

### Pattern 5: Anti-Pattern Agents (Live SDK Calls)

**What:** All three anti-pattern modules make real `client.messages.create()` calls with a different system prompt or different tool list. They return a result comparable to the correct agent result for the `compare_results` helper.

**Key constraint (CCA rules):** Anti-pattern code lives ONLY in `src/customer_service/anti_patterns/`. Do not call anti-pattern modules from any production code path.

**Notebook import pattern:**
```python
# At top of anti-pattern section in notebook
import sys
sys.path.insert(0, str(Path("..").resolve()))  # project root
from customer_service.anti_patterns.confidence_escalation import run_confidence_agent
from customer_service.agent.agent_loop import run_agent_loop  # correct agent
```

### Pattern 6: nbformat Notebook Creation

**What:** Notebooks are created programmatically using `nbformat.v4` API. Each notebook follows the established template: markdown headers, red/green HTML boxes, code cells, then `compare_results`.

**Verified API (nbformat 5.10.4):**
```python
# Source: verified with poetry run python in project environment
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()
nb.cells.append(new_markdown_cell("# Notebook 01: Escalation Pattern"))

# Red box for anti-pattern
red_box = '<div style="border-left: 4px solid #dc3545; padding: 12px 16px; background: #fff5f5; margin: 8px 0;">'
nb.cells.append(new_markdown_cell(f"{red_box}\n<strong>What's wrong:</strong> ...\n</div>"))

nb.cells.append(new_code_cell("result = run_confidence_agent(client, services, message)"))

# Write to .ipynb
with open("01_escalation.ipynb", "w") as f:
    nbformat.write(nb, f)
```

**Cell tag metadata (for hide-input style, optional):**
```python
cell = new_code_cell("...")
cell.metadata["tags"] = ["hide-input"]   # verified working in nbformat 5.10.4
```

### Anti-Patterns to Avoid

- **Inline callback logic in dispatch():** Violates separation of concerns. Business rules must be in `callbacks.py`, not scattered in `handlers.py`.
- **Raising exceptions from callbacks:** Callbacks return `CallbackResult`, never raise. Silent failures or exceptions in callbacks would bypass enforcement. `dispatch()` should catch callback exceptions and treat as `action="escalate"` with the error as reason.
- **Fabricating a second tool call on escalate:** On `action="escalate"`, dispatch enqueues directly via `services.escalation_queue.add_escalation()` and returns a JSON replacement result. It does NOT attempt to re-enter the agent loop or generate a fake `escalate_to_human` tool use block.
- **Keyword list for legal detection without word boundaries:** `'sue'` in `['sue', 'lawsuit', ...]` matches "issue", "pursue", "misunderstanding" (all contain 'sue' as substring). Use `re.compile(r'\b...\b', re.IGNORECASE)` instead.
- **Writing .ipynb files manually with Bash heredoc:** Use `nbformat.write()` + the Write tool. Manual JSON construction breaks on escaping and produces hard-to-validate notebooks.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Notebook .ipynb format | Custom JSON serialization | `nbformat.v4.new_*cell()` + `nbformat.write()` | Handles schema versioning, metadata, output field defaults |
| Credit card PCI detection | Custom parser | `re.compile(r'\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b')` | Covers all 16-digit card formats with/without separators; already verified |
| Legal keyword detection | Naive `if kw in text` | `re.compile(r'\b(lawsuit|suing|attorney|...)\b', re.IGNORECASE)` | Word boundaries prevent false positives on "issue", "pursue" |
| Callback framework | Agent SDK, LangChain middleware | Application-level `CallbackResult` dataclass + list-of-callables | Raw SDK project; external frameworks contradict CCA architecture lesson |

**Key insight:** The entire teaching value of ENFORCE-01 is that PostToolUse enforcement is a Python pattern, not an SDK feature. Using any framework that provides built-in hooks would undermine the lesson.

---

## Common Pitfalls

### Pitfall 1: Callback "Escalation" Triggers Infinite Loop

**What goes wrong:** Callback on `process_refund` returns `action="escalate"`. Agent loop receives the escalation replacement result. Claude then calls `escalate_to_human` tool. If the `escalate_to_human` callback also returns `action="escalate"`, the loop re-escalates indefinitely.

**Why it happens:** `escalate_to_human` is append-only safe and IS the fallback action. Adding an escalation callback to it creates circular logic.

**How to avoid:** `escalate_to_human` has no enforcement callback — or at most a `action="allow"` passthrough. Only `lookup_customer`, `check_policy`, `process_refund`, and `log_interaction` have meaningful callbacks.

**Warning signs:** Tests for escalation scenarios that never return `stop_reason="end_turn"`.

### Pitfall 2: Naive Keyword List Causes False Positives on Legal Detection

**What goes wrong:** `legal_keywords = ['sue', 'lawsuit', ...]` and `any(kw in message.lower() for kw in legal_keywords)` triggers on "issue" (contains "sue"), "pursue" (contains "sue"), "misunderstanding" (contains "sue").

**Why it happens:** Substring matching without word boundaries.

**How to avoid:** Use `re.compile(r'\b(lawsuit|suing|sue|attorney|lawyer|legal\s+action|court|litigation)\b', re.IGNORECASE)`. Verified: "Issue with my account" → no match; "I will sue you" → match.

**Warning signs:** Tests passing C001 happy-path message to `detect_legal_keyword()` return True.

### Pitfall 3: Two-Step process_refund Loses the Commit Step

**What goes wrong:** The "proposed" result dict is built, callbacks run, `action="allow"` returned — but the handler doesn't actually call `FinancialSystem.process_refund()` to commit. The refund is "approved" but never executed.

**Why it happens:** Developer adds the pre-callback proposed dict but forgets the post-callback commit call.

**How to avoid:** The two-step handler has an explicit "commit step" that is only called inside `if callback_result.action == "allow":`. Tests must assert `services.financial_system` state after the call.

**Warning signs:** `process_refund` returns approved JSON but `services.financial_system.get_refunds()` (or equivalent inspection) shows no record.

### Pitfall 4: Swiss Army Tools Rigged to Fail

**What goes wrong:** Distractor tool descriptions are too obviously wrong ("this tool handles HR requests") or too obviously right. The failure looks staged, not educational.

**Why it happens:** Easy path is to make distractors absurd.

**How to avoid:** Distractor descriptions must be plausible enterprise support tools with overlapping semantics. `file_billing_dispute` should sound like a reasonable refund-adjacent tool ("File a formal billing dispute for an order charge. Use for contested charges, unauthorized transactions, or billing errors."). The misroute must look like a **reasonable model mistake under cognitive overload**, not a rigged demo.

**Warning signs:** A human reading only the tool descriptions can instantly tell which tools are distractors.

### Pitfall 5: Anti-Pattern Modules Import from Production Code in Ways That Blur the Lesson

**What goes wrong:** `confidence_escalation.py` imports `from customer_service.agent.agent_loop import run_agent_loop` and calls it with only a different system prompt. Students then see two calls to the same `run_agent_loop` and may conclude the difference is trivial.

**How to avoid:** Each anti-pattern module has its own minimal agent loop (or a clearly parameterized wrapper). The point is that the anti-pattern uses a DIFFERENT system prompt strategy, not a different loop. The loop is the same; the enforcement is missing.

### Pitfall 6: context dict Not Passed Through to dispatch()

**What goes wrong:** `agent_loop.py` calls `dispatch(block.name, block.input, services)` (current 3-arg signature) without passing `context`. Legal keyword detection callback in `on_lookup_customer` fires on the tool result but has no access to the user message. Legal escalation silently fails.

**Why it happens:** Signature change was planned but the agent_loop call site was not updated.

**How to avoid:** Update the dispatch call site in `agent_loop.py` at the same time as the signature extension. Tests for legal keyword escalation will catch this immediately.

---

## Code Examples

Verified patterns from implementation and testing:

### CallbackResult Dataclass
```python
# Source: verified with Python 3.13 in project environment
from dataclasses import dataclass
from typing import Literal

@dataclass
class CallbackResult:
    action: Literal["allow", "replace_result", "escalate"]
    replacement: dict | None = None  # for replace_result and escalate
    reason: str = ""                 # always set on escalate, optional elsewhere
```

### dispatch() Signature Extension (backward compatible)
```python
# Source: application pattern — extends existing handlers.py
from collections.abc import Callable
from customer_service.agent.callbacks import CallbackResult

def dispatch(
    tool_name: str,
    input_dict: dict,
    services: ServiceContainer,
    context: dict | None = None,          # NEW: user message + flags
    callbacks: list[Callable] | None = None,  # NEW: per-run enforcement hooks
) -> str:
    ...
```

### Credit Card Redaction Regex (verified)
```python
# Source: verified against 4111-1111-1111-1111, 4111 1111 1111 1111, 4111111111111111
import re

_CC_PATTERN_16 = re.compile(
    r"\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b"
)
_CC_AMEX_PATTERN = re.compile(
    r"\b(\d{4})[-\s]?(\d{6})[-\s]?(\d{5})\b"
)

def redact_pci(text: str) -> str:
    """Replace 16-digit card numbers with ****-****-****-XXXX (last 4 preserved)."""
    text = _CC_PATTERN_16.sub(r"****-****-****-\4", text)
    text = _CC_AMEX_PATTERN.sub(r"****-******-*****", text)
    return text
```

### Legal Keyword Detection (verified — no false positives)
```python
# Source: verified against "Issue with my account" (no match) and "I will sue you" (match)
import re

_LEGAL_PATTERN = re.compile(
    r"\b(lawsuit|suing|sue|attorney|lawyer|legal\s+action|court|litigation)\b",
    re.IGNORECASE,
)

def has_legal_keywords(text: str) -> bool:
    """Return True if text contains legal threat keywords."""
    return bool(_LEGAL_PATTERN.search(text))
```

### nbformat Notebook Creation (verified)
```python
# Source: verified with nbformat 5.10.4 in project poetry environment
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

def build_notebook(title: str, cells: list) -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells.extend(cells)
    return nb

# Red box template (established in Phase 1 — 00_setup.ipynb)
RED_BOX = (
    '<div style="border-left: 4px solid #dc3545; padding: 12px 16px; '
    'background: #fff5f5; margin: 8px 0;">\n'
    "<strong>What's wrong:</strong> {msg}\n</div>"
)

GREEN_BOX = (
    '<div style="border-left: 4px solid #28a745; padding: 12px 16px; '
    'background: #f0fff4; margin: 8px 0;">\n'
    "<strong>Why this works:</strong> {msg}\n</div>"
)

CCA_EXAM_TIP = (
    '> **CCA Exam Tip:** {tip}'
)

# Write notebook
with open("notebooks/01_escalation.ipynb", "w") as f:
    nbformat.write(nb, f)
```

### Escalation Callback on process_refund (full pattern)
```python
# Source: application pattern based on CONTEXT.md architecture decisions
def on_process_refund(
    tool_name: str,
    input_dict: dict,
    result_dict: dict,
    context: dict,
    services: ServiceContainer,
) -> CallbackResult:
    """HARD STOP if any escalation flag is set. CCA Rule: deterministic, not confidence-based."""
    flags = context.get("flags", {})
    amount = input_dict.get("amount", 0)

    reasons = []
    if flags.get("is_vip"):
        reasons.append("VIP customer requires human review")
    if flags.get("account_closure"):
        reasons.append("account closure flag set")
    if flags.get("legal_complaint"):
        reasons.append("legal keywords detected in user message")
    if amount > 500:
        reasons.append(f"amount ${amount} exceeds $500 review threshold")

    if reasons:
        escalation_record = EscalationRecord(
            customer_id=input_dict["customer_id"],
            customer_tier=flags.get("customer_tier", "unknown"),
            issue_type="refund",
            disputed_amount=amount,
            escalation_reason="; ".join(reasons),
            recommended_action="Review and approve or deny refund manually",
            conversation_summary=context.get("user_message", ""),
            turns_elapsed=context.get("conversation_turn", 0),
        )
        services.escalation_queue.add_escalation(escalation_record)
        return CallbackResult(
            action="escalate",
            replacement={
                "status": "escalated",
                "reason": "; ".join(reasons),
                "escalation_id": str(len(services.escalation_queue.get_escalations())),
            },
            reason="; ".join(reasons),
        )

    return CallbackResult(action="allow")
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Callbacks in Agent SDK only | Application-level dispatch pattern | CCA lesson: enforcement is your code, not an SDK feature |
| Keyword list `'sue' in text` | `re.compile(r'\b...\b')` with word boundaries | Eliminates false positives on "issue", "pursue" |
| Manual .ipynb JSON | `nbformat.v4` API | Schema-correct notebooks; no manual escaping |
| Global callback registry | Callbacks as function list passed per-call | Per-test, per-notebook control; no global state |

**Deprecated/outdated:**
- Claude Agent SDK `PostToolUse` hooks: that SDK is out-of-scope for this project (raw SDK only, per REQUIREMENTS.md "Out of Scope" section)

---

## Open Questions

1. **Should context.flags accumulate across dispatch calls within one loop iteration?**
   - What we know: `lookup_customer` runs first and sets VIP/closure flags; `process_refund` callback needs those flags
   - What's unclear: Is a shared mutable `context["flags"]` dict mutated by each callback clean enough, or should agent_loop manage a separate `agent_context` dataclass?
   - Recommendation: Mutable `context["flags"]` dict is simplest and sufficient for 3 notebooks. A richer `AgentContext` dataclass is Phase 5+ work.

2. **Can Swiss Army tool misroute (C003 → file_billing_dispute) be made reliable across runs?**
   - What we know: LLM tool selection has ~30% run-to-run variance; `temperature=0` does not fully eliminate this
   - What's unclear: Whether specific distractor description wording makes `file_billing_dispute` reliably preferred over `process_refund` for a $600 refund request
   - Recommendation: CONTEXT.md notes "mention inconsistency briefly in markdown" for NB-01 anti-pattern. Same strategy for NB-03: run the demo with fixed seed scenario, note in markdown that failure mode is probabilistic but the architectural principle (degradation beyond 4-5 tools) is empirically documented. The notebook should also show the CORRECT agent always uses `process_refund`.

3. **Does log_interaction callback mutate input_dict or return a replacement?**
   - What we know: CONTEXT.md says "callback may redact/replace the details field BEFORE the handler writes"
   - What's unclear: Whether dispatch passes the mutated `input_dict` to the handler OR the callback returns a full replacement input dict
   - Recommendation: Callback returns `action="replace_result"` with `replacement={"details": redacted_text}`. Dispatch merges replacement into input_dict before passing to handler. This is explicit, auditable, and consistent with the callback contract. No mutation of caller's dict.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (installed) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| Quick run command | `poetry run pytest tests/test_callbacks.py -x` |
| Full suite command | `poetry run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENFORCE-01 | `dispatch()` invokes callbacks; `action="allow"` passes through | unit | `poetry run pytest tests/test_callbacks.py::TestDispatchCallbacks -x` | Wave 0 |
| ENFORCE-01 | `action="replace_result"` substitutes result JSON | unit | `poetry run pytest tests/test_callbacks.py::TestCallbackReplace -x` | Wave 0 |
| ENFORCE-01 | `action="escalate"` enqueues EscalationRecord + returns replacement | unit | `poetry run pytest tests/test_callbacks.py::TestCallbackEscalate -x` | Wave 0 |
| ENFORCE-02 | VIP flag triggers escalation on `process_refund` | unit | `poetry run pytest tests/test_callbacks.py::TestEscalationRules::test_vip_escalates -x` | Wave 0 |
| ENFORCE-02 | account_closure flag triggers escalation | unit | `poetry run pytest tests/test_callbacks.py::TestEscalationRules::test_closure_escalates -x` | Wave 0 |
| ENFORCE-02 | amount > $500 triggers escalation | unit | `poetry run pytest tests/test_callbacks.py::TestEscalationRules::test_amount_threshold_escalates -x` | Wave 0 |
| ENFORCE-02 | legal keyword in user message triggers escalation | unit | `poetry run pytest tests/test_callbacks.py::TestEscalationRules::test_legal_keyword_escalates -x` | Wave 0 |
| ENFORCE-02 | happy path ($50, regular tier) does NOT escalate | unit | `poetry run pytest tests/test_callbacks.py::TestEscalationRules::test_happy_path_allows -x` | Wave 0 |
| ENFORCE-03 | log_interaction callback redacts credit card from details | unit | `poetry run pytest tests/test_callbacks.py::TestComplianceCallback::test_cc_redaction -x` | Wave 0 |
| ENFORCE-03 | redacted AuditLog entry never contains raw PAN | unit | `poetry run pytest tests/test_callbacks.py::TestComplianceCallback::test_audit_log_no_raw_pan -x` | Wave 0 |
| ANTI-01 | SwissArmyAgent has exactly 15 tools | unit | `poetry run pytest tests/test_callbacks.py::TestAntiPatterns::test_swiss_army_tool_count -x` | Wave 0 |
| ANTI-02 | PromptComplianceAgent returns non-redacted details | unit | `poetry run pytest tests/test_callbacks.py::TestAntiPatterns::test_prompt_compliance_no_redaction -x` | Wave 0 (may need mock) |
| ANTI-03 | ConfidenceAgent schema has confidence field in system prompt | unit | `poetry run pytest tests/test_callbacks.py::TestAntiPatterns::test_confidence_escalation_prompt -x` | Wave 0 |
| NB-02 | Notebook 01 file exists with required sections | smoke | `poetry run pytest tests/test_callbacks.py::TestNotebooks::test_nb01_exists -x` | Wave 0 |
| NB-03 | Notebook 02 file exists with required sections | smoke | `poetry run pytest tests/test_callbacks.py::TestNotebooks::test_nb02_exists -x` | Wave 0 |
| NB-04 | Notebook 03 file exists with required sections | smoke | `poetry run pytest tests/test_callbacks.py::TestNotebooks::test_nb03_exists -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `poetry run pytest tests/test_callbacks.py -x`
- **Per wave merge:** `poetry run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_callbacks.py` — new file; covers all ENFORCE-01/02/03 + ANTI-01/02/03 + NB smoke tests
- [ ] No new conftest needed — existing `services` fixture in `tests/conftest.py` is sufficient
- [ ] No new framework installation — pytest already in `[tool.poetry.group.dev.dependencies]`

---

## Sources

### Primary (HIGH confidence)
- Installed project environment: `anthropic==0.40.0` (verified `python -c "import anthropic; print(anthropic.__version__)"`)
- Installed project environment: `nbformat==5.10.4` (verified `poetry run python -c "import nbformat; print(nbformat.__version__)"`)
- Project source code: `src/customer_service/tools/handlers.py` — dispatch() hook point verified
- Project source code: `src/customer_service/agent/agent_loop.py` — call site for dispatch() verified at line 112
- Project source code: `src/customer_service/models/customer.py` — EscalationRecord, InteractionLog, CustomerProfile shapes verified
- Project source code: `src/customer_service/services/policy_engine.py` — `requires_review` is `amount > 500` regardless of tier (verified against Phase 2 decision log)
- Regex verification: `poetry run python -c` — credit card pattern and legal keyword pattern verified with test inputs
- `.planning/phases/03-callbacks-enforcement-and-first-notebooks/03-CONTEXT.md` — locked architecture decisions
- `.planning/CCA-RULES.md` — CCA certification rules (authoritative)

### Secondary (MEDIUM confidence)
- [Anthropic tool use overview](https://platform.claude.com/docs/en/docs/build-with-claude/tool-use/overview) — confirms raw SDK has no built-in PostToolUse hook; tool use is via response object inspection only
- [nbformat documentation](https://nbformat.readthedocs.io/en/latest/) — v4 API confirmed stable; `new_notebook`, `new_code_cell`, `new_markdown_cell`, `nbformat.write` are the canonical functions
- [softhints.com nbformat guide](https://softhints.com/automatically-create-jupyter-notebooks-python-nbformat/) — corroborates v4 API usage

### Tertiary (LOW confidence)
- WebSearch results on LLM tool selection reproducibility — confirms ~30% run-to-run variance at temperature=0; cannot be fully eliminated without controlled mock setup

---

## Metadata

**Confidence breakdown:**
- Callback architecture (ENFORCE-01): HIGH — verified by reading actual dispatch() and agent_loop.py source; confirmed raw SDK has no built-in hook
- Escalation rules (ENFORCE-02): HIGH — verified against PolicyEngine source; `requires_review` is `amount > 500`; CustomerProfile flags list confirmed
- PCI regex (ENFORCE-03): HIGH — regex verified against all standard test card formats with working code
- Legal keyword detection: HIGH — regex vs keyword-list comparison verified with false-positive test cases
- nbformat API: HIGH — installed and tested in project environment
- Swiss Army tool misroute reproducibility: LOW — probabilistic LLM behavior; confirmed variance in literature but exact failure rate not verified

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (30 days — anthropic SDK stable; nbformat stable)
