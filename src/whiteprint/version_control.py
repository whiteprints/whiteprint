"""Git related functionalities."""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

import pygit2
import yaml
from github import Github
from github.Auth import (
    Token as GithubToken,
)
from github.AuthenticatedUser import (
    AuthenticatedUser as GithubAuthenticatedUser,
)
from github.GithubException import GithubException
from github.Organization import Organization as GithubOrganization
from pygit2 import Oid, Signature
from pygit2.repository import Repository
from returns.maybe import Maybe

from whiteprint.loc import _


__all__: Final = [
    "HEAD",
    "INITIAL_HEAD_NAME",
    "WHITEPRINT_SIGNATURE",
    "add_and_commit",
    "delete_github_repository",
    "git_add_all",
    "init_and_commit",
    "init_repository",
    "protect_repository",
    "setup_github_repository",
]
"""Public module attributes."""

HEAD: Final = "HEAD"
"""Git HEAD ref."""

INITIAL_HEAD_NAME: Final = "main"
"""Git default branch."""

WHITEPRINT_SIGNATURE: Final = Signature(
    name="Python Whiteprint",
    email="1455095+RomainBrault@users.noreply.github.com",
)
"""Whiteprint Git signature for both authoring and commiting.

Note:
    we use a personal Git noreply email address for the moment.
"""


class FailedAuthenticationError(RuntimeError):
    """Authentication failed."""


@dataclass(frozen=True)
class GithubUser:
    """A Github user.

    Attributes:
        token: a GitHub token with repository writing authorization.
        login: the GitHub login name of the user or the organization
            login.
    """

    login: str
    token: GithubToken


@dataclass(frozen=True)
class CommitData:
    """The commit data.

    Attributes:
        message: the commit message.
        author: the author.
        committer: the committer.
    """

    message: str
    author: Signature = field(default_factory=lambda: WHITEPRINT_SIGNATURE)
    committer: Signature = field(default_factory=lambda: WHITEPRINT_SIGNATURE)


def init_repository(destination: Path) -> Repository:
    """Run git init.

    The default branch is named "main".

    Args:
        destination: the path of the Git repository.

    Returns:
        an empty Git repository.
    """
    return cast(
        Repository,
        pygit2.init_repository(
            destination,
            initial_head=INITIAL_HEAD_NAME,
        ),
    )


def git_add_all(repo: Repository) -> Oid:
    """Run git add -A.

    Args:
        repo: a Git Repository.

    Returns:
        a Git Index.
    """
    repo.index.add_all()
    repo.index.write()
    return repo.index.write_tree()


def add_and_commit(
    repo: Repository,
    *,
    commit_data: CommitData,
    ref: str | None = None,
    parents: Iterable[Oid | str] | None = None,
) -> None:
    """Run git add -A && git commit -m `message`.

    Args:
        repo: a Git Repository.
        commit_data: the commit data.
        ref: an optional name of the reference to update. If none, use `HEAD`.
        parents: binary strings representing
            parents of the new commit. If none, use repository's head ref.
    """
    repo.create_commit(
        Maybe.from_optional(ref).or_else_call(lambda: repo.head.name),
        commit_data.author,
        commit_data.committer,
        commit_data.message,
        git_add_all(repo),
        Maybe.from_optional(parents)
        .map(list)
        .or_else_call(lambda: [repo.head.target]),
    )


def init_and_commit(
    destination: Path,
    *,
    commit_data: CommitData,
) -> Repository:
    """Run git init && git commmit -m `message`.

    Args:
        destination: the path of the Git repository.
        commit_data: the commit data.

    Returns:
        a Git repository.
    """
    repo = init_repository(destination)
    add_and_commit(
        repo,
        commit_data=commit_data,
        ref=HEAD,
        parents=[],
    )

    return repo


def _find_entity(
    authenticated_user: GithubAuthenticatedUser,
    *,
    login: str,
) -> GithubAuthenticatedUser | GithubOrganization:
    """Find and return an organization or user from the GitHub loging name.

    Args:
        authenticated_user: an authenticated GitHub user.
        login: the GitHub login name of the user or the organization
            login.

    Returns:
        THe organization or user depending on the loging name.
    """
    organizations = [
        organization
        for organization in authenticated_user.get_orgs()
        if organization.login == login
    ]
    return organizations[0] if len(organizations) == 1 else authenticated_user


