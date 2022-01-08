#!/usr/bin/env python
# Copyright (c) 2019 ACSONE SA/NV
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)

import contextlib
import datetime
import os
import subprocess
import sys
import tempfile

import click
import toml

from .gitutils import commit_if_needed
from .manifest import read_manifest


def _make_issue_format(org, repo):
    return "`#{{issue}} <https://github.com/{org}/{repo}/issues/{{issue}}>`_".format(
        org=org, repo=repo
    )


def _get_towncrier_template():
    return os.path.join(os.path.dirname(__file__), "towncrier-template.rst")


@contextlib.contextmanager
def _prepare_config(addon_dir, org, repo):
    """Inject towncrier options in pyproject.toml"""
    with tempfile.NamedTemporaryFile(dir=addon_dir, mode="w") as config_file:
        config = {
            "tool": {
                "towncrier": {
                    "template": _get_towncrier_template(),
                    "underlines": ["~"],
                    "issue_format": _make_issue_format(org, repo),
                    "directory": "readme/newsfragments",
                    "filename": "readme/HISTORY.rst",
                }
            }
        }
        toml.dump(config, config_file)
        config_file.flush()
        yield config_file.name


@click.command(
    help=(
        "Generate readme/HISTORY.rst from towncrier newsfragments "
        "stored in readme/newfragments/. This script is meant to be run "
        "before oca-gen-addon-readme. See https://pypi.org/project/towncrier/ "
        "for more information and the naming and format of newfragment files."
    )
)
@click.option(
    "--addon-dir",
    "addon_dirs",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    multiple=True,
    help="Directory where addon manifest is located. This option may be repeated.",
)
@click.option("--version")
@click.option("--date")
@click.option(
    "--org", default="OCA", help="GitHub organization name.", show_default=True
)
@click.option("--repo", required=True, help="GitHub repository name.")
@click.option(
    "--commit/--no-commit",
    help="git commit changes, if any (a git add is done in any case).",
)
def oca_towncrier(addon_dirs, version, date, org, repo, commit):
    if not date:
        date = datetime.date.today().isoformat()
    paths = []
    for addon_dir in addon_dirs:
        news_dir = os.path.join(addon_dir, "readme", "newsfragments")
        if not os.path.isdir(news_dir):
            continue
        if not any(not f.startswith(".") for f in os.listdir(news_dir)):
            continue
        addon_version = version or read_manifest(addon_dir)["version"]
        with _prepare_config(addon_dir, org, repo) as config_file_name:
            subprocess.call(
                [
                    sys.executable,
                    "-m",
                    "towncrier",
                    "--config",
                    config_file_name,
                    "--version",
                    addon_version,
                    "--date",
                    date,
                    "--yes",
                ],
                cwd=addon_dir,
            )
        paths.append(news_dir)
        paths.append(os.path.join(addon_dir, "readme", "HISTORY.rst"))
    if commit:
        commit_if_needed(paths, message="[UPD] changelog", add=False)


if __name__ == "__main__":
    oca_towncrier()
