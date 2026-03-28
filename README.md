# CCA Customer Support Resolution Agent

A hands-on coding example for the CCA Exam Prep course demonstrating the Customer Support Resolution Agent scenario.

## Quick Start

```bash
poetry install
poetry run pytest
poetry run jupyter lab
```

## Overview

This project pairs Jupyter notebooks (teaching) with a production Python package. Each notebook demonstrates a CCA anti-pattern side-by-side with the correct architectural pattern.

## CCA Meta-Patterns in This Project

This project doesn't just *teach* CCA patterns — it *uses* them. Here's how:

### CLAUDE.md Hierarchy (Level 2: Project)

- `.claude/CLAUDE.md` — Team standards enforced project-wide (CCA exam: project-level is VCS-tracked, shared across team)
- `CLAUDE.md` (root) — Architecture docs and build commands
- See: `.planning/CCA-RULES.md` "CLAUDE.md Hierarchy" section

### CI/CD Pipeline Flags

- `.github/workflows/ci.yml` — Uses `claude -p --bare --output-format json --allowedTools Read,Grep,Glob`
- `-p`: mandatory for non-interactive CI (without it, pipeline hangs)
- `--bare`: reproducibility (no CLAUDE.md loaded in CI agent)
- `--allowedTools`: principle of least privilege for CI agents
- See: Notebook 08 for interactive walkthrough

### Custom Skill

- `.claude/skills/review-cca-compliance.md` — Invoke to review any code for CCA compliance
- Demonstrates: custom skills as reusable, project-specific instructions

### Programmatic Enforcement (Pre-commit Hooks)

- `.pre-commit-config.yaml` — nbstripout + ruff enforced on every commit
- Same principle as callbacks: code enforces rules, not human memory

---

See `CLAUDE.md` for full architecture documentation.
