""" Generate wheel packages for all Odoo addons in subdirectories

Typical use (pseudo code):
    virtualenv .
    . bin/activate
    pip install maintainer-tools
    pip install setuptools-odoo
    oca-clone-everything
    oca-bdist-all-wheels --dist-dir ~/wheelhouse --branch 8.0

Then you can install an addon with:
    pip install odoo-addon-<addon-name> --find-links=~/wheelhouse

Or in the (hopefully not too distant) future:
    pip install odoo-addon-<addon-name> \\
        --find-links=https://wheelhouse.odoo-community.org/oca-8.0

"""
import argparse
import logging
import os
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
   name="odoo-addons-oca-{repo}",
   description="Meta package for OCA {repo} Odoo addons",
   version="{branch}.{date}",
   install_requires={install_requires},
)
"""


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
        if not filename.startswith('odoo_addons_oca_'):
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
                subprocess.check_call(['python', 'setup.py', 'bdist_wheel',
                                       '--dist-dir', dist_dir],
                                      cwd=addon_setup_path)
                addon_dir = os.path.join(repo, addon_name)
                req = setuptools_odoo.make_pkg_requirement(addon_dir)
                metapackage_reqs.append(req)
            except KeyboardInterrupt:
                raise
            except:
                logging.exception("setup.py error in %s", addon_setup_path)
        # make meta package for each repo
        setup_py_metapackage = SETUP_PY_METAPACKAGE.format(
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
