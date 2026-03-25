# Phase 1: Project Foundation - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Students can clone the repo, run `poetry install`, and execute a setup notebook (00) that verifies their environment. The package skeleton is importable with all sub-packages. A notebook template establishes the visual convention for all 8 notebooks. Pre-commit hooks enforce notebook hygiene and code style. A `__main__.py` entry point provides a runnable skeleton.

</domain>

<decisions>
## Implementation Decisions

### Notebook template design
- Use markdown headers with colored HTML alert boxes for visual differentiation
- Red border-left box for anti-pattern sections (with "What's wrong:" callout)
- Green border-left box for correct-pattern sections (with "Why this works:" callout)
- Horizontal rule (`---`) separates anti-pattern from correct-pattern sections
- Works in all Jupyter renderers without extra dependencies

### Notebook section ordering
- Setup > Anti-pattern > Correct > Compare (in every notebook)
- Show the wrong way first so students feel the pain, then the fix
- Mirrors CCA exam format where wrong answers look plausible
- Ends with side-by-side comparison table + CCA exam tip

### print_usage helper
- Show full token breakdown: input, output, cache read, cache write, total
- Include estimated USD cost with model name shown
- Format: aligned columns with labeled rows
- Location: helper module importable by all notebooks

### compare_results helper
- Dedicated `compare_results(anti_result, correct_result)` function
- Side-by-side table with percentage deltas between anti-pattern and correct
- Covers both token/cost metrics AND business outcome metrics (escalated?, rule enforced?)
- Used in every notebook's comparison section

### Setup notebook (00) scope
- Four verification checks, each with green checkmark or red X:
  1. Python version >= 3.13
  2. anthropic SDK version compatibility
  3. ANTHROPIC_API_KEY set and valid (minimal API call)
  4. Package import verification (all sub-packages importable)
- Seed data preview: load and display sample customers/policies/scenarios
- Friendly error handling: each failure shows specific fix instructions (not bare asserts)
- Uses python-dotenv to load .env file

### Package init exports
- Top-level `__init__.py` re-exports key items for notebook convenience:
  - ServiceContainer, run_agent_loop, all Pydantic models
- Sub-packages remain directly accessible for advanced imports
- Pattern: `from customer_service import X` for common items, `from customer_service.tools import Y` for specifics

### Main entry point
- `__main__.py` provides `python -m customer_service` entry point
- Phase 1: skeleton that shows structure (can't fully run until Phase 2 builds core)
- Console output only, no UI framework
- Will run a single customer scenario end-to-end once agent loop exists

### Claude's Discretion
- Exact HTML/CSS for notebook alert boxes (colors, padding, border width)
- Pre-commit hook configuration details (nbstripout + ruff)
- Helper module file organization (single file vs split)
- Seed data file format (JSON vs Python dicts)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project standards
- `.claude/CLAUDE.md` -- Code style rules, architecture rules, CCA patterns enforced, testing requirements
- `CLAUDE.md` (root) -- Project overview, build commands, architecture description, data flow diagram

### Package configuration
- `pyproject.toml` -- Poetry config, dependencies, ruff settings, pytest config

No external specs -- requirements are fully captured in decisions above and in `.claude/CLAUDE.md`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet -- greenfield project. All directories exist but are empty.

### Established Patterns
- `pyproject.toml` configures: Python 3.13+, ruff (E/F/I/N/W/UP rules), 100-char line length
- Package layout: `src/customer_service/` with sub-packages: agent, anti_patterns, data, models, services, tools
- Dependency group separation: core, dev, notebooks

### Integration Points
- `notebooks/` directory exists (empty) -- notebooks go here
- `src/customer_service/` directory structure exists -- needs `__init__.py` files
- `tests/` directory referenced in pyproject.toml but not yet created

</code_context>

<specifics>
## Specific Ideas

- print_usage output format should feel professional -- aligned columns, clear labels
- Setup notebook should be self-service: students can fix issues without instructor help
- Anti-pattern-first ordering is deliberate pedagogical choice -- "feel the pain" before the fix
- compare_results should make the "aha moment" undeniable with percentage deltas

</specifics>

<deferred>
## Deferred Ideas

- Streamlit UI for interactive agent demo -- could be Phase 5 or separate phase
- Interactive notebook widgets (ipywidgets tabs) -- decided against for simplicity, but could revisit

</deferred>

---

*Phase: 01-project-foundation*
*Context gathered: 2026-03-25*
