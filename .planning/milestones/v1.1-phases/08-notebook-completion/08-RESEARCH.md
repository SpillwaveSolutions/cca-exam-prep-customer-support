# Phase 8: Notebook Completion - Research

**Researched:** 2026-04-06
**Domain:** Jupyter notebook completion + headless notebook testing (nbconvert)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**NB06 Handoffs (NBCOMP-01)**
- Read NB06 end-to-end, inventory all TODO markers
- Verify the handoff comparison output: raw dump should be ~5-10x larger than structured EscalationRecord
- Remove any duplicate code cells (user reported comparison block appeared twice)
- Ensure the notebook follows the project pattern: anti-pattern first → correct pattern → compare → CCA Exam Tip
- Student TODO placeholders (with try/except or conditional guards) should remain — only remove developer TODOs

**NB07 Integration (NBCOMP-02)**
- Read NB07 end-to-end, inventory all TODO markers
- Implement each incomplete section for all 6 CCA patterns
- The notebook uses shared services/result across all 6 pattern sections (one scenario exercises all patterns)
- Ensure imports from both `customer_service` (correct) and `customer_service.anti_patterns` (wrong)
- Must have at least 6 CCA Exam Tip boxes (one per pattern)

**Automated Notebook Testing (user request)**
- Use Papermill (`papermill`) to execute notebooks headlessly in pytest
- Since notebooks call the Anthropic API, the test should either:
  - (a) Run with a mock/stub client (preferred — no API key needed in CI)
  - (b) Use `nbconvert --execute` with a timeout and check for cell errors in output
  - (c) Parse notebook JSON to validate cell structure without execution
- Add to `tests/test_notebook_execution.py`
- The goal is: if a notebook cell has a bug (wrong import, wrong attribute, missing data), the CI catches it
- For cells that call the API, validate the setup cells (imports, make_services, scenario loading) execute without error — skip API-calling cells

### Claude's Discretion
- How to mock/stub API calls for notebook execution testing
- Whether to use Papermill or nbconvert for headless execution
- How to handle cells that require ANTHROPIC_API_KEY (skip, mock, or tag-based filtering)
- How much notebook restructuring is acceptable vs just filling TODOs

### Deferred Ideas (OUT OF SCOPE)
- Full end-to-end notebook execution with live API (requires ANTHROPIC_API_KEY)
- AI-powered auto-fix loop (Papermill + Claude for self-healing notebooks) — interesting idea from user but out of scope for v1.1
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NBCOMP-01 | NB06 handoffs notebook has no remaining TODO markers, no duplicate code cells, and comparison output is verified correct | Research confirms NB06 has 1 student TODO (must remain), 0 duplicate cells, output is already correct (7.8x ratio) |
| NBCOMP-02 | NB07 integration notebook has no remaining TODO markers and all 6 pattern sections execute correctly | Research confirms NB07 has 2 student TODOs (must remain), all 6 pattern sections already complete and producing correct output |
</phase_requirements>

---

## Summary

Both NB06 and NB07 are structurally complete. The user's concern about duplicate cells and missing TODOs was a historical observation that has already been addressed in prior phases. The real work for Phase 8 is confirming the notebooks are complete as-is, verifying the output correctness claims, and adding automated notebook execution tests.

**NB06 (19 cells):** The handoff comparison is correct — raw dump is 7.8x larger (5,416 chars vs 691 chars), both within the 5-10x target. There is exactly 1 student TODO (cell 17, sentiment callback with try/except guard). No developer TODOs. No duplicate cells. The pattern sequence (anti-pattern → correct pattern → compare → CCA Exam Tip) is complete.

**NB07 (30 cells):** All 6 CCA pattern sections are implemented. Has 2 student TODOs (cells 27-28, both with guards). Has 6 CCA Exam Tip boxes (one per pattern). The `test_notebooks_have_todo_placeholders` test expects >= 3 TODOs across both notebooks — current count is exactly 3 (1 in NB06 + 2 in NB07), which satisfies the constraint.

