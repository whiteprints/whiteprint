"""Test the main CLI."""

from click import testing

from whiteprint import version
from whiteprint.cli import entrypoint


class TestCLI:
    """Test the CLI."""

    @staticmethod
    def test_version(cli_runner: testing.CliRunner) -> None:
        """Check if the version printed by the CLI match the API one."""
        result = cli_runner.invoke(
            entrypoint.whiteprint,
            ["--version"],
        )
        assert result.exit_code == 0, "The CLI did not exit properly."
        assert version.__version__ == result.stdout.rstrip(), (
            "The python version returned by the CLI do not match the API"
            " version (given by __version__)."
        )

    @staticmethod
    def test_help_flag_exists(cli_runner: testing.CliRunner) -> None:
        """Check if the version printed by the CLI match the API one."""
        result = cli_runner.invoke(
            entrypoint.whiteprint,
            ["--help"],
        )
        assert result.exit_code == 0, "The CLI did not exit properly."

    @staticmethod
    def test_default(cli_runner: testing.CliRunner) -> None:
        """Check if the CLI called with default arguments return prpperly.

        Args:
            cli_runner: the CLI test runner provided by typer.testing or a
                fixture.
        """
        result = cli_runner.invoke(entrypoint.whiteprint)
        assert result.exit_code == 0, "The CLI did not exit properly."
