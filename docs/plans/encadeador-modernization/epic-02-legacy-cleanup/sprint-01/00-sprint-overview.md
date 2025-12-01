# Sprint 01: Legacy Removal

> **Epic**: [Epic 02: Legacy Code Cleanup](../00-epic-overview.md)  
> **Duration**: 1 day  
> **Goal**: Remove all legacy encoding and terminal utilities  
> **Status**: ✅ Complete

## Sprint Goals

1. Remove encoding conversion code
2. Remove terminal execution utilities
3. Cleanup Settings class
4. Verify all tests pass

## Tickets

| ID | Title | Points | Status | Assignee |
|----|-------|--------|--------|----------|
| [LEGACY-001](./ticket-001-remove-encoding-utils.md) | Remove encoding utilities | 2 | ✅ | - |
| [LEGACY-002](./ticket-002-remove-terminal-utils.md) | Remove terminal utilities | 1 | ✅ | - |
| [LEGACY-003](./ticket-003-cleanup-settings.md) | Cleanup Settings class | 1 | ✅ | - |

**Total Points**: 4

## Ticket Dependencies

```
LEGACY-001 (encoding utils)
    │
    ├──► LEGACY-002 (terminal utils) ──► LEGACY-003 (settings cleanup)
```

## Definition of Done

- [ ] All legacy files deleted
- [ ] All encoding calls removed from repositories
- [ ] Settings cleaned up
- [ ] All tests pass
- [ ] No import errors with `ruff check app/`
- [ ] No remaining references to deleted modules

## Verification Commands

```bash
# Verify no remaining imports
grep -r "from app.utils.encoding" app/
grep -r "from app.utils.terminal" app/
grep -r "from app.internal.fs" app/
grep -r "from app.internal.terminal" app/
grep -r "converte_codificacao" app/
grep -r "encoding_script" app/

# All should return no results
```

## Notes

- Order matters: Remove calls BEFORE deleting files
- Run tests after each deletion
- These files have been unused since migration to UTF-8
