"""Command-Line Interface user defined exceptions."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from click.exceptions import UsageError


if sys.version_info < (3, 12):  # pragma: nocover
    from typing_extensions import override
else:
    from typing import override


__all__: Final = [
    "InvalidAppNameError",
    "InvalidYAMLError",
    "UnsupportedTypeInMappingError",
]


class UnsupportedTypeInMappingError(UsageError):
    """The given type is not supported."""

    @override
    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__("The mapping contains unsupported type.")


@dataclass
class InvalidYAMLError(UsageError):
    """The YAML file is invalid."""

    path: Path
    error: str

    def __post_init__(self) -> None:
        """Initialize the exception.

        Args:
            path: path to the invalid YAML file.
            error: the parser error message.
        """
        super().__init__(
            f"{self.path} is not a valid YAML file, {self.error}.",
        )


@dataclass
class InvalidAppNameError(ValueError):
    """The application name is invalid."""

    app_name: str

    def __post_init__(self) -> None:
        """Initialize the exception."""
        super().__init__(
            f"{self.app_name} is not a valid application name. `__app_name__` "
            "must contain only ASCII alphanumeric characters or underscores "
            "or dashes."
        )
