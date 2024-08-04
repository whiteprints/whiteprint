"""Initialize a new Python project."""

import importlib
import logging
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict, TypeGuard, cast

import platformdirs
import rich_click as click
from click import Path as ClickPath
from click.core import Context, Parameter
from returns.maybe import Maybe

from whiteprint.cli import APP_NAME, __app_name__
from whiteprint.cli.exceptions import (
    InvalidYAMLError,
    UnsupportedTypeInMappingError,
)
from whiteprint.loc import _


if sys.version_info < (3, 11):  # pragma: nocover
    from typing_extensions import Unpack
else:
    from typing import Unpack


__all__: Final = ["init"]
"""Public module attributes."""


Yaml = dict[str, str | int]


YAML_EXT: Final = [".yaml", ".yml"]
COPIER_ANSWER_FILE: Final = Path(".copier-answers.yml")
LABEL_FILE: Final = Path(".github/labels.yml")


@dataclass
class RepositoryConfiguration:
    """The repository configuration.

    Attributes:
        github_token: a github token
        https_origin: use https origin instead of ssh
    """

    github_token: str | None = None
    https_origin: bool = False


def read_yaml(data: Path) -> Yaml:
    """Read a yaml file.

    Use PyYAML `safe_load`.

    Args:
        data: path to a yaml file.

    Raises:
        InvalidYAMLError: the yaml loaded was invalid (a parsing error
            occured).
        UnsupportedTypeInMappingError: a type found in the loaded yaml file is
            not supported.

    Returns:
        The content of the YAML file.
    """
    if not data.is_file():
        return {}

    yaml = importlib.import_module("yaml")
    yaml_parser = importlib.import_module("yaml.parser")
    with data.open("r") as data_file:
        try:
            copier_data: dict[str, object | None] = (
                yaml.safe_load(data_file) or {}
            )
        except yaml_parser.ParserError as parser_error:
            raise InvalidYAMLError(
                Path(data_file.name),
                str(parser_error),
            ) from parser_error

        if _check_dict(copier_data):
            return copier_data

    raise UnsupportedTypeInMappingError


def _copy_license_to_project_root(destination: Path) -> None:
    """Add the license to the COPYING file.

    Forward the license or copyright header from the LICENSE directory to the
    COPYING file.

    Args:
        destination: path to the python project.
    """
    license_name: str = (
        (destination / "COPYING").read_text(encoding="utf-8").strip()
    )
    license_path: Path = destination / "LICENSES" / f"{license_name}.txt"
    if license_path.is_file():
        shutil.copy(
            license_path,
            destination / "COPYING",
        )


def _format_code(
    destination: Path,
    *,
    python: str | None,
) -> None:
    """Reformat the source code with pre-commit if needed.

    Args:
        destination: path to the python project.
        python: force using the given python interpreter for the post
            processing.
    """
    tox = importlib.import_module(
        "whiteprint.tox",
        __package__,
    )
    try:  # pragma: no cover
        tox.run(
            destination=destination,
            args=[
                *(
                    Maybe.from_optional(python)
                    .map(lambda _python: ("--force-python", _python))
                    .value_or(())
                ),
                "-e",
                "pre-commit",
            ],
        )
    except tox.ToxError as tox_error:
        logger = logging.getLogger(__name__)
        logger.debug(
            "Code has been reformated (Nox exit code: %s).",
            tox_error.exit_code,
        )


def _download_licenses(
    destination: Path,
    *,
    python: str | None,
) -> None:
    """Download the needed licenses.

    Args:
        destination: path to the python project.
        python: force using the given python interpreter for the post
            processing.
    """
    tox = importlib.import_module(
        "whiteprint.tox",
        __package__,
    )
    tox.run(
        destination=destination,
        args=[
            *(
                Maybe.from_optional(python)
                .map(lambda _python: ("--force-python", _python))
                .value_or(())
            ),
            "-e",
            "download-licenses",
        ],
    )
    _copy_license_to_project_root(destination)


