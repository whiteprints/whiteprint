"""Subprocess related functionalities."""

import logging
import shutil
import subprocess  # nosec
from pathlib import Path
from subprocess import CompletedProcess  # nosec

from whiteprint import filesystem
from whiteprint.loc import _


def which(tool: str, *, exception: type[Exception]) -> str:
    """Find a ressource on the system.

    Args:
        tool: the ressource to find.
        exception: the exception to raise if the tool is not found.

    Returns:
        a path to the program.
    """
    if (tool_path := shutil.which(tool)) is None:  # pragma: no cover
        raise exception(tool)

    return tool_path


def start_in_directory(
    command: list[str],
    *,
    working_directory: Path = Path(),
    capture_output: bool = False,
    encoding: str | None = None,
) -> CompletedProcess[bytes]:
    """Start a subprocess in a working directory.

    Args:
        command: the command to execute in the subprocess.
        capture_output: capture the output of the command.
        encoding: encoding for the stdin, stderr and stdout streams.
        working_directory: the working directory of the subprocess.

    Returns:
        A completed process instance.
    """
    logger = logging.getLogger(__name__)
    logger.debug(_("Starting process: '%s'"), " ".join(command))
    with filesystem.working_directory(working_directory):
        completed_process = subprocess.run(  # nosec
            command,
            shell=False,
            check=True,
            capture_output=capture_output,
            encoding=encoding,
        )

    logger.debug(
        _(
            "Completed process: '%s' with return code %d."
            " Captured stdout: %s."
            " Captured stderr: %s",
        ),
        completed_process.args,
        completed_process.returncode,
        completed_process.stdout,
        completed_process.stderr,
    )
    return completed_process
