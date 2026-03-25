"""Paths to Blondon_memory sqlite dumps (repo root, next to src/)."""

from __future__ import annotations

from pathlib import Path


def blondon_memory_dir() -> Path:
    """Return `<repo>/Blondon_memory` regardless of current working directory."""
    return Path(__file__).resolve().parents[2] / "Blondon_memory"
