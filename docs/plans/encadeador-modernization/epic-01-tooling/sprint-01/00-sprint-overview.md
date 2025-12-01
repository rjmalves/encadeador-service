# Sprint 01: Tooling Setup

> **Epic**: [Epic 01: Tooling Modernization](../00-epic-overview.md)  
> **Duration**: 1 day  
> **Goal**: Establish modern Python tooling foundation  
> **Status**: ✅ Complete

## Sprint Goals

1. Replace requirements.txt with pyproject.toml
2. Configure linting and type checking
3. Verify all existing tests still pass

## Tickets

| ID | Title | Points | Status | Assignee |
|----|-------|--------|--------|----------|
| [TOOL-001](./ticket-001-create-pyproject-toml.md) | Create pyproject.toml | 2 | ✅ | - |
| [TOOL-002](./ticket-002-configure-ruff-mypy.md) | Configure ruff and mypy | 1 | ✅ | - |
| [TOOL-003](./ticket-003-setup-pytest-coverage.md) | Setup pytest with coverage | 1 | ✅ | - |
| [TOOL-004](./ticket-004-create-uv-lock.md) | Create uv.lock and verify | 1 | ✅ | - |

**Total Points**: 5

## Ticket Dependencies

```
TOOL-001 (pyproject.toml)
    │
    ├──► TOOL-002 (ruff/mypy config)
    │
    └──► TOOL-003 (pytest config)
              │
              └──► TOOL-004 (uv.lock + verify)
```

## Definition of Done

- [ ] All tickets completed and merged
- [ ] `uv sync --all-extras` succeeds
- [ ] `uv run pytest` passes all existing tests
- [ ] `uv run ruff check app/` runs without crashes
- [ ] `uv run mypy app/` runs without crashes
- [ ] Old requirements files deleted
- [ ] No regressions in functionality

## Notes

- This sprint has no external dependencies
- All tickets can be done by a single developer in sequence
- Reference flexibilizador-service for proven configurations