**Primary recommendation:** Phase 8 implementation is primarily adding `tests/test_notebook_execution.py` using `nbconvert`'s `ExecutePreprocessor` (already installed, no new deps). The notebooks themselves need only minor cleanup: remove the empty trailing cell in NB06 (cell 18) and add cell tags to mark API-calling cells for skip during headless execution.

---

## Current State of NB06 (06_handoffs.ipynb)

### Cell Inventory (19 cells total)

| Cell | Type | Content | Status |
|------|------|---------|--------|
| 0 | markdown | Title: NB06 Structured Handoffs | Complete |
| 1 | markdown | ## Setup | Complete |
| 2 | code | Imports (anthropic, customer_service, anti_patterns) | Complete |
| 3 | code | make_services() + `client = anthropic.Anthropic()` | Complete |
| 4 | code | Scenario setup: C003 $600 refund message | Complete |
| 5 | markdown | ## Anti-Pattern: Raw Conversation Dump | Complete |
| 6 | code | `run_agent_loop()` — LIVE API CALL | Complete |
| 7 | code | Anti-pattern: format_raw_handoff, show truncated output | Complete |
| 8 | markdown | Anti-pattern result callout (red border) | Complete |
| 9 | markdown | ## Correct Pattern: Structured EscalationRecord via tool_choice | Complete |
| 10 | code | Reuse result → show escalation_queue record | Complete |
| 11 | code | `_UsageWrapper` + `print_usage` | Complete |
| 12 | markdown | Correct pattern result callout (green border) | Complete |
| 13 | markdown | ## Compare: Raw Dump vs Structured Handoff | Complete |
| 14 | code | Comparison table (chars, ratio, tool_use noise) | Complete |
| 15 | markdown | CCA Exam Tip (blockquote) | Complete |
| 16 | markdown | ## Extension: Custom PostToolUse Callback (TODO) | Complete |
| 17 | code | Student TODO: sentiment callback with try/except guard | **KEEP** |
| 18 | code | **EMPTY CELL** | Remove |

### NB06 Findings

- **No duplicate cells found.** User concern was historical — fixed in prior phases.
- **No developer TODOs.** Only 1 student TODO (cell 17) which must remain.
- **Output is correct:** Raw dump = 5,416 chars, structured = 691 chars, ratio = 7.8x. Within the 5-10x target range.
- **Empty trailing cell (cell 18):** Should be removed for cleanliness.
- **API-calling cells:** Cell 3 (creates `anthropic.Anthropic()`) and cell 6 (`run_agent_loop()`). These need `skip-execution` tags for headless testing.

### NB06 Minor Issues to Fix

1. Remove empty trailing cell (cell 18)
2. Add `skip-execution` tag to cells 3 and 6 for Papermill/nbconvert headless execution

---

## Current State of NB07 (07_integration.ipynb)

### Cell Inventory (30 cells total)

| Cell | Type | Content | Status |
|------|------|---------|--------|
| 0 | markdown | Title: NB07 Integration | Complete |
| 1 | markdown | ## Setup | Complete |
| 2 | code | Imports (all 6 pattern modules) | Complete |
| 3 | code | make_services() + client + scenario message | API SETUP |
| 4 | markdown | Duplicate "demonstrates all 6" paragraph | Redundant but harmless |
| 5 | markdown | ## Pattern 1: Escalation | Complete |
| 6 | code | `run_agent_loop()` — LIVE API CALL | API CALL |
| 7 | markdown | CCA Exam Tip 1 (Escalation) | Complete |
| 8 | markdown | ## Pattern 2: Compliance | Complete |
| 9 | code | Audit log PII inspection | Complete |
| 10 | markdown | CCA Exam Tip 2 (Compliance) | Complete |
| 11 | markdown | Meta-pattern callout (blue) | Complete |
| 12 | markdown | ## Pattern 3: Tool Design | Complete |
| 13 | code | Import TOOLS, count, assert <= 5 | Complete |
| 14 | markdown | CCA Exam Tip 3 (Tool Design) | Complete |
| 15 | markdown | Meta-pattern callout (blue) | Complete |
| 16 | markdown | ## Pattern 4: Context Management | Complete |
| 17 | code | ContextSummary demo, size comparison | Complete |
| 18 | markdown | CCA Exam Tip 4 (Context) | Complete |
| 19 | markdown | ## Pattern 5: Cost Optimization | Complete |
| 20 | code | Show cache usage from result, show cached_prompt blocks | Downstream of API |
| 21 | markdown | CCA Exam Tip 5 (Cost) | Complete |
| 22 | markdown | ## Pattern 6: Structured Handoffs | Complete |
| 23 | code | Show EscalationRecord, compare to raw dump | Downstream of API |
| 24 | markdown | CCA Exam Tip 6 (Handoffs) | Complete |
| 25 | markdown | Meta-pattern callout: NB08 reference | Complete |
| 26 | markdown | ## Extension Exercises (TODOs) | Complete |
| 27 | code | Student TODO: refund_count > 3 escalation (try/except) | **KEEP** |
| 28 | code | Student TODO: PREMIUM customer (if None guard) | **KEEP** |
| 29 | markdown | Summary table: all 6 patterns | Complete |

