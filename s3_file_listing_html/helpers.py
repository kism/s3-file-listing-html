"""Helper functions for file wrangling."""

import shutil
from pathlib import Path

from .constants import STATIC_PATH


def copy_static_files(output_path: Path) -> None:
    """Copy static files to the output path."""
    if STATIC_PATH.exists():
        shutil.copytree(STATIC_PATH, output_path / "static", dirs_exist_ok=True)
    else:
        msg = f"Static path does not exist: {STATIC_PATH}"
        raise FileNotFoundError(msg)
