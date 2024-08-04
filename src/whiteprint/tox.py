"""Git related functionalities."""

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from whiteprint import start_process
from whiteprint.loc import _


__all__: Final = ["ToxError", "ToxNotFoundError", "run"]
"""Public module attributes."""


_TOX_SIGINT_EXIT: Final = 130
"""Nox return code when a SIGINT (ctl+c) is captured."""

_TOX_SUCCESS: Final = 0
"""Tox success return code."""


class ToxNotFoundError(RuntimeError):
    """Tox is not found on the system."""

    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__(_("Tox not found."))


@dataclass
class ToxError(RuntimeError):
    """A Tox error occured.

    Attributes:
        exit_code: Tox's exit code.
    """

    exit_code: int

    def __post_init__(self) -> None:
        """Initialize the Tox error."""
        super().__init__(_("Tox exit code: {}").format(self.exit_code))


def run(destination: Path, *, args: list[str]) -> None:
    """Run a Tox command.

    Args:
        destination: the path of the Tox repository (directory containing a
            file named `tox.ini`).
        args: a list of arguments passed to the tox command.

    Raises:
        ToxError: tox return code is not 0 (_TOX_SUCCESS).
        KeyboardInterrupt: tox return code is 130.
    """
    command = [
        start_process.which("tox", exception=ToxNotFoundError),
        "run",
        *args,
    ]
    completed_process = start_process.start_in_directory(
        command=command,
        working_directory=destination,
    )

    if (
        exit_code := completed_process.returncode
    ) == _TOX_SIGINT_EXIT:  # pragma: no cover
        # We ignore covering the SIGINT case **yet** as it is difficult to test
        # for little benefits.
        # To test this case, we need to run the function in a different
        # process, find the pid and eventualy kill this pid. Also note that
        # multiprocess coverage is non trivial and might require changes in
        # coverage's configuration.
        raise KeyboardInterrupt

    if exit_code != _TOX_SUCCESS:
        raise ToxError(exit_code)
