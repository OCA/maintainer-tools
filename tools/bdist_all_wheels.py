""" Generate wheel packages for all Odoo addons in subdirectories

Typical use (pseudo code):
    virtualenv .
    . bin/activate
    pip install maintainer-tools
    pip install "setuptools-odoo>=2.0.3"
    oca-bdist-all-wheels --dist-dir ~/wheelhouse --branch 8.0

Then you can install an addon with:
    pip install odoo8-addon-<addon-name> --find-links=~/wheelhouse

"""
import argparse
import logging
import os
from os.path import join as opj
import shutil
import subprocess
import tempfile

from .oca_projects import (
    get_repositories, BranchNotFoundError, temporary_clone
)


def make_wheel_if_not_exists(setup_path, dist_dir):
    if not os.path.exists(os.path.join(setup_path, 'setup.py')):
        return
    tmpdir = tempfile.mkdtemp()
    try:
        subprocess.check_call(['python', 'setup.py', 'bdist_wheel',
                               '--dist-dir', tmpdir],
                              cwd=setup_path)
        wheels = [w for w in os.listdir(tmpdir) if w.endswith('.whl')]
        if len(wheels) != 1:
            raise RuntimeError("Wheelfile not found for %s" % setup_path)
        wheel = wheels[0]
        if not os.path.exists(opj(dist_dir, wheel)):
            shutil.move(opj(tmpdir, wheel), dist_dir)
    finally:
        shutil.rmtree(tmpdir)


def main():
    parser = argparse.ArgumentParser(description="Make python wheel packages "
                                                 "for all Odoo addons in "
                                                 "subdirectories")
    parser.add_argument('--branch', required=True,
                        help='git branch to checkout and work on')
    parser.add_argument('--dist-dir', required=True,
                        help='target directory for generated wheels')
    parser.add_argument('--push', action='store_true',
                        help='git push changes made to the setup directory')
    args = parser.parse_args()
    dist_dir = os.path.abspath(args.dist_dir)
    for repo in get_repositories():
        try:
            with temporary_clone(repo, args.branch):
                make_default_setup_cmd = [
                    'setuptools-odoo-make-default',
                    '--addons-dir', '.',
                    '--metapackage', 'oca-' + repo,
                    '--clean',
                ]
                if args.push:
                    subprocess.check_call(
                        make_default_setup_cmd + ['--commit'])
                    subprocess.check_call([
                        'git', 'push', 'origin', args.branch,
                    ])
                else:
                    subprocess.check_call(make_default_setup_cmd)
                # make wheel for each installable addon and _metapackage
                for dir_name in os.listdir('setup'):
                    setup_path = opj('setup', dir_name)
                    try:
                        make_wheel_if_not_exists(setup_path, dist_dir)
                    except Exception:
                        logging.exception("setup.py error in %s", setup_path)
        except BranchNotFoundError:
            pass


if __name__ == '__main__':
    main()
