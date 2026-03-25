"""Wave 0 config file existence and content tests."""

from pathlib import Path

import yaml


def _project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


def test_precommit_config_exists() -> None:
    """pre-commit config file exists."""
    config_path = _project_root() / ".pre-commit-config.yaml"
    assert config_path.exists(), ".pre-commit-config.yaml not found"


def test_precommit_has_ruff() -> None:
    """.pre-commit-config.yaml has ruff-pre-commit repo with ruff-check and ruff-format hooks."""
    config_path = _project_root() / ".pre-commit-config.yaml"
    content = config_path.read_text()
    assert "ruff-pre-commit" in content, "ruff-pre-commit repo missing"
    assert "ruff-check" in content, "ruff-check hook missing"
    assert "ruff-format" in content, "ruff-format hook missing"


def test_precommit_has_nbstripout() -> None:
    """.pre-commit-config.yaml has nbstripout hook."""
    config_path = _project_root() / ".pre-commit-config.yaml"
    content = config_path.read_text()
    assert "nbstripout" in content, "nbstripout hook missing"


def test_precommit_ruff_jupyter() -> None:
    """.pre-commit-config.yaml ruff hooks include jupyter in types_or."""
    config_path = _project_root() / ".pre-commit-config.yaml"
    data = yaml.safe_load(config_path.read_text())
    # Find ruff-pre-commit repo
    ruff_repo = next(
        (r for r in data["repos"] if "ruff-pre-commit" in r["repo"]),
        None,
    )
    assert ruff_repo is not None, "ruff-pre-commit repo not found"
    for hook in ruff_repo["hooks"]:
        assert "jupyter" in hook.get("types_or", []), (
            f"Hook {hook['id']} missing jupyter in types_or"
        )


def test_precommit_ruff_check_args() -> None:
    """.pre-commit-config.yaml ruff-check hook has --fix arg."""
    config_path = _project_root() / ".pre-commit-config.yaml"
    data = yaml.safe_load(config_path.read_text())
    ruff_repo = next(
        (r for r in data["repos"] if "ruff-pre-commit" in r["repo"]),
        None,
    )
    assert ruff_repo is not None, "ruff-pre-commit repo not found"
    ruff_check = next((h for h in ruff_repo["hooks"] if h["id"] == "ruff-check"), None)
    assert ruff_check is not None, "ruff-check hook not found"
    assert "--fix" in ruff_check.get("args", []), "ruff-check missing --fix arg"


def test_pyproject_has_precommit() -> None:
    """pyproject.toml dev dependencies include pre-commit."""
    pyproject_path = _project_root() / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "pre-commit" in content, "pre-commit not in pyproject.toml dev dependencies"


def test_pyproject_has_nbstripout() -> None:
    """pyproject.toml dev dependencies include nbstripout."""
    pyproject_path = _project_root() / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "nbstripout" in content, "nbstripout not in pyproject.toml dev dependencies"


def test_setup_notebook_exists() -> None:
    """notebooks/00_setup.ipynb exists."""
    nb_path = _project_root() / "notebooks" / "00_setup.ipynb"
    assert nb_path.exists(), "notebooks/00_setup.ipynb not found"


def test_setup_notebook_has_cells() -> None:
    """Setup notebook has at least 10 cells."""
    import json

    nb_path = _project_root() / "notebooks" / "00_setup.ipynb"
    nb = json.loads(nb_path.read_text())
    cell_count = len(nb["cells"])
    assert cell_count >= 10, f"Expected at least 10 cells, got {cell_count}"
