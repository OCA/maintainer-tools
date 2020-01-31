#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
This script helps to make a massive change across a whole organization
on contents of a file.

Installation
============

For using this utility, you need to install these dependencies:

* github3.py library for handling Github calls. To install it, use:
  ``sudo pip install github3.py``.

Configuration
=============

You must have a file called oca.cfg on the same folder of the script for
storing credentials parameters. You can generate an skeleton config running
this script for a first time.

Usage
=====
oca-massive-change [-h] [-p PROJECTS [PROJECTS ...]] [-e EMAIL]
                   [-t TARGET_ORG] [-m COMMIT_MESSAGE]
                   target path source_string target_string

Performs a massive change over a whole organization.

positional arguments:
  target                Target branch
  path                  File path
  source_string         Source string (or regexp)
  target_string         Target string (or regexp)

optional arguments:
  -h, --help            show this help message and exit
  -p PROJECTS [PROJECTS ...], --projects PROJECTS [PROJECTS ...]
                        List of specific projects to migrate
  -e EMAIL, --email EMAIL
                        Provides an email address used to commit on GitHub if
                        the one associated to the GitHub account is not public
  -t TARGET_ORG, --target-org TARGET_ORG
                        By default, the GitHub organization used is OCA. This
                        arg lets you provide an alternative organization
  -m COMMIT_MESSAGE, --message COMMIT_MESSAGE
                        By default, '[UPD] Massive change [skip ci]', but can
                        be provided with an alternative one

This script will perform the following operations for each project:

* Look for the selected file in the target branch.
* If found, modify it searching for the source string and replacing it by the
  target string.
* Commit the changes with optional commit message.

Credits
=======

Contributors
------------

* Tecnativa - Pedro M. Baeza

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
"""

from __future__ import print_function
import argparse
import re
from . import github_login
from . import oca_projects
from .config import read_config
from github3.exceptions import NotFoundError

DEFAULT_MESSAGE = "[UPD] Massive change [skip ci]"


class MassiveChanger(object):
    def __init__(self, target, target_org=None, email=None, message=None):
        # Read config
        config = read_config()
        self.gh_token = config.get('GitHub', 'token')
        # Connect to GitHub
        self.github = github_login.login()
        gh_user = self.github.me()
        if not gh_user.email and not email:
            raise Exception(
                'Email required to commit to github. Please provide one on '
                'the command line or make the one of your github profile '
                'public.')
        self.gh_credentials = {'name': gh_user.name or str(gh_user),
                               'email': gh_user.email or email}
        self.gh_target_branch = target
        self.gh_org = target_org or 'OCA'

    def _replace_content(self, repo, path, replace_list, gh_file=None):
        if not gh_file:
            # Re-read path for retrieving content
            gh_file = repo.file_contents(path, self.gh_target_branch)
        content = gh_file.decoded.decode('utf-8')
        for replace in replace_list:
            new_content = re.sub(
                replace[0], replace[1], content, flags=re.DOTALL)
            if new_content == content:
                return {}
        new_file_blob = repo.create_blob(new_content, encoding='utf-8')
        return {
            'path': path,
            'mode': '100644',
            'type': 'blob',
            'sha': new_file_blob,
        }

    def _create_commit(self, repo, tree_data, message, use_sha=True):
        """Create a GitHub commit.
        :param repo: github3 repo reference
        :param tree_data: list with dictionary for the entries of the commit
        :param message: message to use in the commit
        :param use_sha: if False, the tree_data structure will be considered
        the full one, deleting the rest of the entries not listed in this one.
        """
        if not tree_data:
            return
        if use_sha:
            branch = repo.branch(self.gh_target_branch)
            tree_sha = branch.commit.commit.tree.sha
            parents = [branch.commit.sha]
        else:
            tree_sha = None
            parents = []
        tree = repo.create_tree(tree_data, tree_sha)
        commit = repo.create_commit(
            message=message, tree=tree.sha, parents=parents,
            author=self.gh_credentials, committer=self.gh_credentials,
        )
        if use_sha:
            repo.ref('heads/{}'.format(branch.name)).update(commit.sha)
        return commit

    def _do_change(self, project, path, src, dest, message=None):
        print("Performing change in project %s/%s" % (self.gh_org, project))
        repo = self.github.repository(self.gh_org, project)
        try:
            repo.branch(self.gh_target_branch)
        except NotFoundError:
            print("Branch doesn't exist. Skipping...")
            return
        root_contents = repo.directory_contents(
            '', self.gh_target_branch, return_as=dict,
        )
        if not root_contents.get(path):
            print("Path not found. Skipping...")
            return
        new_content = self._replace_content(repo, path, [(src, dest)])
        if not new_content:
            print("Source string not found. Skipping...")
            return
        tree_data = [new_content]
        if not message:
            message = DEFAULT_MESSAGE
        self._create_commit(repo, tree_data, message)

    def do_change(self, path, src, dest, message=None, projects=None):
        if not projects:
            projects = oca_projects.get_repositories()
        for project in projects:
            self._do_change(project, path, src, dest, message=message)


def get_parser():
    parser = argparse.ArgumentParser(
        description='Performs a massive change over a whole organization.',
        add_help=True)
    parser.add_argument('target', help="Target branch")
    parser.add_argument('path', help="File path")
    parser.add_argument('source_string', help="Source string (or regexp)")
    parser.add_argument('target_string', help="Target string (or regexp)")
    parser.add_argument(
        '-p', '--projects', dest='projects', nargs='+',
        default=[], help='List of specific projects to migrate')
    parser.add_argument(
        '-e', '--email', dest='email',
        help=('Provides an email address used to commit on GitHub if the one '
              'associated to the GitHub account is not public'))
    parser.add_argument(
        '-t', '--target-org', dest='target_org',
        help=('By default, the GitHub organization used is OCA. This arg lets '
              'you provide an alternative organization'))
    parser.add_argument(
        '-m', '--message', dest='commit_message',
        help=("By default, '" + DEFAULT_MESSAGE + "', but can be provided with"
              " an alternative one"))
    return parser


def main():
    args = get_parser().parse_args()
    changer = MassiveChanger(
        target=args.target, target_org=args.target_org, email=args.email)
    changer.do_change(
        args.path, args.source_string, args.target_string, args.commit_message,
        projects=args.projects)


if __name__ == '__main__':
    main()
