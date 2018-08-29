# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV
import io
import os

import click
from docutils import ApplicationError
from docutils.core import publish_file
from jinja2 import Template

from .gitutils import commit_if_needed
from .manifest import read_manifest, find_addons, NoManifestFound
from .runbot_ids import get_runbot_ids


FRAGMENTS_DIR = 'readme'

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
        'https://img.shields.io/badge/licence-AGPL--3-blue.png',
        'http://www.gnu.org/licenses/agpl-3.0-standalone.html',
        'License: AGPL-3',
    ),
    'LGPL-3': (
        'https://img.shields.io/badge/licence-LGPL--3-blue.png',
        'http://www.gnu.org/licenses/lgpl-3.0-standalone.html',
        'License: LGPL-3',
    ),
    'GPL-3': (
        'https://img.shields.io/badge/licence-GPL--3-blue.png',
        'http://www.gnu.org/licenses/gpl-3.0-standalone.html',
        'License: GPL-3',
    ),
}

DEVELOPMENT_STATUS_BADGES = {
    'Mature': (
        'https://img.shields.io/badge/maturity-Mature-brightgreen.png',
        'https://odoo-community.org/page/development-status',
        'Mature',
    ),
    'Production/Stable': (
        'https://img.shields.io/badge/maturity-Production%2FStable-green.png',
        'https://odoo-community.org/page/development-status',
        'Production/Stable',
    ),
    'Beta': (
        'https://img.shields.io/badge/maturity-Beta-yellow.png',
        'https://odoo-community.org/page/development-status',
        'Beta',
    ),
    'Alpha': (
        'https://img.shields.io/badge/maturity-Alpha-red.png',
        'https://odoo-community.org/page/development-status',
        'Alpha',
    ),
}

# this comes from pypa/readme_renderer
RST2HTML_SETTINGS = {
    # Prevent local files from being included into the rendered output.
    # This is a security concern because people can insert files
    # that are part of the system, such as /etc/passwd.
    "file_insertion_enabled": False,

    # Halt rendering and throw an exception if there was any errors or
    # warnings from docutils.
    "halt_level": 2,

    # Output math blocks as LaTeX that can be interpreted by MathJax for
    # a prettier display of Math formulas.
    "math_output": "MathJax",

    # Disable raw html as enabling it is a security risk, we do not want
    # people to be able to include any old HTML in the final output.
    "raw_enabled": False,

    # Use typographic quotes, and transform --, ---, and ... into their
    # typographic counterparts.
    "smart_quotes": True,

    # Use the short form of syntax highlighting so that the generated
    # Pygments CSS can be used to style the output.
    "syntax_highlight": "short",
}


def make_runbot_badge(runbot_id, branch):
    return (
        'https://img.shields.io/badge/runbot-Try%20me-875A7B.png',
        'https://runbot.odoo-community.org/runbot/'
        '{runbot_id}/{branch}'.format(**locals()),
        'Try me on Runbot',
    )


def make_weblate_badge(repo_name, branch, addon_name):
    branch = branch.replace('.', '-')
    return (
        'https://img.shields.io/badge/weblate-Translate%20me-F47D42.png',
        'https://translation.odoo-community.org/projects/'
        '{repo_name}-{branch}/{repo_name}-{branch}-{addon_name}'.
        format(**locals()),
        'Translate me on Weblate',
    )


def make_repo_badge(repo_name, branch, addon_name):
    badge_repo_name = repo_name.replace('-', '--')
    return (
        'https://img.shields.io/badge/github-OCA%2F{badge_repo_name}'
        '-lightgray.png?logo=github'.format(**locals()),
        'https://github.com/OCA/{repo_name}/tree/'
        '{branch}/{addon_name}'.format(**locals()),
        'OCA/{repo_name}'.format(**locals()),
    )


