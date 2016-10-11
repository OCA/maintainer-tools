""" Generate wheel packages for all Odoo addons in subdirectories

Typical use (pseudo code):
    virtualenv .
    . bin/activate
    pip install maintainer-tools
    pip install setuptools-odoo
    oca-clone-everything
    oca-bdist-all-wheels --dist-dir ~/wheelhouse --branch 8.0

Then you can install an addon with:
    pip install odoo8-addon-<addon-name> --find-links=~/wheelhouse

"""
import argparse
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile

import setuptools_odoo

from .oca_projects import get_repositories


SETUP_PY_METAPACKAGE = """
import setuptools

setuptools.setup(
   name="odoo{series}-addons-oca-{repo}",
   description="Meta package for OCA {repo} Odoo addons",
   version="{branch}.{date}",
   install_requires={install_requires},
)
"""


def branch_to_series(branch):
    if os.environ.get('SETUPTOOLS_ODOO_LEGACY_MODE'):
        return ''
    if branch.startswith('8.0'):
        return '8'
    elif branch.startswith('9.0'):
        return '9'
    elif branch.startswith('10.0'):
        return '10'
    else:
        raise RuntimeError("Can't determine Odoo series from %s" % branch)


def remove_duplicate_oca_meta_packages(wheeldir):

    def get_metadata_size(whl):
        zf = zipfile.ZipFile(whl, 'r')
        for n in zf.namelist():
            if n.endswith('/METADATA'):
                return len(zf.open(n, 'r').read())
        raise RuntimeError("METADATA not found in %s", whl)

    prev_prefix = None
    prev_metadata_size = None

    for filename in sorted(os.listdir(wheeldir)):
        if not re.match("^odoo[0-9]*_addons_oca_", filename):
            continue
        full_filename = os.path.join(wheeldir, filename)
        prefix = filename.split('-')[0]
        metadata_size = get_metadata_size(full_filename)
        if prefix != prev_prefix or metadata_size != prev_metadata_size:
            prev_prefix = prefix
            prev_metadata_size = metadata_size
            continue
        # print "deleteing", full_filename
        os.remove(full_filename)


def make_wheel_if_not_exists(addon_setup_path, dist_dir):
    tmpdir = tempfile.mkdtemp()
    try:
        subprocess.check_call(['python', 'setup.py', 'bdist_wheel',
                               '--dist-dir', tmpdir],
                              cwd=addon_setup_path)
        wheels = [w for w in os.listdir(tmpdir) if w.endswith('.whl')]
        if len(wheels) != 1:
            raise RuntimeError("Wheelfile not found for %s" % addon_setup_path)
        wheel = wheels[0]
        if not os.path.exists(os.path.join(dist_dir, wheel)):
            shutil.move(os.path.join(tmpdir, wheel), dist_dir)
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
            subprocess.check_call(['git', 'checkout', args.branch], cwd=repo)
            subprocess.check_call(['git', 'reset', '--hard',
                                   'origin/' + args.branch],
                                  cwd=repo)
        except KeyboardInterrupt:
            raise
        except:
            # branch does not exist, move on to next repo
            continue
        subprocess.check_call(['git', 'clean', '-f', '-d', '-x'], cwd=repo)
        subprocess.check_call(['setuptools-odoo-make-default',
                               '-d', '.'], cwd=repo)
        # git commit and push setup dir
        if args.push:
            subprocess.check_call(['git', 'add', 'setup'], cwd=repo)
            if 0 != subprocess.call(['git', 'diff', '--quiet', '--cached',
                                     '--exit-code', 'setup'], cwd=repo):
                subprocess.check_call(['git', 'commit', '-m' '[ADD] setup.py'],
                                      cwd=repo)
                subprocess.check_call(['git', 'push', 'origin', args.branch],
                                      cwd=repo)
        # make wheel for each installable addon
        metapackage_reqs = []
        for addon_name in os.listdir(os.path.join(repo, 'setup')):
            addon_setup_path = os.path.join(repo, 'setup', addon_name)
            if not os.path.isdir(addon_setup_path):
                continue
            try:
                # bdist_wheel for each addon
                make_wheel_if_not_exists(addon_setup_path, dist_dir)
                addon_dir = os.path.join(repo, addon_name)
                req = setuptools_odoo.make_pkg_requirement(addon_dir)
                metapackage_reqs.append(req)
            except KeyboardInterrupt:
                raise
            except:
                logging.exception("setup.py error in %s", addon_setup_path)
        # make meta package for each repo
        setup_py_metapackage = SETUP_PY_METAPACKAGE.format(
            series=branch_to_series(args.branch),
            repo=repo,
            date=time.strftime("%Y%m%d"),
            branch=args.branch,
            install_requires=repr(metapackage_reqs),
        )
        tempdir = tempfile.mkdtemp()
        try:
            with open(os.path.join(tempdir, 'setup.py'), 'w') as f:
                f.write(setup_py_metapackage)
            subprocess.check_call(['python', 'setup.py', 'bdist_wheel',
                                   '--dist-dir', dist_dir],
                                  cwd=tempdir)
        finally:
            shutil.rmtree(tempdir)
    # remove oca meta packages that have not changed since previous build
    remove_duplicate_oca_meta_packages(dist_dir)


if __name__ == '__main__':
    main()