def _post_processing(
    destination: Path,
    *,
    skip_tests: bool,
    python: str | None,
    repository_configuration: RepositoryConfiguration,
) -> None:
    """Apply post processing steps after rendering the template wit Copier.

    Args:
        destination: path to the python project.
        skip_tests: skip the Nox tests step.
        python: force using the given python interpreter for the post
            processing.
        repository_configuration: the configuration of the repository.
    """
    version_control = importlib.import_module(
        "whiteprint.version_control",
        __package__,
    )
    tox = importlib.import_module(
        "whiteprint.tox",
        __package__,
    )
    project_manager = importlib.import_module(
        "whiteprint.project_manager",
        __package__,
    )

    # Create lockfile
    project_manager.lock(destination)

    repository = version_control.init_and_commit(
        destination,
        commit_data=version_control.CommitData(
            message="chore: 🥇 inital commit."
        ),
    )

    # Download the required licenses.
    _download_licenses(
        destination,
        python=python,
    )
    version_control.add_and_commit(
        repository,
        commit_data=version_control.CommitData(
            message="chore: 📃 download license(s)."
        ),
    )

    force_python = (
        Maybe.from_optional(python)
        .map(lambda _python: ("--force-python", _python))
        .value_or(())
    )
    # Generate the dependencies table.
    tox.run(
        destination=destination,
        args=[
            *force_python,
            "-e",
            "export-supply-chain-licenses",
        ],
    )
    version_control.add_and_commit(
        repository,
        commit_data=version_control.CommitData(
            message="docs: 📚 add depencencies."
        ),
    )

    # Fixes with pre-commit.
    _format_code(
        destination,
        python=python,
    )
    version_control.add_and_commit(
        repository,
        commit_data=version_control.CommitData(
            message="chore: 🔨 format code."
        ),
    )

    # Check that nox passes.
    if not skip_tests:
        tox.run(
            destination=destination,
            args=[
                *force_python,
            ],
        )

    if repository_configuration.github_token is not None:
        copier_answers = read_yaml(destination / COPIER_ANSWER_FILE)
        github_user = version_control.GithubUser(
            token=importlib.import_module("github.Auth").Auth.Token(
                repository_configuration.github_token,
            ),
            login=str(copier_answers["github_user"]),
        )
        version_control.setup_github_repository(
            repository,
            project_slug=str(copier_answers["project_slug"]),
            github_user=github_user,
            labels=destination / LABEL_FILE,
        )
        version_control.protect_repository(
            repository,
            project_slug=str(copier_answers["project_slug"]),
            github_user=github_user,
            https_origin=repository_configuration.https_origin,
        )


def _autocomplete_suffix(incomplete: Path) -> list[str]:
    """Autocomplete by listing files with a YAML extension.

    Args:
        incomplete: the incomplete argument to complete. Must be a path to a
            file with a suffix.

    Returns:
        A list of completions.
    """
    if all(incomplete.suffix not in ext for ext in YAML_EXT):
        return []

    return [
        candidate.name
        for candidate in incomplete.parent.glob(f"{incomplete.name}*")
    ]


def autocomplete_yaml_file(
    _ctx: Context | None,
    _param: Parameter | None,
    incomplete: str,
) -> list[str]:
    """Autocomplete by listing files with a YAML extension.

    Args:
        _ctx: unused
        _param: unused
        incomplete: the incomplete argument to complete.

    Returns:
        A list of completions.
    """
    path = Path(incomplete)
    if path.suffix:
        return _autocomplete_suffix(path)

    if path.is_dir():
        name: str = ""
    else:
        name: str = path.stem
        path: Path = path.parent

    proposal: list[str] = []
    for ext in YAML_EXT:
        candidates = path.glob(f"{name}*{ext}")
        proposal.extend(candidate.name for candidate in candidates)

    return proposal


def _check_dict(data: dict[str, object]) -> TypeGuard[Yaml]:
    """Check if the values type of a given dictionary are strings or integers.

    Args:
        data: the dictionary to check:

    Returns:
        a boolean (type guard) indicating whether the values are all strings or
        integers.
    """
    return all(isinstance(v, str | int) for v in data.values())


class InitArgsType(TypedDict):
    """The init command arguments types."""

    destination: Path
    whiteprint_source: str
    vcs_ref: str | None
    exclude: list[str] | None
    use_prereleases: bool
    skip_if_exists: list[str] | None
    no_cleanup_on_error: bool
    defaults: bool
    overwrite: bool
    pretend: bool
    quiet: bool
    skip_tests: bool
    data: Path
    no_data: bool
    user_defaults: Path | None
    python: str | None
    github_token: str | None
    https_origin: bool


