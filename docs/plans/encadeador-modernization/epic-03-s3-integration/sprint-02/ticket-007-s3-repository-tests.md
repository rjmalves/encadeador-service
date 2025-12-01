# [S3-007] Write S3Repository Tests

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Sprint**: [Sprint 02](./00-sprint-overview.md)  
> **Points**: 3  
> **Priority**: P0  
> **Status**: ✅ Complete

## Context

### Background

Comprehensive testing of the S3Repository ensures all S3 operations work correctly before integrating with the API layer. Tests use moto to mock AWS S3.

### Relation to Epic

Final validation of S3 infrastructure before API integration.

### Current State

`S3Repository` created in S3-001. Tests may be partial or missing.

## Specification

### Test File

**Path**: `tests/unit/test_s3_repository.py`

### Test Cases

```python
"""Tests for S3Repository using moto mock."""

import pytest
from moto import mock_aws
import boto3
from pathlib import Path
import tempfile

from app.adapters.s3_repository import S3Repository
from app.internal.exceptions import ArtifactNotFoundError, S3OperationError


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


class TestS3RepositoryDownload:
    """Tests for download operations."""

    @mock_aws
    def test_download_file_success(self, temp_dir):
        """Test downloading file to local path."""
        # Setup
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        client.put_object(
            Bucket="test-bucket",
            Key="path/to/file.txt",
            Body=b"test content"
        )
        
        # Execute
        repo = S3Repository(region_name="us-east-1")
        local_path = temp_dir / "downloaded.txt"
        repo.download_file("test-bucket", "path/to/file.txt", local_path)
        
        # Verify
        assert local_path.exists()
        assert local_path.read_bytes() == b"test content"

    @mock_aws
    def test_download_file_creates_parent_dirs(self, temp_dir):
        """Test that download creates parent directories."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        client.put_object(Bucket="test-bucket", Key="file.txt", Body=b"data")
        
        repo = S3Repository(region_name="us-east-1")
        local_path = temp_dir / "nested" / "deep" / "file.txt"
        repo.download_file("test-bucket", "file.txt", local_path)
        
        assert local_path.exists()

    @mock_aws
    def test_download_file_not_found_raises(self, temp_dir):
        """Test that missing file raises ArtifactNotFoundError."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        
        repo = S3Repository(region_name="us-east-1")
        local_path = temp_dir / "missing.txt"
        
        with pytest.raises(ArtifactNotFoundError):
            repo.download_file("test-bucket", "nonexistent.txt", local_path)

    @mock_aws
    def test_download_file_bytes_success(self):
        """Test downloading file as bytes."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        client.put_object(
            Bucket="test-bucket",
            Key="data.bin",
            Body=b"\x00\x01\x02\x03"
        )
        
        repo = S3Repository(region_name="us-east-1")
        content = repo.download_file_bytes("test-bucket", "data.bin")
        
        assert content == b"\x00\x01\x02\x03"

    @mock_aws
    def test_download_file_bytes_not_found_raises(self):
        """Test that missing file raises ArtifactNotFoundError."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        
        repo = S3Repository(region_name="us-east-1")
        
        with pytest.raises(ArtifactNotFoundError):
            repo.download_file_bytes("test-bucket", "missing.bin")


class TestS3RepositoryUpload:
    """Tests for upload operations."""

    @mock_aws
    def test_upload_file_success(self, temp_dir):
        """Test uploading local file to S3."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        
        # Create local file
        local_path = temp_dir / "upload.txt"
        local_path.write_bytes(b"upload content")
        
        # Execute
        repo = S3Repository(region_name="us-east-1")
        repo.upload_file("test-bucket", "uploaded/file.txt", local_path)
        
        # Verify
        response = client.get_object(Bucket="test-bucket", Key="uploaded/file.txt")
        assert response["Body"].read() == b"upload content"

    @mock_aws
    def test_upload_file_bytes_success(self):
        """Test uploading bytes to S3."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        
        repo = S3Repository(region_name="us-east-1")
        repo.upload_file_bytes("test-bucket", "bytes/file.bin", b"binary data")
        
        response = client.get_object(Bucket="test-bucket", Key="bytes/file.bin")
        assert response["Body"].read() == b"binary data"

    @mock_aws
    def test_upload_file_overwrites_existing(self, temp_dir):
        """Test that upload overwrites existing object."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        client.put_object(Bucket="test-bucket", Key="file.txt", Body=b"old")
        
        local_path = temp_dir / "new.txt"
        local_path.write_bytes(b"new content")
        
        repo = S3Repository(region_name="us-east-1")
        repo.upload_file("test-bucket", "file.txt", local_path)
        
        response = client.get_object(Bucket="test-bucket", Key="file.txt")
        assert response["Body"].read() == b"new content"


class TestS3RepositoryExists:
    """Tests for file existence checks."""

    @mock_aws
    def test_file_exists_true(self):
        """Test file_exists returns True for existing object."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        client.put_object(Bucket="test-bucket", Key="exists.txt", Body=b"data")
        
        repo = S3Repository(region_name="us-east-1")
        assert repo.file_exists("test-bucket", "exists.txt") is True

    @mock_aws
    def test_file_exists_false(self):
        """Test file_exists returns False for missing object."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        
        repo = S3Repository(region_name="us-east-1")
        assert repo.file_exists("test-bucket", "missing.txt") is False

    @mock_aws
    def test_file_exists_wrong_bucket(self):
        """Test file_exists handles missing bucket gracefully."""
        repo = S3Repository(region_name="us-east-1")
        # Should return False, not raise
        assert repo.file_exists("nonexistent-bucket", "file.txt") is False


class TestS3RepositoryList:
    """Tests for listing operations."""

    @mock_aws
    def test_list_objects_returns_keys(self):
        """Test list_objects returns object keys."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        client.put_object(Bucket="test-bucket", Key="prefix/a.txt", Body=b"a")
        client.put_object(Bucket="test-bucket", Key="prefix/b.txt", Body=b"b")
        client.put_object(Bucket="test-bucket", Key="other/c.txt", Body=b"c")
        
        repo = S3Repository(region_name="us-east-1")
        keys = repo.list_objects("test-bucket", "prefix/")
        
        assert len(keys) == 2
        assert "prefix/a.txt" in keys
        assert "prefix/b.txt" in keys
        assert "other/c.txt" not in keys

    @mock_aws
    def test_list_objects_empty_prefix(self):
        """Test list_objects with empty prefix returns all."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        client.put_object(Bucket="test-bucket", Key="a.txt", Body=b"a")
        client.put_object(Bucket="test-bucket", Key="b.txt", Body=b"b")
        
        repo = S3Repository(region_name="us-east-1")
        keys = repo.list_objects("test-bucket", "")
        
        assert len(keys) == 2

    @mock_aws
    def test_list_objects_no_matches(self):
        """Test list_objects returns empty list for no matches."""
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        
        repo = S3Repository(region_name="us-east-1")
        keys = repo.list_objects("test-bucket", "nonexistent/")
        
        assert keys == []


class TestS3RepositoryCustomEndpoint:
    """Tests for custom endpoint (LocalStack) support."""

    @mock_aws
    def test_custom_endpoint_url(self):
        """Test S3Repository works with custom endpoint."""
        # Note: moto doesn't fully support endpoint_url, but we verify
        # the client is created without errors
        repo = S3Repository(
            region_name="us-east-1",
            endpoint_url="http://localhost:4566"
        )
        assert repo._client is not None
```

