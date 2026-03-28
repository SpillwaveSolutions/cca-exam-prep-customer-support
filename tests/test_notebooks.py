"""Smoke tests for notebook existence and structural integrity.

These tests verify:
- Each notebook file exists
- Each notebook follows the required section structure
- Each notebook checks the correct service/metric for its CCA pattern

Tests are deterministic -- no API calls, no mocking. They parse .ipynb JSON.
"""

from pathlib import Path

import nbformat

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"


def _load_notebook(name: str) -> nbformat.NotebookNode:
    """Load a notebook by filename and return parsed nbformat node."""
    path = NOTEBOOKS_DIR / name
    with path.open() as f:
        return nbformat.read(f, as_version=4)


def _get_markdown_source(nb: nbformat.NotebookNode) -> list[str]:
    """Return source text of all markdown cells."""
    return [cell.source for cell in nb.cells if cell.cell_type == "markdown"]


def _get_code_source(nb: nbformat.NotebookNode) -> list[str]:
    """Return source text of all code cells."""
    return [cell.source for cell in nb.cells if cell.cell_type == "code"]


def _all_markdown(nb: nbformat.NotebookNode) -> str:
    """Return concatenated markdown source for substring search."""
    return "\n".join(_get_markdown_source(nb))


def _all_code(nb: nbformat.NotebookNode) -> str:
    """Return concatenated code source for substring search."""
    return "\n".join(_get_code_source(nb))


# ---------------------------------------------------------------------------
# Existence tests
# ---------------------------------------------------------------------------


def test_notebook_01_exists() -> None:
    """notebooks/01_escalation.ipynb must exist."""
    assert (NOTEBOOKS_DIR / "01_escalation.ipynb").exists()


def test_notebook_02_exists() -> None:
    """notebooks/02_compliance.ipynb must exist."""
    assert (NOTEBOOKS_DIR / "02_compliance.ipynb").exists()


def test_notebook_03_exists() -> None:
    """notebooks/03_tool_design.ipynb must exist."""
    assert (NOTEBOOKS_DIR / "03_tool_design.ipynb").exists()


# ---------------------------------------------------------------------------
# Section structure tests
# ---------------------------------------------------------------------------


def test_notebook_01_sections() -> None:
    """NB01 must contain Anti-Pattern, Correct Pattern, Compare, and CCA Exam Tip."""
    nb = _load_notebook("01_escalation.ipynb")
    md = _all_markdown(nb)

    assert "Anti-Pattern" in md, "NB01 missing Anti-Pattern section"
    assert "Correct Pattern" in md, "NB01 missing Correct Pattern section"
    assert "Compare" in md, "NB01 missing Compare section"
    assert "CCA Exam Tip" in md, "NB01 missing CCA Exam Tip"


def test_notebook_02_sections() -> None:
    """NB02 must contain Anti-Pattern, Correct Pattern, Compare, and CCA Exam Tip."""
    nb = _load_notebook("02_compliance.ipynb")
    md = _all_markdown(nb)

    assert "Anti-Pattern" in md, "NB02 missing Anti-Pattern section"
    assert "Correct Pattern" in md, "NB02 missing Correct Pattern section"
    assert "Compare" in md, "NB02 missing Compare section"
    assert "CCA Exam Tip" in md, "NB02 missing CCA Exam Tip"


def test_notebook_03_sections() -> None:
    """NB03 must contain Anti-Pattern, Correct Pattern, Compare, and CCA Exam Tip."""
    nb = _load_notebook("03_tool_design.ipynb")
    md = _all_markdown(nb)

    assert "Anti-Pattern" in md, "NB03 missing Anti-Pattern section"
    assert "Correct Pattern" in md, "NB03 missing Correct Pattern section"
    assert "Compare" in md, "NB03 missing Compare section"
    assert "CCA Exam Tip" in md, "NB03 missing CCA Exam Tip"


# ---------------------------------------------------------------------------
# CCA pattern-specific checks
# ---------------------------------------------------------------------------


def test_notebook_01_checks_escalation_queue() -> None:
    """NB01 must check escalation_queue (NOT financial_system.get_processed)."""
    nb = _load_notebook("01_escalation.ipynb")
    code = _all_code(nb)

    assert "escalation_queue" in code, "NB01 must check escalation_queue for escalation comparison"
    assert "financial_system.get_processed" not in code, (
        "NB01 must NOT check financial_system.get_processed — escalation test is about "
        "escalation_queue, not refund processing"
    )


def test_notebook_02_checks_audit_log() -> None:
    """NB02 must check audit_log for PII leakage vs programmatic redaction."""
    nb = _load_notebook("02_compliance.ipynb")
    code = _all_code(nb)

    assert "audit_log" in code, "NB02 must inspect audit_log for PII compliance check"


