# [S3-003] Create temp directory manager

> **Epic**: [Epic 03: S3 Integration](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0

## Context

### Background

S3 artifacts must be downloaded to local temp directories for processing. The temp manager handles creation, tracking, and cleanup of these directories.

### Relation to Epic

Required for artifact processing workflow.

## Specification

### File to Create

**Path**: `app/utils/temp_manager.py`

### Class

```python
"""Temporary directory management for artifact processing."""

import tempfile
import shutil
from pathlib import Path
from typing import Optional
import logging
import uuid

from app.internal.settings import Settings
from app.internal.exceptions import TempDirectoryError

logger = logging.getLogger(__name__)


class TempDirectoryManager:
    """
    Manager for temporary directories.
    
    Creates temp directories for artifact processing and ensures cleanup.
    """
    
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """
        Initialize manager.
        
        Args:
            base_dir: Base directory for temp dirs (default from settings)
        """
        self._base_dir = base_dir or Path(Settings.temp_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._active_dirs: list[Path] = []
    
    def create_temp_dir(self, prefix: str = "") -> Path:
        """
        Create a new temporary directory.
        
        Args:
            prefix: Optional prefix for directory name
            
        Returns:
            Path to created directory
        """
        dir_name = f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex[:8]
        temp_dir = self._base_dir / dir_name
        temp_dir.mkdir(parents=True, exist_ok=True)
        self._active_dirs.append(temp_dir)
        logger.debug(f"Created temp directory: {temp_dir}")
        return temp_dir
    
    def cleanup_dir(self, temp_dir: Path) -> None:
        """
        Remove a specific temp directory.
        
        Args:
            temp_dir: Directory to remove
        """
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.debug(f"Removed temp directory: {temp_dir}")
        
        if temp_dir in self._active_dirs:
            self._active_dirs.remove(temp_dir)
    
    def cleanup_all(self) -> None:
        """Remove all active temp directories."""
        for temp_dir in list(self._active_dirs):
            self.cleanup_dir(temp_dir)
    
    def __enter__(self) -> "TempDirectoryManager":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup all directories."""
        self.cleanup_all()


def create_temp_dir_for_execution(execution_hash: str) -> Path:
    """
    Convenience function to create temp dir for an execution.
    
    Args:
        execution_hash: Execution identifier
        
    Returns:
        Path to temp directory
    """
    base_dir = Path(Settings.temp_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = base_dir / execution_hash
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    return temp_dir
```

## Acceptance Criteria

- [ ] `temp_manager.py` created with TempDirectoryManager class
- [ ] Creates directories under configurable base path
- [ ] Tracks active directories
- [ ] Cleans up on context manager exit
- [ ] Unit tests cover all methods
- [ ] No temp directories left after tests

## Implementation Guide

### Step 1: Copy from flexibilizador

```bash
cp /home/rogerio/git/flexibilizador-service/app/utils/temp_manager.py \
   /home/rogerio/git/encadeador-service/app/utils/temp_manager.py
```

### Step 2: Update imports

Ensure Settings reference matches encadeador settings.

### Step 3: Create tests

Create `tests/unit/test_temp_manager.py`:

```python
import pytest
from pathlib import Path

from app.utils.temp_manager import TempDirectoryManager, create_temp_dir_for_execution


def test_create_temp_dir(tmp_path):
    manager = TempDirectoryManager(base_dir=tmp_path)
    temp_dir = manager.create_temp_dir(prefix="test")
    
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    assert "test_" in temp_dir.name


def test_cleanup_dir(tmp_path):
    manager = TempDirectoryManager(base_dir=tmp_path)
    temp_dir = manager.create_temp_dir()
    
    # Create a file in the directory
    (temp_dir / "test.txt").write_text("hello")
    
    manager.cleanup_dir(temp_dir)
    
    assert not temp_dir.exists()


def test_context_manager_cleanup(tmp_path):
    with TempDirectoryManager(base_dir=tmp_path) as manager:
        temp_dir = manager.create_temp_dir()
        assert temp_dir.exists()
    
    # After context exit, should be cleaned up
    assert not temp_dir.exists()


def test_cleanup_all(tmp_path):
    manager = TempDirectoryManager(base_dir=tmp_path)
    dirs = [manager.create_temp_dir() for _ in range(3)]
    
    for d in dirs:
        assert d.exists()
    
    manager.cleanup_all()
    
    for d in dirs:
        assert not d.exists()
```

### Step 4: Run tests

```bash
uv run pytest tests/unit/test_temp_manager.py -v
```

## Files to Read Before Starting

- `/home/rogerio/git/flexibilizador-service/app/utils/temp_manager.py` - Reference

## Definition of Done

- [ ] `temp_manager.py` created
- [ ] All unit tests passing
- [ ] Context manager works correctly
- [ ] No temp directories leaked in tests
- [ ] Changes committed

## Blocked By

- [S3-004](./ticket-004-create-exceptions.md) - Uses TempDirectoryError

## Blocks

- [S3-006](../sprint-02/ticket-006-create-s3-unitofwork.md) - UnitOfWork uses temp manager
