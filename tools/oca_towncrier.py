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


def _make_issue_format(org, repo, fragment_format):
    if fragment_format == "md":
        return f"[#{{issue}}](https://github.com/{org}/{repo}/issues/{{issue}})"
    return f"`#{{issue}} <https://github.com/{org}/{repo}/issues/{{issue}}>`_"


def _get_towncrier_template(fragment_format):
    return os.path.join(
        os.path.dirname(__file__), f"towncrier-template.{fragment_format}"
    )


def _get_readme_fragment_format(addon_dir):
    """Detect the format of the readme fragment to generate (md or rst)"""
    fragment_format = "rst"
    readme_dir = os.path.join(addon_dir, "readme")
    if not os.path.isdir(readme_dir):
        return fragment_format
    files = os.listdir(readme_dir)
    files = [
        f
        for f in files
        if not f.startswith(".") and os.path.isfile(os.path.join(readme_dir, f))
    ]
    # The first file found with a .md or .rst extension will determine the format
    for f in files:
        if f.endswith(".md"):
            fragment_format = "md"
            break
        if f.endswith(".rst"):
            fragment_format = "rst"
            break
    return fragment_format


@contextlib.contextmanager
def _prepare_config(addon_dir, org, repo):
    """Inject towncrier options in pyproject.toml"""
    # first detect expected format (we support both md and rst)
    fragment_format = _get_readme_fragment_format(addon_dir)
    with tempfile.NamedTemporaryFile(dir=addon_dir, mode="w") as config_file:
        result_file = os.path.join("readme", f"HISTORY.{fragment_format}")
        config = {
            "tool": {
                "towncrier": {
                    "template": _get_towncrier_template(fragment_format),
                    "underlines": ["~" if fragment_format == "rst" else ""],
                    "issue_format": _make_issue_format(org, repo, fragment_format),
                    "directory": "readme/newsfragments",
                    "filename": result_file,
                }
            }
        }
        toml.dump(config, config_file)
        config_file.flush()
        yield config_file.name, result_file


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
        with _prepare_config(addon_dir, org, repo) as (config_file_name, result_file):
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
        paths.append(os.path.join(addon_dir, result_file))
    if commit:
        commit_if_needed(paths, message="[UPD] changelog", add=False)


if __name__ == "__main__":
    oca_towncrier()
