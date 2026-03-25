# Phase 1: Project Foundation - Research

**Researched:** 2026-03-25
**Domain:** Python package scaffolding, Jupyter notebook tooling, pre-commit hooks, Anthropic SDK token accounting
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Notebook template design:** Markdown headers with colored HTML alert boxes. Red border-left box for anti-pattern sections ("What's wrong:" callout). Green border-left box for correct-pattern sections ("Why this works:" callout). Horizontal rule (`---`) separates sections. Works in all Jupyter renderers without extra dependencies.
- **Notebook section ordering:** Setup > Anti-pattern > Correct > Compare in every notebook. Show the wrong way first so students feel the pain, then the fix. Ends with side-by-side comparison table + CCA exam tip.
- **print_usage helper:** Show full token breakdown: input, output, cache read, cache write, total. Include estimated USD cost with model name shown. Format: aligned columns with labeled rows. Location: helper module importable by all notebooks.
- **compare_results helper:** `compare_results(anti_result, correct_result)`. Side-by-side table with percentage deltas. Covers token/cost metrics AND business outcome metrics (escalated?, rule enforced?).
- **Setup notebook (00) scope:** Four verification checks (Python >= 3.13, anthropic SDK version, ANTHROPIC_API_KEY valid with minimal API call, package import verification). Seed data preview. Friendly error handling. Uses python-dotenv.
- **Package init exports:** Top-level `__init__.py` re-exports ServiceContainer, run_agent_loop, all Pydantic models. `from customer_service import X` pattern.
- **Main entry point:** `__main__.py` skeleton. Phase 1: can't fully run until Phase 2.

### Claude's Discretion

- Exact HTML/CSS for notebook alert boxes (colors, padding, border width)
- Pre-commit hook configuration details (nbstripout + ruff)
- Helper module file organization (single file vs split)
- Seed data file format (JSON vs Python dicts)

### Deferred Ideas (OUT OF SCOPE)

- Streamlit UI for interactive agent demo
- Interactive notebook widgets (ipywidgets tabs)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SETUP-01 | Project skeleton with `src/` layout, pyproject.toml, Poetry config, `.env.example`, `.gitignore` | pyproject.toml already exists and is well-formed; directories exist but need `__init__.py` files; `.env.example` and `.gitignore` must be created |
| SETUP-02 | Notebook template with correct-before-anti-pattern ordering, `print_usage` helper, visual differentiation | Anthropic usage object fields verified; HTML alert box pattern is standard Jupyter HTML output; helper module pattern documented |
| SETUP-03 | Pre-commit hooks (nbstripout + ruff) for notebook and code hygiene | nbstripout 0.9.1 verified; ruff-pre-commit v0.15.7 verified; configuration examples documented |
| NB-01 | Notebook 00 - Setup and environment verification | python-dotenv 1.2.2; find_dotenv() pattern for notebooks; four-check verification pattern documented |
</phase_requirements>

---

## Summary

Phase 1 is a pure scaffolding phase on a greenfield project. The directory structure and `pyproject.toml` already exist; what's missing is `__init__.py` files in all sub-packages, the notebook infrastructure (`notebooks/00_setup.ipynb`, helper module), pre-commit configuration, and the `__main__.py` skeleton.

The Anthropic SDK is at 0.86.0 (latest) but the project's `pyproject.toml` requires `>=0.42.0` which is fine for Phase 1 — the setup notebook needs to make a minimal API call to verify the key, which works with any recent version. The usage object structure is stable: `input_tokens`, `output_tokens`, `cache_read_input_tokens`, and `cache_creation_input_tokens` are all available on the response.

Pre-commit tooling is mature and straightforward: nbstripout 0.9.1 strips notebook outputs before commit; ruff-pre-commit v0.15.7 handles both linting and formatting including Jupyter notebooks natively. The existing ruff configuration (E, F, I, N, W, UP with `target-version = "py313"`) is current and valid as of ruff 0.15.7.

**Primary recommendation:** Create `__init__.py` files for all six sub-packages, a `notebooks/helpers.py` helper module with `print_usage` and `compare_results`, the setup notebook (00), `.pre-commit-config.yaml`, and the `__main__.py` skeleton. This establishes the foundation every later phase builds on.

---

## Standard Stack

### Core (already in pyproject.toml — confirmed current)

