# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV
import os
import shutil
import subprocess
import sys
import tempfile

import click


def find_pkgname(dist_dir):
    """ Find the package name by looking at .whl files """
    pkgname = None
    for f in os.listdir(dist_dir):
        if f.endswith('.whl'):
            new_pkgname = f.split('-')[0].replace('_', '-')
            if pkgname and new_pkgname != pkgname:
                raise RuntimeError("Multiple packages names in %s", dist_dir)
            pkgname = new_pkgname
    if not pkgname:
        raise RuntimeError("Package name not found in %s", dist_dir)
    return pkgname


def dist_to_simple_index(target, setup_dirs, python=sys.executable):
    if not setup_dirs:
        setup_dirs = ['.']
    for setup_dir in setup_dirs:
        if not os.path.exists(os.path.join(setup_dir, 'setup.py')):
            continue
        dist_dir = tempfile.mkdtemp()
        try:
            subprocess.check_call([
                python, 'setup.py',
                'clean',
                'sdist', '--dist-dir', dist_dir,
                'bdist_wheel', '--dist-dir', dist_dir,
            ], cwd=setup_dir)
            pkgname = find_pkgname(dist_dir)
            fulltarget = os.path.join(target, pkgname, '')
            if not os.path.isdir(fulltarget):
                os.mkdir(fulltarget)
            # --ignore-existing: never overwrite an existing package
            # os.path.join: make sure directory names end with /
            subprocess.check_call([
                'rsync', '-rv', '--ignore-existing',
                os.path.join(dist_dir, ''),
                fulltarget,
            ])
        finally:
            shutil.rmtree(dist_dir)


@click.command(help="Build several python packages "
                    "by running setup.py clean bdist bdist_wheel "
                    "in each SETUP_DIR, then rsync generated artifacts to "
                    "TARGET using a PEP 503 compliant directory structure. "
                    "SETUP_DIR entries that do not contain a setup.py are "
                    "silently ignored. Distributions that already exist in "
                    "the target directory are never overwritten.")
@click.option('--target', required=True,
              type=click.Path(dir_okay=True, file_okay=False, exists=True),
              help="Root of a PEP 503 directory structure.")
@click.option('--python', '-p',
              default=sys.executable, show_default=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Python interpreter to use when running setup.py")
@click.argument('setup_dirs', nargs=-1, required=False,
                metavar='[SETUP_DIR] ...')
def main(target, setup_dirs, python):
    dist_to_simple_index(target, setup_dirs, python)
