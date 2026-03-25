# Stack Research

**Domain:** Claude API teaching example — Python agent with tool use
**Researched:** 2026-03-25
**Confidence:** HIGH (core SDK verified against official releases and docs)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.13+ | Runtime | Project constraint; 3.13 ships with improved error messages and perf gains; SDK supports 3.9+ so 3.13 is fine |
| anthropic (Python SDK) | 0.86.0 | Claude API client | Latest stable as of March 18 2026; confirmed via PyPI. Use `>=0.77.0` in pyproject.toml to get structured outputs GA |
| pydantic | 2.12.x | Data models, tool input/output schemas | v2 rewrites core in Rust — 5-50x faster than v1. `model_json_schema()` generates JSON Schema for tool `input_schema` directly. Native integration with `client.messages.parse()` |
| Poetry | 2.x | Dependency management and packaging | Project constraint. Poetry 2.0 (Jan 2025) added `[project]` table support matching PEP 621 — use `[project]` not `[tool.poetry.dependencies]` for new projects |
| JupyterLab | 4.x | Teaching notebook environment | JupyterLab 4 is current; ships richer diff UI and performance improvements over classic Jupyter. Students use `jupyter lab` command |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ipykernel | >=6.29 | Jupyter kernel for Poetry virtualenv | Always — run `poetry run python -m ipykernel install --user --name cca-exam` so notebooks use the Poetry env |
| python-dotenv | >=1.0 | Load `ANTHROPIC_API_KEY` from `.env` | Always — keeps student API keys out of notebook cells |
| pytest | >=8.3 | Unit and integration test runner | Always — anchor all tests with pytest |
| pytest-mock | >=3.14 | Mock `anthropic.Anthropic` client in unit tests | Always for unit tests — deterministic testing of tool routing without hitting the API |
| pytest-recording | >=0.13 | Record/replay HTTP cassettes (backed by VCR.py) | Integration tests — record real API responses once, replay without network in CI |
| nbval | >=0.11 | Validate notebook cells execute without error | CI notebook smoke tests — use `--nbval-lax` to check execution, not output equality |
| nbstripout | >=0.7 | Strip cell outputs before git commit | Always in pre-commit — keeps notebooks diff-clean, prevents API key leaks in outputs |
| rich | >=13.x | Pretty-print conversation turns and tool calls in notebooks | Always — `rich.print()` makes the anti-pattern vs correct pattern contrast visually obvious in teaching cells |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pre-commit | Enforce nbstripout and code formatting before commits | Config: `nbstripout` + `ruff` hooks; run `pre-commit install` after clone |
| ruff | Linting and formatting for the Python package | Replaces black + flake8 + isort in one tool; fast, Poetry plugin available |
| nbstripout | Strip notebook outputs for clean git diffs | Configure via `nbstripout install` or pre-commit hook; critical for teaching repos so students see clean starting state |

## Installation

