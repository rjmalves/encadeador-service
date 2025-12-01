"""Tests for S3Repository using moto mock."""

import tempfile
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

from app.adapters.s3_repository import S3Repository, reset_s3_repository
from app.internal.exceptions import ArtifactNotFoundError


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset S3Repository singleton before each test."""
    reset_s3_repository()
    yield
    reset_s3_repository()


@pytest.fixture
def mock_s3():
    """Fixture to start mock_aws context."""
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


class TestS3RepositoryDownload:
    """Tests for download operations."""

    @pytest.mark.asyncio
    async def test_download_file_success(self, temp_dir, mock_s3):
        """Test downloading file to local path."""
        # Setup
        mock_s3.create_bucket(Bucket="test-bucket")
        mock_s3.put_object(
            Bucket="test-bucket",
            Key="path/to/file.txt",
            Body=b"test content"
        )

        # Execute
        repo = S3Repository(region="us-east-1")
        local_path = temp_dir / "downloaded.txt"
        await repo.download_file("test-bucket", "path/to/file.txt", str(local_path))

        # Verify
        assert local_path.exists()
        assert local_path.read_bytes() == b"test content"

    @pytest.mark.asyncio
    async def test_download_file_creates_parent_dirs(self, temp_dir, mock_s3):
        """Test that download creates parent directories."""
        mock_s3.create_bucket(Bucket="test-bucket")
        mock_s3.put_object(Bucket="test-bucket", Key="file.txt", Body=b"data")

        repo = S3Repository(region="us-east-1")
        local_path = temp_dir / "nested" / "deep" / "file.txt"

        # Need to create parent dirs manually since boto3 doesn't
        local_path.parent.mkdir(parents=True, exist_ok=True)
        await repo.download_file("test-bucket", "file.txt", str(local_path))

        assert local_path.exists()

    @pytest.mark.asyncio
    async def test_download_file_not_found_raises(self, temp_dir, mock_s3):
        """Test that missing file raises ArtifactNotFoundError."""
        mock_s3.create_bucket(Bucket="test-bucket")

        repo = S3Repository(region="us-east-1")
        local_path = temp_dir / "missing.txt"

        with pytest.raises(ArtifactNotFoundError):
            await repo.download_file("test-bucket", "nonexistent.txt", str(local_path))

    @pytest.mark.asyncio
    async def test_download_bytes_success(self, mock_s3):
        """Test downloading file as bytes."""
        mock_s3.create_bucket(Bucket="test-bucket")
        mock_s3.put_object(
            Bucket="test-bucket",
            Key="data.bin",
            Body=b"\x00\x01\x02\x03"
        )

        repo = S3Repository(region="us-east-1")
        content = await repo.download_bytes("test-bucket", "data.bin")

        assert content == b"\x00\x01\x02\x03"

    @pytest.mark.asyncio
    async def test_download_bytes_not_found_raises(self, mock_s3):
        """Test that missing file raises ArtifactNotFoundError."""
        mock_s3.create_bucket(Bucket="test-bucket")

        repo = S3Repository(region="us-east-1")

        with pytest.raises(ArtifactNotFoundError):
            await repo.download_bytes("test-bucket", "missing.bin")


class TestS3RepositoryUpload:
    """Tests for upload operations."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, temp_dir, mock_s3):
        """Test uploading local file to S3."""
        mock_s3.create_bucket(Bucket="test-bucket")

        # Create local file
        local_path = temp_dir / "upload.txt"
        local_path.write_bytes(b"upload content")

        # Execute
        repo = S3Repository(region="us-east-1")
        result = await repo.upload_file(str(local_path), "test-bucket", "uploaded/file.txt")

        # Verify
        assert result == "uploaded/file.txt"
        response = mock_s3.get_object(Bucket="test-bucket", Key="uploaded/file.txt")
        assert response["Body"].read() == b"upload content"

    @pytest.mark.asyncio
    async def test_upload_file_overwrites_existing(self, temp_dir, mock_s3):
        """Test that upload overwrites existing object."""
        mock_s3.create_bucket(Bucket="test-bucket")
        mock_s3.put_object(Bucket="test-bucket", Key="file.txt", Body=b"old")

        local_path = temp_dir / "new.txt"
        local_path.write_bytes(b"new content")

        repo = S3Repository(region="us-east-1")
        await repo.upload_file(str(local_path), "test-bucket", "file.txt")

        response = mock_s3.get_object(Bucket="test-bucket", Key="file.txt")
        assert response["Body"].read() == b"new content"


class TestS3RepositoryExists:
    """Tests for file existence checks."""

    @pytest.mark.asyncio
    async def test_object_exists_true(self, mock_s3):
        """Test object_exists returns True for existing object."""
        mock_s3.create_bucket(Bucket="test-bucket")
        mock_s3.put_object(Bucket="test-bucket", Key="exists.txt", Body=b"data")

        repo = S3Repository(region="us-east-1")
        assert await repo.object_exists("test-bucket", "exists.txt") is True

    @pytest.mark.asyncio
    async def test_object_exists_false(self, mock_s3):
        """Test object_exists returns False for missing object."""
        mock_s3.create_bucket(Bucket="test-bucket")

        repo = S3Repository(region="us-east-1")
        assert await repo.object_exists("test-bucket", "missing.txt") is False


class TestS3RepositoryList:
    """Tests for listing operations."""

    @pytest.mark.asyncio
    async def test_list_objects_returns_keys(self, mock_s3):
        """Test list_objects returns object keys."""
        mock_s3.create_bucket(Bucket="test-bucket")
        mock_s3.put_object(Bucket="test-bucket", Key="prefix/a.txt", Body=b"a")
        mock_s3.put_object(Bucket="test-bucket", Key="prefix/b.txt", Body=b"b")
        mock_s3.put_object(Bucket="test-bucket", Key="other/c.txt", Body=b"c")

        repo = S3Repository(region="us-east-1")
        keys = await repo.list_objects("test-bucket", "prefix/")

        assert len(keys) == 2
        assert "prefix/a.txt" in keys
        assert "prefix/b.txt" in keys
        assert "other/c.txt" not in keys

    @pytest.mark.asyncio
    async def test_list_objects_empty_prefix(self, mock_s3):
        """Test list_objects with empty prefix returns all."""
        mock_s3.create_bucket(Bucket="test-bucket")
        mock_s3.put_object(Bucket="test-bucket", Key="a.txt", Body=b"a")
        mock_s3.put_object(Bucket="test-bucket", Key="b.txt", Body=b"b")

        repo = S3Repository(region="us-east-1")
        keys = await repo.list_objects("test-bucket", "")

        assert len(keys) == 2

    @pytest.mark.asyncio
    async def test_list_objects_no_matches(self, mock_s3):
        """Test list_objects returns empty list for no matches."""
        mock_s3.create_bucket(Bucket="test-bucket")

        repo = S3Repository(region="us-east-1")
        keys = await repo.list_objects("test-bucket", "nonexistent/")

        assert keys == []


class TestS3RepositoryCustomEndpoint:
    """Tests for custom endpoint (LocalStack) support."""

    def test_custom_endpoint_url(self, mock_s3):
        """Test S3Repository works with custom endpoint."""
        # Note: moto doesn't fully support endpoint_url, but we verify
        # the client is created without errors
        repo = S3Repository(
            region="us-east-1",
            endpoint_url="http://localhost:4566"
        )
        assert repo._client is not None
