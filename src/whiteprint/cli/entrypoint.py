"""Command Line Interface app entrypoint."""

import importlib
import os
from functools import lru_cache
from importlib.util import find_spec
from pathlib import Path
from typing import Final, TextIO, TypedDict, get_args

import rich_click as click
from rich_click import Command, Context, File
from rich_click.rich_command import RichGroup as Group
from typing_extensions import Unpack, override

from whiteprint.cli import APP_NAME, __app_name__
from whiteprint.cli.logging import LogLevel, configure_logging
from whiteprint.loc import _


__all__: Final = ["whiteprint"]
"""Public module attributes."""


class LazyCommandLoader(Group):
    """Lazy commands loader.

    Loads lazily all the commands in the submodule .commads. The file
    __init__.py is ignored.
    """

    @staticmethod
    def _commands_submodules() -> list[str]:
        """Find sumnodules path.

        Returns:
            A list of discovered submodules.
        """
        if (
            commands := find_spec(
                "whiteprint.cli.commands",
                __package__,
            )
        ) is None:
            return []

        if (
            commands_submodules := commands.submodule_search_locations
        ) is None:
            return []

        return commands_submodules

    @lru_cache
    @staticmethod
    def _list_commands() -> list[str]:
        """List all the commands.

        Returns:
            A list of commands names.
        """
        commands_submodules = LazyCommandLoader._commands_submodules()
        commands_names = [
            stem
            for command in commands_submodules
            for file in Path(command).glob("*.py")
            if (stem := file.stem) != "__init__"
        ]

        commands_names.sort()
        return commands_names

    @override
    def list_commands(self, ctx: Context) -> list[str]:
        """List all the commands.

        Args:
            ctx: unused.

        Returns:
            A list of commands names.
        """
        return LazyCommandLoader._list_commands()

    @override
    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        """Invoke a command.

        The command must have the name of the module.

        Args:
            ctx: the click context (unused).
            cmd_name: the name of the command to invoke.

        Returns:
            A command.
        """
        try:
            return getattr(
                importlib.import_module(
                    f"whiteprint.cli.commands.{cmd_name}",
                    __package__,
                ),
                cmd_name,
            )
        except (ImportError, AttributeError):
            return None


class CLIArgsType(TypedDict):
    """The CLI arguments types."""

    log_level: LogLevel
    log_file: TextIO


@click.command(
    cls=LazyCommandLoader,
    name=__app_name__,
    help=_(
        "Thank you for using {}, a tool to generate minimal Python projects."
    ).format(__app_name__),
    no_args_is_help=True,
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(
        get_args(LogLevel),
        case_sensitive=False,
    ),
    help=_("Logging verbosity."),
    default=os.environ.get(f"{APP_NAME}_LOG_LEVEL", "ERROR"),
    show_default=True,
)
@click.option(
    "-f",
    "--log-file",
    type=File(
        mode="w",
        encoding="utf-8",
        lazy=True,
    ),
    help=_("A file in which to write the log."),
    default=os.environ.get(f"{APP_NAME}_LOG_FILE", "-"),
    show_default=True,
)
@click.version_option()
def whiteprint(**kwargs: Unpack[CLIArgsType]) -> None:
    """The Whiteprint CLI."""
    configure_logging(
        level=kwargs["log_level"],
        file=kwargs["log_file"],
    )
