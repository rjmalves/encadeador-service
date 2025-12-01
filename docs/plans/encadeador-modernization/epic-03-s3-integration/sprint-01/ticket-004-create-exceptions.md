# [S3-004] Create exception hierarchy

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 1  
> **Priority**: P0 (Blocker)

## Context

### Background

Custom exceptions provide better error handling, clearer error messages, and enable proper HTTP status code mapping in the API layer.

### Relation to Epic

Foundation for all error handling. Must be done first in Sprint 01.

### Current State

Only generic exceptions used. No structured error hierarchy.

## Specification

### File to Create

**Path**: `app/internal/exceptions.py`

### Content

```python
"""Custom exceptions for encadeador-service."""


class EncadeadorError(Exception):
    """Base exception for all encadeador-service errors."""
    
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class S3Error(EncadeadorError):
    """S3 operation failed."""
    
    def __init__(self, message: str, bucket: str | None = None, key: str | None = None) -> None:
        details = {}
        if bucket:
            details["bucket"] = bucket
        if key:
            details["key"] = key
        super().__init__(message, details)


class ArtifactNotFoundError(EncadeadorError):
    """Required artifact not found in S3."""
    
    def __init__(self, message: str, bucket: str | None = None, key: str | None = None) -> None:
        details = {}
        if bucket:
            details["bucket"] = bucket
        if key:
            details["key"] = key
        super().__init__(message, details)


class ParseError(EncadeadorError):
    """Failed to parse DECOMP/NEWAVE file."""
    
    def __init__(self, message: str, filename: str | None = None) -> None:
        details = {}
        if filename:
            details["filename"] = filename
        super().__init__(message, details)


class ChainingError(EncadeadorError):
    """Chaining operation failed."""
    
    def __init__(self, message: str, variable: str | None = None) -> None:
        details = {}
        if variable:
            details["variable"] = variable
        super().__init__(message, details)


class ValidationError(EncadeadorError):
    """Request validation failed."""
    pass


class TempDirectoryError(EncadeadorError):
    """Temp directory operation failed."""
    pass
```

### Exception Hierarchy

```
EncadeadorError (base)
├── S3Error
│   └── ArtifactNotFoundError
├── ParseError
├── ChainingError
├── ValidationError
└── TempDirectoryError
```

### HTTP Status Code Mapping (for reference)

| Exception | HTTP Status | Error Code |
|-----------|-------------|------------|
| ValidationError | 400 | INVALID_REQUEST |
| ArtifactNotFoundError | 404 | ARTIFACT_NOT_FOUND |
| ParseError | 422 | PARSE_ERROR |
| S3Error | 500 | S3_ERROR |
| ChainingError | 500 | CHAINING_ERROR |

## Acceptance Criteria

- [ ] `app/internal/exceptions.py` created
- [ ] All exception classes defined with docstrings
- [ ] Base class stores message and details
- [ ] Imports work: `from app.internal.exceptions import EncadeadorError, S3Error`
- [ ] Type hints on all methods

## Implementation Guide

### Step 1: Create the file

Create `app/internal/exceptions.py` with the content above.

### Step 2: Verify imports

```bash
uv run python -c "
from app.internal.exceptions import (
    EncadeadorError,
    S3Error,
    ArtifactNotFoundError,
    ParseError,
    ChainingError,
    ValidationError,
    TempDirectoryError,
)
print('All exceptions imported successfully')
"
```

### Step 3: Test exception behavior

```bash
uv run python -c "
from app.internal.exceptions import S3Error, ArtifactNotFoundError

# Test S3Error
try:
    raise S3Error('Download failed', bucket='test', key='file.txt')
except S3Error as e:
    assert e.message == 'Download failed'
    assert e.details['bucket'] == 'test'
    print('S3Error works correctly')

# Test ArtifactNotFoundError
try:
    raise ArtifactNotFoundError('Not found', bucket='test', key='missing.txt')
except ArtifactNotFoundError as e:
    assert 'bucket' in e.details
    print('ArtifactNotFoundError works correctly')

print('All exception tests passed!')
"
```

## Files to Read Before Starting

- `/home/rogerio/git/flexibilizador-service/app/internal/exceptions.py` - Reference

## Testing Requirements

### Unit Tests

Create `tests/unit/test_exceptions.py`:

```python
import pytest
from app.internal.exceptions import (
    EncadeadorError,
    S3Error,
    ArtifactNotFoundError,
)


def test_encadeador_error_message():
    error = EncadeadorError("test message")
    assert str(error) == "test message"
    assert error.message == "test message"
    assert error.details == {}


def test_encadeador_error_with_details():
    error = EncadeadorError("test", details={"key": "value"})
    assert error.details == {"key": "value"}


def test_s3_error_with_bucket_key():
    error = S3Error("failed", bucket="my-bucket", key="my-key")
    assert error.details["bucket"] == "my-bucket"
    assert error.details["key"] == "my-key"


def test_artifact_not_found_is_encadeador_error():
    error = ArtifactNotFoundError("not found")
    assert isinstance(error, EncadeadorError)
```

## Definition of Done

- [ ] Exception file created
- [ ] All exception classes defined
- [ ] Imports work correctly
- [ ] Unit tests pass
- [ ] Type hints present
- [ ] Changes committed

## Blocked By

None (first ticket in sprint)

## Blocks

- [S3-001](./ticket-001-create-s3-repository.md) - Uses S3Error, ArtifactNotFoundError
- [S3-003](./ticket-003-create-temp-manager.md) - Uses TempDirectoryError
