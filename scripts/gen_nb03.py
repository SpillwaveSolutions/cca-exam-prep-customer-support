"""Generate notebooks/03_tool_design.ipynb using nbformat."""

from pathlib import Path

import nbformat
import nbformat.v4 as nbf

cells = []

# ---------------------------------------------------------------------------
# Cell 1: Title markdown
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "# Notebook 03: Tool Design Pattern\n\n"
        "The CCA exam tests whether you understand that **tool selection accuracy "
        "degrades measurably when an agent has more than 4–5 tools**. This notebook "
        "shows both patterns on the same scenario — a \\$600 refund for customer "
        "C003 — to demonstrate that 15 overlapping tools cause tool selection errors "
        "that 5 focused tools avoid.\n\n"
        "Pattern covered: **5-tool focused agent with negative bounds** "
        "vs. 15-tool Swiss Army agent with overlapping descriptions."
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
        "from customer_service.anti_patterns.swiss_army_agent import SWISS_ARMY_TOOLS\n"
        "from customer_service.data.customers import CUSTOMERS\n"
        "from customer_service.data.scenarios import SCENARIOS\n"
        "from customer_service.services.audit_log import AuditLog\n"
        "from customer_service.services.container import ServiceContainer\n"
        "from customer_service.services.customer_db import CustomerDatabase\n"
        "from customer_service.services.escalation_queue import EscalationQueue\n"
        "from customer_service.services.financial_system import FinancialSystem\n"
        "from customer_service.services.policy_engine import PolicyEngine\n"
        "from customer_service.tools.definitions import TOOLS\n"
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
        "scenario = SCENARIOS['amount_threshold']  # C003, $600 — same as Notebook 01\n"
        'print(f\'Scenario: {scenario["customer_id"]} - {scenario["message"]}\')\n'
        "print('\\nThis is the SAME scenario as Notebook 01,')\n"
        "print('demonstrating a different CCA failure mode.')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 5: Show tool count comparison
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "# Show the tool count difference before running any agent\n"
        "correct_tool_names = {t['name'] for t in TOOLS}\n"
        "print(f'Correct agent: {len(TOOLS)} tools')\n"
        "print(f'Swiss Army agent: {len(SWISS_ARMY_TOOLS)} tools')\n"
        "print('\\nCorrect tool names:')\n"
        "for t in TOOLS:\n"
        "    print(f'  - {t[\"name\"]}')\n"
        "print('\\nSwiss Army tool names (10 distractors added):')\n"
        "for t in SWISS_ARMY_TOOLS:\n"
        "    marker = '' if t['name'] in correct_tool_names else ' <-- distractor'\n"
        "    print(f'  - {t[\"name\"]}{marker}')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 6: Anti-pattern markdown (red box)
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "## Anti-Pattern: Swiss Army Agent (15 Tools)\n\n"
        '<div style="border-left: 4px solid #dc3545; padding: 12px 16px; '
        'background: #fff5f5; margin: 8px 0;">\n'
        "<strong>What's wrong:</strong> The Swiss Army agent has 15 tools with "
        "overlapping descriptions. Tools like <code>file_billing_dispute</code> "
        "sound similar to <code>process_refund</code> for a dollar-amount issue, "
        "and <code>create_support_ticket</code> overlaps with <code>escalate_to_human</code> "
        "for closure or legal cases. Claude mis-routes to distractor tools instead "
        "of the correct ones, causing observable failures.\n"
        "</div>"
    )
)

# ---------------------------------------------------------------------------
# Cell 7: Run anti-pattern
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "from customer_service.anti_patterns.swiss_army_agent import run_swiss_army_agent\n"
        "\n"
        "anti_services = make_services()\n"
        "print('Running anti-pattern (Swiss Army agent, 15 tools)...')\n"
        "anti_result = run_swiss_army_agent(client, anti_services, scenario['message'])\n"
        "print(f'Stop reason: {anti_result.stop_reason}')\n"
        "print(f'Tool calls: {[tc[\"name\"] for tc in anti_result.tool_calls]}')\n"
        "\n"
        "# Check if any distractor tools were called\n"
        "anti_distractor_calls = [\n"
        "    tc['name'] for tc in anti_result.tool_calls\n"
        "    if tc['name'] not in correct_tool_names\n"
        "]\n"
        "if anti_distractor_calls:\n"
        "    print(f'\\nDISTRACTOR TOOLS CALLED: {anti_distractor_calls}')\n"
        "    print('Tool selection error: agent chose wrong tool from 15-tool set')\n"
        "else:\n"
        "    print('\\nNote: Agent selected correct tools this run (probabilistic)')\n"
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
        "## Correct Pattern: Focused 5-Tool Agent\n\n"
        '<div style="border-left: 4px solid #28a745; padding: 12px 16px; '
        'background: #f0fff4; margin: 8px 0;">\n'
        "<strong>Why this works:</strong> The focused agent has exactly 5 tools, "
        "each with precise descriptions and negative bounds (e.g., "
        '"does NOT handle billing disputes"). '
        "With no overlapping tools, Claude selects correctly every time. "
        "If the task genuinely requires more capabilities, the correct CCA "
        "pattern is coordinator-subagent — not cramming more tools into one agent.\n"
        "</div>"
    )
)

