"""
S3-aware Unit of Work implementations.

This module provides UnitOfWork classes that download artifacts from S3,
process them locally, and upload results back to S3.
"""

from pathlib import Path

from app.adapters.decomprepository import (
    AbstractDecompRepository,
    RawDecompRepository,
)
from app.adapters.newaverepository import (
    AbstractNewaveRepository,
    RawNewaveRepository,
)
from app.adapters.s3_repository import S3Repository
from app.internal.exceptions import ArtifactNotFoundError
from app.internal.settings import Settings
from app.models.program import Program
from app.services.unitofwork import AbstractUnitOfWork
from app.utils.log import Log
from app.utils.temp_manager import async_temp_directory
from app.utils.zip_utils import create_zip, extract_zip


class S3DecompUnitOfWork(AbstractUnitOfWork):
    """
    Unit of Work for DECOMP operations with S3 storage.

    Downloads artifacts from S3, processes locally, uploads results.

    Example:
        async with S3DecompUnitOfWork(
            s3_repo=s3_repo,
            bucket="decomp-bucket",
            execution_hash="abc123",
            role="destination",
        ) as uow:
            # Access files through uow.files
            dadger = await uow.files.get_dadger()
    """

    def __init__(
        self,
        s3_repo: S3Repository,
        bucket: str,
        execution_hash: str,
        role: str = "destination",
    ) -> None:
        """
        Initialize S3 DECOMP unit of work.

        Args:
            s3_repo: S3Repository instance
            bucket: S3 bucket name
            execution_hash: Execution identifier
            role: "source" (read-only outputs) or "destination" (full deck, read-write)
        """
        self._s3_repo = s3_repo
        self._bucket = bucket
        self._execution_hash = execution_hash
        self._role = role
        self._temp_dir: Path | None = None
        self._decomp: RawDecompRepository | None = None
        self._output_key: str | None = None
        self._temp_context = None

    async def __aenter__(self) -> "S3DecompUnitOfWork":
        """Enter context: download artifacts and setup repository."""
        # Create temp directory using async context manager
        self._temp_context = async_temp_directory(
            base_dir=Settings.temp_dir,
            prefix=f"decomp_{self._execution_hash[:8]}_",
        )
        self._temp_dir = await self._temp_context.__aenter__()

        # Download artifacts based on role
        await self._download_artifacts()

        # Create repository pointing to temp directory
        self._decomp = RawDecompRepository(str(self._temp_dir))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context: upload if destination, always cleanup."""
        # If destination and no error, upload modified files
        if self._role == "destination" and exc_type is None:
            await self._upload_results()

        # Cleanup temp directory
        if self._temp_context:
            await self._temp_context.__aexit__(exc_type, exc_val, exc_tb)

    async def _download_artifacts(self) -> None:
        """Download required artifacts from S3."""
        if self._role == "source":
            await self._download_source_outputs()
        else:
            await self._download_destination_deck()

    async def _download_source_outputs(self) -> None:
        """
        Download source output files (relato, relgnl).

        For source cases, we need the output files from a previous execution
        to read chaining data (volumes, GNL dispatch, etc).
        """
        assert self._temp_dir is not None

        # First download caso.dat to determine file extension
        caso_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/saidas/caso.dat"
        caso_path = self._temp_dir / "caso.dat"

        try:
            await self._s3_repo.download_file(self._bucket, caso_key, str(caso_path))
        except ArtifactNotFoundError:
            # Try from entradas if not in saidas
            caso_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/entradas/caso.dat"
            await self._s3_repo.download_file(self._bucket, caso_key, str(caso_path))

        # Read caso.dat to get file extension
        with open(caso_path) as f:
            ext = f.read().strip()

        Log.log().info(f"Source case extension: {ext}")

        # Download relato.{ext}
        relato_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/saidas/relato.{ext}"
        relato_path = self._temp_dir / f"relato.{ext}"
        await self._s3_repo.download_file(self._bucket, relato_key, str(relato_path))

        # Try to download relgnl.{ext} (optional for some cases)
        try:
            relgnl_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/saidas/relgnl.{ext}"
            relgnl_path = self._temp_dir / f"relgnl.{ext}"
            await self._s3_repo.download_file(self._bucket, relgnl_key, str(relgnl_path))
        except ArtifactNotFoundError:
            Log.log().info("relgnl not found (may not be needed)")

    async def _download_destination_deck(self) -> None:
        """
        Download and extract destination deck.

        For destination cases, we download the full deck zip and extract it.
        """
        assert self._temp_dir is not None

        deck_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/entradas/deck_processado.zip"
        zip_path = self._temp_dir / "deck_processado.zip"

        Log.log().info(f"Downloading deck from s3://{self._bucket}/{deck_key}")
        await self._s3_repo.download_file(self._bucket, deck_key, str(zip_path))

        # Extract to temp directory
        extract_zip(zip_path, self._temp_dir)

        # Remove zip after extraction
        zip_path.unlink()
        Log.log().info(f"Extracted deck to {self._temp_dir}")

    async def _upload_results(self) -> None:
        """Package and upload modified files to S3."""
        assert self._temp_dir is not None

        # Create output zip
        output_name = f"{self._execution_hash}_encadeado.zip"
        zip_path = self._temp_dir.parent / output_name

        create_zip(
            self._temp_dir,
            zip_path,
            compression_level=Settings.zip_compression_level,
        )

        # Upload to ingest prefix
        output_key = f"{Settings.s3_ingest_prefix}/{output_name}"
        Log.log().info(f"Uploading result to s3://{self._bucket}/{output_key}")
        await self._s3_repo.upload_file(str(zip_path), self._bucket, output_key)

        # Cleanup zip
        zip_path.unlink()

        self._output_key = output_key

    @property
    def program(self) -> Program:
        return Program.DECOMP

    @property
    def files(self) -> AbstractDecompRepository:
        if not self._decomp:
            raise RuntimeError("Repository not initialized - use async context manager")
        return self._decomp

    @property
    def output_key(self) -> str | None:
        """S3 key of uploaded output (only for destination role after exit)."""
        return self._output_key

    @property
    def execution_hash(self) -> str:
        """Execution hash for this unit of work."""
        return self._execution_hash

    def rollback(self) -> None:
        """Rollback not supported for S3 operations."""
        pass


class S3NewaveUnitOfWork(AbstractUnitOfWork):
    """
    Unit of Work for NEWAVE operations with S3 storage.

    Downloads artifacts from S3, processes locally, uploads results.

    Example:
        async with S3NewaveUnitOfWork(
            s3_repo=s3_repo,
            bucket="newave-bucket",
            execution_hash="def456",
            role="destination",
        ) as uow:
            # Access files through uow.files
            confhd = uow.files.get_confhd()
    """

    def __init__(
        self,
        s3_repo: S3Repository,
        bucket: str,
        execution_hash: str,
        role: str = "destination",
    ) -> None:
        """
        Initialize S3 NEWAVE unit of work.

        Args:
            s3_repo: S3Repository instance
            bucket: S3 bucket name
            execution_hash: Execution identifier
            role: "source" (read-only outputs) or "destination" (full deck, read-write)
        """
        self._s3_repo = s3_repo
        self._bucket = bucket
        self._execution_hash = execution_hash
        self._role = role
        self._temp_dir: Path | None = None
        self._newave: RawNewaveRepository | None = None
        self._output_key: str | None = None
        self._temp_context = None

    async def __aenter__(self) -> "S3NewaveUnitOfWork":
        """Enter context: download artifacts and setup repository."""
        # Create temp directory using async context manager
        self._temp_context = async_temp_directory(
            base_dir=Settings.temp_dir,
            prefix=f"newave_{self._execution_hash[:8]}_",
        )
        self._temp_dir = await self._temp_context.__aenter__()

        # Download artifacts based on role
        await self._download_artifacts()

        # Create repository pointing to temp directory
        self._newave = RawNewaveRepository(str(self._temp_dir))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context: upload if destination, always cleanup."""
        # If destination and no error, upload modified files
        if self._role == "destination" and exc_type is None:
            await self._upload_results()

        # Cleanup temp directory
        if self._temp_context:
            await self._temp_context.__aexit__(exc_type, exc_val, exc_tb)

    async def _download_artifacts(self) -> None:
        """Download required artifacts from S3."""
        if self._role == "source":
            await self._download_source_outputs()
        else:
            await self._download_destination_deck()

    async def _download_source_outputs(self) -> None:
        """
        Download source output files (pmo.dat).

        For source cases, we need the PMO file from a previous execution.
        """
        assert self._temp_dir is not None

        # Download pmo.dat from saidas
        pmo_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/saidas/pmo.dat"
        pmo_path = self._temp_dir / "pmo.dat"

        Log.log().info(f"Downloading PMO from s3://{self._bucket}/{pmo_key}")
        await self._s3_repo.download_file(self._bucket, pmo_key, str(pmo_path))

        # Also need caso.dat and arquivos.dat for repository initialization
        caso_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/saidas/caso.dat"
        caso_path = self._temp_dir / "caso.dat"

        try:
            await self._s3_repo.download_file(self._bucket, caso_key, str(caso_path))
        except ArtifactNotFoundError:
            # Try from entradas
            caso_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/entradas/caso.dat"
            await self._s3_repo.download_file(self._bucket, caso_key, str(caso_path))

    async def _download_destination_deck(self) -> None:
        """
        Download and extract destination deck.

        For destination cases, we download the full deck zip and extract it.
        """
        assert self._temp_dir is not None

        deck_key = f"{Settings.s3_artifacts_prefix}/{self._execution_hash}/entradas/deck_processado.zip"
        zip_path = self._temp_dir / "deck_processado.zip"

        Log.log().info(f"Downloading deck from s3://{self._bucket}/{deck_key}")
        await self._s3_repo.download_file(self._bucket, deck_key, str(zip_path))

        # Extract to temp directory
        extract_zip(zip_path, self._temp_dir)

        # Remove zip after extraction
        zip_path.unlink()
        Log.log().info(f"Extracted deck to {self._temp_dir}")

    async def _upload_results(self) -> None:
        """Package and upload modified files to S3."""
        assert self._temp_dir is not None

        # Create output zip
        output_name = f"{self._execution_hash}_encadeado.zip"
        zip_path = self._temp_dir.parent / output_name

        create_zip(
            self._temp_dir,
            zip_path,
            compression_level=Settings.zip_compression_level,
        )

        # Upload to ingest prefix
        output_key = f"{Settings.s3_ingest_prefix}/{output_name}"
        Log.log().info(f"Uploading result to s3://{self._bucket}/{output_key}")
        await self._s3_repo.upload_file(str(zip_path), self._bucket, output_key)

        # Cleanup zip
        zip_path.unlink()

        self._output_key = output_key

    @property
    def program(self) -> Program:
        return Program.NEWAVE

    @property
    def files(self) -> AbstractNewaveRepository:
        if not self._newave:
            raise RuntimeError("Repository not initialized - use async context manager")
        return self._newave

    @property
    def output_key(self) -> str | None:
        """S3 key of uploaded output (only for destination role after exit)."""
        return self._output_key

    @property
    def execution_hash(self) -> str:
        """Execution hash for this unit of work."""
        return self._execution_hash

    def rollback(self) -> None:
        """Rollback not supported for S3 operations."""
        pass