def gen_one_addon_readme(repo_name, branch, addon_name, addon_dir, manifest):
    fragments = {}
    for fragment_name in FRAGMENTS:
        fragment_filename = os.path.join(
            addon_dir, FRAGMENTS_DIR, fragment_name + '.rst',
        )
        if os.path.exists(fragment_filename):
            with io.open(fragment_filename, 'rU', encoding='utf8') as f:
                fragment = f.read()
                if fragment:
                    if fragment[-1] != '\n':
                        fragment += '\n'
                    fragments[fragment_name] = fragment
    runbot_id = get_runbot_ids()[repo_name]
    badges = []
    development_status = manifest.get('development_status', 'Beta')
    if development_status in DEVELOPMENT_STATUS_BADGES:
        badges.append(DEVELOPMENT_STATUS_BADGES[development_status])
    license = manifest.get('license')
    if license in LICENSE_BADGES:
        badges.append(LICENSE_BADGES[license])
    badges.append(make_repo_badge(repo_name, branch, addon_name))
    badges.append(make_weblate_badge(repo_name, branch, addon_name))
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
            addon_name=addon_name,
            authors=authors,
            badges=badges,
            branch=branch,
            fragments=fragments,
            manifest=manifest,
            repo_name=repo_name,
            runbot_id=runbot_id,
        ))
    return readme_filename


def gen_one_addon_index(readme_filename):
    addon_dir = os.path.dirname(readme_filename)
    index_dir = os.path.join(addon_dir, 'static', 'description')
    index_filename = os.path.join(index_dir, 'index.html')
    if os.path.exists(index_filename):
        with open(index_filename) as f:
            if 'oca-gen-addon-readme' not in f.read():
                # index was created manually
                return
    try:
        if not os.path.isdir(index_dir):
            os.makedirs(index_dir)
        publish_file(
            source_path=readme_filename,
            destination_path=index_filename,
            writer_name='html4css1',
            settings_overrides=RST2HTML_SETTINGS,
        )
        return index_filename
    except ApplicationError:
        raise click.ClickException(
            "Error validating {}".format(readme_filename)
        )


@click.command()
@click.option('--repo-name', required=True,
              help="OCA repository name, eg. server-tools.")
@click.option('--branch', required=True,
              help="Odoo series. eg 11.0.")
@click.option('--addon-dir', 'addon_dirs',
              type=click.Path(dir_okay=True, file_okay=False, exists=True),
              multiple=True,
              help="Directory where addon manifest is located. This option "
                   "may be repeated.")
@click.option('--addons-dir',
              type=click.Path(dir_okay=True, file_okay=False, exists=True),
              help="Directory containing several addons, the README will be "
                   "generated for all installable addons found there.")
@click.option('--commit/--no-commit',
              help="git commit changes to README.rst, if any.")
def gen_addon_readme(repo_name, branch, addon_dirs, addons_dir, commit):
    """ Generate README.rst from fragments.

    Do nothing if readme/DESCRIPTION.rst is absent, otherwise overwrite
    existing README.rst with content generated from the template,
    fragments (DESCRIPTION.rst, USAGE.rst, etc) and the addon manifest.
    """
    addons = []
    if addons_dir:
        addons.extend(find_addons(addons_dir))
    for addon_dir in addon_dirs:
        addon_name = os.path.basename(os.path.abspath(addon_dir))
        manifest = read_manifest(addon_dir)
        addons.append((addon_name, addon_dir, manifest))
    readme_filenames = []
    for addon_name, addon_dir, manifest in addons:
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        if not os.path.exists(
                os.path.join(addon_dir, FRAGMENTS_DIR, 'DESCRIPTION.rst')):
            continue
        readme_filename = gen_one_addon_readme(
            repo_name, branch, addon_name, addon_dir, manifest)
        readme_filenames.append(readme_filename)
        index_filename = gen_one_addon_index(readme_filename)
        if index_filename:
            readme_filenames.append(index_filename)
    if commit:
        commit_if_needed(readme_filenames, '[UPD] README.rst')


if __name__ == '__main__':
    gen_addon_readme()
