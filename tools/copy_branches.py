# -*- coding: utf-8 -*-

"""

Dependency:
    `git-remote-bzr` from https://github.com/felipec/git-remote-bzr
    must be in the `$PATH`.

"""

from __future__ import absolute_import, print_function

import argparse
import os
import re
import subprocess
from contextlib import contextmanager
from pkg_resources import resource_string
import yaml


@contextmanager
def cd(path):
    cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(cwd)


class Migrate(object):

    def __init__(self, path, push=False):
        self.path = path
        self.push = push

    def _clone_bzr(self, bzr_branch):
        # we keep the serie's name so we can handle both projects:
        # lp:banking-addons/7.0
        # lp:banking-addons/bank-statement-reconcile-7.0
        name = bzr_branch.replace('lp:', '').replace('/', '-')
        repo = os.path.join(self.path, name)
        print('Working on', repo)
        if os.path.exists(repo):
            with cd(repo):
                print('  git fetch', 'from', bzr_branch)
                subprocess.check_output(['git', 'fetch'])
        else:
            with cd(self.path):
                print('  git clone', repo, 'from', bzr_branch)
                subprocess.check_output(['git', 'clone',
                                         "bzr::%s" % bzr_branch,
                                         repo])
        return repo

    def _add_remote(self, repo, name, remote):
        with cd(repo):
            remotes = subprocess.check_output(['git', 'remote'])
            remotes = remotes.split('\n')
            if name not in remotes:
                print('  git remote add', name, remote)
                subprocess.check_output(['git', 'remote', 'add',
                                        name, remote])

    def _add_bzr_branch(self, repo, bzr_branch, gh_branch):
        with cd(repo):
            self._add_remote(repo, gh_branch, "bzr::%s" % bzr_branch)
            print('  git fetch', gh_branch, 'from', bzr_branch)
            subprocess.check_output(['git', 'fetch', gh_branch])

    def _push_to_github(self, repo, refs):
        with cd(repo):
            print('  git push github', refs)
            if self.push:
                subprocess.check_output(
                    ['git', 'push', 'github', refs])

    def _push_tags_to_github(self, repo):
        with cd(repo):
            print('  git push github --tags')
            if self.push:
                subprocess.check_output(
                    ['git', 'push', 'github', '--tags'])

    def copy_branches(self, only_projects=None):
        projects = resource_string(__name__, 'branches.yaml')
        projects = yaml.load(projects)
        for project in projects['projects']:
            gh_url = project['github']
            if only_projects:
                gh_name = re.search('git@github.com:OCA/(.+).git',
                                    gh_url).group(1)
                if gh_name not in only_projects:
                    continue
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
            self._add_remote(repo, 'github', gh_url)
            self._push_to_github(repo, 'origin/master')
            self._push_tags_to_github(repo)
            for __, gh_branch in branches:
                refs = ('refs/remotes/{branch}/master:'
                        'refs/heads/{branch}'.format(branch=gh_branch))
                self._push_to_github(repo, refs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path",
                        help="Branches directory")
    parser.add_argument("--no-push", dest="push", action='store_false')
    parser.add_argument("--push", dest="push", action='store_true')
    parser.add_argument("--projects", nargs='*',
                        help="Name of the Github projects that you want to "
                             "migrate.")
    parser.set_defaults(push=False)
    args = parser.parse_args()
    if not os.path.exists(args.path):
        exit("Path %s does not exist" % args.path)
    migration = Migrate(os.path.abspath(args.path), push=args.push)
    migration.copy_branches(only_projects=args.projects)


if __name__ == '__main__':
    main()
