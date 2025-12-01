# [S3-001] Create S3Repository

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 3  
> **Priority**: P0

## Context

### Background

The service needs to download DECOMP/NEWAVE artifacts from S3 and upload processed results. The S3Repository encapsulates all boto3 operations with proper error handling and logging.

### Relation to Epic

Core infrastructure component. All S3 operations flow through this repository.

### Current State

No S3 integration exists. The application reads directly from filesystem.

## Specification

### File to Create

**Path**: `app/adapters/s3_repository.py`

### Class Interface

```python
from typing import Optional, List, BinaryIO
from pathlib import Path


class S3Repository:
    """Repository for S3 operations."""
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ) -> None:
        """
        Initialize S3 client.
        
        Args:
            region_name: AWS region (default from settings)
            endpoint_url: Custom endpoint for LocalStack/MinIO
        """
        ...
    
    def download_file(self, bucket: str, key: str, local_path: Path) -> None:
        """
        Download file from S3 to local path.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local destination path
            
        Raises:
            ArtifactNotFoundError: If object doesn't exist
            S3Error: If download fails
        """
        ...
    
    def download_file_bytes(self, bucket: str, key: str) -> bytes:
        """
        Download file from S3 as bytes.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            File contents as bytes
            
        Raises:
            ArtifactNotFoundError: If object doesn't exist
            S3Error: If download fails
        """
        ...
    
    def upload_file(self, bucket: str, key: str, local_path: Path) -> None:
        """
        Upload local file to S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local source path
            
        Raises:
            S3Error: If upload fails
        """
        ...
    
    def upload_file_bytes(self, bucket: str, key: str, data: bytes) -> None:
        """
        Upload bytes to S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            data: Bytes to upload
            
        Raises:
            S3Error: If upload fails
        """
        ...
    
    def file_exists(self, bucket: str, key: str) -> bool:
        """
        Check if S3 object exists.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            True if object exists, False otherwise
        """
        ...
    
    def list_objects(self, bucket: str, prefix: str) -> List[str]:
        """
        List objects with given prefix.
        
        Args:
            bucket: S3 bucket name
            prefix: Key prefix to filter
            
        Returns:
            List of object keys
        """
        ...
```

### Implementation Notes

```python
import boto3
from botocore.exceptions import ClientError
from typing import Optional, List
from pathlib import Path
import logging

from app.internal.settings import Settings
from app.internal.exceptions import S3Error, ArtifactNotFoundError

logger = logging.getLogger(__name__)


class S3Repository:
    def __init__(
        self,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ) -> None:
        self._region = region_name or Settings.aws_region
        self._endpoint = endpoint_url or Settings.s3_endpoint_url or None
        
        self._client = boto3.client(
            "s3",
            region_name=self._region,
            endpoint_url=self._endpoint if self._endpoint else None,
        )
    
    def download_file(self, bucket: str, key: str, local_path: Path) -> None:
        try:
            logger.info(f"Downloading s3://{bucket}/{key} to {local_path}")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self._client.download_file(bucket, key, str(local_path))
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise ArtifactNotFoundError(f"s3://{bucket}/{key} not found")
            raise S3Error(f"Failed to download s3://{bucket}/{key}: {e}")
    
    # ... implement other methods following same pattern
```

### Dependencies Required

- `boto3>=1.34.0` (already in pyproject.toml)
- `botocore>=1.34.0` (already in pyproject.toml)
- `app.internal.exceptions` (S3-004)

## Acceptance Criteria

- [ ] `S3Repository` class created with all methods
- [ ] Proper error handling with custom exceptions
- [ ] Logging for all operations
- [ ] Works with custom endpoint_url (for LocalStack)
- [ ] Unit tests with moto
- [ ] No hardcoded credentials

## Implementation Guide

### Step 1: Copy from flexibilizador

```bash
cp /home/rogerio/git/flexibilizador-service/app/adapters/s3_repository.py \
   /home/rogerio/git/encadeador-service/app/adapters/s3_repository.py
```

### Step 2: Update imports

Change exception imports to use encadeador exceptions:
```python
# Change from:
from app.internal.exceptions import FlexibilizadorError, S3Error, ArtifactNotFoundError
# To:
from app.internal.exceptions import EncadeadorError, S3Error, ArtifactNotFoundError
```

### Step 3: Update Settings references

Ensure Settings attributes match (may need to wait for S3-005).

### Step 4: Create test file

```bash
mkdir -p tests/unit
touch tests/unit/__init__.py
```

Create `tests/unit/test_s3_repository.py`:

```python
import pytest
from moto import mock_aws
import boto3
from pathlib import Path
import tempfile

from app.adapters.s3_repository import S3Repository


@pytest.fixture
def s3_client():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        yield client


@pytest.fixture
def s3_repo():
    with mock_aws():
        # Create bucket
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        
        # Create repository
        repo = S3Repository(region_name="us-east-1")
        yield repo


def test_download_file_bytes(s3_repo, s3_client):
    # Setup
    s3_client.put_object(Bucket="test-bucket", Key="test.txt", Body=b"hello")
    
    # Test
    with mock_aws():
        s3_client.put_object(Bucket="test-bucket", Key="test.txt", Body=b"hello")
        repo = S3Repository(region_name="us-east-1")
        content = repo.download_file_bytes("test-bucket", "test.txt")
    
    assert content == b"hello"


def test_file_exists_true(s3_repo, s3_client):
    with mock_aws():
        s3_client.put_object(Bucket="test-bucket", Key="exists.txt", Body=b"data")
        repo = S3Repository(region_name="us-east-1")
        assert repo.file_exists("test-bucket", "exists.txt") is True


def test_file_exists_false(s3_repo):
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        repo = S3Repository(region_name="us-east-1")
        assert repo.file_exists("test-bucket", "nonexistent.txt") is False
```

### Step 5: Run tests

```bash
uv run pytest tests/unit/test_s3_repository.py -v
```

## Files to Read Before Starting

- `/home/rogerio/git/flexibilizador-service/app/adapters/s3_repository.py` - Reference
- `/home/rogerio/git/flexibilizador-service/tests/unit/test_s3_repository.py` - Test patterns
- `app/internal/exceptions.py` - Exception classes (from S3-004)

## Testing Requirements

### Unit Tests (with moto)

- [ ] `test_download_file` - Downloads to local path
- [ ] `test_download_file_bytes` - Downloads as bytes
- [ ] `test_upload_file` - Uploads from local path
- [ ] `test_upload_file_bytes` - Uploads bytes
- [ ] `test_file_exists_true` - Returns True for existing
- [ ] `test_file_exists_false` - Returns False for missing
- [ ] `test_list_objects` - Lists with prefix
- [ ] `test_download_not_found` - Raises ArtifactNotFoundError

## Definition of Done

- [ ] S3Repository created with all methods
- [ ] All unit tests passing with moto
- [ ] No hardcoded credentials
- [ ] Logging in place
- [ ] Type hints on all methods
- [ ] Changes committed

## Blocked By

- [S3-004](./ticket-004-create-exceptions.md) - Needs exception classes

## Blocks

- [S3-006](../sprint-02/ticket-006-create-s3-unitofwork.md) - UnitOfWork uses S3Repository
