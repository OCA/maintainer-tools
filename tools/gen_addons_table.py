#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
This script replaces markers in the README.md files
of an OCA repository with the list of addons present
in the repository. It preserves the marker so it
can be run again.

The script must be run from the root of the repository,
where the README.md file can be found.

Markers in README.md must have the form:

[//]: # (addons)
does not matter, will be replaced by the script
[//]: # (end addons)
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


MARKERS = r'(\[//\]: # \(addons\))|(\[//\]: # \(end addons\))'
MANIFESTS = ('__openerp__.py', '__manifest__.py')


def sanitize_cell(s):
    if not s:
        return ''
    s = ' '.join(s.split())
    return s


def render_markdown_table(header, rows):
    table = []
    rows = [header, ['---'] * len(header)] + rows
    for row in rows:
        table.append(' | '.join(row))
    return '\n'.join(table)


def replace_in_readme(readme_path, header, rows_available, rows_unported):
    with io.open(readme_path, encoding='utf8') as f:
        readme = f.read()
    parts = re.split(MARKERS, readme, flags=re.MULTILINE)
    if len(parts) != 7:
        _logger.warning('Addons markers not found or incorrect in %s',
                        readme_path)
        return
    addons = []
    if rows_available:
        addons.extend([
            '\n',
            '\n',
            'Available addons\n',
            '----------------\n',
            render_markdown_table(header, rows_available),
            '\n'
        ])
    if rows_unported:
        addons.extend([
            '\n',
            '\n',
            'Unported addons\n',
            '---------------\n',
            render_markdown_table(header, rows_unported),
            '\n'
        ])
    addons.append('\n')
    parts[2:5] = addons
    readme = ''.join(parts)
    with io.open(readme_path, 'w', encoding='utf8') as f:
        f.write(readme)


@click.command()
@click.option('--commit/--no-commit',
              help="git commit changes to README.rst, if any.")
def gen_addons_table(commit):
    readme_path = 'README.md'
    if not os.path.isfile(readme_path):
        _logger.warning('%s not found', readme_path)
        return
    # list addons in . and __unported__
    addon_paths = []  # list of (addon_path, unported)
    for addon_path in os.listdir('.'):
        addon_paths.append((addon_path, False))
    unported_directory = '__unported__'
    if os.path.isdir(unported_directory):
        for addon_path in os.listdir(unported_directory):
            addon_path = os.path.join(unported_directory, addon_path)
            addon_paths.append((addon_path, True))
    addon_paths = sorted(addon_paths, key=lambda x: x[0])
    # load manifests
    header = ('addon', 'version', 'summary')
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
            link = '[%s](%s/)' % (addon_name, addon_path)
            version = manifest.get('version') or ''
            summary = manifest.get('summary') or manifest.get('name')
            summary = sanitize_cell(summary)
            installable = manifest.get('installable', True)
            if unported and installable:
                _logger.warning('%s is in __unported__ but is marked '
                                'installable.' % addon_path)
                installable = False
            if installable:
                rows_available.append((link, version, summary))
            else:
                rows_unported.append((link, version + ' (unported)', summary))
    # replace table in README.md
    replace_in_readme(readme_path, header, rows_available, rows_unported)
    if commit:
        commit_if_needed(
            [readme_path],
            '[UPD] addons table in README.md [ci skip]',
        )


if __name__ == '__main__':
    gen_addons_table()
