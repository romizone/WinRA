"""Utility functions for WinRA application."""

import os
import sys
from pathlib import Path


SUPPORTED_EXTENSIONS = {".zip", ".rar"}


def is_supported_archive(filepath: str) -> bool:
    """Check if file is a supported archive format."""
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS


def get_archive_type(filepath: str) -> str | None:
    """Return archive type string or None if unsupported."""
    ext = Path(filepath).suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return ext.lstrip(".")
    return None


def get_default_extract_dir(archive_path: str) -> str:
    """Get default extraction directory (same dir as archive, named after archive)."""
    p = Path(archive_path)
    return str(p.parent / p.stem)


def get_default_output_path(source_path: str, target_ext: str) -> str:
    """Get default output path for conversion."""
    p = Path(source_path)
    if not target_ext.startswith("."):
        target_ext = f".{target_ext}"
    return str(p.with_suffix(target_ext))


def ensure_dir(dirpath: str) -> str:
    """Create directory if it doesn't exist. Returns the path."""
    os.makedirs(dirpath, exist_ok=True)
    return dirpath


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)
