"""Tool schema definitions for CCA Customer Support agent.

CCA Rule: Tool descriptions MUST include negative bounds ('does NOT...')
to prevent misrouting. Schemas generated from Pydantic models for
single source of truth (no title keys for Claude API compatibility).
"""

from pydantic import BaseModel, Field

# --- Pydantic input models (single source of truth for schemas) ---


class LookupCustomerInput(BaseModel):
    """Input for lookup_customer tool."""

    customer_id: str = Field(description="Customer ID to look up (e.g., 'C001')")


class CheckPolicyInput(BaseModel):
    """Input for check_policy tool."""

    customer_id: str = Field(description="Customer ID to check policy for")
    requested_amount: float = Field(
        gt=0, description="Refund amount in USD to check against tier policy"
    )


class ProcessRefundInput(BaseModel):
    """Input for process_refund tool."""

    customer_id: str = Field(description="Customer ID for refund")
    order_id: str = Field(description="Order ID to refund")
    amount: float = Field(gt=0, description="Refund amount in USD")
    reason: str = Field(description="Reason for refund")


class EscalateToHumanInput(BaseModel):
    """Input for escalate_to_human tool (CCA structured handoff)."""

    customer_id: str = Field(description="Customer being escalated")
    customer_tier: str = Field(description="Customer tier at time of escalation")
    issue_type: str = Field(description="Type of issue (refund, complaint, etc.)")
    disputed_amount: float = Field(description="Amount in dispute")
    escalation_reason: str = Field(description="Why this is being escalated")
    recommended_action: str = Field(description="Suggested next step for human agent")
    conversation_summary: str = Field(description="Structured summary of conversation so far")
    turns_elapsed: int = Field(description="Number of conversation turns before escalation")


class LogInteractionInput(BaseModel):
    """Input for log_interaction tool."""

    customer_id: str = Field(description="Customer involved in the interaction")
    action: str = Field(description="Action taken (lookup, refund, escalation, etc.)")
    details: str = Field(description="Details of the action taken")


# --- Helper: build tool dict from Pydantic model ---


def _make_tool(name: str, description: str, model: type[BaseModel]) -> dict:
    """Build Claude API tool dict from a Pydantic model.

    Removes top-level 'title' key from schema — required by Claude API.
    """
    schema = model.model_json_schema()
    schema.pop("title", None)
    return {
        "name": name,
        "description": description,
        "input_schema": schema,
    }


# --- 5 tool schema dicts (CCA: exactly 5 focused tools) ---

LOOKUP_CUSTOMER_TOOL = _make_tool(
    name="lookup_customer",
    description=(
        "Look up customer profile by ID. Returns customer tier, account status, and flags. "
        "does NOT modify customer data or process any requests."
    ),
    model=LookupCustomerInput,
)

CHECK_POLICY_TOOL = _make_tool(
    name="check_policy",
    description=(
        "Check refund policy eligibility for a given customer and amount. "
        "Returns approval status, tier limit, and review flag. "
        "does NOT process the refund or modify any records."
    ),
    model=CheckPolicyInput,
)

PROCESS_REFUND_TOOL = _make_tool(
    name="process_refund",
    description=(
        "Process a refund for a customer order. Requires prior policy check approval. "
        "does NOT check policy eligibility — use check_policy first."
    ),
    model=ProcessRefundInput,
)

ESCALATE_TO_HUMAN_TOOL = _make_tool(
    name="escalate_to_human",
    description=(
        "Escalate the current interaction to a human agent with structured context. "
        "does NOT resolve the issue — transfers to human queue."
    ),
    model=EscalateToHumanInput,
)

LOG_INTERACTION_TOOL = _make_tool(
    name="log_interaction",
    description=(
        "Log a customer interaction for compliance and audit purposes. "
        "does NOT affect customer account or trigger any actions."
    ),
    model=LogInteractionInput,
)

# TOOLS list passed to client.messages.create (CCA: 5 focused tools per agent)
TOOLS: list[dict] = [
    LOOKUP_CUSTOMER_TOOL,
    CHECK_POLICY_TOOL,
    PROCESS_REFUND_TOOL,
    ESCALATE_TO_HUMAN_TOOL,
    LOG_INTERACTION_TOOL,
]
