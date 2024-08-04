"""Logging configuration for the CLI."""

import importlib
import logging
from typing import Final, Literal, TextIO, TypeAlias

from whiteprint import console
from whiteprint.loc import _


__all__: Final = ["LogLevel", "configure_logging"]


LogLevel: TypeAlias = Literal[
    "CRITICAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
]


def configure_logging(
    level: LogLevel,
    *,
    file: TextIO,
    log_format: str = _(
        "[{process}:{thread}] [{pathname}:{funcName}:{lineno}]\n{message}",
    ),
    date_format: str = _("[%Y-%m-%dT%H:%M:%S]"),
) -> None:
    """Configure Rich logging handler.

    Args:
        level: The logging verbosity level.
        file: An optional file in which to log.
        log_format: The log message format.
        date_format: The log date format.

    Example:
        >>> from whiteprint.cli.cli_types import LogLevel
        >>>
        >>> configure_logging("INFO")
        None

    See Also:
        https://rich.readthedocs.io/en/stable/logging.html
    """
    rich_traceback = importlib.import_module("rich.traceback")
    suppress = [
        importlib.import_module("beartype"),
        importlib.import_module("click"),
        importlib.import_module("rich"),
        importlib.import_module("rich_click"),
    ]

    rich_traceback.install(
        show_locals=True,
        suppress=suppress,
    )
    handlers = [
        importlib.import_module("rich.logging").RichHandler(
            console=console.STDERR,
        )
        if file.name == "-"
        else logging.StreamHandler(file),
    ]

    logging.basicConfig(
        format=f"{{asctime}}{log_format}",
        handlers=handlers,
        level=level.upper(),
        datefmt=date_format,
        style="{",
    )
    logging.captureWarnings(capture=True)
