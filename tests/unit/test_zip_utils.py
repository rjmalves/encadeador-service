"""Tests for zip utilities."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from app.utils.zip_utils import create_zip, extract_zip, get_zip_file_list


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
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
            zf.writestr("file2.txt", "content2")

        # Extract
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()
        extract_zip(zip_path, extract_dir)

        # Verify
        assert (extract_dir / "file1.txt").read_text() == "content1"
        assert (extract_dir / "file2.txt").read_text() == "content2"

    def test_extract_zip_with_subdirectories(self, temp_dir):
        """Test extracting zip preserves directory structure."""
        # Create test zip with subdirectory
        zip_path = temp_dir / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("root.txt", "root content")
            zf.writestr("subdir/nested.txt", "nested content")

        # Extract
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()
        extract_zip(zip_path, extract_dir)

        # Verify
        assert (extract_dir / "root.txt").read_text() == "root content"
        assert (extract_dir / "subdir" / "nested.txt").read_text() == "nested content"

    def test_extract_zip_not_found_raises(self, temp_dir):
        """Test extracting nonexistent zip raises FileNotFoundError."""
        zip_path = temp_dir / "nonexistent.zip"
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            extract_zip(zip_path, extract_dir)

    def test_extract_zip_corrupted_raises(self, temp_dir):
        """Test extracting corrupted zip raises BadZipFile."""
        # Create corrupted zip
        zip_path = temp_dir / "corrupted.zip"
        zip_path.write_bytes(b"not a valid zip file")

        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with pytest.raises(zipfile.BadZipFile):
            extract_zip(zip_path, extract_dir)


class TestCreateZip:
    """Tests for create_zip function."""

    def test_create_zip_includes_files(self, temp_dir):
        """Test creating zip includes all files."""
        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "a.txt").write_text("content a")
        (source_dir / "b.txt").write_text("content b")

        # Create zip
        zip_path = temp_dir / "output.zip"
        create_zip(source_dir, zip_path)

        # Verify
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "a.txt" in names
            assert "b.txt" in names

    def test_create_zip_with_compression_level(self, temp_dir):
        """Test creating zip with different compression levels."""
        # Create source file
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        # Write a file with repetitive content (compresses well)
        (source_dir / "data.txt").write_text("A" * 10000)

        # Create zip with high compression
        zip_high = temp_dir / "high.zip"
        create_zip(source_dir, zip_high, compression_level=9)

        # Create zip with low compression
        zip_low = temp_dir / "low.zip"
        create_zip(source_dir, zip_low, compression_level=1)

        # High compression should result in smaller file
        assert zip_high.stat().st_size <= zip_low.stat().st_size

    def test_create_zip_source_not_found_raises(self, temp_dir):
        """Test creating zip from nonexistent dir raises FileNotFoundError."""
        source_dir = temp_dir / "nonexistent"
        zip_path = temp_dir / "output.zip"

        with pytest.raises(FileNotFoundError):
            create_zip(source_dir, zip_path)

    def test_create_zip_empty_dir_raises(self, temp_dir):
        """Test creating zip from empty dir raises ValueError."""
        source_dir = temp_dir / "empty"
        source_dir.mkdir()
        zip_path = temp_dir / "output.zip"

        with pytest.raises(ValueError, match="empty"):
            create_zip(source_dir, zip_path)


class TestGetZipFileList:
    """Tests for get_zip_file_list function."""

    def test_get_zip_file_list(self, temp_dir):
        """Test getting list of files in zip."""
        # Create test zip
        zip_path = temp_dir / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        # Get file list
        files = get_zip_file_list(zip_path)

        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files

    def test_get_zip_file_list_empty_zip(self, temp_dir):
        """Test getting file list from empty zip."""
        # Create empty zip
        zip_path = temp_dir / "empty.zip"
        with zipfile.ZipFile(zip_path, "w"):
            pass

        files = get_zip_file_list(zip_path)
        assert files == []
