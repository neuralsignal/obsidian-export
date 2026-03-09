# obsidian-export

Python package for converting Obsidian-flavored Markdown to PDF and DOCX via a 5-stage pipeline.

## Repo Structure

| Path | Purpose |
|------|---------|
| `obsidian_export/` | Source package |
| `obsidian_export/pipeline/` | 5 conversion stages (vault, preprocess, mermaid, svg, pandoc) |
| `obsidian_export/config.py` | Config dataclasses + YAML loading |
| `obsidian_export/cli.py` | CLI entry point |
| `tests/` | Test modules, fixtures, hypothesis property-based tests |
| `pixi.toml` | pixi package manager config |
| `pyproject.toml` | Python package metadata |

## Engineering Standards

- Follow KISS, DRY, YAGNI, fail fast principles
- No default arguments in function signatures
- All runtime values from config
- Custom exception classes (no bare Exception)
- Type hints on all functions
- pytest + hypothesis for testing
- ruff for linting and formatting

## Engineering Constitution

Non-negotiable principles. Violating these is a bug.

- **KISS** -- One tool per job. No clever abstractions, no premature generalization.
- **DRY** -- One source of truth. Shared logic in shared modules. Copy-paste is a defect.
- **No Default Arguments** -- Every value from config or caller. Defaults are hidden assumptions.
- **Fail Fast and Loud** -- No silent swallowing. No try-except-pass. Errors propagate with context.
- **Everything From Config** -- Intervals, paths, feature flags in config files. Code reads config, never invents values.
- **Modular and Independent** -- Each module standalone. No god objects, no shared mutable state.
- **No sys.path Manipulation** -- Use proper packaging via pyproject.toml. Import hacks are violations.
- **Descriptive Package Names** -- Never `src`, `lib`, `utils`, or `core` as importable names.
- **TDD** -- Write failing tests first, then implement. All tests via pytest.
- **Property-Based Testing** -- Use hypothesis for pure functions: parsers, transformers, validators.
- **Strict Typing** -- Type hints for every function argument and return value.
- **Custom Exceptions** -- No bare `Exception`. Use project-specific exception classes with context.
- **Composition Over Inheritance** -- Prefer small composable parts to deep inheritance chains.
- **Thin CLI Wrappers** -- CLI entry points are thin; business logic lives in library modules.

### Error Handling
- Every catch block: log, re-raise, or correct. Never catch-and-ignore.
- Error messages include: what failed, with what input, what the caller should do.
- Use custom exceptions (e.g., `ObsidianParseError`, `ConversionError`).

### Git Discipline
- Commit format: `<type>: <imperative summary>` (feat, fix, docs, chore, refactor, test)
- Never commit: secrets, generated envs, runtime output, machine-specific config
- Always commit: lock files, source code, config templates

### Definition of Done
- Implementation satisfies stated requirement
- Tests pass (existing and new)
- Linting and type-checking pass
- No regressions in related modules
- No untested code paths
- Dependencies pinned and locked
- No secrets, tokens, PII in code or logs
- Documentation updated if behavior changed

## Dark Factory Agent Context

### Label Taxonomy

| Label | Purpose |
|-------|---------|
| `type:bug` | Bug report |
| `type:feat` | Feature request |
| `type:chore` | Maintenance / improvement |
| `priority:1` | Urgent -- implement immediately |
| `priority:2` | Normal (default) |
| `priority:3` | Backlog |
| `claude:implement` | Trigger Claude to implement this issue |
| `status:triaged` | Issue has been triaged |
| `status:in-progress` | Claude is working on this |
| `status:pr-created` | PR created, awaiting review |
| `status:blocked` | Implementation blocked (see comments) |
| `source:dep-audit` | Created by dependency audit agent |
| `source:security-scan` | Created by security scan agent |
| `source:code-quality` | Created by code quality agent |
| `source:test-coverage` | Created by test coverage agent |
| `source:docs-freshness` | Created by docs freshness agent |
| `source:workflow-upgrade` | Created by workflow upgrade agent |

### Build & Test

- Package manager: pixi
- Install: `pixi install`
- Test: `pixi run test-cov`
- Lint: `pixi run lint`
- Format: `pixi run format-check`
- Coverage threshold: 80%
- Test framework: pytest + hypothesis
- Python: >=3.12

### Dependency Tooling

- Primary: pixi (conda-forge + PyPI)
- Lockfile: pixi.lock
- Audit: `pip audit` (run inside pixi shell)

### Security Standards

- No secrets in source
- Subprocess calls use list args (no shell=True)
- File paths validated before operations

### Documentation Standards

- README.md documents CLI usage and all config options
- All public functions have docstrings + type hints
- CHANGELOG.md updated for each release

### Code Quality Standards

- Max file length: 300 lines
- No sys.path manipulation
- Descriptive module names (no utils, core, lib)

### CI Setup

Steps needed before agent workflows can run tests:

1. Install pixi: `prefix-dev/setup-pixi@v0.8.8` with cache
2. Install mermaid-cli: `pixi run setup-mmdc`
3. Install system deps for Puppeteer (headless Chrome):
   ```
   sudo apt-get update && sudo apt-get install -y \
     libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
     libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
     libpango-1.0-0 libcairo2 libasound2t64
   ```

### Pipeline Architecture

```
stage1 (vault) → stage2 (preprocess) → stage3 (mermaid+svg) → stage4 (pandoc) → output (PDF/DOCX)
```
