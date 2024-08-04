"""Hatch build hook for localization."""

from pathlib import Path

from babel.messages.frontend import compile_catalog
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Custome Hatch builld hook for localization using PyBabel."""

    @staticmethod
    def initialize(_version: str, _build_data: dict[str, object]) -> None:
        """Initialize the build hook."""
        for locale_path in map(
            Path,
            (
                "src/whiteprint/locale",
                "whiteprint/locale",
            ),
        ):
            if locale_path.is_dir():
                cmd = compile_catalog()
                cmd.initialize_options()
                cmd.directory = locale_path
                cmd.use_fuzzy = True
                cmd.finalize_options()
                cmd.run()
