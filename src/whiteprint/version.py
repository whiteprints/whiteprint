"""Discover the package's version number."""

from importlib import metadata
from typing import Final


__all__: Final = ["__version__"]
"""Public module attributes."""

__version__: Final = (
    metadata.version(__package__) if __package__ else "package not found"
)
"""The package version number as found by importlib metadata."""
