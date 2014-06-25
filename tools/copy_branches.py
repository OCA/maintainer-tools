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



class Migrate(object):

    def __init__(self, path):
        self.path = path
        self.level = 0

    @contextmanager
    def cd(self, path):
        cwd = os.getcwd()
        os.chdir(path)
        self.level += 1
        yield
        os.chdir(cwd)
        self.level -= 1

    def print(self, *args):
        print('  ' * self.level, *args)

    def _clone_bzr(self, bzr_branch):
        # we keep the serie's name so we can handle both projects:
        # lp:banking-addons/7.0
        # lp:banking-addons/bank-statement-reconcile-7.0
        name = bzr_branch.replace('lp:', '').replace('/', '-')
        repo = os.path.join(self.path, name)
        self.print('Working on', repo)
        if os.path.exists(repo):
            with self.cd(repo):
                self.print('git fetch', 'from', bzr_branch)
                subprocess.check_output(['git', 'fetch'])
        else:
            with self.cd(self.path):
                self.print('git clone', repo, 'from', bzr_branch)
                subprocess.check_output(['git', 'clone',
                                         "bzr::%s" % bzr_branch,
                                         repo])
        return repo

    def _add_bzr_branch(self, repo, bzr_branch, gh_branch):
        with self.cd(repo):
            remotes = subprocess.check_output(['git', 'remote', '-v'])
            remotes = remotes.split('\n')
            remotes = set(remote.split('\t')[0] for remote in remotes)
            if gh_branch not in remotes:
                self.print('git remote add', gh_branch, bzr_branch)
                subprocess.check_output(['git', 'remote', 'add',
                                        gh_branch,
                                        "bzr::%s" % bzr_branch])
            self.print('git fetch', gh_branch, 'from', bzr_branch)
            subprocess.check_output(['git', 'fetch', gh_branch])

    def _push_to_github(self, repo, gh_url):
        with self.cd(repo):
            self.print('git push', gh_url)

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
