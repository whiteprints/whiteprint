"""Test the console module."""

from rich import console as rich_console

from whiteprint import console as whiteprint_console


def test_default_console() -> None:
    """Check that the console is a rich console instance."""
    assert isinstance(whiteprint_console.STDOUT, rich_console.Console)
