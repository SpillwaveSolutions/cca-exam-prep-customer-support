---
created: 2026-04-06T15:56:09.758Z
title: Fix CustomerDatabase init in cost optimization notebook
area: testing
files:
  - notebooks/04_cost_optimization.ipynb
  - src/customer_service/services/customer_database.py
---

## Problem

In notebook `04_cost_optimization.ipynb`, the `make_services()` helper constructs `CustomerDatabase()` with no arguments, but the constructor requires a `customers` positional argument.

Error:
```
TypeError: CustomerDatabase.__init__() missing 1 required positional argument: 'customers'
```

This breaks every cell downstream that depends on `make_services()`.

## Solution

Either:
1. Update `make_services()` in the notebook to pass seed customer data: `CustomerDatabase(customers=load_seed_customers())` or similar
2. Give `CustomerDatabase.__init__` a default (e.g., `customers=None` → empty dict) if that aligns with other notebooks' usage
3. Check how other notebooks (00-03) construct `ServiceContainer` and mirror that pattern

Option 1 is likely correct — the seed data in `src/customer_service/data/` should be loaded, matching how other notebooks do it.
