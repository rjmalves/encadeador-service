# [API-004] Update Chain Router for S3

> **Epic**: [Epic 04: API Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 02](./00-sprint-overview.md)  
> **Points**: 5  
> **Priority**: P0

## Context

### Background

The chain router currently uses base62 URI parsing and filesystem-based UnitOfWork. For S3 integration, the router needs to:
1. Detect S3 mode vs legacy mode from request
2. Create S3-aware UnitOfWork instances
3. Return S3 output keys in response

### Relation to Epic

Core change that connects S3 infrastructure to API layer.

### Current State

```python
@router.post("/")
async def chain(req: ChainingRequest, uriParser: ...):
    sources_paths = [uriParser.parse(s.id) for s in req.sources]
    destination_path = uriParser.parse(req.destination.id)
    sources_uow = [uow_factory(s.program, p) for s, p in ...]
    destination_uow = uow_factory(req.destination.program, destination_path)
    ...
```

## Specification

### File to Modify

**Path**: `app/routers/chain.py`

### Updated Router Implementation

```python
"""Chain router with S3 and legacy mode support."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from app.internal.httpresponse import HTTPResponse
from app.internal.settings import Settings
from app.internal.exceptions import (
    EncadeadorException,
    ArtifactNotFoundError,
    ChainingError,
)
from app.models.chainingrequest import ChainingRequest
from app.models.chainingresponse import ChainingResponse
from app.models.chainingcase import ChainingCase
from app.models.errors import ErrorResponse

from app.adapters.uriparserrepository import AbstractURIParsingRepository
from app.adapters.s3_repository import S3Repository
from app.services.unitofwork import factory as uow_factory
from app.services.s3_unitofwork import S3DecompUnitOfWork, S3NewaveUnitOfWork
from app.utils.temp_manager import TempDirectoryManager

from app.internal.dependencies import uriParser
from app.adapters.chainingrepository import factory as chain_factory
from app.models.program import Program

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chain",
    tags=["chain"],
)


def _get_s3_repository() -> S3Repository:
    """Get S3Repository instance."""
    return S3Repository(
        region_name=Settings.aws_region,
        endpoint_url=Settings.s3_endpoint_url,
    )


def _get_temp_manager() -> TempDirectoryManager:
    """Get TempDirectoryManager instance."""
    return TempDirectoryManager(
        base_dir=Settings.temp_dir,
        max_age_hours=Settings.max_temp_dir_age_hours,
    )


def _create_s3_uow(
    case: ChainingCase,
    role: str,
    s3_repo: S3Repository,
    temp_manager: TempDirectoryManager,
):
    """Create S3-aware UnitOfWork for a case."""
    if case.program == Program.DECOMP:
        return S3DecompUnitOfWork(
            s3_repo=s3_repo,
            bucket=case.bucket,
            execution_hash=case.execution_hash,
            temp_manager=temp_manager,
            role=role,
        )
    elif case.program == Program.NEWAVE:
        return S3NewaveUnitOfWork(
            s3_repo=s3_repo,
            bucket=case.bucket,
            execution_hash=case.execution_hash,
            temp_manager=temp_manager,
            role=role,
        )
    else:
        raise ValueError(f"Unknown program: {case.program}")


async def _chain_s3_mode(req: ChainingRequest) -> ChainingResponse:
    """
    Process chaining request in S3 mode.
    
    Downloads artifacts from S3, processes locally, uploads results.
    """
    s3_repo = _get_s3_repository()
    temp_manager = _get_temp_manager()
    
    logger.info(
        f"Processing S3 mode chaining: "
        f"sources={[s.execution_hash for s in req.sources]}, "
        f"destination={req.destination.execution_hash}"
    )
    
    # Create source UnitOfWorks (read-only)
    source_uows = [
        _create_s3_uow(s, "source", s3_repo, temp_manager)
        for s in req.sources
    ]
    
    # Create destination UnitOfWork (read-write)
    dest_uow = _create_s3_uow(
        req.destination, "destination", s3_repo, temp_manager
    )
    
    # Get chaining repository
    chain_repo = chain_factory(req.destination.program)
    
    # Execute chaining with async context managers
    async with dest_uow:
        # Enter all source contexts
        entered_sources = []
        try:
            for uow in source_uows:
                await uow.__aenter__()
                entered_sources.append(uow)
            
            # Perform chaining
            result = await chain_repo.chain(
                req.variable,
                entered_sources,
                dest_uow,
            )
            
            if isinstance(result, HTTPResponse):
                raise ChainingError(
                    result.detail,
                    {"status_code": result.code}
                )
            
        finally:
            # Exit all source contexts
            for uow in reversed(entered_sources):
                await uow.__aexit__(None, None, None)
    
    return ChainingResponse(
        result=result,
        output_key=dest_uow.output_key,
        output_bucket=req.destination.bucket,
    )


async def _chain_legacy_mode(
    req: ChainingRequest,
    uriParser: AbstractURIParsingRepository,
) -> ChainingResponse:
    """
    Process chaining request in legacy mode.
    
    Uses base62-encoded filesystem paths.
    """
    logger.info(
        f"Processing legacy mode chaining: "
        f"sources={[s.id for s in req.sources]}"
    )
    
    sources_paths = [uriParser.parse(s.id) for s in req.sources]
    destination_path = uriParser.parse(req.destination.id)
    
    for s in sources_paths:
        if isinstance(s, HTTPResponse):
            raise HTTPException(status_code=s.code, detail=s.detail)
    
    if isinstance(destination_path, HTTPResponse):
        raise HTTPException(
            status_code=destination_path.code,
            detail=destination_path.detail,
        )
    
    sources_uow = [
        uow_factory(s.program, p)
        for s, p in zip(req.sources, sources_paths)
    ]
    destination_uow = uow_factory(req.destination.program, destination_path)
    
    chain_repo = chain_factory(req.destination.program)
    result = await chain_repo.chain(req.variable, sources_uow, destination_uow)
    
    if isinstance(result, HTTPResponse):
        raise HTTPException(status_code=result.code, detail=result.detail)
    
    return ChainingResponse(result=result)


@router.post(
    "/",
    response_model=ChainingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Artifact not found"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
    summary="Chain cases",
    description="Chain variables from source case(s) to destination case"
)
async def chain(
    req: ChainingRequest,
    uriParser: AbstractURIParsingRepository = Depends(uriParser),
) -> ChainingResponse:
    """
    Chain variables from source case(s) to destination case.
    
    Supports two modes:
    - **S3 mode**: bucket + execution_hash in request
    - **Legacy mode**: base62-encoded id in request (deprecated)
    
    Args:
        req: Chaining request with sources, destination, and variable
        
    Returns:
        ChainingResponse with results and output location (S3 mode)
        
    Raises:
        HTTPException: On validation, processing, or S3 errors
    """
    # Determine mode from destination (all cases should use same mode)
    if req.destination.is_s3_mode:
        return await _chain_s3_mode(req)
    else:
        return await _chain_legacy_mode(req, uriParser)
```

