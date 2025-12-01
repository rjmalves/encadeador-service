# [API-001] Update Request/Response Models

> **Epic**: [Epic 04: API Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 3  
> **Priority**: P0  
> **Status**: ✅ Complete

## Context

### Background

The current API uses base62-encoded filesystem paths in the `id` field. For S3 integration, the API needs to accept `bucket` and `execution_hash` instead, making the contract clearer and enabling S3 artifact access.

### Relation to Epic

Foundation for the new API contract. All other API changes depend on this.

### Current State

Current request model:
```python
class ChainingCase(BaseModel):
    id: str  # base62-encoded path like "2cA3..."
    program: Program
```

## Specification

### Files to Modify

- `app/models/chainingcase.py`
- `app/models/chainingrequest.py`
- `app/models/chainingresponse.py`

### New ChainingCase Model

**Path**: `app/models/chainingcase.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from app.models.program import Program


class ChainingCase(BaseModel):
    """
    Case reference for chaining operations.
    
    Supports two modes:
    1. S3 mode: bucket + execution_hash
    2. Legacy mode: id (base62 path) - deprecated
    
    Examples:
        S3 mode:
        >>> case = ChainingCase(
        ...     program=Program.DECOMP,
        ...     bucket="decomp-bucket",
        ...     execution_hash="abc123def456"
        ... )
        
        Legacy mode (deprecated):
        >>> case = ChainingCase(
        ...     program=Program.DECOMP,
        ...     id="2cA3xY..."
        ... )
    """
    
    program: Program = Field(..., description="Program type (DECOMP or NEWAVE)")
    
    # S3 mode (preferred)
    bucket: Optional[str] = Field(
        None, 
        description="S3 bucket containing artifacts",
        examples=["decomp-bucket", "newave-bucket"]
    )
    execution_hash: Optional[str] = Field(
        None,
        description="Unique execution identifier",
        examples=["abc123def456", "xyz789ghi012"],
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    
    # Legacy mode (deprecated)
    id: Optional[str] = Field(
        None,
        deprecated=True,
        description="Base62-encoded filesystem path (deprecated, use bucket + execution_hash)"
    )
    
    @property
    def is_s3_mode(self) -> bool:
        """Check if case uses S3 mode."""
        return self.bucket is not None and self.execution_hash is not None
    
    @property
    def is_legacy_mode(self) -> bool:
        """Check if case uses legacy mode."""
        return self.id is not None and not self.is_s3_mode
    
    def model_post_init(self, __context) -> None:
        """Validate that either S3 or legacy mode is specified."""
        if self.is_s3_mode and self.id:
            # Both specified - prefer S3 mode, ignore id
            pass
        elif not self.is_s3_mode and not self.is_legacy_mode:
            raise ValueError(
                "Must specify either (bucket + execution_hash) or id"
            )
```

### Updated ChainingRequest Model

**Path**: `app/models/chainingrequest.py`

```python
from pydantic import BaseModel, Field
from typing import List
from app.models.chainingcase import ChainingCase
from app.models.chainingvariable import ChainingVariable


class ChainingRequest(BaseModel):
    """
    Request model for chaining operations.
    
    Chains variables from source case(s) to destination case.
    
    Example:
        >>> request = ChainingRequest(
        ...     sources=[ChainingCase(
        ...         program=Program.DECOMP,
        ...         bucket="decomp-bucket",
        ...         execution_hash="source123"
        ...     )],
        ...     destination=ChainingCase(
        ...         program=Program.DECOMP,
        ...         bucket="decomp-bucket",
        ...         execution_hash="dest456"
        ...     ),
        ...     variable=ChainingVariable.VARM
        ... )
    """
    
    sources: List[ChainingCase] = Field(
        ...,
        description="Source cases to chain from",
        min_length=1
    )
    destination: ChainingCase = Field(
        ...,
        description="Destination case to chain into"
    )
    variable: ChainingVariable = Field(
        ...,
        description="Variable type to chain"
    )
```

### Updated ChainingResponse Model

**Path**: `app/models/chainingresponse.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.chainingresult import ChainingResult


class ChainingResponse(BaseModel):
    """
    Response model for chaining operations.
    
    Contains results and optionally the S3 key of the output artifact.
    
    Example:
        >>> response = ChainingResponse(
        ...     result=[ChainingResult(...)],
        ...     output_key="ingest/abc123_encadeado.zip"
        ... )
    """
    
    result: List[ChainingResult] = Field(
        ...,
        description="List of chaining results"
    )
    output_key: Optional[str] = Field(
        None,
        description="S3 key of the output artifact (for S3 mode)",
        examples=["ingest/abc123_encadeado.zip"]
    )
    output_bucket: Optional[str] = Field(
        None,
        description="S3 bucket of the output artifact (for S3 mode)",
        examples=["decomp-bucket"]
    )
```

### OpenAPI Schema Examples

Add examples to improve API documentation:

```python
# In chainingrequest.py
class ChainingRequest(BaseModel):
    # ... fields ...
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sources": [{
                        "program": "DECOMP",
                        "bucket": "decomp-bucket",
                        "execution_hash": "abc123"
                    }],
                    "destination": {
                        "program": "DECOMP",
                        "bucket": "decomp-bucket",
                        "execution_hash": "def456"
                    },
                    "variable": "VARM"
                }
            ]
        }
    }
```

## Acceptance Criteria

- [ ] `ChainingCase` supports both S3 and legacy modes
- [ ] Validation ensures one mode is specified
- [ ] S3 mode is preferred when both specified
- [ ] `ChainingResponse` includes output_key and output_bucket
- [ ] OpenAPI docs show correct schema
- [ ] Backward compatible with legacy requests
- [ ] Type hints on all fields
- [ ] Field descriptions for docs

## Implementation Guide

### Step 1: Update ChainingCase

Modify `app/models/chainingcase.py` with new fields and validation.

### Step 2: Update ChainingRequest

Add field constraints and examples to `app/models/chainingrequest.py`.

### Step 3: Update ChainingResponse

Add output fields to `app/models/chainingresponse.py`.

### Step 4: Test model validation

```python
# Test S3 mode
case = ChainingCase(
    program=Program.DECOMP,
    bucket="decomp-bucket",
    execution_hash="abc123"
)
assert case.is_s3_mode

# Test legacy mode
case = ChainingCase(
    program=Program.DECOMP,
    id="2cA3xY"
)
assert case.is_legacy_mode

# Test validation error
try:
    case = ChainingCase(program=Program.DECOMP)  # Should fail
except ValueError:
    pass
```

### Step 5: Verify OpenAPI docs

Start server and check `/docs`:
```bash
uv run uvicorn app.app:app --reload
# Visit http://localhost:8000/docs
```

## Files to Read Before Starting

- `app/models/chainingcase.py` - Current model
- `app/models/chainingrequest.py` - Current model
- `app/models/chainingresponse.py` - Current model
- `app/models/program.py` - Program enum

## Testing Requirements

### Unit Tests

- [ ] Test S3 mode validation
- [ ] Test legacy mode validation
- [ ] Test validation error when neither mode
- [ ] Test S3 mode preferred when both specified
- [ ] Test response model serialization

## Definition of Done

- [ ] Models updated with new fields
- [ ] Backward compatibility preserved
- [ ] OpenAPI schema correct
- [ ] Unit tests passing
- [ ] Changes committed

## Blocked By

- [Epic 03: S3 Integration](../../epic-03-s3-integration/00-epic-overview.md) - S3 infrastructure

## Blocks

- [API-004](../sprint-02/ticket-004-update-chain-router.md) - Router uses models
