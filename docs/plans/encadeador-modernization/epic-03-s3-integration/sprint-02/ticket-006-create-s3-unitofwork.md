# [S3-006] Create S3UnitOfWork classes

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Sprint**: [Sprint 02](./00-sprint-overview.md)  
> **Points**: 5  
> **Priority**: P0

## Context

### Background

The UnitOfWork pattern encapsulates data access for a business transaction. For S3 integration, we need S3-aware UnitOfWork classes that:
1. Download artifacts from S3 to temp directories
2. Create file repositories pointing to temp directories
3. After processing, upload modified files back to S3
4. Clean up temp directories

### Relation to Epic

Core integration component. Bridges S3 storage with existing repository pattern.

### Current State

Existing `DecompUnitOfWork` and `NewaveUnitOfWork` work with local filesystem paths.

## Specification

### File to Create

**Path**: `app/services/s3_unitofwork.py`

### Classes

```python
"""S3-aware Unit of Work implementations."""

from pathlib import Path
from typing import Optional
import logging

from app.adapters.s3_repository import S3Repository
from app.adapters.decomprepository import RawDecompRepository
from app.adapters.newaverepository import RawNewaveRepository
from app.utils.temp_manager import TempDirectoryManager
from app.utils.zip_utils import extract_zip, create_zip
from app.services.unitofwork import AbstractUnitOfWork
from app.models.program import Program

logger = logging.getLogger(__name__)


class S3DecompUnitOfWork(AbstractUnitOfWork):
    """
    Unit of Work for DECOMP operations with S3 storage.
    
    Downloads artifacts from S3, processes locally, uploads results.
    """
    
    def __init__(
        self,
        s3_repo: S3Repository,
        bucket: str,
        execution_hash: str,
        temp_manager: TempDirectoryManager,
        role: str = "destination",  # "source" or "destination"
    ) -> None:
        """
        Initialize S3 DECOMP unit of work.
        
        Args:
            s3_repo: S3Repository instance
            bucket: S3 bucket name
            execution_hash: Execution identifier
            temp_manager: Temp directory manager
            role: Whether this is source (read-only) or destination (read-write)
        """
        self._s3_repo = s3_repo
        self._bucket = bucket
        self._execution_hash = execution_hash
        self._temp_manager = temp_manager
        self._role = role
        self._temp_dir: Optional[Path] = None
        self._decomp: Optional[RawDecompRepository] = None
    
    async def __aenter__(self) -> "S3DecompUnitOfWork":
        """
        Enter context: download artifacts and setup repository.
        """
        # Create temp directory
        self._temp_dir = self._temp_manager.create_temp_dir(
            prefix=f"decomp_{self._execution_hash[:8]}"
        )
        
        # Download artifacts based on role
        await self._download_artifacts()
        
        # Create repository pointing to temp directory
        self._decomp = RawDecompRepository(str(self._temp_dir))
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context: upload if destination, always cleanup.
        """
        # If destination and no error, upload modified files
        if self._role == "destination" and exc_type is None:
            await self._upload_results()
        
        # Cleanup temp directory
        if self._temp_dir:
            self._temp_manager.cleanup_dir(self._temp_dir)
    
    async def _download_artifacts(self) -> None:
        """Download required artifacts from S3."""
        if self._role == "source":
            # For source, only need output files (relato, relgnl)
            await self._download_source_outputs()
        else:
            # For destination, need the full deck
            await self._download_destination_deck()
    
    async def _download_source_outputs(self) -> None:
        """Download source output files (relato, relgnl, etc)."""
        # Download relato
        # Pattern: artifacts/{hash}/saidas/relato.{ext}
        # First need to determine extension from caso.dat
        ...
    
    async def _download_destination_deck(self) -> None:
        """Download and extract destination deck."""
        # Download deck_processado.zip
        deck_key = f"artifacts/{self._execution_hash}/entradas/deck_processado.zip"
        zip_path = self._temp_dir / "deck_processado.zip"
        
        self._s3_repo.download_file(self._bucket, deck_key, zip_path)
        
        # Extract to temp directory
        extract_zip(zip_path, self._temp_dir)
        
        # Remove zip after extraction
        zip_path.unlink()
    
    async def _upload_results(self) -> None:
        """Package and upload modified files to S3."""
        # Create output zip
        output_name = f"{self._execution_hash}_encadeado.zip"
        zip_path = self._temp_dir.parent / output_name
        
        create_zip(self._temp_dir, zip_path)
        
        # Upload to ingest prefix
        output_key = f"ingest/{output_name}"
        self._s3_repo.upload_file(self._bucket, output_key, zip_path)
        
        # Cleanup zip
        zip_path.unlink()
        
        self._output_key = output_key
    
    @property
    def program(self) -> Program:
        return Program.DECOMP
    
    @property
    def files(self) -> RawDecompRepository:
        if not self._decomp:
            raise RuntimeError("Repository not initialized - use async context manager")
        return self._decomp
    
    @property
    def output_key(self) -> Optional[str]:
        """S3 key of uploaded output (only for destination role)."""
        return getattr(self, "_output_key", None)
    
    def rollback(self) -> None:
        """Rollback not supported for S3 operations."""
        pass


class S3NewaveUnitOfWork(AbstractUnitOfWork):
    """
    Unit of Work for NEWAVE operations with S3 storage.
    
    Similar to S3DecompUnitOfWork but for NEWAVE files.
    """
    # ... similar implementation with NEWAVE-specific file patterns
```

