"""Anti-pattern: Raw transcript context accumulator (ANTI-04).

CCA Rule (violated here on purpose):
- WRONG: Append every message and tool result as raw text, pass as context string.
- RIGHT: Use ContextSummary with structured fields (agent/context_manager.py).

Observable failures demonstrated in Notebook 05:
1. O(n) token growth — every turn adds proportionally more tokens
2. Lost-in-middle effect — important facts from early turns get buried
3. Attention dilution — model focuses on recent content, ignores early context
4. Unbounded growth — no compaction or budget enforcement

CCA Exam fact: A bigger context window makes the lost-in-middle effect WORSE,
not better. More context = more dilution of early facts, not less.
"""


class RawTranscriptContext:
    """Anti-pattern: unbounded raw transcript accumulator.

    Demonstrates:
    - O(n) token growth per turn (each append grows the transcript linearly)
    - Lost-in-middle effect after 5-6 turns (early facts get buried)
    - No budget enforcement (transcript grows without bound)

    Contrast with ContextSummary (correct pattern):
    - ContextSummary stays under TOKEN_BUDGET after any number of updates
    - Structured fields (customer_id, issue_type) never get compacted away
    - token_estimate is bounded, not linear in turn count

    Usage (anti-pattern demonstration only):
        ctx = RawTranscriptContext()
        ctx.append("user", "I need a refund for order #12345")
        ctx.append("assistant", "Let me look that up for you.")
        print(ctx.token_estimate())  # grows with every append
        print(ctx.to_context_string())  # CONVERSATION HISTORY: ...
    """

    def __init__(self) -> None:
        self.transcript: str = ""

    def append(self, role: str, content: str) -> None:
        """Append a message to the raw transcript.

        Anti-pattern: every call makes the transcript longer. After 10+ turns
        the transcript easily exceeds 2000 tokens, causing:
        - Higher API costs on every subsequent call
        - Lost-in-middle degradation for facts mentioned in early turns
        """
        self.transcript += f"\n[{role.upper()}]: {content}"

    def to_context_string(self) -> str:
        """Return the full transcript as a context string.

        Anti-pattern: passes the entire raw conversation history as context.
        Compare with ContextSummary.to_system_context() which stays bounded.
        """
        return f"CONVERSATION HISTORY:\n{self.transcript}"

    def token_estimate(self) -> int:
        """Estimate token count using len // 4 character heuristic.

        Returns an increasing value with every append — demonstrating O(n) growth.
        The ContextSummary.token_estimate stays under TOKEN_BUDGET regardless of
        how many updates are made (O(1) amortized via compaction).
        """
        return len(self.transcript) // 4
