"""Test the Click app."""

import importlib


def test_import_click_app() -> None:
    """Test that we can import a click app."""
    assert importlib.import_module(
        "whiteprint.cli._click_app",
    ).__click_app__, "Click app not found."
