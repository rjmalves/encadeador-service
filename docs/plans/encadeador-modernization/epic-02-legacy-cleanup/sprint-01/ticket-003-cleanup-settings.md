# [LEGACY-003] Cleanup Settings class

> **Epic**: [Epic 02: Legacy Code Cleanup](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P0

## Context

### Background

The `Settings` class in `app/internal/settings.py` contains the `encoding_script` attribute that pointed to the now-deleted encoding conversion script. This must be removed to complete the legacy cleanup.

### Relation to Epic

Final cleanup ticket for Epic 02. Removes the last traces of encoding infrastructure.

### Current State

```python
# app/internal/settings.py
class Settings:
    clusterId = os.getenv("CLUSTER_ID", "0")
    basedir = os.getenv("APP_BASEDIR", os.curdir)
    installdir = os.getenv("APP_INSTALLDIR", "/usr/local/bin")
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "80"))
    root_path = os.getenv("ROOT_PATH", "/")
    newave_source = os.getenv("NEWAVE_SOURCE", "FS")
    decomp_source = os.getenv("DECOMP_SOURCE", "FS")
    encoding_script = "app/static/converte_utf8.sh"  # ← REMOVE
    uri_pattern = os.getenv("URI_PATTERN", "BASE62")

    @classmethod
    def read_environments(cls):
        # ... all the same assignments ...
        cls.encoding_script = "app/static/converte_utf8.sh"  # ← REMOVE
```

## Specification

### Changes to `app/internal/settings.py`

**Remove from class attributes**:
```python
# DELETE this line:
encoding_script = "app/static/converte_utf8.sh"
```

**Remove from `read_environments()` method**:
```python
# DELETE this line:
cls.encoding_script = "app/static/converte_utf8.sh"
```

### Final Settings Class

```python
import os


class Settings:
    clusterId = os.getenv("CLUSTER_ID", "0")
    basedir = os.getenv("APP_BASEDIR", os.curdir)
    installdir = os.getenv("APP_INSTALLDIR", "/usr/local/bin")
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "80"))
    root_path = os.getenv("ROOT_PATH", "/")
    newave_source = os.getenv("NEWAVE_SOURCE", "FS")
    decomp_source = os.getenv("DECOMP_SOURCE", "FS")
    uri_pattern = os.getenv("URI_PATTERN", "BASE62")

    @classmethod
    def read_environments(cls):
        cls.clusterId = os.getenv("CLUSTER_ID", "0")
        cls.basedir = os.getenv("APP_BASEDIR", os.curdir)
        cls.installdir = os.getenv("APP_INSTALLDIR", "/usr/local/bin")
        cls.host = os.getenv("HOST", "localhost")
        cls.port = int(os.getenv("PORT", "80"))
        cls.root_path = os.getenv("ROOT_PATH", "/")
        cls.newave_source = os.getenv("NEWAVE_SOURCE", "FS")
        cls.decomp_source = os.getenv("DECOMP_SOURCE", "FS")
        cls.uri_pattern = os.getenv("URI_PATTERN", "BASE62")
```

## Acceptance Criteria

- [ ] `encoding_script` class attribute removed
- [ ] `encoding_script` assignment in `read_environments()` removed
- [ ] No references to `encoding_script` anywhere in codebase
- [ ] `Settings` class still works: `uv run python -c "from app.internal.settings import Settings; print(Settings.host)"`
- [ ] All tests pass

## Implementation Guide

### Step 1: Verify no remaining references

```bash
cd /home/rogerio/git/encadeador-service

# Should return nothing after LEGACY-001
grep -rn "encoding_script" app/
grep -rn "Settings.encoding_script" app/
```

### Step 2: Edit settings.py

Remove the two lines containing `encoding_script`.

### Step 3: Verify

```bash
# Settings still works
uv run python -c "
from app.internal.settings import Settings
Settings.read_environments()
print(f'Host: {Settings.host}')
print(f'Port: {Settings.port}')
print('Settings OK')
"

# No encoding_script attribute
uv run python -c "
from app.internal.settings import Settings
assert not hasattr(Settings, 'encoding_script'), 'encoding_script still exists!'
print('encoding_script removed successfully')
"

# Tests pass
uv run pytest tests/ -v
```

### Step 4: Commit

```bash
git add -A
git commit -m "chore: remove legacy encoding infrastructure

- Remove encoding_script from Settings
- Delete app/utils/encoding.py
- Delete app/utils/terminal.py
- Delete app/internal/fs.py
- Delete app/internal/terminal.py
- Remove encoding conversion from repositories

All files are now UTF-8; encoding conversion was no-op."
```

## Files to Read Before Starting

- `app/internal/settings.py` - Current state

## Testing Requirements

### Verification

```bash
# Settings works
uv run python -c "from app.internal.settings import Settings; Settings.read_environments()"

# Application starts
uv run python -c "from app.app import make_app; print(make_app())"

# All tests pass
uv run pytest tests/ -v
```

## Definition of Done

- [ ] `encoding_script` removed from Settings
- [ ] No remaining references in codebase
- [ ] Settings class works correctly
- [ ] All tests pass
- [ ] Epic 02 complete
- [ ] Changes committed

## Blocked By

- [LEGACY-001](./ticket-001-remove-encoding-utils.md)
- [LEGACY-002](./ticket-002-remove-terminal-utils.md)

## Blocks

- [Epic 03: S3 Integration](../../epic-03-s3-integration/00-epic-overview.md) - Clean codebase for S3 work
