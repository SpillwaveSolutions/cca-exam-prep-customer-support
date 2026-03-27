"""Tests for ContextSummary class (OPTIM-02): structured context management.

CCA Rules tested here:
- ContextSummary uses structured fields, not raw transcripts
- token_estimate stays under TOKEN_BUDGET after 10+ updates (compaction works)
- Key facts (customer_id, issue_type) survive compaction
- tools_called retains all entries internally; to_system_context() shows last 5
- Direct field assignment leaves token_estimate stale (Pitfall 5 documented)
- update() always refreshes token_estimate
"""

from customer_service.agent.context_manager import TOKEN_BUDGET, ContextSummary


class TestContextSummary:
    """Behavioral tests for ContextSummary class."""

    def test_initial_state(self):
        """Fresh ContextSummary has turn_count=0, empty tools_called, empty decisions_made."""
        summary = ContextSummary()
        assert summary.turn_count == 0
        assert summary.tools_called == []
        assert summary.decisions_made == []
        assert summary.customer_id == ""
        assert summary.issue_type == ""
        assert summary.pending_actions == []

    def test_initial_token_estimate_is_zero(self):
        """Fresh ContextSummary has token_estimate=0 before any update."""
        summary = ContextSummary()
        assert summary.token_estimate == 0

    def test_update_increments_turn_count(self):
        """Each update() call increments turn_count by exactly 1."""
        summary = ContextSummary()
        summary.update("lookup_customer", "found C001")
        assert summary.turn_count == 1
        summary.update("check_policy", "eligible for refund")
        assert summary.turn_count == 2
        summary.update("process_refund", "refund processed")
        assert summary.turn_count == 3

    def test_update_appends_to_tools_called(self):
        """update() appends tool_name to tools_called list."""
        summary = ContextSummary()
        summary.update("lookup_customer", "found C001")
        assert summary.tools_called == ["lookup_customer"]
        summary.update("check_policy", "eligible")
        assert summary.tools_called == ["lookup_customer", "check_policy"]

    def test_update_appends_to_decisions_made(self):
        """update() appends result_summary to decisions_made list."""
        summary = ContextSummary()
        summary.update("lookup_customer", "found C001")
        assert "found C001" in summary.decisions_made
        summary.update("check_policy", "eligible for refund up to $500")
        assert "eligible for refund up to $500" in summary.decisions_made

    def test_estimate_accuracy_after_each_update(self):
        """token_estimate == len(to_system_context()) // 4 after every update.

        This is the CCA Pitfall 5 safeguard: token_estimate must always match
        the actual output of to_system_context(). update() must call
        _update_token_estimate() after every mutation.
        """
        summary = ContextSummary()
        summary.customer_id = "C001"
        summary.issue_type = "refund"

        for i in range(5):
            summary.update(f"tool_{i}", f"result summary number {i}")
            expected = len(summary.to_system_context()) // 4
            assert summary.token_estimate == expected, (
                f"After {i + 1} updates: token_estimate={summary.token_estimate} "
                f"but len(to_system_context()) // 4={expected}. "
                "update() must call _update_token_estimate() after every mutation."
            )

    def test_budget_enforcement_after_10_updates(self):
        """token_estimate stays <= TOKEN_BUDGET after 10+ updates with long summaries.

        This is the key behavioral test for OPTIM-02. Compaction must fire
        automatically to keep the summary within budget. Without compaction,
        token_estimate would grow linearly — the same anti-pattern as RawTranscriptContext.
        """
        summary = ContextSummary()
        summary.customer_id = "C001"
        summary.issue_type = "refund_request"

        # Use 50-char result summaries to stress the budget
        long_summary = "x" * 50
        for i in range(10):
            summary.update(f"tool_{i}", long_summary)

        assert summary.token_estimate <= TOKEN_BUDGET, (
            f"After 10 updates, token_estimate={summary.token_estimate} "
            f"exceeds TOKEN_BUDGET={TOKEN_BUDGET}. "
            "Compaction must fire automatically when budget is exceeded."
        )

    def test_key_facts_preserved_after_compaction(self):
        """customer_id and issue_type survive compaction.

        Structured fields (customer_id, issue_type) are preserved in
        to_system_context() output even after compaction removes old decisions.
        This is the core correctness guarantee of ContextSummary over raw transcripts.
        """
        summary = ContextSummary()
        summary.customer_id = "C001"
        summary.issue_type = "refund"

        # Trigger compaction with 10 updates
        long_summary = "x" * 50
        for i in range(10):
            summary.update(f"tool_{i}", long_summary)

        context_output = summary.to_system_context()
        assert "C001" in context_output, (
            "customer_id 'C001' must survive compaction. "
            "Structured fields are never compacted — only decisions_made is truncated."
        )
        assert "refund" in context_output, (
            "issue_type 'refund' must survive compaction. Structured fields are never compacted."
        )

    def test_to_system_context_has_session_context_header(self):
        """to_system_context() output starts with 'SESSION CONTEXT:' header."""
        summary = ContextSummary()
        output = summary.to_system_context()
        assert "SESSION CONTEXT:" in output, (
            f"Expected 'SESSION CONTEXT:' in output, got: {output[:80]!r}"
        )

    def test_to_system_context_includes_customer_id_and_issue_type(self):
        """to_system_context() includes customer_id and issue_type when set."""
        summary = ContextSummary()
        summary.customer_id = "C001"
        summary.issue_type = "account_closure"
        # Trigger estimate refresh
        summary.update("lookup_customer", "found")
        output = summary.to_system_context()
        assert "C001" in output
        assert "account_closure" in output

    def test_tools_called_not_compacted(self):
        """tools_called internal list retains ALL entries after 10 updates.

        The internal tools_called list must NOT be truncated by compaction.
        It keeps all 10 entries so callers can inspect the full tool history.
        However, to_system_context() must display only the LAST 5 tools
        to keep the rendered output bounded.
        """
        summary = ContextSummary()

        for i in range(10):
            summary.update(f"tool_{i}", "some result")

        # Internal list must keep all 10 entries
        assert len(summary.tools_called) == 10, (
            f"Expected tools_called to have 10 entries, got {len(summary.tools_called)}. "
            "The internal tools_called list must never be compacted."
        )

        # to_system_context() must show ONLY the last 5 (tools_called[-5:])
        output = summary.to_system_context()

        # Last 5 tools (tool_5 through tool_9) must appear in output
        for i in range(5, 10):
            assert f"tool_{i}" in output, (
                f"tool_{i} (one of last 5) must appear in to_system_context() output"
            )

        # First 5 tools (tool_0 through tool_4) must NOT appear in output
        for i in range(5):
            assert f"tool_{i}" not in output, (
                f"tool_{i} (one of first 5) must NOT appear in to_system_context() output. "
                "to_system_context() should only show the last 5 tools (tools_called[-5:])."
            )

    def test_estimate_after_direct_field_set(self):
        """Direct field assignment leaves token_estimate stale at 0 until update() called.

        CCA Pitfall 5: if customer_id or issue_type is set directly (bypassing update()),
        the estimate won't refresh. This test proves the pitfall exists and that
        update() correctly refreshes the estimate.

        This is a teaching test — notebooks show students this pitfall directly.
        """
        summary = ContextSummary()

        # Set fields directly (bypassing update())
        summary.customer_id = "C001"
        summary.issue_type = "refund"

        # token_estimate is still 0 — direct assignment does not trigger recalculation
        assert summary.token_estimate == 0, (
            f"Expected token_estimate=0 after direct field assignment, "
            f"got {summary.token_estimate}. "
            "Direct field assignment must NOT trigger _update_token_estimate(). "
            "This is CCA Pitfall 5 — demonstrate the staleness deliberately."
        )

        # After calling update(), estimate must be refreshed and correct
        summary.update("lookup_customer", "found customer")

        expected = len(summary.to_system_context()) // 4
        assert summary.token_estimate == expected, (
            f"After update(), token_estimate={summary.token_estimate} "
            f"but expected {expected} (len(to_system_context()) // 4). "
            "update() must call _update_token_estimate() to refresh the estimate."
        )
        assert summary.token_estimate > 0, (
            "After update(), token_estimate must be > 0 since context now has content"
        )
