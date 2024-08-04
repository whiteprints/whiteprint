"""Manage python Whiteprint tools."""

import logging
import sys
from dataclasses import dataclass, field
from logging import Logger
from subprocess import CalledProcessError  # nosec
from typing import Final, TypedDict

import rich_click as click

from whiteprint import start_process
from whiteprint.loc import _
from whiteprint.project_manager import (
    PROJECT_MANAGER_NAME,
    ProjectManagerNotFoundError,
)


if sys.version_info < (3, 11):  # pragma: nocover
    from typing_extensions import Unpack
else:
    from typing import Unpack


def which_installed_tools(project_manager: str) -> list[str]:
    """Find the tools installed.

    Returns:
        A list of installed tools.
    """
    return (
        str(
            start_process.start_in_directory(
                [project_manager, "tool", "list"],
                capture_output=True,
                encoding="utf-8",
            ).stdout,
        )
        .strip()
        .split()
    )


@dataclass
class Tool:
    """A project tool.

    Attributes:
        name: the name of the tool
        commands: the commands exposed by the tools
    """

    name: str
    commands: list[str]
    extras: list[str] = field(default_factory=list)


WHITEPRINT_TOOLS: Final = (
    Tool(name="Babel", commands=["pybabel"]),
    Tool(name="bandit", commands=["bandit"]),
    Tool(name="blacken-docs", commands=["blacken-docs"]),
    Tool(name="pre-commit", commands=["pre-commit"]),
    Tool(name="pyright", commands=["pyright"]),
    Tool(name="radon", commands=["radon"]),
    Tool(name="reuse", commands=["reuse"]),
    Tool(name="ruff", commands=["ruff"]),
    Tool(name="tox", commands=["tox"], extras=["tox-uv"]),
    Tool(name="tox-ini-fmt", commands=["tox-ini-fmt"]),
    Tool(name="tryceratops", commands=["tryceratops"]),
    Tool(name="uv", commands=["uv"]),
    Tool(name="xenon", commands=["xenon"]),
    Tool(name="yq", commands=["tomlq"]),
    Tool(name="build", commands=["pyproject-build"]),
)


@click.group(help=_("Manage whiteprint tools."))
def tool() -> None:
    """Manage whiteprint tools."""


@tool.command()
def list_tools() -> None:
    """List the tools installed."""
    project_manager = start_process.which(
        PROJECT_MANAGER_NAME, exception=ProjectManagerNotFoundError
    )
    start_process.start_in_directory([project_manager, "tool", "list"])


class InstallArgsType(TypedDict):
    """The install command arguments types.

    Attributes:
        reinstall: reinstall a tool.
        refresh: refresh all the cached data.
        upgrade: upgrade a tool.
    """

    reinstall: bool
    refresh: bool
    upgrade: bool


@tool.command()
@click.option(
    "--upgrade",
    "-U",
    type=bool,
    help=_(
        "Allow package upgrades, ignoring pinned versions in any existing "
        "output file"
    ),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--reinstall",
    type=bool,
    help=_(
        "Reinstall all packages, regardless of whether they're already "
        "installed. Implies `--refresh`."
    ),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--refresh",
    type=bool,
    help=_("Refresh all cached data."),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--force",
    type=bool,
    help=_("Force installation of the tool."),
    is_flag=True,
    default=False,
    show_default=True,
)
def install(**kwargs: Unpack[InstallArgsType]) -> None:
    """Install the global tools required by whiteprint projects."""
    project_manager = start_process.which(
        PROJECT_MANAGER_NAME, exception=ProjectManagerNotFoundError
    )

    command_prefix = [
        project_manager,
        "tool",
        "install",
        "--quiet",
        *[f"--{key}" for key in kwargs],
    ]

    logger = logging.getLogger(__name__)
    for tool in WHITEPRINT_TOOLS:
        command = [*command_prefix, tool.name]
        if tool.extras:
            command += ["--with", *tool.extras]

        _try_install_tool(command, logger=logger)


def _try_install_tool(command: list[str], *, logger: Logger) -> None:
    """Try to install a tool.

    Args:
        command: the command to exectute to instal the tool.
        logger: a logger instance.
    """
    try:
        start_process.start_in_directory(command)
    except CalledProcessError:
        logger.warning(
            _(
                "Failed to install tool '%s'. "
                "Some functionalities may be missing."
            ),
            tool.name,
        )
    else:
        logger.info(_("Installed tool: %s"), tool.name)


@tool.command()
def uninstall() -> None:
    """Uninstall the global tools required by whiteprint projects."""
    project_manager = start_process.which(
        PROJECT_MANAGER_NAME, exception=ProjectManagerNotFoundError
    )
    installed_tools = which_installed_tools(project_manager)

    command_prefix = [project_manager, "tool", "uninstall", "--quiet"]
    logger = logging.getLogger(__name__)
    for tool in WHITEPRINT_TOOLS:
        if tool.name in installed_tools:
            start_process.start_in_directory(
                [*command_prefix, tool.name],
            )
            logger.info(_("Uninstalled tool: %s"), tool)
