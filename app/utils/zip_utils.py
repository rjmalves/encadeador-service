"""
Zip file utilities for DECOMP/NEWAVE artifact handling.

This module provides functions to extract and create zip files
for deck processing.
"""

import zipfile
from pathlib import Path

from app.utils.log import Log


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """
    Extract a zip file to a destination directory.

    All files are extracted to the root of dest_dir (no subdirectories).

    Args:
        zip_path: Path to the zip file
        dest_dir: Directory to extract files to

    Raises:
        zipfile.BadZipFile: If zip file is corrupted
        FileNotFoundError: If zip file doesn't exist
    """
    Log.log().info(f"Extracting {zip_path} to {dest_dir}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Validate zip integrity
        bad_file = zf.testzip()
        if bad_file is not None:
            raise zipfile.BadZipFile(f"Corrupted file in archive: {bad_file}")

        zf.extractall(dest_dir)

    Log.log().info(f"Extracted {len(list(dest_dir.iterdir()))} files")


def create_zip(
    source_dir: Path,
    zip_path: Path,
    compression_level: int = 6,
) -> None:
    """
    Create a zip file from all files in a directory.

    Files are added at root level (no directory structure preserved).

    Args:
        source_dir: Directory containing files to zip
        zip_path: Path for the output zip file
        compression_level: Compression level (0-9, default 6)

    Raises:
        FileNotFoundError: If source_dir doesn't exist
        ValueError: If source_dir is empty
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    files = [f for f in source_dir.iterdir() if f.is_file()]
    if not files:
        raise ValueError(f"Source directory is empty: {source_dir}")

    Log.log().info(f"Creating zip {zip_path} from {len(files)} files")

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=compression_level,
    ) as zf:
        for file_path in files:
            # Add file at root level (just filename, no path)
            zf.write(file_path, file_path.name)

    Log.log().info(f"Created zip: {zip_path} ({zip_path.stat().st_size} bytes)")


def get_zip_file_list(zip_path: Path) -> list[str]:
    """
    Get list of files in a zip archive.

    Args:
        zip_path: Path to the zip file

    Returns:
        List of filenames in the archive
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        return zf.namelist()