| Library | Version (PyPI latest) | Purpose | Notes |
|---------|----------------------|---------|-------|
| anthropic | 0.86.0 (pyproject: `>=0.42.0`) | Anthropic API calls | Usage object fields verified; `>=0.42.0` is acceptable for Phase 1 |
| pydantic | 2.12.5 (pyproject: `>=2.0`) | Data models, JSON schema generation | `model_json_schema()` stable in v2 |
| python-dotenv | 1.2.2 (pyproject: `>=1.0`) | Load `.env` in notebooks | `find_dotenv()` for notebook path traversal |
| poetry | 2.3.2 (installed) | Dependency management, src layout | `[tool.poetry.group.*]` syntax already used correctly |

### Dev Tooling (already in pyproject.toml — confirmed current)

| Library | Version (PyPI latest) | Purpose | Notes |
|---------|----------------------|---------|-------|
| ruff | 0.15.7 (pyproject: `>=0.4`) | Lint + format, including notebooks | Notebook support built-in since 0.6; no extra config needed |
| pytest | 8.x (pyproject: `>=8.0`) | Tests | Standard; no changes for Phase 1 |
| pre-commit | 4.5.1 | Git hook runner | Not yet in pyproject.toml — add to dev group |
| nbstripout | 0.9.1 | Strip notebook output before commit | Add to dev group AND .pre-commit-config.yaml |

### Notebook Extras (already in pyproject.toml)

| Library | Version (pyproject) | Purpose |
|---------|---------------------|---------|
| jupyter | `>=1.0` | Jupyter Lab |
| ipykernel | `>=6.0` | Kernel for notebooks |
| tabulate | `>=0.9` | Formatted tables in compare_results |

**Add to pyproject.toml dev group:**
```bash
poetry add --group dev pre-commit nbstripout
```

**Version verification (confirmed against PyPI on 2026-03-25):**
- anthropic: 0.86.0
- pydantic: 2.12.5
- python-dotenv: 1.2.2
- ruff: 0.15.7
- pre-commit: 4.5.1
- nbstripout: 0.9.1

---

## Architecture Patterns

### Package Structure (all directories exist — only need `__init__.py`)

```
src/customer_service/
├── __init__.py              # Re-exports: ServiceContainer, run_agent_loop, all models
├── agent/
│   └── __init__.py          # Empty initially; populated Phase 2
├── anti_patterns/
│   └── __init__.py          # Empty initially; populated Phase 3
├── data/
│   └── __init__.py          # Seed data loader; populated Phase 2
├── models/
│   └── __init__.py          # Empty initially; populated Phase 2
├── services/
│   └── __init__.py          # Empty initially; populated Phase 2
└── tools/
    └── __init__.py          # Empty initially; populated Phase 2
```

```
notebooks/
├── helpers.py               # print_usage, compare_results, alert_box helpers
├── 00_setup.ipynb           # Environment verification notebook (Phase 1)
└── (01–07 created in later phases)
```

### Pattern 1: Package `__init__.py` with conditional re-exports

Top-level `__init__.py` re-exports only what exists. Since Phase 1 is skeleton-only, re-exports are stubs with `# noqa: F401` to silence unused-import lint:

```python
# src/customer_service/__init__.py
# Source: pyproject.toml architecture + CLAUDE.md
"""CCA Customer Support Resolution Agent package."""

__version__ = "0.1.0"

# These will be populated as phases complete.
# Importing now enables: from customer_service import ServiceContainer
try:
    from customer_service.services import ServiceContainer  # noqa: F401
except ImportError:
    pass

try:
    from customer_service.agent.agent_loop import run_agent_loop  # noqa: F401
except ImportError:
    pass
```

For Phase 1, the simpler approach is to just define `__version__` and a docstring. Sub-package `__init__.py` files are empty files — they just make directories into packages.

### Pattern 2: print_usage helper

The Anthropic usage object has these fields (verified against official docs 2026-03-25):

```python
# Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
# notebooks/helpers.py
def print_usage(response, model: str = "claude-sonnet-4-20250514") -> None:
    """Print token usage with cost estimate. Works with or without caching."""
    u = response.usage
    inp   = u.input_tokens
    out   = u.output_tokens
    cr    = getattr(u, "cache_read_input_tokens", 0) or 0
    cw    = getattr(u, "cache_creation_input_tokens", 0) or 0
    total = inp + out + cr + cw

    print(f"\n{'Token Usage':─<40}")
    print(f"  {'Input tokens:':<28} {inp:>8,}")
    print(f"  {'Output tokens:':<28} {out:>8,}")
    if cr:
        print(f"  {'Cache read tokens:':<28} {cr:>8,}")
    if cw:
        print(f"  {'Cache write tokens:':<28} {cw:>8,}")
    print(f"  {'Total tokens:':<28} {total:>8,}")
    print(f"  {'Model:':<28} {model}")
```

