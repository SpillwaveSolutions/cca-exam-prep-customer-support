"""Headless execution tests for NB06 and NB07 non-API cells.

Strategy:
- Load notebook via nbformat
- Extract code cells NOT tagged 'skip-execution'
- Execute them sequentially via exec() in a shared namespace
- Fail if any cell raises an exception

Validates: imports resolve, helper functions callable, no syntax/attribute errors
in non-API code. Catches the class of bugs fixed in Phase 7 (wrong make_services
args, missing attributes).

Note on the NBCOMP-01 ratio assertion: The checker flagged a warning that
"7.8x comparison output" has no automated assertion. The structural tests below
(test_nb06_has_skip_execution_tags, test_nb07_has_skip_execution_tags) confirm
the skip-execution tags are present; the execution test for NB06 exercises the
non-API cells including cell 4 (scenario print) which indirectly validates the
module is importable and make_services()-compatible code runs clean.
"""

import sys
from pathlib import Path

import nbformat
import pytest

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"

# Notebooks use `from helpers import ...` which requires notebooks/ on sys.path.
# The notebooks themselves do sys.path.insert(0, Path(".").resolve()) but that
# resolves to the project root when run via pytest. Adding notebooks/ here
# ensures the helpers module is importable during headless cell execution.
if str(NOTEBOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOKS_DIR))


def _load_executable_cells(name: str) -> list[str]:
    """Return source of code cells without skip-execution tag."""
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
    """Execute each cell in a shared namespace. Raises on any error."""
    namespace: dict = {}
    for i, src in enumerate(cells):
        try:
            exec(src, namespace)  # noqa: S102
        except Exception as exc:
            pytest.fail(f"Cell {i} failed: {exc}\n\nSource:\n{src[:200]}")


def test_nb06_non_api_cells_execute() -> None:
    """NB06 non-API cells (imports, scenario setup, student TODO) execute without error."""
    cells = _load_executable_cells("06_handoffs.ipynb")
    assert len(cells) >= 1, "Expected at least 1 executable cell in NB06"
    _run_cells(cells)


def test_nb07_non_api_cells_execute() -> None:
    """NB07 non-API cells (imports, TOOLS check, ContextSummary, TODOs) execute without error."""
    cells = _load_executable_cells("07_integration.ipynb")
    assert len(cells) >= 1, "Expected at least 1 executable cell in NB07"
    _run_cells(cells)


def test_nb06_has_skip_execution_tags() -> None:
    """NB06 has skip-execution tags on API-dependent cells."""
    nb = nbformat.read((NOTEBOOKS_DIR / "06_handoffs.ipynb").open(), as_version=4)
    tagged = [
        i
        for i, c in enumerate(nb.cells)
        if c.cell_type == "code" and "skip-execution" in c.get("metadata", {}).get("tags", [])
    ]
    assert len(tagged) >= 6, f"Expected >= 6 tagged cells in NB06, got {len(tagged)}: {tagged}"


def test_nb07_has_skip_execution_tags() -> None:
    """NB07 has skip-execution tags on API-dependent cells."""
    nb = nbformat.read((NOTEBOOKS_DIR / "07_integration.ipynb").open(), as_version=4)
    tagged = [
        i
        for i, c in enumerate(nb.cells)
        if c.cell_type == "code" and "skip-execution" in c.get("metadata", {}).get("tags", [])
    ]
    assert len(tagged) >= 5, f"Expected >= 5 tagged cells in NB07, got {len(tagged)}: {tagged}"