```bash
# Install Poetry 2.x first if not present
curl -sSL https://install.python-poetry.org | python3 -

# Create project
poetry new customer_service_agent
cd customer_service_agent

# Core runtime dependencies
poetry add "anthropic>=0.77.0" "pydantic>=2.12.0" "python-dotenv>=1.0"

# Jupyter teaching environment
poetry add "jupyterlab>=4.0" "ipykernel>=6.29" "rich>=13.0"

# Dev and testing dependencies
poetry add --group dev pytest pytest-mock "pytest-recording>=0.13" nbval nbstripout pre-commit ruff

# Register the Poetry kernel with Jupyter
poetry run python -m ipykernel install --user --name cca-exam --display-name "CCA Exam (Python 3.13)"

# Initialize pre-commit hooks
poetry run pre-commit install
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| anthropic (raw SDK) | claude-agent-sdk-python | When you want the full Agent SDK loop (hooks, memory, computer use) — PROJECT.md explicitly excludes this to teach fundamentals |
| pydantic v2 | dataclasses or TypedDict | Never for this project — Pydantic v2's `model_json_schema()` is essential for generating `input_schema` for tools without manual JSON Schema authoring |
| pytest + pytest-mock | unittest.mock directly | Both work; pytest-mock gives cleaner `mocker` fixture syntax in test functions |
| pytest-recording (VCR) | Mocking the entire client | VCR cassettes test real API response shapes; mocks test routing logic. Use both: mocks for unit, cassettes for integration |
| Poetry 2.x | uv / pip / pipenv | uv is faster but lacks the maturity for a teaching project; PROJECT.md specifies Poetry explicitly |
| JupyterLab 4 | VS Code Jupyter extension | JupyterLab is self-contained and requires no IDE config — better for student onboarding |
| nbstripout | Manual clean script | nbstripout as pre-commit hook is automatic and can't be forgotten |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Claude Agent SDK (claude-agent-sdk-python) | Hides the tool loop internals — students won't understand what `stop_reason == "tool_use"` means if the SDK handles it transparently | Raw `anthropic` SDK — write the while loop explicitly so each step is visible |
| async / asyncio | PROJECT.md explicitly excludes async — synchronous code is more readable for teaching and stack traces are cleaner | Synchronous `client.messages.create()` calls |
| LangChain / LangGraph | Abstractions hide Claude-specific patterns (prompt caching, tool_choice, structured outputs) that the CCA exam tests directly | Direct `anthropic` SDK calls |
| instructor library | Adds another layer on top of Pydantic + Anthropic; obscures the `output_config` API students need to know | `client.messages.parse()` with Pydantic directly |
| `output_format` parameter (old beta API) | Deprecated — migrated to `output_config.format` in v0.77+. Old beta header (`structured-outputs-2025-11-13`) still works in transition but will break | `output_config={"format": {...}}` or `client.messages.parse()` with `output_format=MyModel` (the parse() helper still accepts it) |
| `[tool.poetry.dependencies]` table (Poetry 1.x style) | Poetry 2.0 changed to PEP 621 `[project]` table — old style still works but mixing styles creates confusion | `[project.dependencies]` table in pyproject.toml |
| ipytest | Runs pytest inside a notebook cell — conflates notebook teaching cells with test infrastructure | Keep tests in `tests/` package; run `pytest` from CLI |
| Firebase or any external service | PROJECT.md constraint: students need only `ANTHROPIC_API_KEY` — external services add setup friction | In-memory Python dicts and functions that simulate the services |

## Stack Patterns by Variant

**For the raw agentic tool loop (all notebooks 01-07):**
- Write the `while response.stop_reason == "tool_use":` loop explicitly
- Use `[block for block in response.content if block.type == "tool_use"]` to extract tool calls
- Append assistant message first, then user message with `tool_result` blocks
- Never use the tool runner helper — it hides the loop that students must understand

**For prompt caching demonstration (notebook 04):**
- Use the automatic caching shortcut: `cache_control={"type": "ephemeral"}` at request top level (added in SDK v0.83.0)
- For explicit cache breakpoints: add `"cache_control": {"type": "ephemeral"}` to the last static system block
- Track cache performance via `response.usage.cache_read_input_tokens` and `cache_creation_input_tokens`
- Use 1-hour TTL (`"ttl": "1h"`) for the policy document demo — show the 0.1x cost for cache hits vs 1.25x for writes

**For structured outputs (notebook 06, escalation handoffs):**
- Use `client.messages.parse(output_format=EscalationHandoff)` where `EscalationHandoff` is a Pydantic `BaseModel`
- For strict tool use on individual tools: add `"strict": True` to the tool definition dict
- Combine both: strict tool use for tool calls + `output_config` for the final structured response
- Required model: Claude Sonnet 4.6 or Claude Opus 4.6 for full structured outputs GA support

**For the Swiss Army anti-pattern (notebook 02):**
- Define all 15 tools as a flat list — show the context window cost via `response.usage.input_tokens`
- Then show the 5-tool correct version — make the token count contrast visible with `rich.print()`

**For PostToolUse callback pattern (programmatic escalation enforcement):**
- This is NOT the Agent SDK hooks — implement as a Python function that wraps each tool call result
- Pattern: `result = dispatch_tool(tool_name, tool_input); result = apply_escalation_policy(tool_name, tool_input, result)`
- This is the "application layer enforcement" pattern the CCA exam tests

**For testing:**
- Unit tests: mock `anthropic.Anthropic` with `pytest-mock`; assert tool routing logic
- Integration tests: `pytest-recording` with `--vcr-record=none` in CI after initial cassette recording
- Notebook smoke tests: `pytest --nbval-lax notebooks/` in CI to catch broken notebook cells

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| anthropic 0.86.0 | pydantic 2.12.x | SDK uses pydantic internally; both must be v2. SDK pyproject.toml lists both pydantic-v1 and pydantic-v2 extras — the default install uses v2 |
| anthropic 0.86.0 | Python 3.9–3.14 | 3.13 is fully supported; no known issues |
| pydantic 2.12.x | Python 3.9–3.14 | v2.12 added Python 3.14 support |
| poetry 2.x | Python 3.9–3.14 | Use `pyenv` or `mise` to manage Python versions alongside Poetry |
| jupyterlab 4.x | ipykernel >=6.29 | JupyterLab 4 requires ipykernel 6+ for async kernel support |
| nbstripout 0.7+ | pre-commit | pre-commit hook ID: `nbstripout`; no special configuration needed |
| pytest-recording | vcrpy (bundled) | Do NOT install `pytest-vcr` alongside `pytest-recording` — they are incompatible |

## Sources

- https://github.com/anthropics/anthropic-sdk-python/releases — SDK version history; v0.86.0 confirmed as latest (March 18, 2026). HIGH confidence.
- https://pypi.org/project/anthropic/ — Python >=3.9 requirement confirmed. HIGH confidence.
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching — Cache TTLs, automatic caching, explicit breakpoints, supported models. HIGH confidence.
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs — `output_config` migration from `output_format`, `client.messages.parse()`, strict tool use. HIGH confidence.
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use — Complete raw SDK agentic loop pattern. HIGH confidence.
- https://pypi.org/project/pydantic/ — Pydantic 2.12.5 confirmed as latest (Nov 2025). HIGH confidence.
- https://python-poetry.org/docs/pyproject/ — Poetry 2.0 `[project]` table migration. MEDIUM confidence (confirmed via Poetry docs).
- https://github.com/kiwicom/pytest-recording — pytest-recording VCR integration for LLM API testing. MEDIUM confidence.
- https://github.com/kynan/nbstripout — nbstripout pre-commit hook for teaching notebooks. HIGH confidence.
- https://dev.to/nebulagg/how-to-test-ai-agent-tool-calls-with-pytest-ol8 — pytest-mock patterns for LLM agent testing. MEDIUM confidence (blog post, patterns verified against pytest docs).

---
*Stack research for: CCA Exam Prep — Customer Support Agent (Claude API Python teaching example)*
*Researched: 2026-03-25*
