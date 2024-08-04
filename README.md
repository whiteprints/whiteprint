<h1 align="center">
  <a href="https://whiteprint.readthedocs.io/"><img src="https://raw.githubusercontent.com/whiteprints/whiteprint/main/docs/images/logo.png" alt="python whiteprint"></a>
</h1>
<p align="center">
    <em>Python Whiteprint, generate easily Python projects with (opinionated) best practices.</em>
</p>
<p align="center">
  <a href="https://pypi.python.org/pypi/whiteprint">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/whiteprint.svg"/>
  </a>
  <a href="https://github.com/whiteprints/whiteprint/actions/workflows/tests.yml">
    <img alt="PyPI" src="https://github.com/whiteprints/whiteprint/actions/workflows/tests.yml/badge.svg?branch=main"/>
  </a>
  <a href="https://codecov.io/gh/whiteprints/whiteprint">
    <img alt="pypi" src="https://codecov.io/gh/whiteprints/whiteprint/branch/main/graph/badge.svg?token=GSYS7VUB5R"/>
  </a>
  <a href="https://pre-commit.com/">
    <img alt="pypi" src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white"/>
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img alt="pypi" src="https://img.shields.io/github/license/whiteprints/whiteprint"/>
  </a>
  <a href="https://www.contributor-covenant.org/version/2/1/code_of_conduct/">
    <img alt="pypi" src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg"/>
  </a>
</p>

---

**Documentation**: <a href="https://whiteprint.readthedocs.io/en/latest/" target="_blank">https://whiteprint.readthedocs.io/en/latest/</a>

**Source Code**: <a href="https://github.com/whiteprints/whiteprint" target="_blank">https://github.com/whiteprints/whiteprint</a>

---

# Installation

Ensure that you have [git](https://git-scm.com/) and
[python3](https://www.python.org/) installed.

Then install the required Python tools:

```console
$ python3 -m pip install --user --upgrade pipx
$ pipx install poetry
$ pipx install nox
$ pipx inject nox nox-poetry rich
```

Eventually install Python Whiteprint:

```console
$ pipx install whiteprint
```

# Example

Create a local project

```console
$ whiteprint init <my_project>
```

Create a GitHub project

```console
$ whiteprint init <my_project> --github-token <my_github_token>
```

Note that the GitHub token must have repository, workflows and packages
permissions.

# Yet another Python Project scaffold/cookiecutter/generator?

<p align="center"><em>
Yes.
</em></p>

This project build upon the excellents [cookiecutter-hypermodern-python] by
[@cjolowicz](https://github.com/cjolowicz) as well as [python-blueprint] by
[@johnthagen](https://github.com/johnthagen).

You might want to check these projects as they might be more suited to your
needs.

The documentation of this project is heavily inspired from @cjolowicz's work.
We also recommend readings @cjolowicz's [guide on modern Python
tooling](https://cjolowicz.github.io/posts/hypermodern-python-01-setup/).

# Differences compared to [cookiecutter-hypermodern-python]

- Use [copier](https://copier.readthedocs.io/en/latest/) instead of the
  cookiecutter project,
- tweaks in the generated project (e.g. dynamic type checking with beartype,
  [auto-API documentation](https://sphinx-autoapi.readthedocs.io/en/latest/)),
- manage licenses with [Reuse](https://reuse.software/),
- more Github Actions and Community Standards and Community Standards,
- [Ruff](https://beta.ruff.rs/docs/) instead of Flake8 to auto-fix a maximum of
  code smells,
- strict linting with [pylint](https://pylint.readthedocs.io/en/latest/),
- OCI Container images,
- localization with [Babel](https://babel.pocoo.org/en/latest/index.html).

[cookiecutter-hypermodern-python]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2022.6.3.post1/
[python-blueprint]: https://github.com/johnthagen/python-blueprint
