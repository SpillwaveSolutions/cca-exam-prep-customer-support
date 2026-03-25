"""Wave 0 import smoke tests — verify all sub-packages are importable."""


def test_import_root() -> None:
    """Package root is importable and has correct version."""
    import customer_service

    assert customer_service.__version__ == "0.1.0"


def test_import_agent() -> None:
    """Agent sub-package is importable."""
    import customer_service.agent  # noqa: F401


def test_import_anti_patterns() -> None:
    """Anti-patterns sub-package is importable."""
    import customer_service.anti_patterns  # noqa: F401


def test_import_data() -> None:
    """Data sub-package is importable."""
    import customer_service.data  # noqa: F401


def test_import_models() -> None:
    """Models sub-package is importable."""
    import customer_service.models  # noqa: F401


def test_import_services() -> None:
    """Services sub-package is importable."""
    import customer_service.services  # noqa: F401


def test_import_tools() -> None:
    """Tools sub-package is importable."""
    import customer_service.tools  # noqa: F401


def test_main_entry() -> None:
    """__main__.py entry point is importable and main() returns 0."""
    from customer_service.__main__ import main

    result = main()
    assert result == 0