def test_notebook_03_checks_tool_count() -> None:
    """NB03 must reference SWISS_ARMY_TOOLS and demonstrate 15 vs 5 tool comparison."""
    nb = _load_notebook("03_tool_design.ipynb")
    code = _all_code(nb)

    assert "SWISS_ARMY_TOOLS" in code, "NB03 must import/use SWISS_ARMY_TOOLS"
    # Either the literal "15" or len(SWISS_ARMY_TOOLS) comparison should appear
    assert "15" in code or "len(SWISS_ARMY_TOOLS)" in code, (
        "NB03 must demonstrate the 15-tool count (Swiss Army anti-pattern)"
    )


# ---------------------------------------------------------------------------
# Import checks — verify correct anti-pattern imports in each notebook
# ---------------------------------------------------------------------------


def test_notebook_01_imports_confidence_agent() -> None:
    """NB01 must import run_confidence_agent from anti_patterns."""
    nb = _load_notebook("01_escalation.ipynb")
    code = _all_code(nb)

    assert "run_confidence_agent" in code, (
        "NB01 must import and use run_confidence_agent for anti-pattern section"
    )


def test_notebook_01_imports_build_callbacks() -> None:
    """NB01 must import build_callbacks for correct pattern section."""
    nb = _load_notebook("01_escalation.ipynb")
    code = _all_code(nb)

    assert "build_callbacks" in code, (
        "NB01 must use build_callbacks for correct pattern demonstration"
    )


def test_notebook_02_imports_prompt_compliance_agent() -> None:
    """NB02 must import run_prompt_compliance_agent from anti_patterns."""
    nb = _load_notebook("02_compliance.ipynb")
    code = _all_code(nb)

    assert "run_prompt_compliance_agent" in code, (
        "NB02 must import and use run_prompt_compliance_agent for anti-pattern section"
    )


def test_notebook_03_imports_swiss_army_agent() -> None:
    """NB03 must import run_swiss_army_agent from anti_patterns."""
    nb = _load_notebook("03_tool_design.ipynb")
    code = _all_code(nb)

    assert "run_swiss_army_agent" in code, (
        "NB03 must import and use run_swiss_army_agent for anti-pattern section"
    )


# ---------------------------------------------------------------------------
# NB04: Cost Optimization — existence, structure, import, CCA pattern
# ---------------------------------------------------------------------------


def test_notebook_04_exists() -> None:
    """notebooks/04_cost_optimization.ipynb must exist."""
    assert (NOTEBOOKS_DIR / "04_cost_optimization.ipynb").exists()


def test_notebook_04_sections() -> None:
    """NB04 must contain Anti-Pattern, Correct Pattern, Compare, and CCA Exam Tip."""
    nb = _load_notebook("04_cost_optimization.ipynb")
    md = _all_markdown(nb)

    assert "Anti-Pattern" in md, "NB04 missing Anti-Pattern section"
    assert "Correct Pattern" in md, "NB04 missing Correct Pattern section"
    assert "Compare" in md, "NB04 missing Compare section"
    assert "CCA Exam Tip" in md, "NB04 missing CCA Exam Tip"


def test_notebook_04_imports() -> None:
    """NB04 must import get_system_prompt_with_caching and POLICY_DOCUMENT."""
    nb = _load_notebook("04_cost_optimization.ipynb")
    code = _all_code(nb)

    assert "get_system_prompt_with_caching" in code, (
        "NB04 must import get_system_prompt_with_caching for caching demo"
    )
    assert "POLICY_DOCUMENT" in code, "NB04 must import POLICY_DOCUMENT to show token count"


def test_notebook_04_cca_pattern() -> None:
    """NB04 must reference cache_control or cache_read (caching-specific)."""
    nb = _load_notebook("04_cost_optimization.ipynb")
    code = _all_code(nb)

    assert "cache_control" in code or "cache_read" in code, (
        "NB04 must reference cache_control or cache_read_input_tokens"
    )


def test_notebook_04_batch_api_mentioned() -> None:
    """NB04 must mention Batch API anti-pattern."""
    nb = _load_notebook("04_cost_optimization.ipynb")
    md = _all_markdown(nb)

    assert "Batch API" in md, "NB04 must explain Batch API anti-pattern"


# ---------------------------------------------------------------------------
# NB05: Context Management — existence, structure, import, CCA pattern
# ---------------------------------------------------------------------------


def test_notebook_05_exists() -> None:
    """notebooks/05_context_management.ipynb must exist."""
    assert (NOTEBOOKS_DIR / "05_context_management.ipynb").exists()


