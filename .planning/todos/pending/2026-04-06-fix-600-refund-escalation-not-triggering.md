---
created: 2026-04-06T15:48:56.594Z
title: Fix $600 refund escalation not triggering in correct pattern
area: agent
files:
  - notebooks/01_escalation.ipynb
  - src/customer_service/agent/callbacks.py
---

## Problem

In notebook `01_escalation.ipynb`, the "correct pattern" demo runs a $600 refund scenario but the escalation queue comes back empty. The deterministic escalation rule (amount > $500 triggers mandatory human escalation) should fire via the PostToolUse callback in `callbacks.py`, but it does not.

Observed output:
```
Escalation queue length: 0
UNEXPECTED: Correct pattern did not escalate — check callbacks.py
```

HIL (human-in-the-loop) should have been activated by the callback before the refund was processed. Either the callback is not wired into the agent loop for this notebook cell, the amount threshold check has a bug, or the tool call never reaches `process_refund` with the right parameters.

## Solution

1. Check `callbacks.py` — verify the `process_refund` PostToolUse hook checks amount > 500 and queues an escalation
2. Check `agent_loop.py` — verify callbacks are passed to the loop in the notebook's correct-pattern cell
3. Check the notebook cell itself — ensure it instantiates the agent with callbacks enabled
4. Trace the tool call sequence — the agent may be resolving the issue without calling `process_refund` at all (e.g., escalating via a different path or skipping the refund)