### S3 Path Patterns

| Role | Artifact | S3 Path |
|------|----------|---------|
| Source | relato | `artifacts/{hash}/saidas/relato.{ext}` |
| Source | relgnl | `artifacts/{hash}/saidas/relgnl.{ext}` |
| Destination | deck | `artifacts/{hash}/entradas/deck_processado.zip` |
| Output | result | `ingest/{hash}_encadeado.zip` |

## Acceptance Criteria

- [ ] `S3DecompUnitOfWork` created with async context manager
- [ ] `S3NewaveUnitOfWork` created with async context manager
- [ ] Downloads artifacts from correct S3 paths
- [ ] Extracts zip files to temp directory
- [ ] Creates repository pointing to temp directory
- [ ] Uploads results to ingest prefix (destination only)
- [ ] Cleans up temp directories on exit
- [ ] Works with moto mock S3

## Implementation Guide

### Step 1: Create file structure

```bash
touch app/services/s3_unitofwork.py
```

### Step 2: Implement S3DecompUnitOfWork

Follow the specification above. Key points:
- Use async context manager (`__aenter__`, `__aexit__`)
- Handle both "source" and "destination" roles
- Use injected `S3Repository` and `TempDirectoryManager`

### Step 3: Implement S3NewaveUnitOfWork

Similar pattern but with NEWAVE-specific file handling.

### Step 4: Update unitofwork.py factory

Add S3 variants to the factory function in `app/services/unitofwork.py`.

### Step 5: Create tests

```python
# tests/unit/test_s3_unitofwork.py
import pytest
from moto import mock_aws
import boto3
import zipfile
from pathlib import Path

from app.adapters.s3_repository import S3Repository
from app.services.s3_unitofwork import S3DecompUnitOfWork
from app.utils.temp_manager import TempDirectoryManager


@pytest.fixture
def mock_s3_with_deck():
    """Setup mock S3 with DECOMP deck."""
    with mock_aws():
        # Create bucket
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="decomp-bucket")
        
        # Create mock deck zip
        # ... create and upload test artifacts
        
        yield client


@mock_aws
async def test_s3_decomp_unitofwork_downloads_deck(tmp_path):
    # Setup
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="decomp-bucket")
    
    # Create and upload test deck
    deck_zip = tmp_path / "deck.zip"
    with zipfile.ZipFile(deck_zip, "w") as zf:
        zf.writestr("caso.dat", "rv0")
        zf.writestr("dadger.rv0", "test content")
    
    client.upload_file(
        str(deck_zip),
        "decomp-bucket",
        "artifacts/abc123/entradas/deck_processado.zip"
    )
    
    # Test
    s3_repo = S3Repository(region_name="us-east-1")
    temp_manager = TempDirectoryManager(base_dir=tmp_path / "temp")
    
    async with S3DecompUnitOfWork(
        s3_repo=s3_repo,
        bucket="decomp-bucket",
        execution_hash="abc123",
        temp_manager=temp_manager,
        role="destination",
    ) as uow:
        # Verify files were downloaded
        assert (uow._temp_dir / "caso.dat").exists()
        assert (uow._temp_dir / "dadger.rv0").exists()
```

## Files to Read Before Starting

- `app/services/unitofwork.py` - Existing UnitOfWork pattern
- `app/adapters/decomprepository.py` - RawDecompRepository interface
- `/home/rogerio/git/flexibilizador-service/app/services/` - Reference patterns

## Definition of Done

- [ ] S3DecompUnitOfWork implemented
- [ ] S3NewaveUnitOfWork implemented
- [ ] Async context manager works
- [ ] Downloads from correct S3 paths
- [ ] Uploads to ingest prefix
- [ ] Temp directories cleaned up
- [ ] Unit tests with moto
- [ ] Changes committed

## Blocked By

- [S3-001](../sprint-01/ticket-001-create-s3-repository.md) - S3Repository
- [S3-002](../sprint-01/ticket-002-create-zip-utils.md) - Zip utilities
- [S3-003](../sprint-01/ticket-003-create-temp-manager.md) - Temp manager
- [S3-005](./ticket-005-update-settings-s3.md) - Settings

## Blocks

- [Epic 04: API Modernization](../../epic-04-api-modernization/00-epic-overview.md)
