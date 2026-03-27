"""System prompts for CCA Customer Support agent.

CCA Rule: System prompts provide CONTEXT only. Business rules are
enforced in callbacks.py (Phase 3), not here.

Phase 4 addition: POLICY_DOCUMENT constant and get_system_prompt_with_caching()
support prompt caching (OPTIM-01). The SDK accepts system= as either a plain
string or a list of TextBlockParam dicts with optional cache_control.
"""

# ---------------------------------------------------------------------------
# POLICY_DOCUMENT: Comprehensive refund and returns policy for prompt caching.
#
# CCA Teaching Note: This document is sized to EXCEED the 2048-token minimum
# required for prompt caching on claude-sonnet-4-6. Target: 2200+ tokens
# (~8800+ characters). Below this threshold, caching silently does not
# activate even when cache_control is correctly set.
#
# On the first API call:  cache_creation_input_tokens > 0 (writing to cache)
# On subsequent calls:    cache_read_input_tokens > 0    (reading from cache)
# Savings:                up to 90% cost reduction on repeated context
# ---------------------------------------------------------------------------

POLICY_DOCUMENT = """
=============================================================================
CUSTOMER SUPPORT POLICY REFERENCE — CONFIDENTIAL INTERNAL DOCUMENT
Version 4.2 | Effective Date: January 1, 2025 | Supersedes: Version 4.1
=============================================================================

SECTION 1: CUSTOMER TIER DEFINITIONS AND ELIGIBILITY
-----------------------------------------------------

All customers are classified into one of three service tiers based on total
annual spend and account tenure. Tier classification is recalculated on the
first day of each calendar quarter and governs refund limits, return windows,
and escalation priority.

1.1  STANDARD TIER
     Eligibility: Annual spend below $500 OR account tenure below 12 months
     Refund limit: Up to $500 per transaction without manager approval
     Return window: 30 calendar days from date of delivery
     Restocking fee: 15% on non-defective returns over $50
     Priority queue: Standard (72-hour response SLA)
     Expedited processing: Not eligible without exception approval

1.2  PREMIUM TIER
     Eligibility: Annual spend $500–$1,999 AND account tenure at least 6 months
     Refund limit: Up to $1,500 per transaction without manager approval
     Return window: 60 calendar days from date of delivery
     Restocking fee: Waived for first return per quarter; 10% thereafter
     Priority queue: Elevated (24-hour response SLA)
     Expedited processing: Available on request, no charge

1.3  VIP TIER
     Eligibility: Annual spend $2,000 or above AND account tenure at least 12 months
     Refund limit: Up to $4,000 per transaction without executive approval
     Return window: 90 calendar days from date of delivery
     Restocking fee: Always waived
     Priority queue: VIP (4-hour response SLA, dedicated agent assignment)
     Expedited processing: Always activated automatically
     Escalation: ANY VIP complaint triggers immediate supervisor notification
     Account closure requests: Always routed to retention specialist, never resolved
                               by front-line agents without senior approval


SECTION 2: REFUND PROCESSING RULES
------------------------------------

2.1  STANDARD REFUND WORKFLOW
     All refund requests follow this sequence:
     (a) Verify customer identity via account ID
     (b) Look up order in transaction history (order must be within return window)
     (c) Check refund eligibility against policy (Section 2.2)
     (d) Verify no existing chargeback or dispute on the same order
     (e) Process refund to original payment method
     (f) Log the interaction in the audit system with outcome and policy basis
     (g) Send confirmation to customer's registered email address

2.2  REFUND ELIGIBILITY MATRIX
     The following conditions determine whether a refund can be approved
     without manager or executive review:

     APPROVED (no escalation required):
     - Item not received within promised delivery window (any tier)
     - Manufacturer defect confirmed by customer photo evidence (any tier)
     - Shipping damage reported within 48 hours of delivery (any tier)
     - Order duplicated due to system error (any tier)
     - Item significantly different from product description (any tier)
     - Refund amount is within tier limit (Standard ≤$500, Premium ≤$1,500, VIP ≤$4,000)

     REQUIRES REVIEW (amount > $500 regardless of tier):
     - Any single refund transaction exceeding $500 must be flagged for
       supervisor review. This threshold applies regardless of customer tier.
       A VIP customer requesting a $4,000 refund still triggers the review flag.
       The review flag is informational — the agent continues processing and
       the supervisor is notified asynchronously.

     ESCALATION REQUIRED (cannot be resolved by front-line agent):
     - Account closure or cancellation requests (any tier)
     - Legal complaints, litigation threats, or attorney representation notices
     - Fraud allegations against the company
     - Media escalations (journalist, blogger, social media influencer with
       documented reach above 10,000 followers)
     - Any VIP tier complaint (automatic escalation, per Section 1.3)
     - Refund denials where customer claims statutory consumer rights

2.3  PARTIAL REFUNDS
     Partial refunds are available in the following cases:
     - Item received with minor cosmetic damage but functional: 20% partial refund
     - Item received with one defective component in a multi-component kit: refund
       the defective component's prorated value only
     - Late delivery (1–3 days past promised window): $10 goodwill credit
     - Late delivery (4–7 days past promised window): 25% partial refund
     - Late delivery (8+ days past promised window): full refund offered

2.4  GIFT RETURNS
     Returns on gift purchases follow special rules:
     - Gift recipient may return without the original purchaser's involvement
     - Refund issued as store credit to the recipient, not cash to original purchaser
     - Gift receipts extend return window by an additional 15 days beyond tier limit
     - No restocking fee applies to gift returns regardless of tier

2.5  INTERNATIONAL ORDERS
     Orders shipped internationally follow modified policies:
     - Return window: 45 calendar days from date of customs clearance
     - Restocking fee: Waived for all international returns (logistics cost recovery)
     - Customs duties and import taxes: Not refundable under any circumstances
     - Refund currency: Original transaction currency; exchange rate fluctuations
       are not compensated
     - International orders above $200 require supervisor co-approval

2.6  SUBSCRIPTION CANCELLATIONS
     Monthly and annual subscription products have separate cancellation rules:
     - Monthly: Cancel anytime, prorated refund for unused days in billing cycle
     - Annual: Cancel within 30 days for full refund; after 30 days, prorated refund
               for full unused months only (no daily proration after day 30)
     - Subscription cancellation requests do not count toward per-transaction
       refund limits but must still be logged for compliance purposes
     - Auto-renewal cancellation: Must be requested at least 48 hours before
       renewal date to avoid the charge; post-renewal cancellation treated as
       standard subscription cancellation (30-day window applies)


SECTION 3: DAMAGE AND DEFECT CATEGORIES
-----------------------------------------

3.1  MANUFACTURER DEFECT
     Definition: Failure attributable to production quality, materials, or design
     Observable indicators: Failure on first use, structural failure without
     physical impact, component failure within 90 days of purchase
     Required evidence: Customer description and photo (if physical product)
     Eligible for: Full refund or replacement at customer's choice
     Time limit: 1 year warranty from date of purchase (Standard/Premium);
                 2 years (VIP)

3.2  SHIPPING DAMAGE
     Definition: Physical damage sustained during transit
     Observable indicators: Dented or crushed packaging, visible impact damage,
     crushed or shattered components
     Required evidence: Photo of outer packaging AND damaged item within 48 hours
     Eligible for: Full refund or reshipping at customer's choice
     Carrier liability: Agent must create carrier claim ticket in addition to refund
     Time limit: Reported within 48 hours of delivery confirmation

3.3  CUSTOMER-CAUSED DAMAGE
     Definition: Damage resulting from misuse, improper storage, or accidental impact
     Observable indicators: Impact cracks, liquid damage, burn marks, pet damage
     Refund eligibility: Not eligible for standard refund. May be eligible for
     manufacturer repair program if item is still within warranty period.
     Exception: If product instructions were misleading, refer to Section 3.1
                (manufacturer defect evaluation)
     VIP exception: VIP customers may receive one courtesy replacement per year
                    for customer-caused damage as a goodwill gesture

3.4  WEAR AND TEAR
     Definition: Normal degradation over time with regular use
     Observable indicators: Fading, minor scratches, surface dulling, worn edges
     Refund eligibility: Not eligible for refund
     Available remedies: Product care advice, referral to manufacturer service
                         program if applicable
     Note: Agents must not represent wear-and-tear as a defect to customers.
           Misrepresentation of eligibility is a policy violation subject to
           internal review.


SECTION 4: COMPLIANCE REQUIREMENTS
-------------------------------------

4.1  PCI-DSS DATA HANDLING
     Payment Card Industry Data Security Standard requirements:
     - Agents must NEVER request, record, or repeat full card numbers
     - Last 4 digits only may be referenced for transaction verification
     - Card numbers must never appear in any log, note, or ticket
     - Refunds must be processed to the original card — no cash equivalents
       unless original card is cancelled (requires supervisor approval)
     - Agents who receive card numbers verbally must instruct customers not to
       share them and must not enter them into any system

4.2  GDPR AND DATA PRIVACY
     General Data Protection Regulation compliance requirements:
     - Customer data may only be used for the stated purpose of the interaction
     - Agents must not access records unrelated to the current support request
     - Right to erasure requests must be escalated to the data privacy team
       within 24 hours — do not attempt to process them during the call
     - Customers in EU/EEA must be informed of data retention policy on request:
       "Support interaction records are retained for 7 years per legal obligation"
     - Do not confirm customer email, address, or phone to unverified callers

4.3  AUDIT TRAIL REQUIREMENTS
     Every agent interaction must be logged with the following fields:
     - Customer ID (required)
     - Interaction timestamp (automatic)
     - Tools used and sequence (automatic via agent loop)
     - Outcome: resolved, escalated, or unresolved
     - Policy basis for decision (required — cite section number)
     - Agent ID or system identifier
     Incomplete logs are a compliance violation subject to review.
     Agents may not delete or modify logs after submission.

4.4  FINANCIAL SYSTEM INTEGRITY
     Refund processing rules for financial compliance:
     - Refunds cannot exceed the original transaction amount
     - Multiple partial refunds on the same order must not total more than
       the original transaction amount (system enforces this)
     - Refunds to accounts with active fraud holds require financial team approval
     - Month-end refund processing (last 2 business days of each month) requires
       dual-agent approval for amounts above $1,000


SECTION 5: ESCALATION CRITERIA AND PROCEDURES
------------------------------------------------

5.1  MANDATORY ESCALATION TRIGGERS
     The following conditions require IMMEDIATE escalation to a human supervisor.
     Agents must not attempt to resolve these cases independently:

     (a) AMOUNT THRESHOLD: Refund request exceeds $500
         Action: Flag for review; continue processing; notify supervisor
         Note: This is informational — agent still processes the refund

     (b) ACCOUNT CLOSURE: Customer requests to close or delete their account
         Action: Escalate entirely; do not process; transfer to retention team
         Reason: Retention team has tools and authority agents do not

     (c) VIP TIER: Any complaint from a VIP-tier customer
         Action: Notify supervisor immediately; continue assisting
         Reason: VIP customers have dedicated handling SLA requirements

     (d) LEGAL THREAT: Customer mentions lawyers, lawsuits, small claims court,
         or consumer protection agencies
         Action: Stop making commitments; escalate to legal liaison
         Reason: Admissions made during escalation may have legal implications
         Warning: Do not apologize in ways that admit liability once legal
                  threat is made

5.2  ESCALATION RECORD FORMAT
     When escalating, agents must provide a structured handoff containing:
     - customer_id and customer_tier
     - issue_type and disputed_amount
     - escalation_reason (one of: amount_threshold, account_closure, vip_tier,
                          legal_complaint, media_escalation)
     - recommended_action (what the agent thinks should happen)
     - conversation_summary (3–5 sentence plain language summary)
     - turns_elapsed (number of exchanges in this session)
     Raw conversation transcripts are NOT acceptable as handoff documents.
     The structured record allows the receiving supervisor to act immediately.

5.3  ESCALATION TIMING
     - VIP complaints: escalation notification within 2 minutes of trigger
     - Legal threats: escalation notification within 5 minutes
     - Amount threshold: supervisor notification within the same session
     - Account closure: escalation before any account action is taken


SECTION 6: EDGE CASES AND SPECIAL HANDLING
--------------------------------------------

6.1  DUPLICATE ORDERS
     When a customer places duplicate orders due to checkout confusion:
     - Refund the duplicate order in full regardless of amount
     - No restocking fee applies
     - Waive any return shipping cost
     - Log as "system error - duplicate" for tracking purposes

6.2  PRICE MATCH REQUESTS
     Company policy provides a 7-day price match guarantee:
     - Customer must provide proof of lower price at qualifying competitor
     - Maximum price match discount: $100 per order
     - Price match is processed as a partial refund, not store credit
     - Qualifying competitors are listed in the price match policy addendum
       (internal reference: PM-ADDENDUM-2025)

6.3  LOST PACKAGE CLAIMS
     When a customer reports a package as lost (tracking shows delivered):
     - Ask customer to check with neighbors and building management first
     - If still lost after 48 hours: file carrier claim AND process courtesy
       reshipment at no charge
     - If carrier confirms non-delivery: process full refund immediately
     - If carrier confirms delivery with photo: escalate to fraud review team

6.4  HAZARDOUS MATERIALS
     Returns of items containing batteries, liquids, or other regulated materials:
     - Do not instruct customer to ship without verifying hazmat compliance
     - Provide pre-paid hazmat-compliant return label (available via logistics tool)
     - Standard return windows do not apply — follow hazmat schedule instead


SECTION 7: SYSTEM NOTES FOR AGENTS
-------------------------------------

7.1  TOOL USAGE ORDER
     Always follow this sequence when handling refund requests:
     1. lookup_customer — verify identity and get tier, account status
     2. check_policy — confirm eligibility before making any commitment
     3. process_refund — only after policy check approves
     4. escalate_to_human — if any mandatory trigger applies (Section 5.1)
     5. log_interaction — ALWAYS as the final step, every session

7.2  WHAT NOT TO SAY
     Agents must avoid the following phrases that create legal exposure:
     - "We guarantee this won't happen again" (implied warranty)
     - "I can see it was our fault" (admission of liability before review)
     - "We'll take care of everything" (open-ended commitment)
     - "Just sue us" or similar dismissive language
     - Any statement that contradicts this policy document

7.3  DE-ESCALATION LANGUAGE
     Recommended phrases for difficult interactions:
     - "I understand how frustrating this must be."
     - "Let me look into exactly what I can do for you."
     - "I want to make sure we find the right resolution."
     - "I'm going to escalate this to someone with more authority to help."

=============================================================================
END OF POLICY DOCUMENT — Version 4.2 — Effective January 1, 2025
Questions: supportpolicy@company.internal | Review cycle: Quarterly
=============================================================================
"""


