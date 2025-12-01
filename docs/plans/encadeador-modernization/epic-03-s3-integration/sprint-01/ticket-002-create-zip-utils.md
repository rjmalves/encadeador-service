# [S3-002] Create zip utilities

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0

## Context

### Background

DECOMP/NEWAVE artifacts are stored as zip files in S3. We need utilities to extract downloaded zips and create new zips for upload.

### Relation to Epic

Required for artifact handling in S3 workflow.

## Specification

### File to Create

**Path**: `app/utils/zip_utils.py`

### Functions

```python
"""Zip file utilities for artifact handling."""

import zipfile
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """
    Extract zip file to directory.
    
    Args:
        zip_path: Path to zip file
        extract_to: Directory to extract to
        
    Raises:
        FileNotFoundError: If zip file doesn't exist
        zipfile.BadZipFile: If file is not a valid zip
    """
    logger.info(f"Extracting {zip_path} to {extract_to}")
    extract_to.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)


def create_zip(
    source_dir: Path,
    zip_path: Path,
    compression: int = zipfile.ZIP_DEFLATED,
    compression_level: int = 6,
) -> None:
    """
    Create zip file from directory contents.
    
    Args:
        source_dir: Directory to zip
        zip_path: Output zip path
        compression: Compression method
        compression_level: Compression level (1-9)
    """
    logger.info(f"Creating {zip_path} from {source_dir}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(
        zip_path, "w", compression=compression, compresslevel=compression_level
    ) as zf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir)
                zf.write(file_path, arcname)


def extract_file_from_zip(
    zip_path: Path,
    filename: str,
    extract_to: Optional[Path] = None,
) -> bytes:
    """
    Extract single file from zip and return contents.
    
    Args:
        zip_path: Path to zip file
        filename: Name of file within zip
        extract_to: Optional path to write file
        
    Returns:
        File contents as bytes
        
    Raises:
        KeyError: If filename not in zip
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        content = zf.read(filename)
        
        if extract_to:
            extract_to.parent.mkdir(parents=True, exist_ok=True)
            extract_to.write_bytes(content)
        
        return content


def list_zip_contents(zip_path: Path) -> list[str]:
    """
    List files in zip archive.
    
    Args:
        zip_path: Path to zip file
        
    Returns:
        List of filenames in zip
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        return zf.namelist()
```

## Acceptance Criteria

- [ ] `zip_utils.py` created with all functions
- [ ] `extract_zip` extracts all files preserving structure
- [ ] `create_zip` creates valid zip from directory
- [ ] `extract_file_from_zip` returns file bytes
- [ ] `list_zip_contents` returns file list
- [ ] Unit tests cover all functions
- [ ] Logging for operations

## Implementation Guide

### Step 1: Copy from flexibilizador

```bash
cp /home/rogerio/git/flexibilizador-service/app/utils/zip_utils.py \
   /home/rogerio/git/encadeador-service/app/utils/zip_utils.py
```

### Step 2: Create tests

Create `tests/unit/test_zip_utils.py`:

```python
import pytest
import tempfile
from pathlib import Path
import zipfile

from app.utils.zip_utils import (
    extract_zip,
    create_zip,
    extract_file_from_zip,
    list_zip_contents,
)


@pytest.fixture
def sample_zip(tmp_path):
    """Create a sample zip file for testing."""
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file1.txt", "content1")
        zf.writestr("subdir/file2.txt", "content2")
    return zip_path


def test_extract_zip(sample_zip, tmp_path):
    extract_to = tmp_path / "extracted"
    extract_zip(sample_zip, extract_to)
    
    assert (extract_to / "file1.txt").read_text() == "content1"
    assert (extract_to / "subdir" / "file2.txt").read_text() == "content2"


def test_create_zip(tmp_path):
    # Create source directory
    source = tmp_path / "source"
    source.mkdir()
    (source / "test.txt").write_text("hello")
    
    # Create zip
    zip_path = tmp_path / "output.zip"
    create_zip(source, zip_path)
    
    # Verify
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, "r") as zf:
        assert "test.txt" in zf.namelist()


def test_extract_file_from_zip(sample_zip):
    content = extract_file_from_zip(sample_zip, "file1.txt")
    assert content == b"content1"


def test_list_zip_contents(sample_zip):
    contents = list_zip_contents(sample_zip)
    assert "file1.txt" in contents
    assert "subdir/file2.txt" in contents
```

### Step 3: Run tests

```bash
uv run pytest tests/unit/test_zip_utils.py -v
```

## Files to Read Before Starting

- `/home/rogerio/git/flexibilizador-service/app/utils/zip_utils.py` - Reference

## Definition of Done

- [ ] `zip_utils.py` created
- [ ] All unit tests passing
- [ ] Logging in place
- [ ] Type hints present
- [ ] Changes committed

## Blocked By

None (can be done in parallel with S3-003, S3-004)

## Blocks

- [S3-006](../sprint-02/ticket-006-create-s3-unitofwork.md) - UnitOfWork uses zip utils
