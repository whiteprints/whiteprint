"""Everything related to the command line interface."""

import importlib
from typing import Final


__all__: Final = ["APP_NAME", "__app_name__"]

__app_name__: Final = "whiteprint"
"""The name of the application."""

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    if load_dotenv(".env"):
        importlib.import_module("logging").get_logger(__name__).info(
            "Loading environment variables from `.env` file."
        )

if __debug__ and not (
    __app_name__.replace("_", "").replace("-", "").isalnum()
    and __app_name__.isascii()
):
    raise importlib.import_module(
        "whiteprint.cli.exceptions", __package__
    ).InvalidAppNameError(__app_name__)

APP_NAME = __app_name__.replace("-", "_").upper()
"""The name of the application in capital letters."""