def get_system_prompt() -> str:
    """Return the system prompt for the customer support agent.

    This prompt provides context and guidance. Actual enforcement of
    escalation rules, compliance checks, and refund limits happens in
    programmatic callbacks (Phase 3), not in this prompt.
    """
    return (
        "You are a customer support agent for an online retail company. "
        "Your role is to help customers with refund requests, account inquiries, "
        "and general support issues.\n\n"
        "You have access to 5 tools:\n"
        "1. lookup_customer - Find customer profile by ID\n"
        "2. check_policy - Check refund eligibility against policy\n"
        "3. process_refund - Process an approved refund\n"
        "4. escalate_to_human - Transfer to human agent when needed\n"
        "5. log_interaction - Record the interaction for audit\n\n"
        "Always look up the customer first before taking any action. "
        "Check policy before processing refunds. "
        "Log every interaction for compliance purposes.\n\n"
        "Be professional, empathetic, and efficient. "
        "If you cannot resolve an issue, escalate to a human agent "
        "with a clear summary of the situation."
    )


def get_system_prompt_with_caching() -> list[dict]:
    """Return system prompt as list-of-blocks with cache_control on static policy.

    CCA Pattern (OPTIM-01): Pass system= as a list of TextBlockParam dicts.
    The POLICY_DOCUMENT block carries cache_control: {"type": "ephemeral"},
    which instructs claude-sonnet-4-6 to cache it for subsequent requests.

    Block 0: AGENT_INSTRUCTIONS — NOT cached (small, ~75 tokens, may vary per variant)
    Block 1: POLICY_DOCUMENT — CACHED (large, 2200+ tokens, static across requests)

    CCA Anti-pattern warning: Do NOT put cache_control on block 0 (instructions).
    The cache breakpoint marks the LAST static block. Caching the small instructions
    block instead of the large policy document defeats the entire purpose.

    Token savings:
        First call:  cache_creation_input_tokens > 0 (writing to cache, 1.25x cost)
        Second call: cache_read_input_tokens > 0     (reading from cache, 0.1x cost)
        Net savings: up to 90% on the policy portion across repeated requests

    Compatibility: run_agent_loop accepts str | list[dict] for system_prompt.
    The Anthropic SDK's client.messages.create(system=...) natively accepts both.
    """
    return [
        {
            "type": "text",
            "text": get_system_prompt(),
            # No cache_control on instructions — small block, not worth caching
        },
        {
            "type": "text",
            "text": POLICY_DOCUMENT,
            "cache_control": {"type": "ephemeral"},
        },
    ]