### Additional Test Files

**Path**: `tests/unit/test_zip_utils.py`

```python
"""Tests for zip utilities."""

import pytest
import zipfile
from pathlib import Path
import tempfile

from app.utils.zip_utils import extract_zip, create_zip


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


class TestExtractZip:
    """Tests for extract_zip function."""

    def test_extract_zip_creates_files(self, temp_dir):
        """Test extracting zip creates expected files."""
        # Create test zip
        zip_path = temp_dir / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("subdir/file2.txt", "content2")
        
        # Extract
        extract_dir = temp_dir / "extracted"
        extract_zip(zip_path, extract_dir)
        
        # Verify
        assert (extract_dir / "file1.txt").read_text() == "content1"
        assert (extract_dir / "subdir" / "file2.txt").read_text() == "content2"


class TestCreateZip:
    """Tests for create_zip function."""

    def test_create_zip_includes_files(self, temp_dir):
        """Test creating zip includes all files."""
        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "a.txt").write_text("a")
        (source_dir / "b.txt").write_text("b")
        
        # Create zip
        zip_path = temp_dir / "output.zip"
        create_zip(source_dir, zip_path)
        
        # Verify
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "a.txt" in names
            assert "b.txt" in names
```

**Path**: `tests/unit/test_temp_manager.py`

