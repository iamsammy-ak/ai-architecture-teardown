"""Locating the project root (the directory that holds ``bench/manifest.yaml``)."""

from __future__ import annotations

from pathlib import Path

MARKER = Path("bench") / "manifest.yaml"


def project_root(start: Path | None = None) -> Path:
    """The nearest directory at or above ``start`` (default: the working directory) that contains the manifest.

    Falls back to the source checkout this package lives in, so commands work from any subdirectory of the
    repository and from an editable install.
    """
    candidates = [start or Path.cwd(), Path(__file__).resolve().parents[2]]
    for base in candidates:
        for directory in (base, *base.parents):
            if (directory / MARKER).is_file():
                return directory
    raise FileNotFoundError(f"could not find {MARKER.as_posix()} above {candidates[0]}")
