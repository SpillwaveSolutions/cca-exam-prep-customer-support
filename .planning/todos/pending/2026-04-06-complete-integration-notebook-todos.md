---
created: 2026-04-06T16:02:35.304Z
title: Complete integration notebook TODOs
area: testing
files:
  - notebooks/07_integration.ipynb
---

## Problem

Notebook `07_integration.ipynb` is incomplete — it has many TODO markers remaining. This is the capstone notebook that should tie together all 6 CCA patterns (escalation, compliance, tool design, context management, cost optimization, handoffs) into an integrated demo.

## Solution

1. Read `07_integration.ipynb` and inventory all TODO markers
2. Implement each TODO — likely includes:
   - Integrated agent run combining all patterns
   - Side-by-side comparison of anti-pattern vs correct architecture
   - Summary table or scorecard across all 6 dimensions
   - Verification cells proving each pattern works correctly
3. Ensure the notebook imports from both `customer_service` (correct) and `customer_service.anti_patterns` (wrong) per the project pattern
4. Run end-to-end and verify output matches teaching goals