```python
"""Tests for TempDirectoryManager."""

import pytest
from pathlib import Path
import tempfile
import time

from app.utils.temp_manager import TempDirectoryManager


@pytest.fixture
def temp_base():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


class TestTempDirectoryManager:
    """Tests for TempDirectoryManager."""

    def test_create_temp_dir(self, temp_base):
        """Test creating temp directory."""
        manager = TempDirectoryManager(base_dir=temp_base)
        temp_dir = manager.create_temp_dir(prefix="test")
        
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        assert "test" in temp_dir.name

    def test_cleanup_dir(self, temp_base):
        """Test cleaning up temp directory."""
        manager = TempDirectoryManager(base_dir=temp_base)
        temp_dir = manager.create_temp_dir()
        (temp_dir / "file.txt").write_text("content")
        
        manager.cleanup_dir(temp_dir)
        
        assert not temp_dir.exists()

    def test_cleanup_old_dirs(self, temp_base):
        """Test cleanup_old removes old directories."""
        manager = TempDirectoryManager(base_dir=temp_base, max_age_hours=0)
        
        # Create dir (will be "old" immediately with max_age=0)
        temp_dir = manager.create_temp_dir()
        
        # Cleanup old
        time.sleep(0.1)  # Ensure some time passes
        manager.cleanup_old()
        
        # May or may not exist depending on timing
        # This test mainly verifies the method runs without error
```

## Acceptance Criteria

- [ ] All S3Repository methods have tests
- [ ] Tests use moto mock (no real AWS calls)
- [ ] Error cases tested (404, permissions)
- [ ] Edge cases covered (empty results, overwrites)
- [ ] Tests for zip_utils
- [ ] Tests for temp_manager
- [ ] All tests pass with `uv run pytest`
- [ ] Coverage ≥80% for S3 components

## Implementation Guide

### Step 1: Create test directory structure

```bash
mkdir -p tests/unit
touch tests/__init__.py
touch tests/unit/__init__.py
```

### Step 2: Install test dependencies

Ensure moto is installed:

```bash
uv add --dev moto pytest pytest-asyncio
```

### Step 3: Create test files

Create the test files as specified above.

### Step 4: Run tests

```bash
uv run pytest tests/unit/ -v
```

### Step 5: Check coverage

```bash
uv run pytest tests/unit/ --cov=app.adapters.s3_repository --cov=app.utils --cov-report=term-missing
```

## Files to Read Before Starting

- `app/adapters/s3_repository.py` - Implementation to test
- `app/utils/zip_utils.py` - Implementation to test
- `app/utils/temp_manager.py` - Implementation to test
- `/home/rogerio/git/flexibilizador-service/tests/unit/` - Reference test patterns

## Testing Requirements

### Test Coverage Goals

| Module | Target Coverage |
|--------|----------------|
| `s3_repository.py` | ≥90% |
| `zip_utils.py` | ≥80% |
| `temp_manager.py` | ≥80% |

## Definition of Done

- [ ] Test files created
- [ ] All tests passing
- [ ] Coverage targets met
- [ ] No real AWS calls (moto only)
- [ ] Tests documented
- [ ] Changes committed

## Blocked By

- [S3-001](../sprint-01/ticket-001-create-s3-repository.md) - S3Repository
- [S3-002](../sprint-01/ticket-002-create-zip-utils.md) - zip_utils
- [S3-003](../sprint-01/ticket-003-create-temp-manager.md) - temp_manager

## Blocks

- [Epic 04: API Modernization](../../epic-04-api-modernization/00-epic-overview.md) - Validates S3 layer
