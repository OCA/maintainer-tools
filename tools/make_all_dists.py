""" Generate python packages for all Odoo OCA repositories

Typical use (pseudo code):
    virtualenv .
    . bin/activate
    pip install maintainer-tools
    pip install "setuptools-odoo>=2.0.4"
    oca-make-all-dists --target ~/wheelhouse/oca-simple --push

Then you can install an addon with:
    pip install odoo8-addon-<addon-name> --find-links=~/wheelhouse

"""
import os
from os.path import join as opj
import subprocess
import sys

import click

from .oca_projects import get_repositories_and_branches, temporary_clone
from .dist_to_simple_index import dist_to_simple_index


@click.command()
@click.option('--target', required=True,
              type=click.Path(dir_okay=True, file_okay=False, exists=True),
              help="Root of a PEP 503 directory structure.")
@click.option('--push/--no-push',
              help="Git push changes made to setup directories.")
def main(target, push):
    """ Build sdists and wheels for all OCA repositories """
    target = os.path.abspath(target)
    for repo, branch in get_repositories_and_branches():
        if branch in ('6.1', '7.0'):
            continue
        with temporary_clone(repo, branch):
            sys.stderr.write(
                "============> setuptools-odoo-make-default in %s@%s\n" %
                (repo, branch)
            )
            make_default_setup_cmd = [
                'setuptools-odoo-make-default',
                '--addons-dir', '.',
                '--metapackage', 'oca-' + repo,
                '--clean',
            ]
            if push:
                subprocess.check_call(
                    make_default_setup_cmd + ['--commit'])
                subprocess.check_call([
                    'git', 'push', 'origin', branch,
                ])
            else:
                subprocess.check_call(make_default_setup_cmd)
            # make dists for each installable addon and _metapackage
            sys.stderr.write(
                "============> dist_to_simple_index in %s@%s\n" %
                (repo, branch)
            )
            setup_dirs = [opj('setup', d) for d in os.listdir('setup')]
            dist_to_simple_index(target, setup_dirs)