### NB07 Findings

- **All 6 pattern sections are implemented.** No developer TODOs.
- **Has 6 CCA Exam Tips** (cells 7, 10, 14, 18, 21, 24) — satisfies `test_notebook_07_has_six_cca_exam_tips`.
- **2 student TODOs** (cells 27-28) — both have proper guards (try/except and if None).
- **Total TODO count:** NB06=1 + NB07=2 = 3, which satisfies `test_notebooks_have_todo_placeholders` (expects >= 3).
- **API-calling cells:** Cell 3 (setup, creates client + services) and cell 6 (run_agent_loop). Cells 20 and 23 are downstream of the API call (use `result`).
- **Redundant markdown cell 4** ("This notebook demonstrates all 6 CCA patterns") duplicates cell 1. Minor issue — planner should decide whether to remove.

### NB07 Minor Issues to Fix

1. Add `skip-execution` tag to cells 3 and 6 for headless testing
2. Optional: remove duplicate markdown cell 4

---

## Automated Notebook Testing Strategy

### Tool Recommendation: nbconvert ExecutePreprocessor (NOT Papermill)

**Why nbconvert over Papermill:**

| Factor | nbconvert ExecutePreprocessor | Papermill |
|--------|------------------------------|-----------|
| Already installed | YES (via `jupyter` group dep) | NO — new dependency |
| New dep required | No | Yes (`papermill` not in pyproject.toml) |
| Cell tag filtering | YES — `skip-execution` tag native | YES but different tag |
| CI-ready | YES | YES |
| Complexity | Low | Medium |

Papermill is not installed (`ModuleNotFoundError: No module named 'papermill'`). nbconvert 7.17.0 is already available. Using nbconvert avoids a new dependency while providing equivalent functionality.

**Decision:** Use nbconvert with `skip-execution` cell tags. Add Papermill to `notebooks` group only if there is specific reason beyond what nbconvert provides.

### Cell Tag Strategy

Tag API-calling cells with `"skip-execution"` in their metadata. nbconvert's `ExecutePreprocessor` supports a `skip` tag (via `TagRemovePreprocessor` or directly checking tags in preprocessing). The simpler approach is to parse cell tags manually in the test.

**Cells to tag `skip-execution`:**

| Notebook | Cell | Why |
|----------|------|-----|
| NB06 | Cell 3 | Creates `anthropic.Anthropic()` — needs API key |
| NB06 | Cell 6 | `run_agent_loop()` — live API call |
| NB07 | Cell 3 | Creates `anthropic.Anthropic()` + `run_agent_loop` setup |
| NB07 | Cell 6 | `run_agent_loop()` — live API call |

Cells 20 and 23 in NB07 (which use `result` downstream) must also be skipped because `result` is undefined if cell 6 is skipped. Tag these as `skip-execution` as well.

**Full skip list for NB07:** cells 3, 6, 20, 23

### Test Architecture for test_notebook_execution.py

```python
"""Automated headless execution tests for NB06 and NB07.

Strategy:
- Use nbformat to load the notebook
- Extract code cells NOT tagged 'skip-execution'
- Execute them in sequence using exec() in a shared namespace
- Fail if any cell raises an exception

This validates: imports are valid, helper functions are callable,
non-API code has no syntax/attribute errors.
"""
```