### Mode Detection Logic

| Condition | Mode | Behavior |
|-----------|------|----------|
| `bucket` + `execution_hash` present | S3 | Download from S3, upload results |
| Only `id` present | Legacy | Use filesystem paths |
| Mixed modes | Error | Validate all cases use same mode |

### S3 Path Patterns

| Artifact | S3 Key Pattern |
|----------|---------------|
| Source outputs | `artifacts/{hash}/saidas/relato.*` |
| Dest deck | `artifacts/{hash}/entradas/deck_processado.zip` |
| Output | `ingest/{hash}_encadeado.zip` |

## Acceptance Criteria

- [x] Router detects S3 vs legacy mode
- [x] S3 mode downloads artifacts from S3
- [x] S3 mode uploads results to ingest prefix
- [x] Response includes output_key and output_bucket (S3 mode)
- [x] Legacy mode unchanged (backward compatible)
- [x] Proper error handling for S3 failures
- [x] Logging for mode detection and operations
- [x] OpenAPI docs reflect both modes

## Implementation Guide

### Step 1: Import new dependencies

Add imports for S3Repository, S3UnitOfWork, TempDirectoryManager.

### Step 2: Add helper functions

Add `_get_s3_repository()`, `_get_temp_manager()`, `_create_s3_uow()`.

### Step 3: Implement S3 mode handler

Add `_chain_s3_mode()` function.

### Step 4: Refactor legacy mode

Extract current logic to `_chain_legacy_mode()`.

### Step 5: Update main handler

Add mode detection and dispatch to appropriate handler.

### Step 6: Test both modes

```bash
# S3 mode
curl -X POST http://localhost:8000/chain -H "Content-Type: application/json" -d '{
  "sources": [{
    "program": "DECOMP",
    "bucket": "decomp-bucket",
    "execution_hash": "source123"
  }],
  "destination": {
    "program": "DECOMP",
    "bucket": "decomp-bucket",
    "execution_hash": "dest456"
  },
  "variable": "VARM"
}'

# Legacy mode (deprecated)
curl -X POST http://localhost:8000/chain -H "Content-Type: application/json" -d '{
  "sources": [{"program": "DECOMP", "id": "2cA3..."}],
  "destination": {"program": "DECOMP", "id": "4dB5..."},
  "variable": "VARM"
}'
```

## Files to Read Before Starting

- `app/routers/chain.py` - Current implementation
- `app/services/s3_unitofwork.py` - S3UnitOfWork classes
- `app/adapters/s3_repository.py` - S3Repository
- `app/models/chainingcase.py` - Mode detection methods

## Testing Requirements

### Unit Tests

- [x] Test mode detection (S3 vs legacy)
- [x] Test S3 mode creates correct UnitOfWork
- [x] Test legacy mode unchanged

### Integration Tests

- [x] Test full S3 flow with moto
- [x] Test error handling for missing artifacts

## Definition of Done

- [x] Router updated with mode detection
- [x] S3 mode fully implemented
- [x] Legacy mode unchanged
- [x] Error handling complete
- [x] Logging in place
- [x] Unit tests passing
- [x] Integration tests passing
- [x] Changes committed

## Blocked By

- [API-001](../sprint-01/ticket-001-update-models.md) - Updated models
- [S3-006](../../epic-03-s3-integration/sprint-02/ticket-006-create-s3-unitofwork.md) - S3UnitOfWork

## Blocks

- [API-006](./ticket-006-api-integration-tests.md) - Integration tests
