"""Filesystem utilities."""

import contextlib
import logging
import os
from collections.abc import Generator
from pathlib import Path
from typing import Final

from whiteprint.loc import _


__all__: Final = ["working_directory"]
"""Public module attributes."""


@contextlib.contextmanager
def working_directory(path: Path) -> Generator[None, None, None]:
    """Sets the current working directory (cwd) within the context.

    Args:
        path (Path): The path to the cwd

    Yields:
        None
    """
    # It is important to resolve the current directory before using chdir,
    # after the chdir function is called, the information about the current
    # directory is definitively lost, hence the absolute path of the current
    # directory must be known before.
    origin = Path.cwd()
    logger = logging.getLogger(__name__)
    try:
        new_directory = path.resolve()
        logger.debug(_("Changing current directory to: %s"), new_directory)
        os.chdir(new_directory)
        yield
    finally:
        logger.debug(_("Changing current directory to: %s"), origin)
        os.chdir(origin)
