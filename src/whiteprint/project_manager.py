"""Rye."""

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from whiteprint import start_process


__all__: Final = [
    "PROJECT_MANAGER_NAME",
    "ProjectManagerNotFoundError",
    "lock",
]
"""Public module attributes."""


PROJECT_MANAGER_NAME: Final = "uv"


@dataclass
class ProjectManagerNotFoundError(RuntimeError):
    """The project manager was not found on the system."""

    project_manager_name: str

    def __post_init__(self) -> None:
        """Initialize the exception.

        Args:
            project_manager_name: the name of the project manager.
        """
        super().__init__(
            f"The project manager '{self.project_manager_name}' was not found",
        )


class LockingFailedError(RuntimeError):
    """Loocking failed."""


def lock(
    destination: Path,
    *,
    quiet: bool = True,
) -> None:
    """Run lock.

    Args:
        destination: the path of the Poetry repository (directory containing
            the file named `pyproject.toml`).
        quiet: if True run the locking process in quiet mode otherwise run in
            verbose mode.
        no_cache: disable cache for locking.
    """
    command: list[str] = [
        start_process.which(
            PROJECT_MANAGER_NAME, exception=ProjectManagerNotFoundError
        ),
        "lock",
        "--upgrade",
    ]

    # We ignore covering the --quiet and --verbose flags **yet** as it is
    # difficult to test for little benefits. These flags are not supposed
    # to change the locking results.
    if quiet:  # pragma: no cover
        command += ["--quiet"]
    else:  # pragma: no cover
        command += ["--verbose"]

    start_process.start_in_directory(command, working_directory=destination)
