#!/usr/bin/env python
# Copyright (c) 2019 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import contextlib
import datetime
import os
import shutil
import subprocess
import sys

import click
import toml

from .manifest import read_manifest


def _make_issue_format(org, repo):
    return "`#{{issue}} <https://github.com/{org}/{repo}/issues/{{issue}}>`_".format(
        org=org, repo=repo
    )


def _get_towncrier_template():
    return os.path.join(os.path.dirname(__file__), "towncrier-template.rst")


@contextlib.contextmanager
def _preserve_file(path):
    if not os.path.exists(path):
        try:
            yield
        finally:
            os.unlink(path)
    else:
        save_path = path + ".save"
        assert not os.path.exists(save_path)
        try:
            shutil.copy2(path, save_path)
            yield
        finally:
            shutil.copy2(save_path, path)
            os.unlink(save_path)


@contextlib.contextmanager
def _prepare_pyproject_toml(addon_dir, org, repo):
    """Inject towncrier options in pyproject.toml"""
    pyproject_path = os.path.join(addon_dir, "pyproject.toml")
    with _preserve_file(pyproject_path):
        pyproject = {}
        if os.path.exists(pyproject_path):
            with open(pyproject_path) as f:
                pyproject = toml.load(f)
        if "tool" not in pyproject:
            pyproject["tool"] = {}
        pyproject["tool"]["towncrier"] = {
            "template": _get_towncrier_template(),
            "underlines": ["~"],
            "title_format": "{version} ({project_date})",
            "issue_format": _make_issue_format(org, repo),
            "directory": "readme/newsfragments",
            "filename": "readme/HISTORY.rst",
        }
        with open(pyproject_path, "w") as f:
            toml.dump(pyproject, f)
        yield


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
    help="Directory where addon manifest is located. This option " "may be repeated.",
)
@click.option("--version")
@click.option("--date")
@click.option(
    "--org", default="OCA", help="GitHub organization name", show_default=True
)
@click.option("--repo", required=True, help="GitHub repository name.")
def oca_towncrier(addon_dirs, version, date, org, repo):
    if not date:
        date = datetime.date.today().isoformat()
    for addon_dir in addon_dirs:
        news_dir = os.path.join(addon_dir, "readme", "newsfragments")
        if not os.path.isdir(news_dir):
            continue
        if not any(not f.startswith(".") for f in os.listdir(news_dir)):
            continue
        addon_version = version or read_manifest(addon_dir)["version"]
        with _prepare_pyproject_toml(addon_dir, org, repo):
            subprocess.call(
                [
                    sys.executable,
                    "-m",
                    "towncrier",
                    "--version",
                    addon_version,
                    "--date",
                    date,
                    "--yes",
                ],
                cwd=addon_dir,
            )


if __name__ == "__main__":
    oca_towncrier()
