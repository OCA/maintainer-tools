# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import os
import subprocess
from contextlib import contextmanager
from pkg_resources import resource_string
import yaml

"""

Dependency:
    `git-remote-bzr` from https://github.com/felipec/git-remote-bzr
    must be in the `$PATH`.

"""


@contextmanager
def cd(path):
    cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(cwd)


class Migrate(object):

    def __init__(self, path):
        self.path = path


    def _clone_bzr(self, bzr_branch):
        # we keep the serie's name so we can handle both projects:
        # lp:banking-addons/7.0
        # lp:banking-addons/bank-statement-reconcile-7.0
        name = bzr_branch.replace('lp:', '').replace('/', '-')
        repo = os.path.join(self.path, name)
        if os.path.exists(repo):
            with cd(repo):
                subprocess.check_output(['git', 'pull', repo])
                print('git pull', repo, 'from', bzr_branch)
        else:
            with cd(self.path):
                subprocess.check_output(['git', 'clone',
                                         "bzr::%s" % bzr_branch,
                                         repo])
                print('git clone', repo, 'from', bzr_branch)
        return repo

    def _add_bzr_branch(self, repo, bzr_branch, gh_branch):
        print('\tAdd', bzr_branch, '→', gh_branch)
        return

    def _push_to_github(self, repo, gh_url):
        print('\tPush to', gh_url)

    def copy_branches(self):
        projects = resource_string(__name__, 'branches.yaml')
        projects = yaml.load(projects)
        for project in projects['projects']:
            gh_url = project['github']
            master = None
            branches = []
            for source, target in project['branches']:
                if target == 'master':
                    master = source
                else:
                    branches.append((source, target))
            assert master, "No master branch for %s" % gh_url
            repo = self._clone_bzr(master)
            for source, target in branches:
                self._add_bzr_branch(repo, source, target)
            self._push_to_github(repo, gh_url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path",
                        help="Branches directory")
    args = parser.parse_args()
    if not os.path.exists(args.path):
        exit("Path %s does not exist" % args.path)
    migration = Migrate(os.path.abspath(args.path))
    migration.copy_branches()


if __name__ == '__main__':
    main()
