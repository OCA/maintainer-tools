#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
This script replaces markers in the README.md file
of an OCA repository with the list of addons present
in the repository. It preserves the marker so it
can be run again.

Markers in README.md must have the form:

\b
<!-- prettier-ignore-start -->
[//]: # (addons)
does not matter, will be replaced by the script
[//]: # (end addons)
<!-- prettier-ignore-end -->
"""

from __future__ import print_function
import ast
import io
import logging
import os
import re

import click

from .gitutils import commit_if_needed

_logger = logging.getLogger(__name__)


MARKERS = r"(\[//\]: # \(addons\))|(\[//\]: # \(end addons\))"
MANIFESTS = ("__openerp__.py", "__manifest__.py")


def sanitize_cell(s):
    if not s:
        return ""
    s = " ".join(s.split())
    return s


def render_markdown_table(header, rows):
    table = []
    rows = [header, ["---"] * len(header)] + rows
    for row in rows:
        table.append(" | ".join(row))
    return "\n".join(table)


def render_maintainers(manifest):
    maintainers = manifest.get("maintainers") or []
    return " ".join(
        [
            "[![{maintainer}]"
            "(https://github.com/{maintainer}.png?size=30px)]"
            "(https://github.com/{maintainer})".format(maintainer=x)
            for x in maintainers
        ]
    )


def replace_in_readme(readme_path, header, rows_available, rows_unported):
    with io.open(readme_path, encoding="utf8") as f:
        readme = f.read()
    parts = re.split(MARKERS, readme, flags=re.MULTILINE)
    if len(parts) != 7:
        _logger.warning("Addons markers not found or incorrect in %s", readme_path)
        return
    addons = []
    # TODO Use the same heading styles as Prettier (prefixing the line with
    # `##` instead of adding all `----------` under it)
    if rows_available:
        addons.extend(
            [
                "\n",
                "\n",
                "Available addons\n",
                "----------------\n",
                render_markdown_table(header, rows_available),
                "\n",
            ]
        )
    if rows_unported:
        addons.extend(
            [
                "\n",
                "\n",
                "Unported addons\n",
                "---------------\n",
                render_markdown_table(header, rows_unported),
                "\n",
            ]
        )
    addons.append("\n")
    parts[2:5] = addons
    readme = "".join(parts)
    with io.open(readme_path, "w", encoding="utf8") as f:
        f.write(readme)


@click.command(help=__doc__)
@click.option("--commit/--no-commit", help="git commit changes to README.rst, if any.")
@click.option(
    "--readme-path",
    default="README.md",
    type=click.Path(dir_okay=False, file_okay=True),
    help="README.md file with addon table markers",
)
@click.option(
    "--addons-dir",
    default=".",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="Directory containing several addons",
)
def gen_addons_table(commit, readme_path, addons_dir):
    if not os.path.isfile(readme_path):
        _logger.warning("%s not found", readme_path)
        return
    # list addons in . and __unported__
    addon_paths = []  # list of (addon_path, unported)
    for addon_path in os.listdir(addons_dir):
        addon_paths.append((addon_path, False))
    unported_directory = os.path.join(
        "" if addons_dir == "." else addons_dir, "__unported__"
    )
    if os.path.isdir(unported_directory):
        for addon_path in os.listdir(unported_directory):
            addon_path = os.path.join(unported_directory, addon_path)
            addon_paths.append((addon_path, True))
    addon_paths = sorted(addon_paths, key=lambda x: x[0])
    # load manifests
    header = ("addon", "version", "maintainers", "summary")
    rows_available = []
    rows_unported = []
    for addon_path, unported in addon_paths:
        for manifest_file in MANIFESTS:
            manifest_path = os.path.join(addon_path, manifest_file)
            has_manifest = os.path.isfile(manifest_path)
            if has_manifest:
                break
        if has_manifest:
            with open(manifest_path) as f:
                manifest = ast.literal_eval(f.read())
            addon_name = os.path.basename(addon_path)
            link = "[%s](%s/)" % (addon_name, addon_path)
            version = manifest.get("version") or ""
            summary = manifest.get("summary") or manifest.get("name")
            summary = sanitize_cell(summary)
            installable = manifest.get("installable", True)
            if unported and installable:
                _logger.warning(
                    "%s is in __unported__ but is marked " "installable." % addon_path
                )
                installable = False
            if installable:
                rows_available.append(
                    (link, version, render_maintainers(manifest), summary)
                )
            else:
                rows_unported.append(
                    (
                        link,
                        version + " (unported)",
                        render_maintainers(manifest),
                        summary,
                    )
                )
    # replace table in README.md
    replace_in_readme(readme_path, header, rows_available, rows_unported)
    if commit:
        commit_if_needed(
            [readme_path],
            "[UPD] addons table in README.md",
        )


if __name__ == "__main__":
    gen_addons_table()