**Key insight on cache token accounting (HIGH confidence, verified):**
- `input_tokens` = uncached tokens (after last cache breakpoint)
- `cache_read_input_tokens` = tokens served from cache (charged at 10% base price)
- `cache_creation_input_tokens` = tokens written to cache (charged at 125% for 5m TTL)
- `total_input = input_tokens + cache_read_input_tokens + cache_creation_input_tokens`
- Do NOT double-count: cache fields are NOT additive on top of `input_tokens`

### Pattern 3: python-dotenv in notebooks

```python
# Source: https://github.com/theskumar/python-dotenv (verified 2026-03-25)
# At top of every notebook's setup cell:
from dotenv import load_dotenv, find_dotenv

# find_dotenv() walks up from notebook location to find .env
load_dotenv(find_dotenv(), override=False)
```

`override=False` (default) means: env var set in shell takes precedence over `.env` file. This is correct for student environments where `ANTHROPIC_API_KEY` may already be in their shell profile.

### Pattern 4: Pre-commit configuration

```yaml
# .pre-commit-config.yaml
# Source: https://github.com/kynan/nbstripout (0.9.1) + https://github.com/astral-sh/ruff-pre-commit (v0.15.7)
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.7
    hooks:
      - id: ruff-check
        types_or: [python, pyi, jupyter]
        args: [--fix]
      - id: ruff-format
        types_or: [python, pyi, jupyter]

  - repo: https://github.com/kynan/nbstripout
    rev: 0.9.1
    hooks:
      - id: nbstripout
```

**Hook ordering matters:** `ruff-check` (with `--fix`) before `ruff-format`. Both run on `jupyter` types — this is native since ruff 0.6, no extra config needed.

**nbstripout behavior as pre-commit hook:** When run as a pre-commit hook (not git filter), it modifies the working copy. Outputs are stripped from the staged `.ipynb` file AND from disk. This is intentional — commits stay clean, students re-run cells to see output.

### Pattern 5: Notebook alert boxes (HTML in markdown cells)

```html
<!-- Anti-pattern (red) -->
<div style="border-left: 4px solid #dc3545; padding: 12px 16px; background: #fff5f5; margin: 8px 0;">
<strong>What's wrong:</strong> [explanation of the anti-pattern failure]
</div>

<!-- Correct pattern (green) -->
<div style="border-left: 4px solid #28a745; padding: 12px 16px; background: #f0fff4; margin: 8px 0;">
<strong>Why this works:</strong> [explanation of the correct approach]
</div>
```

These render in JupyterLab, VS Code notebooks, nbviewer, and GitHub preview. No extra dependencies.

### Pattern 6: `__main__.py` skeleton

```python
# src/customer_service/__main__.py
"""
Entry point: python -m customer_service

Phase 1: Skeleton only. Full implementation in Phase 2.
"""
import sys


def main() -> None:
    print("CCA Customer Support Resolution Agent")
    print("Phase 1: Package skeleton ready.")
    print("Run 'poetry run jupyter lab' to open notebooks.")
    print("See notebooks/00_setup.ipynb to verify your environment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Pattern 7: Setup notebook verification structure

```python
# Cell pattern for each of the 4 verification checks
import sys

OK = "\033[92m[OK]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"

