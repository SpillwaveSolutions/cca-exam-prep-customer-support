"""Tests for prompt caching (OPTIM-01) and anti-patterns (ANTI-04).

CCA Rules tested here:
- Prompt Caching: get_system_prompt_with_caching() returns correct 2-block list-of-dicts
- POLICY_DOCUMENT >= 2048 tokens (critical threshold for claude-sonnet-4-6)
- agent_loop accepts list[dict] system_prompt without code changes
- Cache token fields (cache_creation_input_tokens, cache_read_input_tokens) accumulate
- RawTranscriptContext demonstrates O(n) token growth (ANTI-04)
- BATCH_API_EXPLANATION provides CCA teaching content
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from customer_service.agent.agent_loop import run_agent_loop
from customer_service.agent.system_prompts import (
    POLICY_DOCUMENT,
    get_system_prompt,
    get_system_prompt_with_caching,
)
from customer_service.anti_patterns.batch_api_live import BATCH_API_EXPLANATION
from customer_service.anti_patterns.raw_transcript import RawTranscriptContext


def _make_usage(inp=100, out=50, cr=0, cw=0):
    """Create a mock usage object matching Anthropic SDK shape."""
    return SimpleNamespace(
        input_tokens=inp,
        output_tokens=out,
        cache_read_input_tokens=cr,
        cache_creation_input_tokens=cw,
    )


def _make_text_block(text="Done"):
    return SimpleNamespace(type="text", text=text)


def _make_response(stop_reason="end_turn", content=None, usage=None):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=content or [_make_text_block()],
        usage=usage or _make_usage(),
    )


class TestPolicyDocument:
    """POLICY_DOCUMENT must exceed the 2048-token minimum for claude-sonnet-4-6 caching."""

    def test_policy_document_exceeds_2048_tokens(self):
        """CRITICAL: POLICY_DOCUMENT must be >= 2048 tokens using len // 4 heuristic.

        claude-sonnet-4-6 requires a minimum of 2048 tokens in the cached block.
        Below this threshold, caching silently does not activate even with
        cache_control set correctly.
        """
        token_estimate = len(POLICY_DOCUMENT) // 4
        assert token_estimate > 2048, (
            f"POLICY_DOCUMENT is only ~{token_estimate} tokens "
            f"(len={len(POLICY_DOCUMENT)} chars). "
            f"claude-sonnet-4-6 requires >= 2048 tokens for caching to activate. "
            f"Target: at least 9000 characters (~2250 tokens)."
        )

    def test_policy_document_is_string(self):
        """POLICY_DOCUMENT must be a non-empty string."""
        assert isinstance(POLICY_DOCUMENT, str)
        assert len(POLICY_DOCUMENT) > 0

    def test_policy_document_has_policy_content(self):
        """POLICY_DOCUMENT must contain substantive policy text, not filler."""
        # Must mention key policy concepts
        doc_lower = POLICY_DOCUMENT.lower()
        assert "refund" in doc_lower, "POLICY_DOCUMENT must contain refund policy"
        assert "customer" in doc_lower, "POLICY_DOCUMENT must reference customers"


class TestSystemPromptCaching:
    """get_system_prompt_with_caching() must return correct 2-block list structure."""

    def test_returns_list_not_string(self):
        """Return type must be list, not str."""
        result = get_system_prompt_with_caching()
        assert isinstance(result, list), (
            f"Expected list, got {type(result)}. "
            "run_agent_loop passes this directly to SDK system= parameter."
        )

    def test_returns_exactly_two_blocks(self):
        """Must return exactly 2 content blocks."""
        result = get_system_prompt_with_caching()
        assert len(result) == 2, f"Expected 2 blocks, got {len(result)}"

    def test_block_zero_is_agent_instructions(self):
        """Block 0: type='text', text matches get_system_prompt(), no cache_control."""
        result = get_system_prompt_with_caching()
        block0 = result[0]
        assert block0["type"] == "text"
        assert block0["text"] == get_system_prompt()
        assert "cache_control" not in block0, (
            "Block 0 (agent instructions) should NOT have cache_control. "
            "cache_control belongs on the large static POLICY_DOCUMENT block."
        )

    def test_block_one_is_cached_policy(self):
        """Block 1: type='text', text == POLICY_DOCUMENT, cache_control is ephemeral."""
        result = get_system_prompt_with_caching()
        block1 = result[1]
        assert block1["type"] == "text"
        assert block1["text"] == POLICY_DOCUMENT
        assert "cache_control" in block1, "Block 1 (POLICY_DOCUMENT) must have cache_control"
        assert block1["cache_control"] == {"type": "ephemeral"}, (
            f"Expected cache_control={{'type': 'ephemeral'}}, got {block1['cache_control']}"
        )

    def test_cache_control_on_correct_block(self):
        """CCA Anti-pattern check: cache_control must be on the LAST block (POLICY_DOCUMENT).

        Common mistake: putting cache_control on the smaller AGENT_INSTRUCTIONS block.
        The cache breakpoint marks everything BEFORE it as cacheable.
        """
        result = get_system_prompt_with_caching()
        # Block 0 (instructions) should NOT have cache_control
        assert "cache_control" not in result[0]
        # Block 1 (policy) MUST have cache_control
        assert "cache_control" in result[1]


class TestAgentLoopSystemType:
    """run_agent_loop must accept list[dict] system_prompt (caching form)."""

    def test_accepts_list_system_prompt(self, services):
        """Verify agent_loop passes list system_prompt to SDK without error."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("Resolved.")],
        )
        caching_prompt = get_system_prompt_with_caching()

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Help me with my order.",
            system_prompt=caching_prompt,
        )

        assert result.stop_reason == "end_turn"
        mock_client.messages.create.assert_called_once()

    def test_sdk_receives_list_as_system_kwarg(self, services):
        """Verify client.messages.create receives the list form as system= kwarg."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_response()
        caching_prompt = get_system_prompt_with_caching()

        run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Test.",
            system_prompt=caching_prompt,
        )

        # Extract the system= argument passed to client.messages.create
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] is caching_prompt, (
            "run_agent_loop must pass system_prompt directly as system= to SDK. "
            "The SDK natively accepts both str and list[dict]."
        )


class TestCacheTokenAccounting:
    """Cache token fields accumulate correctly via mock client.

    These tests prove that when the mock API returns cache fields,
    run_agent_loop accumulates them into UsageSummary correctly.
    """

    def test_cache_write_on_first_call(self, services):
        """Mock returns cache_creation_input_tokens=2200; result must show 2200.

        Simulates first call where POLICY_DOCUMENT is written to cache.
        cache_creation_input_tokens represents tokens being cached (written).
        """
        mock_client = MagicMock()
        # First call: cache write (2200 tokens cached, 0 read from cache)
        mock_client.messages.create.return_value = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("Issue resolved.")],
            usage=_make_usage(inp=100, out=50, cr=0, cw=2200),
        )

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Process my refund.",
            system_prompt=get_system_prompt_with_caching(),
        )

        assert result.usage.cache_creation_input_tokens == 2200, (
            f"Expected cache_creation_input_tokens=2200, "
            f"got {result.usage.cache_creation_input_tokens}. "
            "run_agent_loop must accumulate cache_creation_input_tokens from response.usage."
        )
        assert result.usage.cache_read_input_tokens == 0, (
            "First call should have cache_read_input_tokens=0 (cache miss, writing)"
        )

    def test_cache_read_on_second_call(self, services):
        """Mock returns cache_read_input_tokens=2200; result must show 2200.

        Simulates second call where POLICY_DOCUMENT is served from cache.
        cache_read_input_tokens represents tokens read from cache (cheaper).
        """
        mock_client = MagicMock()
        # Second call: cache read (2200 tokens served from cache, 0 written)
        mock_client.messages.create.return_value = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("Issue resolved from cache.")],
            usage=_make_usage(inp=100, out=50, cr=2200, cw=0),
        )

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Process my refund again.",
            system_prompt=get_system_prompt_with_caching(),
        )

        assert result.usage.cache_read_input_tokens == 2200, (
            f"Expected cache_read_input_tokens=2200, "
            f"got {result.usage.cache_read_input_tokens}. "
            "run_agent_loop must accumulate cache_read_input_tokens from response.usage."
        )
        assert result.usage.cache_creation_input_tokens == 0, (
            "Second call (cache hit) should have cache_creation_input_tokens=0"
        )

    def test_cache_tokens_accumulate_across_iterations(self, services):
        """Cache tokens accumulate across multiple loop iterations.

        Two API calls: first writes cache (cw=2200), second reads cache (cr=2200).
        UsageSummary must sum both across the single run_agent_loop call.
        """
        from types import SimpleNamespace

        mock_client = MagicMock()

        def _make_tool_use_block():
            return SimpleNamespace(
                type="tool_use",
                name="lookup_customer",
                input={"customer_id": "C001"},
                id="toolu_01",
            )

        # First iteration: tool_use with cache write
        iter1 = _make_response(
            stop_reason="tool_use",
            content=[_make_tool_use_block()],
            usage=_make_usage(inp=100, out=30, cr=0, cw=2200),
        )
        # Second iteration: end_turn with cache read
        iter2 = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("Done")],
            usage=_make_usage(inp=50, out=20, cr=2200, cw=0),
        )
        mock_client.messages.create.side_effect = [iter1, iter2]

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Look up my account.",
            system_prompt=get_system_prompt_with_caching(),
        )

        assert result.usage.cache_creation_input_tokens == 2200  # from iter1
        assert result.usage.cache_read_input_tokens == 2200  # from iter2


class TestRawTranscriptAntiPattern:
    """RawTranscriptContext demonstrates O(n) token growth per append (ANTI-04).

    This is the anti-pattern: raw transcripts grow unbounded, causing lost-in-middle
    attention dilution. CCA Exam: bigger context window makes it WORSE, not better.
    """

    def test_token_estimate_grows_with_each_append(self):
        """3 appends must each produce strictly larger token_estimate than previous."""
        ctx = RawTranscriptContext()
        estimate_before = ctx.token_estimate()
        assert estimate_before == 0, "Fresh context should have 0 token estimate"

        ctx.append("user", "I need a refund for order #12345 from last week.")
        estimate_after_1 = ctx.token_estimate()
        assert estimate_after_1 > estimate_before, (
            f"After 1 append: estimate {estimate_after_1} must exceed {estimate_before}"
        )

        ctx.append("assistant", "I can help you with that. Let me look up your order.")
        estimate_after_2 = ctx.token_estimate()
        assert estimate_after_2 > estimate_after_1, (
            f"After 2 appends: estimate {estimate_after_2} must exceed {estimate_after_1}"
        )

        ctx.append("user", "The order arrived damaged. I have photos if needed.")
        estimate_after_3 = ctx.token_estimate()
        assert estimate_after_3 > estimate_after_2, (
            f"After 3 appends: estimate {estimate_after_3} must exceed {estimate_after_2}"
        )

    def test_to_context_string_starts_with_conversation_history(self):
        """to_context_string() output must start with 'CONVERSATION HISTORY:' header."""
        ctx = RawTranscriptContext()
        ctx.append("user", "Hello")
        output = ctx.to_context_string()
        assert output.startswith("CONVERSATION HISTORY:"), (
            f"Expected output to start with 'CONVERSATION HISTORY:', got: {output[:50]!r}"
        )

    def test_append_includes_role_and_content(self):
        """Appended role and content must appear in to_context_string()."""
        ctx = RawTranscriptContext()
        ctx.append("user", "My order is broken.")
        output = ctx.to_context_string()
        assert "user" in output.lower() or "USER" in output
        assert "My order is broken." in output

    def test_empty_transcript_token_estimate_is_zero(self):
        """Fresh RawTranscriptContext must have zero token estimate."""
        ctx = RawTranscriptContext()
        assert ctx.token_estimate() == 0


class TestBatchApiExplanation:
    """BATCH_API_EXPLANATION provides CCA teaching content about the anti-pattern.

    CCA Rule: Batch API is WRONG for live customer support.
    - Up to 24-hour latency — completely unacceptable for real-time support
    - NOT eligible for Zero Data Retention (ZDR)
    - Correct approach: Real-Time API + Prompt Caching (90% savings on repeated context)
    """

    def test_is_non_empty_string(self):
        """BATCH_API_EXPLANATION must be a non-empty string."""
        assert isinstance(BATCH_API_EXPLANATION, str)
        assert len(BATCH_API_EXPLANATION) > 0

    def test_mentions_batch_api(self):
        """Must contain 'Batch API' to be findable as CCA teaching content."""
        assert "Batch API" in BATCH_API_EXPLANATION, (
            f"BATCH_API_EXPLANATION must mention 'Batch API'. "
            f"Content preview: {BATCH_API_EXPLANATION[:100]!r}"
        )

    def test_mentions_24_hour_latency(self):
        """Must mention the 24-hour latency — the key reason Batch API is wrong for live support."""
        assert "24" in BATCH_API_EXPLANATION, (
            "BATCH_API_EXPLANATION must mention '24' (as in 24-hour latency). "
            "This is the critical CCA fact: Batch API has up to 24h latency, "
            "making it completely unacceptable for live customer support."
        )

    def test_has_substantial_content(self):
        """Explanation must be substantive enough for student learning."""
        assert len(BATCH_API_EXPLANATION) > 200, (
            f"BATCH_API_EXPLANATION is too short ({len(BATCH_API_EXPLANATION)} chars). "
            "Must be substantive enough for student reference."
        )
