"""Tag API-dependent cells in NB06 and NB07 with skip-execution metadata.

Run via: poetry run python scripts/tag_notebook_cells.py
"""

from pathlib import Path

import nbformat

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"

# Cells to tag with 'skip-execution' in each notebook
NB06_SKIP_CELLS = {3, 6, 7, 10, 11, 14}
NB07_SKIP_CELLS = {3, 6, 9, 20, 23}


def add_skip_tags(nb_path: Path, skip_indices: set[int]) -> int:
    """Add skip-execution tag to specified cells. Returns number of cells tagged."""
    nb = nbformat.read(nb_path.open(), as_version=4)
    tagged_count = 0

    for i, cell in enumerate(nb.cells):
        if i not in skip_indices:
            continue
        tags = cell.setdefault("metadata", {}).setdefault("tags", [])
        if "skip-execution" not in tags:
            tags.append("skip-execution")
            tagged_count += 1
            print(f"  Tagged cell {i} ({cell.cell_type}): {cell.source[:60]!r}")

    nbformat.write(nb, nb_path.open("w"))
    return tagged_count


def remove_empty_trailing_cell(nb_path: Path) -> bool:
    """Remove the last cell if it is empty/whitespace-only code cell. Returns True if removed."""
    nb = nbformat.read(nb_path.open(), as_version=4)
    if not nb.cells:
        return False

    last = nb.cells[-1]
    if last.cell_type == "code" and not last.source.strip():
        nb.cells.pop()
        nbformat.write(nb, nb_path.open("w"))
        print(f"  Removed empty trailing cell (was index {len(nb.cells)})")
        return True

    return False


def verify_notebook(
    nb_path: Path, skip_indices: set[int], expected_cell_count: int | None = None
) -> None:
    """Verify tags are present and cell count matches expected."""
    nb = nbformat.read(nb_path.open(), as_version=4)
    errors = []

    for i in skip_indices:
        if i >= len(nb.cells):
            errors.append(f"Cell {i} does not exist (notebook has {len(nb.cells)} cells)")
            continue
        tags = nb.cells[i].get("metadata", {}).get("tags", [])
        if "skip-execution" not in tags:
            errors.append(f"Cell {i} missing skip-execution tag")

    if expected_cell_count is not None and len(nb.cells) != expected_cell_count:
        errors.append(f"Expected {expected_cell_count} cells, got {len(nb.cells)}")

    if errors:
        print(f"  ERRORS in {nb_path.name}:")
        for e in errors:
            print(f"    - {e}")
    else:
        print(f"  OK: {nb_path.name} — {len(nb.cells)} cells, all skip-execution tags present")


def main() -> None:
    nb06_path = NOTEBOOKS_DIR / "06_handoffs.ipynb"
    nb07_path = NOTEBOOKS_DIR / "07_integration.ipynb"

    print("=== Processing NB06 (06_handoffs.ipynb) ===")
    remove_empty_trailing_cell(nb06_path)
    count = add_skip_tags(nb06_path, NB06_SKIP_CELLS)
    print(f"  Tagged {count} cells")
    verify_notebook(nb06_path, NB06_SKIP_CELLS, expected_cell_count=18)

    print()
    print("=== Processing NB07 (07_integration.ipynb) ===")
    count = add_skip_tags(nb07_path, NB07_SKIP_CELLS)
    print(f"  Tagged {count} cells")
    verify_notebook(nb07_path, NB07_SKIP_CELLS, expected_cell_count=30)

    print()
    print("=== Checking student TODOs ===")
    nb6 = nbformat.read(nb06_path.open(), as_version=4)
    nb7 = nbformat.read(nb07_path.open(), as_version=4)
    todo_count = sum(
        1 for c in nb6.cells + nb7.cells if c.cell_type == "code" and "# TODO:" in c.source
    )
    print(f"  TODO count across NB06+NB07: {todo_count} (need >= 3)")
    assert todo_count >= 3, f"Expected >= 3 student TODOs, got {todo_count}"
    print("  OK")


if __name__ == "__main__":
    main()