def test_notebook_05_sections() -> None:
    """NB05 must contain Anti-Pattern, Correct Pattern, Compare, and CCA Exam Tip."""
    nb = _load_notebook("05_context_management.ipynb")
    md = _all_markdown(nb)

    assert "Anti-Pattern" in md, "NB05 missing Anti-Pattern section"
    assert "Correct Pattern" in md, "NB05 missing Correct Pattern section"
    assert "Compare" in md, "NB05 missing Compare section"
    assert "CCA Exam Tip" in md, "NB05 missing CCA Exam Tip"


def test_notebook_05_imports() -> None:
    """NB05 must import ContextSummary and RawTranscriptContext."""
    nb = _load_notebook("05_context_management.ipynb")
    code = _all_code(nb)

    assert "ContextSummary" in code, "NB05 must import ContextSummary for correct pattern section"
    assert "RawTranscriptContext" in code, (
        "NB05 must import RawTranscriptContext for anti-pattern section"
    )


def test_notebook_05_cca_pattern() -> None:
    """NB05 must reference token_estimate (context management specific)."""
    nb = _load_notebook("05_context_management.ipynb")
    code = _all_code(nb)

    assert "token_estimate" in code, (
        "NB05 must reference token_estimate to demonstrate O(n) vs O(1) growth"
    )


# ---------------------------------------------------------------------------
# NB06: Handoffs — existence, structure, import, CCA pattern
# ---------------------------------------------------------------------------


def test_notebook_06_exists() -> None:
    assert (NOTEBOOKS_DIR / "06_handoffs.ipynb").exists()


def test_notebook_06_sections() -> None:
    nb = _load_notebook("06_handoffs.ipynb")
    md = _all_markdown(nb)
    assert "Anti-Pattern" in md
    assert "Correct Pattern" in md
    assert "Compare" in md
    assert "CCA Exam Tip" in md


def test_notebook_06_imports_raw_handoff() -> None:
    nb = _load_notebook("06_handoffs.ipynb")
    code = _all_code(nb)
    assert "format_raw_handoff" in code


def test_notebook_06_references_tool_choice() -> None:
    nb = _load_notebook("06_handoffs.ipynb")
    code = _all_code(nb)
    md = _all_markdown(nb)
    assert "tool_choice" in code or "tool_choice" in md


def test_notebook_06_checks_escalation_queue() -> None:
    nb = _load_notebook("06_handoffs.ipynb")
    code = _all_code(nb)
    assert "escalation_queue" in code


# ---------------------------------------------------------------------------
# NB07: Integration — existence, structure, all 6 patterns
# ---------------------------------------------------------------------------


def test_notebook_07_exists() -> None:
    assert (NOTEBOOKS_DIR / "07_integration.ipynb").exists()


def test_notebook_07_has_six_cca_exam_tips() -> None:
    nb = _load_notebook("07_integration.ipynb")
    md = _all_markdown(nb)
    assert md.count("CCA Exam Tip") >= 6


def test_notebook_07_imports_key_modules() -> None:
    nb = _load_notebook("07_integration.ipynb")
    code = _all_code(nb)
    assert "run_agent_loop" in code
    assert "build_callbacks" in code
    assert "ContextSummary" in code


def test_notebook_07_references_all_patterns() -> None:
    nb = _load_notebook("07_integration.ipynb")
    md = _all_markdown(nb)
    assert "Escalation" in md or "escalation" in md
    assert "Compliance" in md or "compliance" in md
    assert "Tool Design" in md or "Tool design" in md or "tool design" in md
    assert "Context" in md or "context" in md
    assert "Cost" in md or "Caching" in md or "caching" in md
    assert "Handoff" in md or "handoff" in md


# ---------------------------------------------------------------------------
# Student TODOs — existence and safety
# ---------------------------------------------------------------------------


def test_notebooks_have_todo_placeholders() -> None:
    """At least 3 TODO placeholders across NB06 and NB07."""
    todo_count = 0
    for name in ("06_handoffs.ipynb", "07_integration.ipynb"):
        nb = _load_notebook(name)
        code = _all_code(nb)
        todo_count += code.count("# TODO:")
    assert todo_count >= 3, f"Expected >=3 TODOs across NB06+NB07, found {todo_count}"


def test_todo_guards_use_try_except() -> None:
    """TODO cells must use try/except or conditional guard, not bare assert."""
    for name in ("06_handoffs.ipynb", "07_integration.ipynb"):
        nb = _load_notebook(name)
        code_cells = _get_code_source(nb)
        for cell_code in code_cells:
            if "# TODO:" in cell_code:
                has_guard = (
                    "try:" in cell_code
                    or "except" in cell_code
                    or ("if " in cell_code and "None" in cell_code)
                )
                assert has_guard, f"TODO cell in {name} must have try/except or conditional guard"
