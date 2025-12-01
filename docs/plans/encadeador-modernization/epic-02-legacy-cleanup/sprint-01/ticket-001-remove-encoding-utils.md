# [LEGACY-001] Remove encoding utilities

> **Epic**: [Epic 02: Legacy Code Cleanup](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0

## Context

### Background

The `converte_codificacao` function in `app/utils/encoding.py` was used to convert DECOMP/NEWAVE files from various encodings (ISO-8859-1, etc.) to UTF-8. Since all files are now natively UTF-8, this code is dead weight that adds latency and complexity.

### Relation to Epic

Primary cleanup task. Removes the most significant legacy code path.

### Current State

```python
# app/adapters/decomprepository.py (lines ~130-140)
caminho = str(pathlib.Path(self.__path).joinpath(arq_dadger))
script = str(
    pathlib.Path(Settings.installdir).joinpath(
        Settings.encoding_script
    )
)
await converte_codificacao(caminho, script)  # ← REMOVE THIS
```

## Specification

### Changes Required

#### 1. Modify `app/adapters/decomprepository.py`

**Remove import** (line ~18):
```python
# DELETE this line:
from app.utils.encoding import converte_codificacao
```

**In `get_dadger()` method** (~line 130-140):

BEFORE:
```python
async def get_dadger(self) -> Union[Dadger, HTTPResponse]:
    if self.__read_dadger is False:
        self.__read_dadger = True
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_dadger = arq.dadger
            if not arq_dadger:
                raise FileNotFoundError()
            caminho = str(pathlib.Path(self.__path).joinpath(arq_dadger))
            script = str(
                pathlib.Path(Settings.installdir).joinpath(
                    Settings.encoding_script
                )
            )
            await converte_codificacao(caminho, script)  # REMOVE
            Log.log().info(f"Lendo arquivo {arq_dadger}")
            self.__dadger = Dadger.read(join(self.__path, arq_dadger))
```

AFTER:
```python
async def get_dadger(self) -> Union[Dadger, HTTPResponse]:
    if self.__read_dadger is False:
        self.__read_dadger = True
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_dadger = arq.dadger
            if not arq_dadger:
                raise FileNotFoundError()
            Log.log().info(f"Lendo arquivo {arq_dadger}")
            self.__dadger = Dadger.read(join(self.__path, arq_dadger))
```

**Same change in `get_dadgnl()` method** (~line 170-185).

#### 2. Modify `app/adapters/newaverepository.py`

**Remove import**:
```python
# DELETE this line:
from app.utils.encoding import converte_codificacao
```

**In `get_dger()` method**: Remove the same encoding block pattern.

#### 3. Delete `app/utils/encoding.py`

```bash
rm app/utils/encoding.py
```

#### 4. Delete `app/static/converte_utf8.sh` (if exists)

```bash
rm -f app/static/converte_utf8.sh
```

## Acceptance Criteria

- [ ] `converte_codificacao` import removed from `decomprepository.py`
- [ ] `converte_codificacao` import removed from `newaverepository.py`
- [ ] Encoding conversion code blocks removed from both repositories
- [ ] `app/utils/encoding.py` deleted
- [ ] `app/static/converte_utf8.sh` deleted
- [ ] No import errors: `uv run python -c "from app.adapters.decomprepository import RawDecompRepository"`
- [ ] All tests pass: `uv run pytest`

## Implementation Guide

### Step 1: Find all usages

```bash
cd /home/rogerio/git/encadeador-service

# Find imports
grep -rn "converte_codificacao" app/
grep -rn "from app.utils.encoding" app/
```

### Step 2: Modify decomprepository.py

Edit `app/adapters/decomprepository.py`:
1. Remove the import line
2. Remove the encoding block from `get_dadger()`
3. Remove the encoding block from `get_dadgnl()`
4. Remove `import pathlib` if no longer needed

### Step 3: Modify newaverepository.py

Edit `app/adapters/newaverepository.py`:
1. Remove the import line
2. Remove the encoding block from `get_dger()`
3. Remove `import pathlib` if no longer needed

### Step 4: Test after modifications

```bash
# Verify imports still work
uv run python -c "
from app.adapters.decomprepository import RawDecompRepository
from app.adapters.newaverepository import RawNewaveRepository
print('Imports OK')
"

# Run tests
uv run pytest tests/ -v
```

### Step 5: Delete files

```bash
rm app/utils/encoding.py
rm -f app/static/converte_utf8.sh
```

### Step 6: Final verification

```bash
# Verify no remaining references
grep -r "converte_codificacao" app/ && echo "FAIL: References remain" || echo "OK"
grep -r "encoding.py" app/ && echo "FAIL: References remain" || echo "OK"

# Run tests again
uv run pytest tests/ -v
```

## Files to Read Before Starting

- `app/adapters/decomprepository.py` - Lines containing encoding calls
- `app/adapters/newaverepository.py` - Lines containing encoding calls
- `app/utils/encoding.py` - Understand what's being removed

## Testing Requirements

### Unit Tests

```bash
# Existing tests should pass
uv run pytest tests/app/adapters/test_decomprepository.py -v
uv run pytest tests/app/adapters/test_newaverepository.py -v
```

### Integration Verification

```bash
# Application still starts
uv run python -c "from app.app import make_app; print(make_app())"
```

## Definition of Done

- [ ] Import statements removed
- [ ] Encoding conversion code removed
- [ ] Files deleted
- [ ] All tests pass
- [ ] No remaining references
- [ ] Changes committed

## Blocked By

- [Epic 01: Tooling](../../epic-01-tooling/00-epic-overview.md) - Need pytest working

## Blocks

- [LEGACY-002](./ticket-002-remove-terminal-utils.md) - encoding.py uses terminal.py
- [LEGACY-003](./ticket-003-cleanup-settings.md) - Removes encoding_script reference