def setup_github_repository(
    repo: Repository,
    *,
    project_slug: str,
    github_user: GithubUser,
    labels: Path,
    retry: int = 3,
) -> None:
    """Create a repository on GitHub and push the local one.

    Args:
        repo: the local repository.
        project_slug: a slug of the project name.
        github_user: a Github user.
        labels: a path to a yaml file containing a list of labels with their
            descriptions.
        retry: number of retries to obtain the Github user.

    Raises:
        FailedAuthenticationError: the autentication to GitHub failed.
    """
    # We ignore covering the case of a failed authentication **yet** as it is
    # difficult to test for little benefits.
    with Github(auth=github_user.token, retry=retry) as github:
        if not isinstance(
            authenticated_user := github.get_user(),
            GithubAuthenticatedUser,
        ):  # pragma: no cover
            raise FailedAuthenticationError

        github_repository = _find_entity(
            authenticated_user,
            login=github_user.login,
        ).create_repo(project_slug)

        repo.remotes.set_url(
            "origin",
            github_repository.clone_url,
        )
        repo.remotes.add_fetch("origin", "+refs/heads/*:refs/remotes/origin/*")

        logger = logging.getLogger(__name__)
        for label in yaml.safe_load(labels.read_text()):
            try:
                github_repository.create_label(**label)
                continue
            except GithubException as github_exception:
                logger.debug(github_exception)

    logger.debug(_("Pushing ref %s"), repo.head.target)
    repo.remotes["origin"].push(
        [f"refs/heads/{INITIAL_HEAD_NAME}"],
        callbacks=pygit2.callbacks.RemoteCallbacks(
            credentials=pygit2.UserPass(
                "x-access-token",
                github_user.token.token,
            ),
        ),
    )


def protect_repository(
    repo: Repository,
    *,
    project_slug: str,
    github_user: GithubUser,
    https_origin: bool,
    retry: int = 3,
) -> None:
    """Protect a Github repository.

    Args:
        repo: the local repository.
        project_slug: a slug of the project name (Repository to delete).
        github_user: a Github user.
        https_origin: force the origin to be an HTTPS URL.
        retry: number of retries to obtain the Github user.

    Raises:
        FailedAuthenticationError: the autentication to GitHub failed.
    """
    # We ignore covering the case of a failed authentication **yet** as it is
    # difficult to test for little benefits.
    with Github(auth=github_user.token, retry=retry) as github:
        authenticated_user = github.get_user()
        if not isinstance(
            authenticated_user := github.get_user(),
            GithubAuthenticatedUser,
        ):  # pragma: no cover
            raise FailedAuthenticationError

        github_repository = _find_entity(
            authenticated_user,
            login=github_user.login,
        ).get_repo(
            project_slug,
        )

        branch = github_repository.get_branch(INITIAL_HEAD_NAME)
        branch.edit_protection(
            strict=True,
            enforce_admins=True,
            lock_branch=True,
        )
        branch.edit_required_pull_request_reviews(
            require_code_owner_reviews=True,
        )
        branch.edit_required_status_checks(strict=True)

        # We do not test coverage here as it is too complex for little gains
        # (e.g. it requires the creation of an SSH key for the test session).
        if not https_origin:  # pragma: no cover
            repo.remotes.set_url("origin", github_repository.ssh_url)


def delete_github_repository(
    project_slug: str,
    *,
    token: GithubToken,
    retry: int = 3,
) -> None:
    """Delete a GitHub repository.

    Args:
        project_slug: a slug of the project name (Repository to delete).
        token: a GitHub token with repository writing authorization.
        retry: number of retries to obtain the Github user.
    """
    with Github(auth=token, retry=retry) as github:
        github_user = github.get_user()

        # We ignore covering the case of a failed repository creation **yet**
        # as it is difficult to test for little benefits.
        try:
            github_repository = github_user.get_repo(
                project_slug,
            )
        except GithubException as github_exception:  # pragma: no cover
            logger = logging.getLogger(__name__)
            logger.debug(github_exception)
        else:
            github_repository.delete()