# Check 1: Python version
if sys.version_info >= (3, 13):
    print(f"{OK} Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    print(f"{FAIL} Python {sys.version_info.major}.{sys.version_info.minor} — need 3.13+")
    print("    Fix: install Python 3.13 via pyenv or python.org")
```

The minimal API call for key verification should use `client.messages.create()` with `max_tokens=1` and a simple "hello" message. This is cheapest and confirms both key validity and network access.

### Anti-Patterns to Avoid

- **Bare assert for verification:** `assert sys.version_info >= (3, 13)` raises `AssertionError` with no guidance. Use `if/else` with fix instructions.
- **Relative imports in notebooks:** Notebooks run with working directory as the notebook dir, not project root. Always add `sys.path.insert(0, ...)` or rely on `poetry install`.
- **Hardcoded `.env` path:** Use `find_dotenv()` not `load_dotenv(".env")` — the latter breaks when running notebooks from subdirectories.
- **Double-counting cache tokens in cost estimate:** `total_input_cost = input_tokens * price` — wrong. Cache read/write have different rates. See token accounting section above.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Notebook output stripping | Custom git filter script | nbstripout 0.9.1 | Handles metadata, cell outputs, execution counts; edge cases in nbformat |
| Python linting + formatting | Custom ruff config from scratch | Existing pyproject.toml ruff config | Already configured for py313, 100-char, E/F/I/N/W/UP — correct |
| Environment variable loading | `os.environ` + manual file parsing | python-dotenv `find_dotenv()` | Handles path traversal, comment lines, quoting, override semantics |
| Markdown table formatting | Custom string joining | tabulate (already in notebooks deps) | Handles alignment, padding, multiple table formats |
| Pre-commit orchestration | Shell scripts calling ruff/nbstripout | pre-commit framework | Handles hook isolation, versioned hooks, staged-only processing |

**Key insight:** The project's pre-commit stack is two tools doing one job each. Any custom scripting here creates maintenance burden for what is effectively devtool plumbing.

---

## Common Pitfalls

### Pitfall 1: Missing `__init__.py` breaks imports silently

**What goes wrong:** Sub-packages without `__init__.py` are namespace packages (PEP 420), not regular packages. `from customer_service.models import X` may work accidentally with some Python path configurations but fail for students who install from the wheel.

**Why it happens:** `poetry install` in editable mode sometimes masks the problem locally.

**How to avoid:** Create explicit empty `__init__.py` in every sub-package directory. The `src/` layout with `packages = [{include = "customer_service", from = "src"}]` in pyproject.toml requires proper package markers.

**Warning signs:** `ModuleNotFoundError` on student machines that don't match local dev environment.

### Pitfall 2: nbstripout pre-commit hook vs git filter confusion

**What goes wrong:** Running `nbstripout --install` (git filter mode) AND adding it to `.pre-commit-config.yaml` (hook mode) creates double-stripping. The git filter mode is a project-wide silent filter; the pre-commit hook is explicit and shows in `git diff`.

**Why it happens:** nbstripout docs cover both modes; many tutorials use the filter mode.

**How to avoid:** Use ONLY the pre-commit hook (`.pre-commit-config.yaml`). Do NOT run `nbstripout --install`. This keeps behavior explicit and auditable.

**Warning signs:** Students see notebook outputs disappear from disk after `git add` even without committing.

### Pitfall 3: ruff `types_or` vs `types` for Jupyter files

**What goes wrong:** Using `types: [python]` excludes `.ipynb` files from ruff checks.

**Why it happens:** Jupyter notebooks are not Python files (they're JSON); pre-commit's file type detection won't match them as `python`.

**How to avoid:** Use `types_or: [python, pyi, jupyter]`. The `jupyter` type is supported by pre-commit's identify library and matches `.ipynb`.

**Warning signs:** `poetry run ruff check notebooks/` works but pre-commit doesn't flag notebook issues.

### Pitfall 4: API key verification with max_tokens too low

**What goes wrong:** Using `max_tokens=1` for the verification call can occasionally return an empty response body or trigger edge case behavior.

**Why it happens:** Claude's minimum response may be 2-3 tokens for acknowledgment.

**How to avoid:** Use `max_tokens=10` for the verification call. Still cheap (fractions of a cent), avoids edge cases.

### Pitfall 5: Top-level `__init__.py` re-exports that don't exist yet

**What goes wrong:** `from customer_service.agent.agent_loop import run_agent_loop` in `__init__.py` fails on import because `agent_loop.py` doesn't exist until Phase 2.

**Why it happens:** Eager re-exports break the Phase 1 requirement that "all sub-packages are importable."

**How to avoid:** Keep Phase 1 `__init__.py` minimal — just `__version__` and a docstring. Add re-exports in Phase 2 as files are created.

**Warning signs:** Setup notebook's package import check fails immediately.

---

## Code Examples

### Anthropic SDK usage object (verified against official docs 2026-03-25)

```python
# Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
# Full usage object structure (all fields):
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=10,
    messages=[{"role": "user", "content": "Hi"}],
)
# response.usage fields:
#   .input_tokens                  int  — uncached new tokens
#   .output_tokens                 int  — generated tokens
#   .cache_read_input_tokens       int  — tokens read from cache (or 0)
#   .cache_creation_input_tokens   int  — tokens written to cache (or 0)
#
# Total input cost basis:
#   total_input = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
```

### stop_reason values (verified 2026-03-25)

```python
# Source: https://platform.claude.com/docs/en/api/handling-stop-reasons
# All valid stop_reason values as of 2026-03-25:
#   "end_turn"                    — natural completion
#   "tool_use"                    — Claude wants to call a tool
#   "max_tokens"                  — hit max_tokens limit
#   "stop_sequence"               — hit a custom stop sequence
#   "pause_turn"                  — server tool loop hit iteration limit (server tools only)
#   "refusal"                     — safety refusal
#   "model_context_window_exceeded" — hit context window (Sonnet 4.5+ default; older via beta header)