# =============================================================================
# Factory Functions
# =============================================================================


def s3_unitofwork_factory(
    program: Program,
    s3_repo: S3Repository,
    bucket: str,
    execution_hash: str,
    role: str = "destination",
) -> S3DecompUnitOfWork | S3NewaveUnitOfWork:
    """
    Create an S3-aware UnitOfWork based on program type.

    Args:
        program: Program type (DECOMP or NEWAVE)
        s3_repo: S3Repository instance
        bucket: S3 bucket name
        execution_hash: Execution identifier
        role: "source" or "destination"

    Returns:
        S3DecompUnitOfWork or S3NewaveUnitOfWork

    Example:
        uow = s3_unitofwork_factory(
            program=Program.DECOMP,
            s3_repo=s3_repo,
            bucket="decomp-bucket",
            execution_hash="abc123",
        )
        async with uow:
            # process
    """
    if program == Program.DECOMP:
        return S3DecompUnitOfWork(
            s3_repo=s3_repo,
            bucket=bucket,
            execution_hash=execution_hash,
            role=role,
        )
    elif program == Program.NEWAVE:
        return S3NewaveUnitOfWork(
            s3_repo=s3_repo,
            bucket=bucket,
            execution_hash=execution_hash,
            role=role,
        )
    else:
        raise ValueError(f"Unsupported program type: {program}")
