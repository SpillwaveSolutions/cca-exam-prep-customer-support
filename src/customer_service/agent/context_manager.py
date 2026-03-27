"""Structured context management for CCA Customer Support agent.

CCA Rule (OPTIM-02): Use structured JSON summaries, NOT raw transcripts.

Raw transcripts cause:
- O(n) token growth per turn (unbounded)
- Lost-in-middle effect (critical early facts get buried)
- Attention dilution (model focuses on recent content)

ContextSummary prevents these by:
- Fixed-field schema (customer_id, issue_type, etc. never get compacted)
- Budget enforcement (token_estimate <= TOKEN_BUDGET after any number of updates)
- Automatic compaction (truncates decisions_made when budget is exceeded)

CCA Pitfall 5 (documented, not fixed):
    Direct field assignment (e.g., summary.customer_id = "C001") does NOT
    trigger _update_token_estimate(). The token_estimate stays stale until
    update() is called. This is intentional — notebooks use this to demonstrate
    the pitfall to students.
"""

from dataclasses import dataclass, field

# TOKEN_BUDGET: maximum token_estimate allowed before compaction fires.
# Using len(text) // 4 character heuristic — approximately 75 tokens.
# Fits comfortably in a system block without eating into the prompt cache savings.
TOKEN_BUDGET = 300


@dataclass
class ContextSummary:
    """Structured session context for multi-turn agent conversations.

    CCA Rule: structured summaries beat raw transcripts for context preservation.
    Fixed fields prevent unbounded growth; token_estimate enables budget gating;
    compaction keeps the summary bounded without losing critical structured data.

    Usage:
        summary = ContextSummary()
        summary.customer_id = "C001"
        summary.issue_type = "refund"
        summary.update("lookup_customer", "Found Alice, Standard tier")
        summary.update("check_policy", "Eligible for refund up to $500")
        system_context = summary.to_system_context()
        # Inject into system message or pass to next agent turn

    CCA Pitfall 5 (documented):
        Direct field assignment (summary.customer_id = "C001") does NOT
        update token_estimate. Call update() after setting fields to refresh.
        This pitfall is demonstrated deliberately in test_estimate_after_direct_field_set.
    """

    customer_id: str = ""
    issue_type: str = ""
    tools_called: list[str] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)
    turn_count: int = 0
    token_estimate: int = 0

    def update(self, tool_name: str, result_summary: str) -> None:
        """Record one tool dispatch. Compacts decisions_made if over budget.

        This is the ONLY method that updates token_estimate. Direct field
        assignment (summary.customer_id = "X") does NOT refresh the estimate —
        this is CCA Pitfall 5, documented intentionally for teaching.

        Args:
            tool_name: Name of the tool called (e.g., "lookup_customer")
            result_summary: Short summary of what the tool returned
        """
        self.tools_called.append(tool_name)
        self.decisions_made.append(result_summary)
        self.turn_count += 1
        self._update_token_estimate()
        if self.token_estimate > TOKEN_BUDGET:
            self._compact()

    def to_system_context(self) -> str:
        """Render structured text for injection into the system message.

        Shows the last 5 tools_called and last 3 decisions_made to keep
        the output bounded. The internal tools_called list retains ALL entries.

        Returns:
            Structured string beginning with 'SESSION CONTEXT:' header,
            including customer_id, issue_type, recent tools, and recent decisions.
        """
        return (
            f"SESSION CONTEXT:\n"
            f"Customer: {self.customer_id} | Issue: {self.issue_type}\n"
            f"Turn: {self.turn_count} | Tools used: {', '.join(self.tools_called[-5:])}\n"
            f"Decisions: {'; '.join(self.decisions_made[-3:])}\n"
            f"Pending: {'; '.join(self.pending_actions)}"
        )

    def _update_token_estimate(self) -> None:
        """Recalculate token_estimate from current to_system_context() output.

        Uses len(text) // 4 character heuristic — approximately 10% error
        acceptable for a budget gate in a teaching demo. No API call needed.
        """
        self.token_estimate = len(self.to_system_context()) // 4

    def _compact(self) -> None:
        """Keep only the most recent decisions when over budget.

        Truncates decisions_made to last 2 entries, then recalculates estimate.
        If still over budget (e.g., pending_actions is large), further truncates
        pending_actions.

        Note: tools_called is NEVER compacted — the internal list retains all
        entries. to_system_context() displays only tools_called[-5:] for output.
        Note: customer_id and issue_type are NEVER compacted — they are fixed
        structured fields that survive compaction unconditionally.
        """
        self.decisions_made = self.decisions_made[-2:]
        self._update_token_estimate()
        if self.token_estimate > TOKEN_BUDGET:
            # If still over budget, truncate pending_actions as second lever
            self.pending_actions = self.pending_actions[-1:] if self.pending_actions else []
            self._update_token_estimate()
