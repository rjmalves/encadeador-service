"""Tests for TempDirectoryManager utilities."""

import tempfile
import time
from pathlib import Path

import pytest

from app.utils.temp_manager import (
    async_temp_directory,
    cleanup_directory,
    cleanup_old_temp_dirs,
    temp_directory,
)


@pytest.fixture
def temp_base():
    """Create base temp directory for tests."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


class TestTempDirectory:
    """Tests for temp_directory context manager."""

    def test_temp_directory_creates_dir(self, temp_base):
        """Test that temp_directory creates a directory."""
        with temp_directory(base_dir=str(temp_base), prefix="test_") as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            assert "test_" in temp_dir.name

    def test_temp_directory_cleanup_on_exit(self, temp_base):
        """Test that temp_directory cleans up on normal exit."""
        with temp_directory(base_dir=str(temp_base)) as temp_dir:
            # Create some files
            (temp_dir / "file.txt").write_text("content")
            temp_path = temp_dir

        # After exit, directory should be cleaned up
        assert not temp_path.exists()

    def test_temp_directory_cleanup_on_exception(self, temp_base):
        """Test that temp_directory cleans up even on exception."""
        temp_path = None
        try:
            with temp_directory(base_dir=str(temp_base)) as temp_dir:
                temp_path = temp_dir
                (temp_dir / "file.txt").write_text("content")
                raise ValueError("Test exception")
        except ValueError:
            pass

        # After exception, directory should still be cleaned up
        assert temp_path is not None
        assert not temp_path.exists()


class TestAsyncTempDirectory:
    """Tests for async_temp_directory context manager."""

    @pytest.mark.asyncio
    async def test_async_temp_directory_creates_dir(self, temp_base):
        """Test that async_temp_directory creates a directory."""
        async with async_temp_directory(base_dir=str(temp_base), prefix="async_") as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            assert "async_" in temp_dir.name

    @pytest.mark.asyncio
    async def test_async_temp_directory_cleanup_on_exit(self, temp_base):
        """Test that async_temp_directory cleans up on normal exit."""
        async with async_temp_directory(base_dir=str(temp_base)) as temp_dir:
            (temp_dir / "file.txt").write_text("content")
            temp_path = temp_dir

        assert not temp_path.exists()

    @pytest.mark.asyncio
    async def test_async_temp_directory_cleanup_on_exception(self, temp_base):
        """Test that async_temp_directory cleans up even on exception."""
        temp_path = None
        try:
            async with async_temp_directory(base_dir=str(temp_base)) as temp_dir:
                temp_path = temp_dir
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert temp_path is not None
        assert not temp_path.exists()


class TestCleanupDirectory:
    """Tests for cleanup_directory function."""

    def test_cleanup_directory_removes_dir(self, temp_base):
        """Test cleanup_directory removes directory and contents."""
        test_dir = temp_base / "to_cleanup"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "nested.txt").write_text("nested")

        result = cleanup_directory(test_dir)

        assert result is True
        assert not test_dir.exists()

    def test_cleanup_directory_nonexistent_returns_true(self, temp_base):
        """Test cleanup_directory returns True for nonexistent dir."""
        nonexistent = temp_base / "nonexistent"

        result = cleanup_directory(nonexistent)

        assert result is True


class TestCleanupOldTempDirs:
    """Tests for cleanup_old_temp_dirs function."""

    def test_cleanup_old_removes_old_dirs(self, temp_base):
        """Test cleanup removes directories older than max_age."""
        # Create old directory
        old_dir = temp_base / "chain_old"
        old_dir.mkdir()
        (old_dir / "file.txt").write_text("old")

        # Make it "old" by setting mtime in the past
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        import os
        os.utime(old_dir, (old_time, old_time))

        # Create recent directory
        new_dir = temp_base / "chain_new"
        new_dir.mkdir()
        (new_dir / "file.txt").write_text("new")

        # Cleanup with 24 hour max age
        removed = cleanup_old_temp_dirs(base_dir=str(temp_base), max_age_hours=24)

        assert removed == 1
        assert not old_dir.exists()
        assert new_dir.exists()

    def test_cleanup_old_nonexistent_base_returns_zero(self, temp_base):
        """Test cleanup returns 0 for nonexistent base dir."""
        removed = cleanup_old_temp_dirs(base_dir=str(temp_base / "nonexistent"))

        assert removed == 0

    def test_cleanup_old_ignores_non_chain_dirs(self, temp_base):
        """Test cleanup only removes directories with 'chain_' prefix."""
        # Create directory without prefix
        other_dir = temp_base / "other_dir"
        other_dir.mkdir()
        (other_dir / "file.txt").write_text("content")

        # Make it old
        old_time = time.time() - (25 * 3600)
        import os
        os.utime(other_dir, (old_time, old_time))

        removed = cleanup_old_temp_dirs(base_dir=str(temp_base), max_age_hours=24)

        assert removed == 0
        assert other_dir.exists()
