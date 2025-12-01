# [LEGACY-002] Remove terminal utilities

> **Epic**: [Epic 02: Legacy Code Cleanup](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P0

## Context

### Background

Terminal utility files (`app/utils/terminal.py` and `app/internal/terminal.py`) were used for executing shell commands, primarily for the encoding conversion script. With encoding conversion removed, these are unused.

Additionally, `app/internal/fs.py` contains a directory context manager that is not used anywhere.

### Relation to Epic

Secondary cleanup after encoding removal. Removes supporting utilities.

### Current State

```
app/
├── internal/
│   ├── fs.py          # set_directory context manager (UNUSED)
│   └── terminal.py    # run_terminal functions (UNUSED)
└── utils/
    └── terminal.py    # Duplicate terminal functions (UNUSED)
```

## Specification

### Files to Delete

| File | Lines | Content | Used By |
|------|-------|---------|---------|
| `app/internal/fs.py` | 20 | `set_directory` context manager | Nothing |
| `app/internal/terminal.py` | 53 | `run_terminal`, `run_terminal_retry` | encoding.py (deleted) |
| `app/utils/terminal.py` | 53 | Duplicate of internal/terminal.py | encoding.py (deleted) |

### Pre-deletion Verification

```bash
# Verify no imports exist
grep -rn "from app.internal.fs import" app/
grep -rn "from app.internal.terminal import" app/
grep -rn "from app.utils.terminal import" app/

# All should return empty (except the files themselves)
```

## Acceptance Criteria

- [ ] Verified no remaining imports of these modules
- [ ] `app/internal/fs.py` deleted
- [ ] `app/internal/terminal.py` deleted
- [ ] `app/utils/terminal.py` deleted
- [ ] No import errors in application
- [ ] All tests pass

## Implementation Guide

### Step 1: Verify no usages

```bash
cd /home/rogerio/git/encadeador-service

# Search for imports (should be empty after LEGACY-001)
grep -rn "from app.internal.fs" app/
grep -rn "from app.internal.terminal" app/
grep -rn "from app.utils.terminal" app/
grep -rn "set_directory" app/
grep -rn "run_terminal" app/
```

### Step 2: Delete files

```bash
rm app/internal/fs.py
rm app/internal/terminal.py
rm app/utils/terminal.py
```

### Step 3: Update __init__.py files (if needed)

Check if these modules are exported in `__init__.py`:

```bash
cat app/internal/__init__.py
cat app/utils/__init__.py
```

Remove any references to deleted modules.

### Step 4: Verify

```bash
# Check imports still work
uv run python -c "
from app.internal.settings import Settings
from app.internal.httpresponse import HTTPResponse
from app.utils.log import Log
print('Imports OK')
"

# Run tests
uv run pytest tests/ -v
```

## Files to Read Before Starting

- `app/internal/fs.py` - Confirm unused
- `app/internal/terminal.py` - Confirm unused
- `app/utils/terminal.py` - Confirm unused

## Testing Requirements

### Verification

```bash
# Application starts
uv run python -c "from app.app import make_app; print('OK')"

# Tests pass
uv run pytest tests/ -v

# No dangling imports
uv run ruff check app/ 2>&1 | grep -i "import" || echo "No import issues"
```

## Definition of Done

- [ ] No remaining usages verified
- [ ] All three files deleted
- [ ] `__init__.py` files updated if needed
- [ ] All tests pass
- [ ] Application starts correctly
- [ ] Changes committed

## Blocked By

- [LEGACY-001](./ticket-001-remove-encoding-utils.md) - encoding.py imports terminal.py

## Blocks

- [LEGACY-003](./ticket-003-cleanup-settings.md) - Complete cleanup before settings
