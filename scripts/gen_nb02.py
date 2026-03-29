"""Generate notebooks/02_compliance.ipynb using nbformat."""

from pathlib import Path

import nbformat
import nbformat.v4 as nbf

cells = []

# ---------------------------------------------------------------------------
# Cell 1: Title markdown
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "# Notebook 02: Compliance Pattern\n\n"
        "The CCA exam tests whether you understand that PCI compliance and data "
        "redaction must be **enforced programmatically in code**, not just requested "
        "in a system prompt. This notebook shows both patterns on the same scenario — "
        "a customer who includes a credit card number in their message — so you can "
        "see whether PII reaches the audit log.\n\n"
        "Pattern covered: **PostToolUse compliance callback with regex redaction** "
        "vs. prompt-only compliance instructions."
    )
)

# ---------------------------------------------------------------------------
# Cell 2: Setup section header
# ---------------------------------------------------------------------------
cells.append(nbf.new_markdown_cell("## Setup"))

# ---------------------------------------------------------------------------
# Cell 3: Imports
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "# Add project root so helpers and customer_service are importable\n"
        "sys.path.insert(0, str(Path('.').resolve()))\n"
        "\n"
        "import anthropic\n"
        "from helpers import compare_results, print_usage\n"
        "\n"
        "from customer_service.data.customers import CUSTOMERS\n"
        "from customer_service.data.scenarios import SCENARIOS\n"
        "from customer_service.services.audit_log import AuditLog\n"
        "from customer_service.services.container import ServiceContainer\n"
        "from customer_service.services.customer_db import CustomerDatabase\n"
        "from customer_service.services.escalation_queue import EscalationQueue\n"
        "from customer_service.services.financial_system import FinancialSystem\n"
        "from customer_service.services.policy_engine import PolicyEngine\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 4: Client and services setup
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "def make_services() -> ServiceContainer:\n"
        '    """Create a fresh ServiceContainer with seed customer data."""\n'
        "    return ServiceContainer(\n"
        "        customer_db=CustomerDatabase(CUSTOMERS),\n"
        "        policy_engine=PolicyEngine(),\n"
        "        financial_system=FinancialSystem(),\n"
        "        escalation_queue=EscalationQueue(),\n"
        "        audit_log=AuditLog(),\n"
        "    )\n"
        "\n"
        "\n"
        "client = anthropic.Anthropic()\n"
        "scenario = SCENARIOS['happy_path']  # C001, $50 refund\n"
        "# Inject a credit card number into the message for compliance testing\n"
        "pii_message = scenario['message'] + ' My card is 4111-1111-1111-1111.'\n"
        "print(f'Customer ID: {scenario[\"customer_id\"]}')\n"
        "print(f'Message with PII: {pii_message}')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 5: Anti-pattern markdown (red box)
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "## Anti-Pattern: Prompt-Only Compliance\n\n"
        '<div style="border-left: 4px solid #dc3545; padding: 12px 16px; '
        'background: #fff5f5; margin: 8px 0;">\n'
        "<strong>What's wrong:</strong> The system prompt says "
        '"never log credit card numbers" and "redact before logging," but there is '
        "no programmatic enforcement. Claude sometimes follows this instruction, "
        "sometimes doesn't — compliance becomes probabilistic. A single missed "
        "redaction is a PCI violation.\n"
        "</div>"
    )
)

# ---------------------------------------------------------------------------
# Cell 6: Run anti-pattern
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "from customer_service.anti_patterns.prompt_compliance import (\n"
        "    run_prompt_compliance_agent,\n"
        ")\n"
        "\n"
        "anti_services = make_services()\n"
        "print('Running anti-pattern (prompt-only compliance)...')\n"
        "anti_result = run_prompt_compliance_agent(client, anti_services, pii_message)\n"
        "print(f'Stop reason: {anti_result.stop_reason}')\n"
        "print(f'Tool calls: {[tc[\"name\"] for tc in anti_result.tool_calls]}')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 7: Check anti-pattern audit log for PII leakage
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "# Check whether the raw card number reached the audit log\n"
        "anti_logs = anti_services.audit_log.get_entries()\n"
        "print(f'Audit log entries: {len(anti_logs)}')\n"
        "\n"
        "anti_pii_leaked = False\n"
        "for entry in anti_logs:\n"
        "    details = entry.details\n"
        "    if '4111' in details and '****' not in details:\n"
        "        anti_pii_leaked = True\n"
        "        print(f'PII LEAKED in audit log: {details[:120]}...')\n"
        "\n"
        "if not anti_pii_leaked:\n"
        "    print('Note: Prompt happened to redact this run (probabilistic — varies by run)')\n"
        "    for entry in anti_logs:\n"
        "        print(f'  Log entry: {entry.details[:80]}...')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 8: Print usage for anti-pattern
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "class _UsageWrapper:\n"
        "    def __init__(self, u):\n"
        "        self.usage = u\n"
        "\n"
        "print_usage(_UsageWrapper(anti_result.usage))\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 9: Correct pattern markdown (green box)
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "## Correct Pattern: Programmatic Compliance via Callback\n\n"
        '<div style="border-left: 4px solid #28a745; padding: 12px 16px; '
        'background: #f0fff4; margin: 8px 0;">\n'
        "<strong>Why this works:</strong> The PostToolUse compliance callback "
        "intercepts every <code>log_interaction</code> call and applies a regex "
        "to redact 16-digit card numbers before they reach the audit log. "
        "This is deterministic — the regex fires regardless of whether Claude "
        "remembered to redact, regardless of prompt wording, on every single call.\n"
        "</div>"
    )
)

