""" Generate addon README.rst from fragments """
import io
import os

import click
from jinja2 import Template

from .runbot_ids import get_runbot_ids
from .manifest import read_manifest


FRAGMENTS = (
    'DESCRIPTION',
    'INSTALL',
    'CONFIGURE',
    'USAGE',
    'ROADMAP',
    'DEVELOP',
    'CONTRIBUTORS',
    'CREDITS',
    'HISTORY',
)

LICENSE_BADGES = {
    'AGPL-3': (
        'https://img.shields.io/badge/licence-AGPL--3-blue.svg',
        'http://www.gnu.org/licenses/agpl-3.0-standalone.html',
        'License: AGPL-3',
    ),
    'LGPL-3': (
        'https://img.shields.io/badge/licence-LGPL--3-blue.svg',
        'http://www.gnu.org/licenses/lgpl-3.0-standalone.html',
        'License: LGPL-3',
    ),
    'GPL-3': (
        'https://img.shields.io/badge/licence-GPL--3-blue.svg',
        'http://www.gnu.org/licenses/gpl-3.0-standalone.html',
        'License: GPL-3',
    ),
}

# TODO use better badges from Valeria

DEVELOPMENT_STATUS_BADGES = {
    'Mature': (
        'https://img.shields.io/badge/maturity-Mature-green.svg',
        None,
        'Mature',
    ),
    'Production/Stable': (
        'https://img.shields.io/badge/maturity-Production%2FStable-green.svg',
        None,
        'Production/Stable',
    ),
    'Beta': (
        'https://img.shields.io/badge/maturity-Beta-green.svg',
        None,
        'Beta',
    ),
    'Alpha': (
        'https://img.shields.io/badge/maturity-Alpha-green.svg',
        None,
        'Alpha',
    ),
}


def make_runbot_badge(runbot_id, branch):
    return (
        'https://img.shields.io/badge/runbot-Try%20me-875A7B.svg',
        'https://runbot.odoo-community.org/runbot/'
        '{runbot_id}/{branch}'.format(**locals()),
        'Try me on Runbot',
    )


@click.command()
@click.option('--repo-name', required=True)
@click.option('--branch', required=True)
@click.option('--addon-dir',
              type=click.Path(dir_okay=True, file_okay=False, exists=True),
              default='.',
              show_default=True)
def gen_addon_readme(repo_name, branch, addon_dir):
    """ Generate README.rst from fragments """
    fragments = {}
    for fragment_name in FRAGMENTS:
        fragment_filename = os.path.join(addon_dir, fragment_name + '.rst')
        if os.path.exists(fragment_filename):
            with io.open(fragment_filename, 'rU', encoding='utf8') as f:
                fragments[fragment_name] = f.read()
    runbot_id = get_runbot_ids()[repo_name]
    manifest = read_manifest(addon_dir)
    badges = []
    license = manifest.get('license')
    if license in LICENSE_BADGES:
        badges.append(LICENSE_BADGES[license])
    development_status = manifest.get('development_status')
    if development_status in DEVELOPMENT_STATUS_BADGES:
        badges.append(DEVELOPMENT_STATUS_BADGES[development_status])
    badges.append(make_runbot_badge(runbot_id, branch))
    # TODO manifest maintainers key
    # generate
    template_filename = \
        os.path.join(os.path.dirname(__file__), 'gen_addon_readme.template')
    readme_filename = \
        os.path.join(addon_dir, 'README.rst')
    with io.open(template_filename, 'rU', encoding='utf8') as tf:
        template = Template(tf.read())
    with io.open(readme_filename, 'w', encoding='utf8') as rf:
        rf.write(template.render(
            badges=badges,
            branch=branch,
            fragments=fragments,
            manifest=manifest,
            repo_name=repo_name,
            runbot_id=runbot_id,
        ))


if __name__ == '__main__':
    gen_addon_readme()
