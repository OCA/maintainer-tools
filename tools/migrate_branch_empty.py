#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
This script helps to create a new branch for a new Odoo version, catching the
required metafiles from another existing branch, and making the needed changes
on contents.

Installation
============

For using this utility, you need to install these dependencies:

* github3.py library for handling Github calls. To install it, use:
  `sudo pip install github3.py`.

Configuration
=============

You must have a file called oca.cfg on the same folder of the script for
storing credentials parameters. You can generate an skeleton config running
this script for a first time.

Usage
=====
oca-migrate-branch-empty [-h] [-p PROJECTS [PROJECTS ...]] [-e EMAIL]
                        [-t TARGET_ORG]
                        source target

positional arguments:
  source                Source branch (existing)
  target                Target branch (to create)

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

This script will perform the following operations for each project:

* Create an empty branch with 'target' as name. If it already exists, then
  the project is skipped.
* Catch these possible metafiles from source branch, replacing all references
  to it by the target branch:
  * .travis.yml
  * .gitignore
  * CONTRIBUTING.md
  * LICENSE
  * README.md
* Make target branch the default branch in the repository.

Known issues / Roadmap
======================

* Pin the migration issue when GitHub API allows it.
* Issue enumerating the module list contains a list to a Wiki page that should
  be formatted this way:
  https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-{branch}
* Make the created branch protected (no support yet from github3 library).

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@tecnativa.com>

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

MANIFESTS = ("__openerp__.py", "__manifest__.py")


class BranchMigrator(object):
    def __init__(self, source, target, target_org=None, email=None):
        # Read config
        config = read_config()
        self.gh_token = config.get("GitHub", "token")
        # Connect to GitHub
        self.github = github_login.login()
        gh_user = self.github.me()
        if not gh_user.email and not email:
            raise Exception(
                "Email required to commit to github. Please provide one on "
                "the command line or make the one of your github profile "
                "public."
            )
        self.gh_credentials = {
            "name": gh_user.name or str(gh_user),
            "email": gh_user.email or email,
        }
        self.gh_source_branch = source
        self.gh_target_branch = target
        self.gh_org = target_org or "OCA"

    def _replace_content(self, repo, path, replace_list, gh_file=None):
        if not gh_file:
            # Re-read path for retrieving content
            gh_file = repo.file_contents(path, self.gh_source_branch)
        content = gh_file.decoded.decode("utf-8")
        for replace in replace_list:
            content = re.sub(replace[0], replace[1], content, flags=re.DOTALL)
        new_file_blob = repo.create_blob(content, encoding="utf-8")
        return {
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": new_file_blob,
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
            message=message,
            tree=tree.sha,
            parents=parents,
            author=self.gh_credentials,
            committer=self.gh_credentials,
        )
        return commit

    def _create_metafiles(self, repo, root_contents):
        """Create metafiles (README.md, .travis.yml...) pointing to the new
        branch.
        """
        tree_data = []
        source_string = self.gh_source_branch.replace(".", r"\.")
        target_string = self.gh_target_branch
        source_string_dash = self.gh_source_branch.replace(".", "-")
        target_string_dash = self.gh_target_branch.replace(".", "-")
        REPLACES = {
            "README.md": {
                None: [
                    (source_string, target_string),
                    (source_string_dash, target_string_dash),
                    (r"\[//]: # \(addons\).*\[//]: # \(end addons\)", ""),
                ],
            },
            ".travis.yml": {
                None: [
                    (source_string, target_string),
                    (source_string_dash, target_string_dash),
                    (
                        r"(?i)([^\n]+ODOO_REPO=['\"]ODOO[^\n]+)\n([^\n]+"
                        r"ODOO_REPO=['\"]oca\/ocb[^\n]+)",
                        r"\2\n\1",
                    ),
                ],
                "11.0": [
                    ("2.7", "3.5"),
                    (r"(?m)virtualenv:.*\n.*system_site_packages: true\n", ""),
                ],
                "12.0": [
                    (r"addons:\n", r'addons:\n  postgresql: "9.6"'),
                ],
            },
            ".gitignore": {
                None: [],
            },
            "CONTRIBUTING.md": {
                None: [],
            },
            "LICENSE": {
                None: [],
            },
        }
        for filename in REPLACES:
            if not root_contents.get(filename):
                continue
            replaces = []
            for version in REPLACES[filename]:
                if version and self.gh_target_branch != version:
                    continue
                replaces += REPLACES[filename][version]
            tree_data.append(self._replace_content(repo, filename, replaces))
        commit = self._create_commit(
            repo,
            tree_data,
            "[MIG] Add metafiles\n\n[skip ci]",
            use_sha=False,
        )
        return commit

    def _make_default_branch(self, repo):
        repo.edit(repo.name, default_branch=self.gh_target_branch)

    def _migrate_project(self, project):
        print("Migrating project %s/%s" % (self.gh_org, project))
        # Create new branch
        repo = self.github.repository(self.gh_org, project)
        try:
            repo.branch(self.gh_source_branch)
        except NotFoundError:
            print("Source branch non existing. Skipping...")
            return
        try:
            repo.branch(self.gh_target_branch)
        except NotFoundError:
            pass
        else:
            print("Branch already exists. Skipping...")
            return
        root_contents = repo.directory_contents(
            "",
            self.gh_source_branch,
            return_as=dict,
        )
        commit = self._create_metafiles(repo, root_contents)
        repo.create_ref(
            "refs/heads/%s" % self.gh_target_branch,
            commit.sha,
        )
        # TODO: GitHub is returning 404
        # self._make_default_branch(repo)

    def do_migration(self, projects=None):
        if not projects:
            projects = oca_projects.get_repositories()
        for project in projects:
            self._migrate_project(project)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Migrate one OCA branch from one version to another, "
        "applying the needed transformations",
        add_help=True,
    )
    parser.add_argument("source", help="Source branch (existing)")
    parser.add_argument("target", help="Target branch (to create)")
    parser.add_argument(
        "-p",
        "--projects",
        dest="projects",
        nargs="+",
        default=[],
        help="List of specific projects to migrate",
    )
    parser.add_argument(
        "-e",
        "--email",
        dest="email",
        help=(
            "Provides an email address used to commit on GitHub if the one "
            "associated to the GitHub account is not public"
        ),
    )
    parser.add_argument(
        "-t",
        "--target-org",
        dest="target_org",
        help=(
            "By default, the GitHub organization used is OCA. This arg lets "
            "you provide an alternative organization"
        ),
    )
    return parser


def main():
    args = get_parser().parse_args()
    migrator = BranchMigrator(
        source=args.source,
        target=args.target,
        target_org=args.target_org,
        email=args.email,
    )
    migrator.do_migration(projects=args.projects)


if __name__ == "__main__":
    main()