# ---------------------------------------------------------------------------
# Cell 10: Run correct pattern
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "from customer_service.agent import build_callbacks, get_system_prompt, run_agent_loop\n"
        "\n"
        "correct_services = make_services()\n"
        "callbacks = build_callbacks()\n"
        "print('Running correct pattern (programmatic compliance callback)...')\n"
        "correct_result = run_agent_loop(\n"
        "    client,\n"
        "    correct_services,\n"
        "    pii_message,\n"
        "    get_system_prompt(),\n"
        "    callbacks=callbacks,\n"
        ")\n"
        "print(f'Stop reason: {correct_result.stop_reason}')\n"
        "print(f'Tool calls: {[tc[\"name\"] for tc in correct_result.tool_calls]}')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 11: Check correct pattern audit log for redaction
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "# Verify that the full card number never reached the audit log\n"
        "correct_logs = correct_services.audit_log.get_entries()\n"
        "print(f'Audit log entries: {len(correct_logs)}')\n"
        "\n"
        "correct_pii_safe = True\n"
        "for entry in correct_logs:\n"
        "    details = entry.details\n"
        "    if '4111-1111-1111-1111' in details:\n"
        "        correct_pii_safe = False\n"
        "        print(f'PII LEAKED (unexpected): {details[:120]}')\n"
        "    if '****' in details:\n"
        "        print(f'Correctly redacted entry: {details[:100]}')\n"
        "\n"
        "print(f'\\nPII safely redacted in audit log: {correct_pii_safe}')\n"
        "if correct_pii_safe:\n"
        "    print('SUCCESS: Programmatic callback prevented PII from reaching audit log')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 12: Print usage for correct pattern
# ---------------------------------------------------------------------------
cells.append(nbf.new_code_cell("print_usage(_UsageWrapper(correct_result.usage))\n"))

# ---------------------------------------------------------------------------
# Cell 13: Compare results header
# ---------------------------------------------------------------------------
cells.append(nbf.new_markdown_cell("## Compare Results"))

# ---------------------------------------------------------------------------
# Cell 14: Side-by-side comparison
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "compare_results(\n"
        "    {\n"
        "        'pii_leaked': anti_pii_leaked,\n"
        "        'audit_log_entries': len(anti_logs),\n"
        "        'tool_calls': len(anti_result.tool_calls),\n"
        "    },\n"
        "    {\n"
        "        'pii_leaked': not correct_pii_safe,\n"
        "        'audit_log_entries': len(correct_logs),\n"
        "        'tool_calls': len(correct_result.tool_calls),\n"
        "    },\n"
        ")\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 15: CCA Exam Tip
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "> **CCA Exam Tip:** If an exam answer says 'add PCI compliance rules "
        "to the system prompt,' it is WRONG. Compliance must be enforced "
        "programmatically through validation hooks and callbacks. System prompts "
        "provide context; code enforces rules. Prompt instructions are probabilistic "
        "guidance — a regex in a PostToolUse callback is a deterministic guarantee."
    )
)

# ---------------------------------------------------------------------------
# Cell 16: Summary
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "## Summary\n\n"
        "- **Anti-pattern failure:** Prompt-only compliance is probabilistic — "
        "Claude may or may not redact PII before logging, depending on the run. "
        "Any single missed redaction is a real PCI violation.\n"
        "- **Correct pattern guarantee:** PostToolUse compliance callback applies "
        "a regex to every `log_interaction` call before it writes to the audit log. "
        "The card number is replaced with `****-****-****-NNNN` (last 4 preserved) "
        "deterministically on every call.\n"
        "- **Key principle:** Compliance enforcement belongs in code (callbacks), "
        "not in natural language (system prompts). This is CCA architectural "
        "principle #2: programmatic hooks are the only reliable enforcement mechanism."
    )
)

# ---------------------------------------------------------------------------
# Build and write notebook
# ---------------------------------------------------------------------------
nb = nbf.new_notebook()
nb.cells = cells
nb.metadata.update(
    {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.13.0",
        },
    }
)

output_path = Path(__file__).parent.parent / "notebooks" / "02_compliance.ipynb"
with output_path.open("w") as f:
    nbformat.write(nb, f)

print(f"Written: {output_path}")
