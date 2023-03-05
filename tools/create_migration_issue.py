#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
This script creates a migration issue for a new Odoo version
in all repositories. This issue lists all known addons in the previous version.

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
oca-create-migration-issues [-h] [-p PROJECTS [PROJECTS ...]] [-e EMAIL]
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

* Create a milestone (if it does not exist) for new version.
* Create an issue enumerating the modules to migrate, with the milestone
  assigned, and with the labels "help wanted" and "work in progress" (if
  exist).

Known issues / Roadmap
======================

* Issue enumerating the module list contains a list to a Wiki page that should
  be formatted this way:
  https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-{branch}

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Stéphane Bidoul <stephane.bidoul@acsone.eu>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
"""

from __future__ import print_function
import argparse
from . import github_login
from . import oca_projects
from .config import read_config

import github3

MANIFESTS = ("__openerp__.py", "__manifest__.py")


class MigrationIssuesCreator(object):
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

    def _get_modules_list(self, repo, root_contents):
        """Get the list of the modules in previous branch."""
        modules = []
        for root_content in root_contents.values():
            if root_content.type != "dir":
                continue
            module_contents = repo.directory_contents(
                root_content.path, self.gh_source_branch, return_as=dict
            ).keys()
            if any(x in module_contents for x in MANIFESTS):
                modules.append(root_content.path)
        return modules

    def _create_branch_milestone(self, repo):
        for milestone in repo.milestones():
            if milestone.title == self.gh_target_branch:
                print(" milestone already exists")
                return milestone
        return repo.create_milestone(self.gh_target_branch)

    def _create_migration_issue(self, repo, modules, milestone):
        title = "Migration to version %s" % self.gh_target_branch
        # Check first if it already exists
        for issue in repo.issues(milestone=milestone.number):
            if issue.title == title:
                print(" migration issue already exists")
                return issue
        body = (
            "# Todo\n\nhttps://github.com/OCA/maintainer-tools/wiki/"
            "Migration-to-version-%s\n\n# Modules to migrate\n\n"
            % self.gh_target_branch
        )
        body += "\n".join(["- [ ] %s" % x for x in modules])
        body += (
            "\n\nMissing module? Check https://github.com/OCA/maintainer-"
            "tools/wiki/%5BFAQ%5D-Missing-modules-in-migration-issue-list"
        )
        # Make sure labels exists
        labels = []
        for label in repo.labels():
            if label.name in ["help wanted", "work in progress", "no stale"]:
                labels.append(label.name)
        return repo.create_issue(
            title=title, body=body, milestone=milestone.number, labels=labels
        )

    def _migrate_project(self, project):
        print("Preparing project %s/%s" % (self.gh_org, project))
        repo = self.github.repository(self.gh_org, project)
        try:
            root_contents = repo.directory_contents(
                "",
                self.gh_source_branch,
                return_as=dict,
            )
        except github3.exceptions.NotFoundError:
            print(
                " no commit found on branch {}, skipping".format(self.gh_source_branch)
            )
            return
        modules = self._get_modules_list(repo, root_contents)
        milestone = self._create_branch_milestone(repo)
        self._create_migration_issue(repo, sorted(modules), milestone)

    def do_migration(self, projects=None):
        if not projects:
            projects = oca_projects.get_repositories()
        for project in sorted(projects):
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
    migrator = MigrationIssuesCreator(
        source=args.source,
        target=args.target,
        target_org=args.target_org,
        email=args.email,
    )
    migrator.do_migration(projects=args.projects)


if __name__ == "__main__":
    main()
