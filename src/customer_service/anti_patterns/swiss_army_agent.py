"""CCA Anti-Pattern 3: Swiss Army 15-Tool Agent.

WRONG PATTERN: A single agent is given 15 tools covering customer support,
shipping, inventory, billing, and account management. Beyond 4-5 tools,
Claude's tool selection accuracy degrades measurably.

WHY IT FAILS:
- file_billing_dispute overlaps with process_refund (canonical misroute for $600 refund)
- create_support_ticket overlaps with escalate_to_human (misroute for closure/legal)
- Tool descriptions that cover the same problem space confuse routing
- Claude picks plausible-but-wrong tools — the failure looks like a reasonable mistake

CCA CORRECT PATTERN:
- 4-5 focused tools per agent (see tools/definitions.py)
- Use coordinator-subagent pattern when more tools are needed (Phase 5)

This module is imported ONLY by notebooks to demonstrate tool-selection degradation.
Do NOT reduce the tool count or add guidance — the anti-pattern must fail.
"""

from customer_service.agent.agent_loop import AgentResult, run_agent_loop
from customer_service.services.container import ServiceContainer
from customer_service.tools.definitions import TOOLS

# ---------------------------------------------------------------------------
# 10 distractor tools — plausible cross-domain tools for a support agent
# ---------------------------------------------------------------------------

_DISTRACTOR_TOOLS: list[dict] = [
    {
        "name": "check_shipping_status",
        "description": (
            "Check the shipping and delivery status of a customer order. "
            "Returns tracking info, carrier, and estimated delivery date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "order_id": {"type": "string", "description": "Order ID to track"},
            },
            "required": ["customer_id", "order_id"],
        },
    },
    {
        "name": "lookup_order_history",
        "description": (
            "Look up a customer's complete order history including past purchases, "
            "returns, and exchanges."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "check_inventory",
        "description": (
            "Check current inventory levels and availability for a specific product or SKU."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "product_sku": {"type": "string", "description": "Product SKU to check"},
            },
            "required": ["customer_id", "product_sku"],
        },
    },
    {
        "name": "update_billing_info",
        "description": (
            "Update a customer's billing information including payment method and billing address."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "billing_field": {
                    "type": "string",
                    "description": "Field to update (payment_method, billing_address)",
                },
                "new_value": {"type": "string", "description": "New value for the field"},
            },
            "required": ["customer_id", "billing_field", "new_value"],
        },
    },
    {
        # CANONICAL MISROUTE: overlaps with process_refund for $600 refund
        # Claude picks this instead of process_refund when tool count is high
        "name": "file_billing_dispute",
        "description": (
            "File a billing dispute or chargeback claim for a customer transaction. "
            "Initiates the dispute resolution process for contested charges."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "transaction_amount": {
                    "type": "number",
                    "description": "Amount being disputed in USD",
                },
                "dispute_reason": {
                    "type": "string",
                    "description": "Reason for the dispute",
                },
            },
            "required": ["customer_id", "transaction_amount", "dispute_reason"],
        },
    },
    {
        # CANONICAL MISROUTE: overlaps with escalate_to_human for closure/legal
        # Claude picks this instead of escalate_to_human when tool count is high
        "name": "create_support_ticket",
        "description": (
            "Create a new support ticket for tracking and follow-up on unresolved "
            "customer issues. Routes to the appropriate support team."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "issue_summary": {
                    "type": "string",
                    "description": "Brief summary of the customer issue",
                },
                "priority": {
                    "type": "string",
                    "description": "Ticket priority: low, medium, high, urgent",
                },
            },
            "required": ["customer_id", "issue_summary", "priority"],
        },
    },
    {
        "name": "reset_password",
        "description": (
            "Reset a customer's account password and send a temporary credential via email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "update_account_settings",
        "description": ("Update customer account preferences and notification settings."),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "setting_name": {
                    "type": "string",
                    "description": "Name of the setting to update",
                },
                "setting_value": {
                    "type": "string",
                    "description": "New value for the setting",
                },
            },
            "required": ["customer_id", "setting_name", "setting_value"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": (
            "Search the internal knowledge base for policy documents, FAQs, and "
            "resolution procedures."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "query": {
                    "type": "string",
                    "description": "Search query for the knowledge base",
                },
            },
            "required": ["customer_id", "query"],
        },
    },
    {
        "name": "send_feedback_survey",
        "description": ("Send a post-interaction customer satisfaction survey via email."),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
            },
            "required": ["customer_id"],
        },
    },
]

# CCA Anti-Pattern: 15 tools = 5 correct + 10 distractors
# Beyond 5 tools, tool selection accuracy degrades measurably (CCA rule)
SWISS_ARMY_TOOLS: list[dict] = TOOLS + _DISTRACTOR_TOOLS

# ---------------------------------------------------------------------------
# System prompt — no special guidance about tool selection (that's the trap)
# ---------------------------------------------------------------------------

SWISS_ARMY_SYSTEM_PROMPT: str = (
    "You are a customer support agent for an online retail company. "
    "Your role is to help customers with refund requests, account inquiries, "
    "and general support issues.\n\n"
    "You have access to tools for customer lookup, policy checking, refund "
    "processing, escalation, interaction logging, shipping, order history, "
    "inventory, billing, dispute filing, support tickets, account management, "
    "knowledge base search, and customer surveys.\n\n"
    "Always look up the customer first before taking any action. "
    "Use the most appropriate tool for each step. "
    "Log every interaction for compliance purposes.\n\n"
    "Be professional, empathetic, and efficient. "
    "If you cannot resolve an issue, escalate to a human agent "
    "with a clear summary of the situation."
)


def run_swiss_army_agent(
    client: object,
    services: ServiceContainer,
    user_message: str,
    model: str = "claude-sonnet-4-6",
) -> AgentResult:
    """Run the Swiss Army 15-tool anti-pattern agent.

    ANTI-PATTERN: 15 tools overwhelm Claude's routing. For a $600 refund,
    Claude picks file_billing_dispute instead of process_refund. For account
    closure or legal issues, Claude picks create_support_ticket instead of
    escalate_to_human.

    Uses run_agent_loop with SWISS_ARMY_TOOLS override via the tools parameter.

    Args:
        client: Anthropic API client
        services: Injected ServiceContainer
        user_message: Customer message
        model: Claude model identifier

    Returns:
        AgentResult — likely with wrong tool selections due to tool overload
    """
    return run_agent_loop(
        client=client,
        services=services,
        user_message=user_message,
        system_prompt=SWISS_ARMY_SYSTEM_PROMPT,
        model=model,
        tools=SWISS_ARMY_TOOLS,
    )
    # NOTE: No callbacks. Uses 15 tools — the tool count anti-pattern.
    # The correct pattern uses exactly 5 focused tools (tools/definitions.py).
