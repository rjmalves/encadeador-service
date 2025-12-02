"""Chain router with S3 and legacy mode support."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.chainingrepository import factory as chain_factory
from app.adapters.s3_repository import get_s3_repository
from app.adapters.uriparserrepository import AbstractURIParsingRepository
from app.internal.dependencies import uriParser
from app.internal.exceptions import ChainingError
from app.internal.httpresponse import HTTPResponse
from app.models.chainingcase import ChainingCase
from app.models.chainingrequest import ChainingRequest
from app.models.chainingresponse import ChainingResponse
from app.models.errors import ErrorResponse
from app.services.s3_unitofwork import s3_unitofwork_factory
from app.services.unitofwork import AbstractUnitOfWork
from app.services.unitofwork import factory as uow_factory

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chain",
    tags=["chain"],
)


def _create_s3_uow(
    case: ChainingCase,
    role: str,
) -> AbstractUnitOfWork:
    """Create S3-aware UnitOfWork for a case."""
    s3_repo = get_s3_repository()
    return s3_unitofwork_factory(
        program=case.program,
        s3_repo=s3_repo,
        bucket=case.bucket,  # type: ignore
        execution_hash=case.execution_hash,  # type: ignore
        role=role,
    )


async def _chain_s3_mode(req: ChainingRequest) -> ChainingResponse:
    """
    Process chaining request in S3 mode.

    Downloads artifacts from S3, processes locally, uploads results.
    """
    logger.info(
        f"Processing S3 mode chaining: "
        f"sources={[s.execution_hash for s in req.sources]}, "
        f"destination={req.destination.execution_hash}"
    )

    # Create source UnitOfWorks (read-only)
    source_uows = [_create_s3_uow(s, "source") for s in req.sources]

    # Create destination UnitOfWork (read-write)
    dest_uow = _create_s3_uow(req.destination, "destination")

    # Get chaining repository
    chain_repo = chain_factory(req.destination.program)

    # Execute chaining with async context managers
    async with dest_uow:
        # Enter all source contexts
        entered_sources: list[AbstractUnitOfWork] = []
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
                raise ChainingError(result.detail, {"status_code": result.code})

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
        f"Processing legacy mode chaining: sources={[s.id for s in req.sources]}"
    )

    # In legacy mode, id is guaranteed to be set by validation
    sources_paths = [uriParser.parse(s.id) for s in req.sources]  # type: ignore[arg-type]
    destination_path = uriParser.parse(req.destination.id)  # type: ignore[arg-type]

    for s in sources_paths:
        if isinstance(s, HTTPResponse):
            raise HTTPException(status_code=s.code, detail=s.detail)

    if isinstance(destination_path, HTTPResponse):
        raise HTTPException(
            status_code=destination_path.code, detail=destination_path.detail
        )

    sources_uow = [
        uow_factory(s.program, p)
        for s, p in zip(req.sources, sources_paths, strict=True)
    ]
    destination_uow = uow_factory(req.destination.program, destination_path)

    chain_repo = chain_factory(req.destination.program)
    result = await chain_repo.chain(req.variable, sources_uow, destination_uow)

    if isinstance(result, HTTPResponse):
        raise HTTPException(status_code=result.code, detail=result.detail)

    return ChainingResponse(result=result, output_key=None, output_bucket=None)


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
    description="Chain variables from source case(s) to destination case",
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
