---
created: 2026-04-06T15:58:11.886Z
title: Fix context management notebook anti-pattern demo
area: testing
files:
  - notebooks/05_context-management.ipynb
  - src/customer_service/anti_patterns/raw_transcript.py
  - src/customer_service/agent/context_manager.py
---

## Problem

In notebook `05_context-management.ipynb`, the anti-pattern demo cell that runs a multi-turn conversation with `RawTranscript` has issues. The cell:

1. Calls `make_services()` without seed data (same `CustomerDatabase` init bug as NB04)
2. Uses `raw_transcript.append("user", msg1)` and `raw_transcript.append("assistant", ...)` — need to verify `RawTranscript` has an `append` method with that signature
3. Calls `raw_transcript.token_estimate()` and `raw_transcript.to_context_string()` — verify these methods exist
4. Checks for `'birthday'` substring in the context string to demonstrate information retention/loss

The notebook needs to successfully demonstrate that the raw transcript anti-pattern causes unbounded token growth while the structured summary (correct pattern) stays compact.

## Solution

1. Fix `make_services()` call — pass seed customer data (same fix as NB04 todo)
2. Verify `RawTranscript` API in `raw_transcript.py` matches the notebook's usage (`append`, `token_estimate`, `to_context_string`)
3. Ensure the multi-turn scenario messages in `user_messages` reference "birthday" so the substring check is meaningful
4. Test both anti-pattern and correct-pattern cells end-to-end