**Execution approach:** Load notebook as JSON, build a list of (cell_index, source) for cells without `skip-execution` tag, then execute each cell's source via `exec()` in a shared `namespace` dict. This avoids a full kernel (no `jupyter_client` overhead) and is fast (~< 1s per notebook).

**Safe cells that WILL execute:**

For NB06: cells 2, 4, 7, 10, 11, 14, 17 (import cell, scenario print, anti-pattern display, etc.)

Note: Cell 7 (`format_raw_handoff(result.messages)`) references `result` from cell 6 (skipped) — this cell must also be tagged `skip-execution`.

For NB07: cells 2, 13, 17, 27, 28 (import cell, TOOLS check, ContextSummary demo, student TODOs)

Revised full skip lists:
- NB06 skip: cells 3, 6, 7, 10, 11, 14 (all cells that reference `result`, `services`, or `raw_output` from the API call)
- NB07 skip: cells 3, 6, 9, 17, 20, 23 (all cells using `result` or `services`)

**Simpler alternative — just test imports and standalone cells:**

Rather than tracking dependencies, the test executes only cells that are demonstrably standalone:
- NB06: cell 2 (imports) and cell 4 (scenario setup, print only)
- NB07: cell 2 (imports) and cell 13 (TOOLS import + assertion)

This is narrower but completely safe and catches the most common failures (wrong imports, missing attributes).

**Recommendation:** The test should execute the import cell and any cells that do not reference `result`, `services`, `raw_output`, `raw_len`, `structured_len`, or `all_escalations`. These variables are only set by API-calling cells.

### Variables set by API-call cells (mark as skip-execution dependencies)

| Variable | Set in cell | Used in cells |
|----------|-------------|---------------|
| NB06: `result` | Cell 6 | Cells 7, 10, 11 |
| NB06: `services` | Cell 3 | Cells 10, 14 |
| NB06: `raw_output`, `raw_len` | Cell 7 | Cell 14 |
| NB06: `all_escalations`, `structured_len` | Cell 10 | Cell 14 |
| NB07: `result` | Cell 6 | Cells 20, 23 |
| NB07: `services` | Cell 3 | Cells 9, 23 |

### Final recommended skip list (add `skip-execution` tag to these cells)

**NB06:** cells 3, 6, 7, 10, 11, 14 (plus existing empty cell 18 to remove)

**NB07:** cells 3, 6, 9, 20, 23

**Safe to execute without API key:**

- NB06: cell 2 (imports), cell 4 (print scenario), cell 17 (student TODO with guard)
- NB07: cell 2 (imports), cell 13 (TOOLS import + assertion), cell 17 (ContextSummary standalone), cell 27 (student TODO try/except), cell 28 (student TODO if-guard)

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nbformat | 5.10.4 | Load/parse .ipynb JSON | Already in use in all test files |
| nbconvert | 7.17.0 | Headless execution | Already installed via jupyter group |
| pytest | >=8.0 | Test runner | Project standard |

### Not Needed
| Library | Why Not |
|---------|---------|
| papermill | Not installed, nbconvert covers the use case |
| jupyter_client | Not needed for exec()-based approach |

---

## Architecture Patterns

### Pattern: nbformat-based cell extraction + exec()

```python
def _get_executable_cells(nb: nbformat.NotebookNode) -> list[str]:
    """Return source of code cells that do NOT have skip-execution tag."""
    cells = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        tags = cell.get("metadata", {}).get("tags", [])
        if "skip-execution" in tags:
            continue
        src = cell.source
        if not src.strip():
            continue
        cells.append(src)
    return cells


def _exec_cells(cells: list[str]) -> None:
    """Execute each cell source in a shared namespace. Raises on error."""
    namespace: dict = {}
    for src in cells:
        exec(src, namespace)  # noqa: S102
```

### Pattern: Cell tag addition (in notebook JSON)

```json
{
  "cell_type": "code",
  "metadata": {
    "tags": ["skip-execution"]
  },
  "source": "..."
}
```

Add to cells via nbformat:

