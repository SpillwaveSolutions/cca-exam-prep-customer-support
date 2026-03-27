"""Anti-pattern: Using Batch API for live customer support (ANTI-04 cost pattern).

CCA Rule (OPTIM-01 — what NOT to do):
- WRONG: "Use Batch API for live support to save 50% on costs"
- RIGHT:  "Use Prompt Caching for repeated policy context (90% savings)"

This module contains the CCA teaching explanation. There is no runnable code
here because the Batch API pattern should never be executed for live support.
The Batch API is appropriate ONLY for background pipelines where no one is
waiting for a response.
"""

BATCH_API_EXPLANATION = """
CCA EXAM TOPIC: Batch API vs Prompt Caching for Live Customer Support
======================================================================

THE WRONG ANSWER (Common Exam Trap)
-------------------------------------
"Use the Batch API to cut costs by 50% on customer support operations."

This answer is ALWAYS wrong for live customer support. If you see it on the
CCA exam, eliminate it immediately. Here is why.

WHY BATCH API IS WRONG FOR LIVE SUPPORT
-----------------------------------------

1. LATENCY — The Batch API processes requests asynchronously with up to 24-hour
   turnaround time. A customer waiting for a refund resolution cannot wait 24
   hours. This makes the Batch API completely unacceptable for any real-time
   interaction — support chats, phone-to-AI routing, self-service portals, or
   any scenario where a human is on the other end waiting for a response.

2. NOT ZDR-ELIGIBLE — The Batch API is not eligible for Zero Data Retention (ZDR).
   Organizations with strict data security requirements (financial services,
   healthcare, legal) often require ZDR for customer data. The Real-Time API
   supports ZDR; the Batch API does not. This is an absolute disqualifier for
   many enterprise customer support deployments.

3. WRONG COST LEVER — The Batch API saves costs by accepting delay in exchange
   for compute scheduling flexibility. For live support, the correct cost lever
   is Prompt Caching: sending the same large static context (policy documents,
   tool descriptions, knowledge base) on every API call. Prompt Caching provides
   up to 90% cost savings on the repeated context portion — far more than the
   Batch API's 50% discount — without any latency penalty.

THE RIGHT ANSWER: PROMPT CACHING + REAL-TIME API
--------------------------------------------------
For live customer support, the correct cost optimization strategy is:

  1. Real-Time API (always) — Someone is waiting; latency matters.

  2. Prompt Caching — Large static blocks (policy docs, system context, tool
     schemas) appear in every request. Marking them with cache_control saves
     up to 90% on those tokens after the first call.

     First call:  cache_creation_input_tokens > 0  (cache write, 1.25x cost)
     Second call: cache_read_input_tokens > 0       (cache read, 0.10x cost)
     Net savings: roughly 90% on the cached portion across a session

  3. Structured Context Management — Use ContextSummary to keep the dynamic
     session context bounded (prevents transcript growth from eating into
     the savings from caching the static policy block).

CCA EXAM TIP: DECISION RULE
-----------------------------
Use this decision rule on the exam when you see cost optimization questions:

  "Is someone waiting for the response?"
      YES → Real-Time API + Prompt Caching
      NO, and no ZDR requirement → Batch API acceptable

  "Is the system prompt large and repeated on every call?"
      YES → Prompt Caching (cache the static portion)
      NO  → No caching benefit; optimize elsewhere

  "Batch API for live support" → ALWAYS WRONG, eliminate immediately.

SUMMARY
--------
Batch API: up to 24-hour latency, not ZDR-eligible, wrong for live support.
Prompt Caching: sub-second latency, ZDR-eligible, 90% savings on repeated context.
Real-Time API + Prompt Caching: the correct answer for live customer support costs.
"""
