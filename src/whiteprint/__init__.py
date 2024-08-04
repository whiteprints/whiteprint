"""Top-level module."""

import importlib
from typing import Final

from whiteprint.version import __version__


__all__: Final = ["__version__"]
"""Public module attributes."""


if __debug__:
    beartype = importlib.import_module("beartype")
    beartype_claw = importlib.import_module("beartype.claw")
    beartype_claw.beartype_this_package(
        conf=beartype.BeartypeConf(is_color=False),
    )

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    if load_dotenv(".env"):
        importlib.import_module("logging").get_logger(__name__).info(
            "Loading environment variables from `.env` file."
        )