```python
cell.metadata["tags"] = cell.metadata.get("tags", [])
if "skip-execution" not in cell.metadata["tags"]:
    cell.metadata["tags"].append("skip-execution")
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Notebook cell execution | Custom subprocess runner | nbconvert ExecutePreprocessor or exec() | nbconvert handles kernel lifecycle; exec() is simpler for no-kernel approach |
| Cell filtering | String parsing of source | nbformat cell.metadata.tags | Standardized, tooling-compatible |
| Test discovery | Custom file walker | pytest with standard test file | Project already uses pytest |

---

## Common Pitfalls

### Pitfall 1: exec() shared namespace pollution

**What goes wrong:** Cell A sets `services = make_services()` and cell B uses it. If cells are executed in wrong order or a cell is skipped, NameError.

**How to avoid:** Only execute truly standalone cells (imports, print statements, assertion-only cells). Do not attempt to execute cells that depend on API call results.

### Pitfall 2: Removing student TODOs

**What goes wrong:** Developer removes cell 17 in NB06 or cells 27/28 in NB07 — `test_notebooks_have_todo_placeholders` fails (needs >= 3 TODOs).

**How to avoid:** Only remove developer TODOs (empty cells, incomplete section headers). Student TODOs (# TODO: with HINTS: block and guard) must remain.

**Current count:** NB06=1 + NB07=2 = exactly 3. Cannot remove any without breaking the test.

### Pitfall 3: Empty cell removal changes cell indices

**What goes wrong:** Other code or tests that reference cells by index break if cell 18 in NB06 is removed.

**How to avoid:** Existing tests (`test_notebooks.py`, `test_notebook_fixes.py`) use content-based checks (string search), not cell index references. Safe to remove empty cells.

### Pitfall 4: TODO count drops below 3 after NB06/NB07 cleanup

**What goes wrong:** If NB06's student TODO is removed (wrongly classified as developer TODO), total drops to 2 and `test_notebooks_have_todo_placeholders` fails.

**Warning signs:** Any edit that reduces `# TODO:` count in NB06 or NB07. Always recount after edits.

### Pitfall 5: Papermill dependency added to wrong group

**What goes wrong:** If Papermill is added to `[tool.poetry.dependencies]` (production group) instead of `[tool.poetry.group.dev.dependencies]`, it inflates production installs.

**How to avoid:** Add to `dev.dependencies` only. But the recommendation is to use nbconvert which is already installed.

---

## Code Examples

### How to add cell tags to a notebook (Python)

```python
# Source: nbformat documentation pattern
import json
from pathlib import Path

nb_path = Path("notebooks/06_handoffs.ipynb")
nb_json = json.loads(nb_path.read_text())

SKIP_CELLS_NB06 = {3, 6, 7, 10, 11, 14}  # cell indices to tag

for i, cell in enumerate(nb_json["cells"]):
    if i in SKIP_CELLS_NB06:
        tags = cell.setdefault("metadata", {}).setdefault("tags", [])
        if "skip-execution" not in tags:
            tags.append("skip-execution")

nb_path.write_text(json.dumps(nb_json, indent=1))
```

### Test pattern for test_notebook_execution.py