# Phase 1 skeleton agentic loop pattern (Phase 2 will implement full version):
while True:
    response = client.messages.create(...)
    if response.stop_reason == "end_turn":
        break
    elif response.stop_reason == "tool_use":
        # extract tool_use blocks, execute, send tool_result back
        pass
    elif response.stop_reason == "max_tokens":
        raise RuntimeError("Response truncated; increase max_tokens")
    # Note: do NOT check content type to determine loop exit — use stop_reason
```

### Pydantic v2 model_json_schema (Phase 2 preview, not Phase 1 work)

```python
# Source: https://docs.pydantic.dev/latest/concepts/json_schema/
# Phase 2 will use this pattern for tool input_schema generation:
from pydantic import BaseModel, Field

class LookupCustomerInput(BaseModel):
    customer_id: str = Field(description="The unique customer ID")

schema = LookupCustomerInput.model_json_schema()
# Produces: {"type": "object", "properties": {"customer_id": {"type": "string",
#            "description": "The unique customer ID"}}, "required": ["customer_id"],
#            "title": "LookupCustomerInput"}
#
# For tool definition, use schema as input_schema directly (it is valid JSON Schema)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pyproject.toml` `[tool.poetry.dependencies]` only | Poetry 2.0 supports `[project]` PEP 621 table | Poetry 2.0 (Jan 2025) | Our pyproject uses `[tool.poetry.*]` — still valid but legacy style |
| ruff `[tool.ruff] select` (flat) | `[tool.ruff.lint] select` (nested) | ruff ~0.2 | pyproject.toml already uses correct nested format |
| isort + flake8 + black separately | ruff handles all three | ruff stable | Only ruff needed; existing config is correct |
| nbstripout git filter (`nbstripout --install`) | pre-commit hook | nbstripout 0.6+ | Hook approach is explicit and auditable; use this |
| `anthropic.usage.cache_creation_input_tokens` not available | Available in all recent SDK versions | SDK ~0.20+ | Available in `>=0.42.0` as required by pyproject.toml |

**Deprecated/outdated:**
- `black` + `isort` combination: replaced by `ruff format` + `ruff check --select I`
- `nbformat` manual output stripping: replaced by nbstripout
- Content-type checking for loop exit (`if any(b.type == "text" for b in response.content)`): replaced by `stop_reason == "end_turn"`

---

## Open Questions

