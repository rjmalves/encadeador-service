# [TOOL-002] Configure ruff and mypy

> **Epic**: [Epic 01: Tooling Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P0

## Context

### Background

After creating `pyproject.toml`, we need to add tool configurations for:
- **ruff**: Fast Python linter and formatter (replaces flake8, black, isort)
- **mypy**: Static type checker

These tools ensure code quality and consistency with flexibilizador-service.

### Relation to Epic

Part of tooling modernization. Enables consistent code quality enforcement.

### Current State

No linting or type checking configured. Code may have style inconsistencies.

## Specification

### Add to pyproject.toml

Append the following sections to the existing `pyproject.toml`:

```toml
# =============================================================================
# Tool Configuration
# =============================================================================

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "B008",   # do not perform function calls in argument defaults
    "B904",   # raise without from inside except
    "ARG001", # unused function argument (common in interfaces)
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ARG001", "ARG002"]
"app/adapters/chainingrepository.py" = ["ARG002"]  # Interface methods

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.mypy]
python_version = "3.11"
warn_return_any = false
warn_unused_ignores = false
disallow_untyped_defs = false
ignore_missing_imports = true
check_untyped_defs = true
no_implicit_optional = true

# Strict mode for new code only
[[tool.mypy.overrides]]
module = [
    "app.routers.health",
    "app.models.errors",
    "app.internal.exceptions",
    "app.utils.zip_utils",
    "app.utils.temp_manager",
    "app.adapters.s3_repository",
]
disallow_untyped_defs = true
warn_return_any = true
```

### Configuration Rationale

| Setting | Value | Reason |
|---------|-------|--------|
| `target-version` | py311 | Match runtime version |
| `line-length` | 88 | Black default, widely adopted |
| `ignore E501` | Yes | Let formatter handle line length |
| `ignore B008` | Yes | FastAPI uses `Depends()` in defaults |
| `ignore_missing_imports` | Yes | Third-party libs may lack stubs |

## Acceptance Criteria

- [ ] ruff configuration added to pyproject.toml
- [ ] mypy configuration added to pyproject.toml
- [ ] `uv run ruff check app/` runs without crashes
- [ ] `uv run ruff format app/ --check` runs (may report changes needed)
- [ ] `uv run mypy app/` runs without crashes (errors expected in legacy code)
- [ ] Per-file ignores configured for known exceptions

## Implementation Guide

### Step 1: Add configuration

Append the tool configuration sections to `pyproject.toml`.

### Step 2: Run ruff check

```bash
cd /home/rogerio/git/encadeador-service

# Check for lint issues (don't fix yet)
uv run ruff check app/

# Check formatting (don't fix yet)
uv run ruff format app/ --check --diff
```

### Step 3: Run mypy

```bash
# Check types (expect errors in legacy code)
uv run mypy app/
```

### Step 4: Document baseline

Record the number of issues for tracking:
- ruff check: X issues
- mypy: Y errors

**Note**: Do NOT fix issues in this ticket. Just establish the baseline.

## Files to Read Before Starting

- `/home/rogerio/git/flexibilizador-service/pyproject.toml` - Reference ruff/mypy config
- `app/adapters/chainingrepository.py` - Complex file that may need ignores

## Testing Requirements

### Verification

```bash
# ruff runs without crashing
uv run ruff check app/ || echo "Issues found (expected)"

# mypy runs without crashing  
uv run mypy app/ || echo "Errors found (expected)"

# Formatting check runs
uv run ruff format app/ --check || echo "Format changes needed (expected)"
```

## Definition of Done

- [ ] Tool configuration sections added to pyproject.toml
- [ ] `ruff check` runs without crashes
- [ ] `ruff format --check` runs without crashes
- [ ] `mypy` runs without crashes
- [ ] Baseline issue counts documented in PR description
- [ ] Changes committed

## Blocked By

- [TOOL-001](./ticket-001-create-pyproject-toml.md) - Needs pyproject.toml to exist

## Blocks

- [TOOL-004](./ticket-004-create-uv-lock.md) - Full config needed for final verification