```python
"""tests/test_notebook_execution.py — headless execution of non-API cells."""
import sys
from pathlib import Path

import nbformat
import pytest

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"
sys.path.insert(0, str(NOTEBOOKS_DIR.parent))  # make helpers importable


def _load_executable_cells(name: str) -> list[str]:
    path = NOTEBOOKS_DIR / name
    nb = nbformat.read(path.open(), as_version=4)
    cells = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        tags = cell.get("metadata", {}).get("tags", [])
        if "skip-execution" in tags:
            continue
        src = cell.source.strip()
        if src:
            cells.append(src)
    return cells


def _run_cells(cells: list[str]) -> None:
    namespace: dict = {}
    for src in cells:
        exec(src, namespace)  # noqa: S102


def test_nb06_non_api_cells_execute() -> None:
    """NB06 non-API cells (imports, setup, scenario) execute without error."""
    cells = _load_executable_cells("06_handoffs.ipynb")
    assert len(cells) >= 1, "Expected at least 1 executable cell in NB06"
    _run_cells(cells)


def test_nb07_non_api_cells_execute() -> None:
    """NB07 non-API cells (imports, TOOLS check, ContextSummary) execute without error."""
    cells = _load_executable_cells("07_integration.ipynb")
    assert len(cells) >= 1, "Expected at least 1 executable cell in NB07"
    _run_cells(cells)
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `poetry run pytest tests/test_notebook_execution.py -x` |
| Full suite command | `poetry run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NBCOMP-01 | NB06 has no remaining developer TODOs, no duplicate cells, comparison output correct | structural | `poetry run pytest tests/test_notebooks.py::test_notebooks_have_todo_placeholders tests/test_notebooks.py::test_notebook_06_sections -x` | ✅ |
| NBCOMP-01 | NB06 non-API cells execute without error | execution | `poetry run pytest tests/test_notebook_execution.py::test_nb06_non_api_cells_execute -x` | ❌ Wave 0 |
| NBCOMP-02 | NB07 has no remaining developer TODOs, all 6 pattern sections complete | structural | `poetry run pytest tests/test_notebooks.py::test_notebook_07_has_six_cca_exam_tips tests/test_notebooks.py::test_notebook_07_references_all_patterns -x` | ✅ |
| NBCOMP-02 | NB07 non-API cells execute without error | execution | `poetry run pytest tests/test_notebook_execution.py::test_nb07_non_api_cells_execute -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `poetry run pytest tests/test_notebooks.py tests/test_notebook_execution.py -x`
- **Per wave merge:** `poetry run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_notebook_execution.py` — covers NBCOMP-01 and NBCOMP-02 execution validation
- [ ] Cell tags `skip-execution` in NB06 cells 3, 6, 7, 10, 11, 14 — required before test can run
- [ ] Cell tags `skip-execution` in NB07 cells 3, 6, 9, 20, 23 — required before test can run
- [ ] Remove empty cell 18 from NB06

---

## Open Questions

1. **Should exec()-based cell execution be in a subprocess for isolation?**
   - What we know: exec() in-process is simpler but pollutes the test process namespace
   - What's unclear: whether any NB import causes side effects that break other tests
   - Recommendation: Try in-process first; switch to subprocess if test isolation issues arise

2. **Should NB07 redundant markdown cell 4 be removed?**
   - What we know: cell 4 is a duplicate of cell 1's text ("This notebook demonstrates all 6 CCA patterns")
   - What's unclear: whether it's intentional duplication for visual flow or accidental
   - Recommendation: Remove it — it adds noise with no pedagogical value

3. **Should Papermill be added as a dev dependency anyway for future use?**
   - What we know: user mentioned Papermill by name; nbconvert covers the immediate need
   - Recommendation: Do not add Papermill now — the CONTEXT.md says "use Papermill or nbconvert", and nbconvert is already installed

---

## Sources

### Primary (HIGH confidence)

- Direct inspection of `notebooks/06_handoffs.ipynb` (19 cells, full cell inventory)
- Direct inspection of `notebooks/07_integration.ipynb` (30 cells, full cell inventory)
- `tests/test_notebooks.py` — existing structural tests, patterns to follow
- `tests/test_notebook_fixes.py` — Phase 7 test patterns
- `pyproject.toml` — dependency inventory (no papermill, nbformat 5.10.4, nbconvert 7.17.0)
- `poetry run pytest` output — 252 tests passing, baseline confirmed

### Secondary (MEDIUM confidence)

- nbconvert 7.17.0 documentation patterns for cell tagging and `ExecutePreprocessor`
- nbformat cell metadata `tags` field — standard Jupyter convention

---

## Metadata

**Confidence breakdown:**
- NB06 current state: HIGH — read full notebook, counted cells, verified output values
- NB07 current state: HIGH — read full notebook, counted cells, verified pattern coverage
- TODO counts: HIGH — programmatically counted via Python
- Test infrastructure: HIGH — ran `poetry run pytest`, confirmed 252 passing, checked installed packages
- nbconvert approach: HIGH — confirmed nbconvert 7.17.0 installed, tested imports work

**Research date:** 2026-04-06
**Valid until:** 2026-05-06 (stable project, no fast-moving dependencies)