1. **Seed data file format (Claude's discretion)**
   - What we know: `src/customer_service/data/` exists and is empty; it's referenced in setup notebook
   - What's unclear: JSON files (portable) vs Python dicts (easier to import)
   - Recommendation: Use Python dicts in a `seed.py` file — simpler to import without json parsing, no file path resolution needed in Phase 1

2. **Helper module organization (Claude's discretion)**
   - What we know: `print_usage` and `compare_results` must be importable by all notebooks
   - What's unclear: Single `helpers.py` at `notebooks/helpers.py` vs a proper package at `src/customer_service/notebooks/`
   - Recommendation: `notebooks/helpers.py` — notebooks import it via `sys.path.insert(0, str(Path(__file__).parent))`. Simple, no package installation needed. Move to package if it grows beyond ~150 lines.

3. **Alert box exact CSS values (Claude's discretion)**
   - What we know: Red for anti-pattern, green for correct; border-left style
   - What's unclear: Exact hex colors, padding, font-weight
   - Recommendation: Use Bootstrap-inspired defaults: `#dc3545` (danger red), `#28a745` (success green), `#fff5f5`/`#f0fff4` backgrounds, 4px border, 12px 16px padding. These are widely recognized and render well in dark mode too.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| Quick run command | `poetry run pytest tests/ -x -q` |
| Full suite command | `poetry run pytest tests/` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SETUP-01 | Package importable: `import customer_service` succeeds | smoke | `poetry run pytest tests/test_imports.py -x` | Wave 0 |
| SETUP-01 | All sub-packages importable (agent, models, services, tools, data, anti_patterns) | smoke | `poetry run pytest tests/test_imports.py -x` | Wave 0 |
| SETUP-02 | `print_usage` callable with a mock usage object; returns None; prints expected fields | unit | `poetry run pytest tests/test_helpers.py::test_print_usage -x` | Wave 0 |
| SETUP-02 | `compare_results` callable with two dicts; returns None; prints percentage deltas | unit | `poetry run pytest tests/test_helpers.py::test_compare_results -x` | Wave 0 |
| SETUP-03 | `.pre-commit-config.yaml` exists and is valid YAML with nbstripout + ruff entries | smoke | `poetry run pytest tests/test_config.py::test_precommit_config -x` | Wave 0 |
| NB-01 | `notebooks/00_setup.ipynb` exists | smoke | `poetry run pytest tests/test_config.py::test_setup_notebook_exists -x` | Wave 0 |

**Note on NB-01:** Full notebook execution (4 verification checks including live API call) is manual-only for Phase 1. The automated test confirms the file exists and has the expected cell count structure. Live API call is verified by student running the notebook.

### Sampling Rate

- **Per task commit:** `poetry run pytest tests/test_imports.py tests/test_helpers.py tests/test_config.py -x -q`
- **Per wave merge:** `poetry run pytest tests/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/__init__.py` — makes tests/ a package
- [ ] `tests/test_imports.py` — covers SETUP-01 import smoke tests
- [ ] `tests/test_helpers.py` — covers SETUP-02 helper function unit tests
- [ ] `tests/test_config.py` — covers SETUP-03 config file existence, NB-01 notebook existence
- [ ] Framework already installed via `poetry install` — no gap

---

## Sources

### Primary (HIGH confidence)

- Official Anthropic docs: https://platform.claude.com/docs/en/api/handling-stop-reasons — stop_reason values, tool_use loop pattern, empty response handling
- Official Anthropic docs: https://platform.claude.com/docs/en/build-with-claude/prompt-caching — cache_control API, usage object cache fields, minimum token thresholds
- PyPI anthropic: 0.86.0 (latest as of 2026-03-25)
- Pydantic official docs: https://docs.pydantic.dev/latest/concepts/json_schema/ — model_json_schema(), Field descriptions, mode parameter
- PyPI pydantic: 2.12.5 (latest as of 2026-03-25)
- PyPI python-dotenv: 1.2.2 (latest as of 2026-03-25)
- PyPI ruff: 0.15.7 (latest as of 2026-03-25)
- PyPI pre-commit: 4.5.1 (latest as of 2026-03-25)
- PyPI nbstripout: 0.9.1 (latest as of 2026-03-25, released 2026-02-21)

### Secondary (MEDIUM confidence)

- GitHub nbstripout: https://github.com/kynan/nbstripout — pre-commit-hooks.yaml, hook ID `nbstripout`, `--extra-keys` arg syntax
- GitHub ruff-pre-commit: https://github.com/astral-sh/ruff-pre-commit — hook IDs `ruff-check` and `ruff-format`, `types_or` for jupyter
- Ruff docs: https://docs.astral.sh/ruff/integrations/ — native notebook support since 0.6, no extra config needed
- python-dotenv PyPI: https://pypi.org/project/python-dotenv/ — find_dotenv() path traversal, override=False semantics

### Tertiary (LOW confidence)

- None — all Phase 1 findings are verifiable from official sources or PyPI.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI on 2026-03-25
- Architecture (package structure, __init__.py): HIGH — standard Python src layout, pyproject.toml already defines it
- Pre-commit configuration: HIGH — verified against official repos and PyPI
- print_usage helper: HIGH — usage object fields verified against official Anthropic docs
- Pitfalls: HIGH — derived from documented behavior in official sources and known Python packaging edge cases
- Notebook HTML alert boxes: MEDIUM — standard HTML/CSS rendered by Jupyter, no official spec; CSS values are conventional

**Research date:** 2026-03-25
**Valid until:** 2026-06-25 (stable tooling, 90-day estimate)

**Key version pins for .pre-commit-config.yaml:**
- `rev: v0.15.7` for ruff-pre-commit
- `rev: 0.9.1` for nbstripout
