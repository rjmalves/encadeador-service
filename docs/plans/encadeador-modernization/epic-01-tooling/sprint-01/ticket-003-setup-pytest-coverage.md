# [TOOL-003] Setup pytest with coverage

> **Epic**: [Epic 01: Tooling Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P1

## Context

### Background

Configure pytest with coverage reporting to establish baseline test metrics. This enables tracking test coverage improvements throughout the modernization.

### Relation to Epic

Part of tooling modernization. Required for CI/CD and quality gates.

### Current State

Tests exist in `tests/` directory but no coverage configuration.

## Specification

### Add to pyproject.toml

Append the following sections to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]

[tool.coverage.run]
source = ["app"]
branch = true
omit = [
    "app/__pycache__/*",
    "tests/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
show_missing = true
fail_under = 0  # No minimum for now, establish baseline first
```

### Configuration Rationale

| Setting | Value | Reason |
|---------|-------|--------|
| `asyncio_mode = "auto"` | auto | Automatic async test detection |
| `addopts = "-v --tb=short"` | verbose, short traceback | Clear test output |
| `branch = true` | Yes | Track branch coverage |
| `fail_under = 0` | 0% | Establish baseline first |

## Acceptance Criteria

- [ ] pytest configuration added to pyproject.toml
- [ ] coverage configuration added to pyproject.toml
- [ ] `uv run pytest` runs all tests
- [ ] `uv run pytest --cov=app` generates coverage report
- [ ] All existing tests pass
- [ ] Baseline coverage percentage documented

## Implementation Guide

### Step 1: Add configuration

Append pytest and coverage sections to `pyproject.toml`.

### Step 2: Run tests

```bash
cd /home/rogerio/git/encadeador-service

# Run tests with verbose output
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML report (optional)
uv run pytest tests/ --cov=app --cov-report=html
```

### Step 3: Document baseline

Record baseline coverage for tracking:
```
Current Coverage: XX%
- app/adapters/: XX%
- app/routers/: XX%
- app/services/: XX%
- app/models/: XX%
```

## Files to Read Before Starting

- `tests/conftest.py` - Existing test fixtures
- `tests/app/` - Existing test structure
- `/home/rogerio/git/flexibilizador-service/pyproject.toml` - Reference pytest config

## Testing Requirements

### Verification

```bash
# All tests pass
uv run pytest tests/ -v

# Coverage runs
uv run pytest tests/ --cov=app --cov-report=term-missing

# Async tests work
uv run pytest tests/ -v -k "async" || echo "No async tests yet"
```

## Definition of Done

- [ ] pytest configuration added to pyproject.toml
- [ ] coverage configuration added to pyproject.toml
- [ ] All existing tests pass
- [ ] Coverage report generates successfully
- [ ] Baseline coverage documented in PR
- [ ] Changes committed

## Blocked By

- [TOOL-001](./ticket-001-create-pyproject-toml.md) - Needs pyproject.toml

## Blocks

- [TOOL-004](./ticket-004-create-uv-lock.md) - Full config needed for verification