@click.command(
    epilog=_(
        "This command mostly forwards copier's CLI. For more details see"
        " https://copier.readthedocs.io/en/stable/reference/cli/#copier.cli.CopierApp."
    ),
)
@click.argument(
    "destination",
    type=ClickPath(
        exists=False,
        file_okay=False,
        dir_okay=True,
        readable=False,
        writable=True,
        executable=False,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
    metavar="DIRECTORY",
    default=Path(),
)
@click.option(
    "--whiteprint-source",
    "-w",
    type=str,
    help=_(
        "The location of the Python Whiteprint Git repository (string"
        " that can be resolved to a template path, be it local or remote)."
    ),
    default=os.environ.get(
        f"{APP_NAME}_REPOSITORY", "gh:whiteprints/whiteprint.git"
    ),
    show_default=True,
)
@click.option(
    "--vcs-ref",
    "-v",
    type=str,
    help=_(
        "Specify the VCS tag/commit to use in the Python Whiteprint"
        " Git repository."
    ),
    default=os.environ.get(f"{APP_NAME}_REPOSITORY"),
    show_default=True,
)
@click.option(
    "--exclude",
    "-x",
    type=str,
    help=_(
        "User-chosen additional file exclusion patterns. Can be"
        " repeated to ignore multiple files."
    ),
    multiple=True,
    default=None,
    show_default=True,
)
@click.option(
    "--use-prereleases",
    "-P",
    type=bool,
    help=_(
        "Consider prereleases when detecting the latest one."
        " Useless if specifying a --vcs-ref."
    ),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--skip-if-exists",
    "-s",
    type=str,
    help=_(
        "User-chosen additional file skip patterns. Can be repeated to"
        " ignore multiple files."
    ),
    multiple=True,
    default=None,
    show_default=True,
)
@click.option(
    "--no-cleanup-on-error",
    "-C",
    type=bool,
    help=_("Do NOT delete the destination DIRECTORY if there is an error."),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--defaults",
    "-D",
    type=bool,
    help=_(
        "Use default answers to questions, which might be null if not"
        " specified."
    ),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--overwrite",
    "-O",
    type=bool,
    help=_("When set, overwrite files that already exist, without asking."),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--pretend",
    "-P",
    type=bool,
    help=_("When set, produce no real rendering."),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--quiet",
    "-Q",
    type=bool,
    help=_("When set, disable all output."),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--skip-tests",
    "-S",
    type=bool,
    help=_("Skip tests after initializing the repository."),
    is_flag=True,
    default=os.environ.get(f"{APP_NAME}_SKIP_TESTS", False),
    show_default=True,
)
@click.option(
    "--data",
    type=ClickPath(
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=False,
        executable=False,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
    help=_("User data."),
    shell_complete=autocomplete_yaml_file,
    default=os.environ.get(
        f"{APP_NAME}_DATA",
        Path(platformdirs.user_config_dir(__app_name__)) / "config.yml",
    ),
    show_default=True,
)
@click.option(
    "--no-data",
    "-n",
    help=_("Force not using --data."),
    is_flag=True,
    default=False,
)
@click.option(
    "--user-defaults",
    type=ClickPath(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=False,
        executable=False,
        resolve_path=True,
        allow_dash=False,
        path_type=Path,
    ),
    help=_("User defaults choices."),
    shell_complete=autocomplete_yaml_file,
    default=(
        Maybe.from_optional(os.environ.get(f"{APP_NAME}_USER_DEFAULTS"))
        .map(Path)
        .value_or(None)
    ),
    show_default=True,
)
@click.option(
    "--python",
    "-p",
    type=str,
    help=_(
        "force using the given python interpreter for the post processing."
    ),
    default=os.environ.get(f"{APP_NAME}_PYTHON"),
    show_default=True,
)
@click.option(
    "--github-token",
    type=str,
    help=_(
        "Github Token to push the newly created repository to"
        " Github. The token must have writing permissions."
    ),
    default=os.environ.get(f"{APP_NAME}_GITHUB_TOKEN"),
    show_default=True,
)
@click.option(
    "--https_origin",
    "-H",
    type=bool,
    help=_("Force the origin to be an https URL."),
    is_flag=True,
    default=os.environ.get(f"{APP_NAME}_HTTPS_ORIGIN", False),
    show_default=True,
)
def init(**kwargs: Unpack[InitArgsType]) -> None:
    """Initalize a new Python project.

    DIRECTORY is the destination path where to create the Python project.
    """
    data_dict = (
        Yaml()
        if kwargs["no_data"]
        else (
            Maybe.from_optional(kwargs["data"]).map(read_yaml).value_or(Yaml())
        )
    )
    data_dict.update(
        {
            "git_platform": (
                Maybe.from_optional(kwargs["github_token"])
                .map(lambda _token: "github")
                .value_or("no_git_platform")
            ),
        },
    )
    user_defaults_dict = (
        Maybe.from_optional(kwargs["user_defaults"])
        .map(read_yaml)
        .value_or(Yaml(project_name=kwargs["destination"].name))
    )
    importlib.import_module("copier.main").Worker(
        src_path=kwargs["whiteprint_source"],
        dst_path=kwargs["destination"],
        answers_file=COPIER_ANSWER_FILE,
        vcs_ref=kwargs["vcs_ref"],
        data=data_dict,
        exclude=Maybe.from_optional(kwargs["exclude"]).value_or(
            cast(list[str], []),
        ),
        use_prereleases=kwargs["use_prereleases"],
        skip_if_exists=Maybe.from_optional(kwargs["skip_if_exists"]).value_or(
            cast(list[str], []),
        ),
        cleanup_on_error=not kwargs["no_cleanup_on_error"],
        defaults=kwargs["defaults"],
        user_defaults=user_defaults_dict,
        overwrite=kwargs["overwrite"],
        pretend=kwargs["pretend"],
        quiet=kwargs["quiet"],
        unsafe=True,
    ).run_copy()

    _post_processing(
        kwargs["destination"],
        skip_tests=kwargs["skip_tests"],
        python=kwargs["python"],
        repository_configuration=RepositoryConfiguration(
            github_token=kwargs["github_token"],
            https_origin=kwargs["https_origin"],
        ),
    )