# ---------------------------------------------------------------------------
# Cell 10: Run correct pattern
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "from customer_service.agent import get_system_prompt, run_agent_loop\n"
        "\n"
        "correct_services = make_services()\n"
        "print('Running correct pattern (focused 5-tool agent)...')\n"
        "correct_result = run_agent_loop(\n"
        "    client,\n"
        "    correct_services,\n"
        "    scenario['message'],\n"
        "    get_system_prompt(),\n"
        ")\n"
        "print(f'Stop reason: {correct_result.stop_reason}')\n"
        "print(f'Tool calls: {[tc[\"name\"] for tc in correct_result.tool_calls]}')\n"
        "\n"
        "# All calls should be from the correct tool set\n"
        "correct_distractor_calls = [\n"
        "    tc['name'] for tc in correct_result.tool_calls\n"
        "    if tc['name'] not in correct_tool_names\n"
        "]\n"
        "if not correct_distractor_calls:\n"
        "    print('\\nSUCCESS: All tool calls from correct 5-tool set')\n"
        "else:\n"
        "    print(f'\\nUNEXPECTED distractor calls: {correct_distractor_calls}')\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 11: Print usage for correct pattern
# ---------------------------------------------------------------------------
cells.append(nbf.new_code_cell("print_usage(_UsageWrapper(correct_result.usage))\n"))

# ---------------------------------------------------------------------------
# Cell 12: Compare results header
# ---------------------------------------------------------------------------
cells.append(nbf.new_markdown_cell("## Compare Results"))

# ---------------------------------------------------------------------------
# Cell 13: Side-by-side comparison
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_code_cell(
        "compare_results(\n"
        "    {\n"
        "        'tool_count_available': len(SWISS_ARMY_TOOLS),\n"
        "        'distractor_tools_called': len(anti_distractor_calls),\n"
        "        'tool_calls_total': len(anti_result.tool_calls),\n"
        "    },\n"
        "    {\n"
        "        'tool_count_available': len(TOOLS),\n"
        "        'distractor_tools_called': len(correct_distractor_calls),\n"
        "        'tool_calls_total': len(correct_result.tool_calls),\n"
        "    },\n"
        ")\n"
    )
)

# ---------------------------------------------------------------------------
# Cell 14: CCA Exam Tip
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "> **CCA Exam Tip:** Beyond 4–5 tools per agent, tool selection accuracy "
        "degrades measurably. If an exam scenario describes an agent with 12+ tools "
        "and selection errors, the answer is to split into focused agents with 4–5 "
        "tools each using the **coordinator-subagent pattern** — NOT to improve tool "
        "descriptions or add a disambiguation prompt. Adding tools to a single agent "
        "is always the wrong answer."
    )
)

# ---------------------------------------------------------------------------
# Cell 15: Summary
# ---------------------------------------------------------------------------
cells.append(
    nbf.new_markdown_cell(
        "## Summary\n\n"
        "- **Anti-pattern failure:** A 15-tool Swiss Army agent with overlapping "
        "descriptions causes tool selection errors. Claude routes to distractor tools "
        "like `file_billing_dispute` instead of `process_refund`, or to "
        "`create_support_ticket` instead of `escalate_to_human`.\n"
        "- **Correct pattern guarantee:** A focused 5-tool agent with precise "
        "descriptions and negative bounds gives Claude unambiguous choices. "
        "Tool selection is accurate because there is no ambiguity.\n"
        "- **Key principle:** When a task requires more than 5 tools, the CCA "
        "correct answer is the coordinator-subagent pattern — a coordinator agent "
        "that routes to specialized sub-agents, each with 4–5 focused tools."
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

output_path = Path(__file__).parent.parent / "notebooks" / "03_tool_design.ipynb"
with output_path.open("w") as f:
    nbformat.write(nb, f)

print(f"Written: {output_path}")
