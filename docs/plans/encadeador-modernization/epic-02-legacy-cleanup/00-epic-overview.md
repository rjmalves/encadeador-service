# Epic 02: Legacy Code Cleanup

> **Epic Owner**: TBD  
> **Duration**: 1 day  
> **Status**: ✅ Complete

## Summary

Remove legacy encoding conversion and terminal utilities that are no longer needed. All DECOMP/NEWAVE files are now UTF-8, eliminating the need for charset conversion. This reduces code complexity and removes unused dependencies.

## Business Value

- Reduced codebase complexity (~140 lines removed)
- Eliminated dead code paths
- Faster file operations (no encoding detection)
- Cleaner dependency graph

## Scope

### Included

- Delete unused utility files (`encoding.py`, `terminal.py`, `fs.py`)
- Remove encoding conversion calls from repositories
- Remove `encoding_script` setting
- Update imports and `__init__.py` files

### Excluded

- Modifying core chaining logic
- Changing file parsing behavior
- Adding new functionality

## Dependencies

| Type | Dependency | Description |
|------|------------|-------------|
| **Requires** | Epic 01 (Tooling) | Need ruff/pytest for validation |
| **Enables** | Epic 03 (S3) | Clean base for S3 integration |

## Acceptance Criteria

- [x] `app/internal/fs.py` deleted
- [x] `app/internal/terminal.py` deleted
- [x] `app/utils/encoding.py` deleted
- [x] `app/utils/terminal.py` deleted
- [x] `app/static/converte_utf8.sh` deleted
- [x] `converte_codificacao` calls removed from `decomprepository.py`
- [x] `converte_codificacao` calls removed from `newaverepository.py`
- [x] `encoding_script` removed from `Settings`
- [x] All existing tests pass
- [x] `ruff check app/` shows no import errors

## Sprint Breakdown

### Sprint 01 (1 day)

| Ticket ID | Title | Points | Priority |
|-----------|-------|--------|----------|
| [LEGACY-001](./sprint-01/ticket-001-remove-encoding-utils.md) | Remove encoding utilities | 2 | P0 |
| [LEGACY-002](./sprint-01/ticket-002-remove-terminal-utils.md) | Remove terminal utilities | 1 | P0 |
| [LEGACY-003](./sprint-01/ticket-003-cleanup-settings.md) | Cleanup Settings class | 1 | P0 |

**Sprint Total**: 4 points

## Technical Approach

1. **Impact Analysis**: Identify all usages before deletion
2. **Sequential Removal**: Remove calls before deleting files
3. **Test After Each Change**: Ensure tests pass at each step
4. **Verify No Regressions**: Full test suite after completion

## Files Affected

### Files to Delete

| File | Lines | Purpose | Safe to Delete? |
|------|-------|---------|-----------------|
| `app/internal/fs.py` | ~20 | Directory context manager | ✅ Unused |
| `app/internal/terminal.py` | ~53 | Terminal execution | ✅ Unused |
| `app/utils/encoding.py` | ~20 | Charset conversion | ✅ UTF-8 now |
| `app/utils/terminal.py` | ~53 | Duplicate utilities | ✅ Unused |
| `app/static/converte_utf8.sh` | ~10 | Shell script | ✅ UTF-8 now |

### Files to Modify

| File | Change |
|------|--------|
| `app/adapters/decomprepository.py` | Remove encoding calls |
| `app/adapters/newaverepository.py` | Remove encoding calls |
| `app/internal/settings.py` | Remove `encoding_script` |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking file parsing | Files are already UTF-8; encoding was no-op |
| Missing usages | grep for all imports before deletion |
| Test failures | Run tests after each file deletion |

## Estimated Effort

**Total**: 4 story points / 1 day
**Confidence**: High (straightforward deletions with clear scope)
