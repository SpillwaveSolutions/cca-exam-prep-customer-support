# Phase 6: Testing and CI/CD - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Automated test coverage verification, GitHub Actions CI/CD using `claude -p --bare` for PR review, meta-teaching content showing how the project itself follows CCA patterns (README section + custom skill + standalone notebook + inline callouts in existing notebooks). Test gap analysis documents coverage against CCA-RULES.md.

No new production code. No new anti-patterns. No new services or tools.

</domain>

<decisions>
## Implementation Decisions

### GitHub Actions workflow
- On pull_request: `claude -p --bare` reviews the diff for CCA compliance, posts comment
- On push to main: `poetry run pytest` + `poetry run ruff check src/`
- CI flags (CCA exam topic): `-p` mandatory for non-interactive, `--bare` for reproducibility, `--output-format json` for structured output, `--allowedTools Read,Grep,Glob` for sandboxing
- The workflow YAML itself is a CCA teaching artifact — annotated with comments explaining why each flag is used
- ANTHROPIC_API_KEY stored as GitHub secret (CCA rule: credentials in user-level config, not project files)

### Meta-teaching content (ALL THREE approaches)
1. **README.md section**: "CCA Meta-Patterns in This Project" explaining how the project uses its own patterns:
   - `.claude/CLAUDE.md` — CLAUDE.md hierarchy (Level 2, project-level)
   - CI/CD — `-p --bare` flags (CCA CI/CD rules)
   - Custom skill — `review-cca-compliance.md` (on-demand CCA review)
   - Pre-commit hooks — nbstripout + ruff (programmatic enforcement)
2. **Standalone notebook (08)**: A meta-teaching notebook walking students through the project's own CCA patterns interactively
3. **Inline callouts**: Add meta-teaching notes to existing notebooks where they demonstrate CCA patterns (e.g., in NB07 integration, note that the project's own CI/CD pipeline uses the same flags)

### Custom skill
- `.claude/skills/review-cca-compliance.md` — a skill students can invoke to review any code for CCA pattern compliance
- Checks: tool count, tool descriptions (negative bounds), escalation patterns (deterministic vs confidence), context management, cost optimization approach
- This is itself a CCA teaching artifact (custom skills in `.claude/skills/`)

### Test gap analysis
- Gap analysis only — document which CCA behaviors are tested vs untested
- No new tests in Phase 6 (234 existing tests may be sufficient)
- Document untested behaviors as "manual verification required" with specific notebook commands
- Focus on CCA behavioral coverage against CCA-RULES.md, not code coverage percentage

### Verification rules (behavior-first)
- CI workflow YAML is syntactically valid (actionlint or equivalent)
- README meta-teaching section references actual file paths that exist
- Custom skill file is valid SKILL.md format
- Every claim in gap analysis maps to either an existing test or a documented manual step

### Claude's Discretion
- Exact CI workflow YAML structure (jobs, steps, environment)
- README section wording and structure
- Which existing notebooks get inline meta-teaching callouts
- Custom skill prompt/checklist content
- Gap analysis format and coverage criteria

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CCA certification rules (HIGHEST PRIORITY)
- `.planning/CCA-RULES.md` — CI/CD rules: `-p` mandatory, `--bare` recommended, `--output-format json`, `--allowedTools`. CLAUDE.md hierarchy. Custom skills.

### Source articles
- `/Users/richardhightower/articles/articles/cca-cicd/work/final/article_publication_ready.md` — CI/CD pipeline patterns, `-p --bare` flags, `--json-schema`, sandboxing
- `/Users/richardhightower/articles/articles/cca-developer-productivity/work/final/article_publication_ready.md` — CLAUDE.md hierarchy, custom skills, hooks, description-discernment loop

### Project standards
- `.claude/CLAUDE.md` — Existing project standards + behavior-first verification rules
- `CLAUDE.md` (root) — Build commands, architecture overview

### Test infrastructure
- `tests/` — 15 test files, 234 tests, conftest.py with fixtures
- `pyproject.toml` — pytest config, ruff config

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 234 tests across 15 files — comprehensive coverage already exists
- `.claude/CLAUDE.md` (2.5KB) — project standards already written
- `.claude/skills/` directory exists (empty — ready for custom skill)
- `.github/workflows/` directory exists (empty — ready for CI workflow)
- `Taskfile.yml` — already has `task test`, `task lint`, `task verify`
- `.pre-commit-config.yaml` — nbstripout + ruff already configured

### Established Patterns
- TDD: tests written first throughout project
- Behavior-first: test stores, not API responses
- CCA Exam Tip boxes in notebooks
- Per-tool callback registry for enforcement
- Structured error context in dispatch

### Integration Points
- `.github/workflows/ci.yml` — new workflow file
- `.claude/skills/review-cca-compliance.md` — new custom skill
- `README.md` — add meta-teaching section
- `notebooks/08_meta_teaching.ipynb` — new standalone notebook
- Existing notebooks — add inline meta-teaching callouts

</code_context>

<specifics>
## Specific Ideas

- The CI workflow comments should explain CCA exam relevance: "# -p flag: mandatory for non-interactive CI (CCA exam: without this, pipeline hangs)"
- The custom skill should be something students can actually invoke on their own code — make it feel like a real review tool, not just documentation
- The meta-teaching notebook (08) could have students inspect .claude/CLAUDE.md, run the custom skill, and see the CI workflow — making it hands-on
- Gap analysis should reference specific CCA-RULES.md rules by name when documenting coverage

</specifics>

<deferred>
## Deferred Ideas

- Streamlit UI — post-milestone consideration
- VCR cassettes for API response recording — decided against (adds complexity, mocks are sufficient)
- nbval notebook execution testing — decided against (requires live API key)

</deferred>

---

*Phase: 06-testing-and-ci-cd*
*Context gathered: 2026-03-28*
