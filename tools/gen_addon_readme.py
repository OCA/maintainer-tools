""" Generate addon README.rst from fragments """
import io
import os

import click
from jinja2 import Template

from .gitutils import commit_if_needed
from .manifest import read_manifest, find_addons, NoManifestFound
from .runbot_ids import get_runbot_ids


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


def gen_one_addon_readme(repo_name, branch, addon_dir, manifest):
    fragments = {}
    for fragment_name in FRAGMENTS:
        fragment_filename = os.path.join(addon_dir, fragment_name + '.rst')
        if os.path.exists(fragment_filename):
            with io.open(fragment_filename, 'rU', encoding='utf8') as f:
                fragments[fragment_name] = f.read()
    runbot_id = get_runbot_ids()[repo_name]
    badges = []
    license = manifest.get('license')
    if license in LICENSE_BADGES:
        badges.append(LICENSE_BADGES[license])
    development_status = manifest.get('development_status')
    if development_status in DEVELOPMENT_STATUS_BADGES:
        badges.append(DEVELOPMENT_STATUS_BADGES[development_status])
    badges.append(make_runbot_badge(runbot_id, branch))
    authors = [
        a.strip()
        for a in manifest.get('author', '').split(',')
        if '(OCA)' not in a
        # remove OCA because it's in authors for the purpose
        # of finding OCA addons in apps.odoo.com, OCA is not
        # a real author, but is rather referenced in the
        # maintainers section
    ]
    # generate
    template_filename = \
        os.path.join(os.path.dirname(__file__), 'gen_addon_readme.template')
    readme_filename = \
        os.path.join(addon_dir, 'README.rst')
    with io.open(template_filename, 'rU', encoding='utf8') as tf:
        template = Template(tf.read())
    with io.open(readme_filename, 'w', encoding='utf8') as rf:
        rf.write(template.render(
            authors=authors,
            badges=badges,
            branch=branch,
            fragments=fragments,
            manifest=manifest,
            repo_name=repo_name,
            runbot_id=runbot_id,
        ))
    return readme_filename


@click.command()
@click.option('--repo-name', required=True)
@click.option('--branch', required=True)
@click.option('--addon-dir', 'addon_dirs',
              type=click.Path(dir_okay=True, file_okay=False, exists=True),
              multiple=True)
@click.option('--addons-dir',
              type=click.Path(dir_okay=True, file_okay=False, exists=True))
@click.option('--commit/--no-commit')
def gen_addon_readme(repo_name, branch, addon_dirs, addons_dir, commit):
    """ Generate README.rst from fragments """
    addon_dirs = list(addon_dirs)
    if addons_dir:
        for _, addon_dir, _ in find_addons(addons_dir):
            addon_dirs.append(addon_dir)
    readme_filenames = []
    for addon_dir in addon_dirs:
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        if not os.path.exists(os.path.join(addon_dir, 'DESCRIPTION.rst')):
            continue
        readme_filename = gen_one_addon_readme(
            repo_name, branch, addon_dir, manifest)
        readme_filenames.append(readme_filename)
    if commit:
        commit_if_needed(readme_filenames, '[UPD] README.rst')


if __name__ == '__main__':
    gen_addon_readme()
