#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
This script helps to create a new branch for a new Odoo version from the
another existing branch, making the needed changes on contents.

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
oca-migrate-branch [-h] [-p PROJECTS [PROJECTS ...]] [-e EMAIL]
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

* Create a branch starting from branch 'source' with 'target' as name. If it
  already exists, then the project is skipped.
* Mark all modules as installable = False.
* Replace in README.md all references to source branch by the target branch.
* Replace in .travis.yml all references to source branch by the target branch.
* Remove __unported__ dir.
* Make target branch the default branch in the repository.
* Create a milestone (if not exist) for new version.
* Create an issue enumerating the modules to migrate, with the milestone
  assigned, and with the labels "help wanted" and "work in progress" (if
  exist).

Known issues / Roadmap
======================

* Modules without installable key in the manifest are filled with this key,
  but the indentation for this added line is assumed to be 4 spaces, and the
  closing brace indentation is 0.
* Issue enumerating the module list contains a list to a Wiki page that should
  be formatted this way:
  https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-{branch}
* Make the created branch protected (no support yet from github3 library).

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>

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

import argparse
import re
from . import github_login
from . import oca_projects
from .config import read_config

MANIFESTS = ('__openerp__.py', '__manifest__.py')


class BranchMigrator(object):
    def __init__(self, source, target, target_org=None, email=None):
        # Read config
        config = read_config()
        self.gh_token = config.get('GitHub', 'token')
        # Connect to GitHub
        self.github = github_login.login()
        gh_user = self.github.user()
        if not gh_user.email and not email:
            raise Exception(
                'Email required to commit to github. Please provide one on '
                'the command line or make the one of your github profile '
                'public.')
        self.gh_credentials = {'name': gh_user.name or str(gh_user),
                               'email': gh_user.email or email}
        self.gh_source_branch = source
        self.gh_target_branch = target
        self.gh_org = target_org or 'OCA'

    def _replace_content(self, repo, path, replace_list, gh_file=None):
        if not gh_file:
            # Re-read path for retrieving content
            gh_file = repo.contents(path, self.gh_target_branch)
        content = gh_file.decoded
        for replace in replace_list:
            content = re.sub(replace[0], replace[1], content, flags=re.DOTALL)
        new_file_blob = repo.create_blob(content, encoding='utf-8')
        return {
            'path': path,
            'mode': '100644',
            'type': 'blob',
            'sha': new_file_blob
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
        branch = repo.branch(self.gh_target_branch)
        tree_sha = branch.commit.commit.tree.sha if use_sha else None
        tree = repo.create_tree(tree_data, tree_sha)
        commit = repo.create_commit(
            message=message, tree=tree.sha, parents=[branch.commit.sha],
            author=self.gh_credentials, committer=self.gh_credentials)
        repo.ref('heads/{}'.format(branch.name)).update(commit.sha)
        return commit

    def _mark_modules_uninstallable(self, repo, root_contents):
        """Make uninstallable the existing modules in the repo."""
        tree_data = []
        modules = []
        for root_content in root_contents.values():
            if root_content.type != 'dir':
                continue
            module_contents = repo.contents(
                root_content.path, self.gh_target_branch)
            for manifest_file in MANIFESTS:
                manifest = module_contents.get(manifest_file)
                if manifest:
                    break
            if manifest:
                modules.append(root_content.path)
                # Re-read path for retrieving content
                gh_file = repo.contents(manifest.path, self.gh_target_branch)
                manifest_dict = eval(gh_file.decoded)
                if manifest_dict.get('installable') is None:
                    src = ",?\s*}"
                    dest = ",\n    'installable': False,\n}"
                else:
                    src = '["\']installable["\']: *True'
                    dest = "'installable': False"
                tree_data.append(self._replace_content(
                    repo, manifest.path, [(src, dest)], gh_file=gh_file))
        self._create_commit(
            repo, tree_data, "[MIG] Make modules uninstallable")
        return modules

    def _rename_manifests(self, repo, root_contents):
        """ Rename __openerp__.py to __manifest__.py as per Odoo 10.0 API """
        branch = repo.branch(self.gh_target_branch)
        tree = repo.tree(branch.commit.sha).recurse().tree
        tree_data = []
        for entry in tree:
            if entry.type == 'tree':
                continue
            path = entry.path
            if path.endswith('__openerp__.py'):
                path = path.replace('__openerp__.py', '__manifest__.py')
            tree_data.append({
                'path': path,
                'sha': entry.sha,
                'type': entry.type,
                'mode': entry.mode,
            })
        self._create_commit(
            repo, tree_data, "[MIG] Rename manifest files", use_sha=False)

    def _delete_setup_dirs(self, repo, root_contents, modules):
        if 'setup' not in root_contents:
            return
        exclude_paths = ['setup/%s' % module for module in modules]
        branch = repo.branch(self.gh_target_branch)
        tree = repo.tree(branch.commit.sha).recurse().tree
        tree_data = []
        for entry in tree:
            if entry.type == 'tree':
                continue
            for path in exclude_paths:
                if entry.path == path or entry.path.startswith(path + '/'):
                    break
            else:
                tree_data.append({
                    'path': entry.path,
                    'sha': entry.sha,
                    'type': entry.type,
                    'mode': entry.mode,
                })
        self._create_commit(
            repo, tree_data, "[MIG] Remove setup module directories",
            use_sha=False)

    def _delete_unported_dir(self, repo, root_contents):
        if '__unported__' not in root_contents.keys():
            return
        branch = repo.branch(self.gh_target_branch)
        tree = repo.tree(branch.commit.sha).tree
        tree_data = []
        # Reconstruct tree without __unported__ entry
        for entry in tree:
            if '__unported__' not in entry.path:
                tree_data.append({
                    'path': entry.path,
                    'sha': entry.sha,
                    'type': entry.type,
                    'mode': entry.mode,
                })
        self._create_commit(
            repo, tree_data, "[MIG] Remove __unported__ dir", use_sha=False)

    def _update_metafiles(self, repo, root_contents):
        """Update metafiles (README.md, .travis.yml...) for pointing to
        the new branch.
        """
        tree_data = []
        source_string = self.gh_source_branch.replace('.', '\.')
        target_string = self.gh_target_branch
        source_string_dash = self.gh_source_branch.replace('.', '-')
        target_string_dash = self.gh_target_branch.replace('.', '-')
        if root_contents.get('README.md'):
            tree_data.append(self._replace_content(
                repo, 'README.md',
                [(source_string, target_string),
                 (source_string_dash, target_string_dash),
                 ("\[//]: # \(addons\).*\[//]: # \(end addons\)",
                  "[//]: # (addons)\n[//]: # (end addons)")]))
        if root_contents.get('.travis.yml'):
            tree_data.append(self._replace_content(
                repo, '.travis.yml',
                [(source_string, target_string),
                 (source_string_dash, target_string_dash)]))
        self._create_commit(
            repo, tree_data, "[MIG] Update metafiles")

    def _make_default_branch(self, repo):
        repo.edit(repo.name, default_branch=self.gh_target_branch)

    def _create_branch_milestone(self, repo):
        for milestone in repo.iter_milestones():
            if milestone.title == self.gh_target_branch:
                return milestone
        return repo.create_milestone(self.gh_target_branch)

    def _create_migration_issue(self, repo, modules, milestone):
        title = "Migration to version %s" % self.gh_target_branch
        # Check first if it already exists
        for issue in repo.iter_issues(milestone=milestone.number):
            if issue.title == title:
                return issue
        body = ("# Todo\n\nhttps://github.com/OCA/maintainer-tools/wiki/"
                "Migration-to-version-%s\n\n# Modules to migrate\n\n" %
                self.gh_target_branch)
        body += "\n".join(["- [ ] %s" % x for x in modules])
        # Make sure labels exists
        labels = []
        for label in repo.iter_labels():
            if label.name in ['help wanted', 'work in progress']:
                labels.append(label.name)
        return repo.create_issue(
            title=title, body=body, milestone=milestone.number, labels=labels)

    def _migrate_project(self, project):
        print "Migrating project %s/%s" % (self.gh_org, project)
        # Create new branch
        repo = self.github.repository(self.gh_org, project)
        source_branch = repo.branch(self.gh_source_branch)
        if not source_branch:
            print "Source branch non existing. Skipping..."
            return
        branch = repo.branch(self.gh_target_branch)
        if branch:
            print "Branch already exists. Skipping..."
            return
        repo.create_ref(
            'refs/heads/%s' % self.gh_target_branch,
            source_branch.commit.sha)
        root_contents = repo.contents('', self.gh_target_branch)
        modules = self._mark_modules_uninstallable(repo, root_contents)
        if self.gh_target_branch == '10.0':
            self._rename_manifests(repo, root_contents)
        self._delete_unported_dir(repo, root_contents)
        self._delete_setup_dirs(repo, root_contents, modules)
        self._update_metafiles(repo, root_contents)
        self._make_default_branch(repo)
        milestone = self._create_branch_milestone(repo)
        self._create_migration_issue(repo, sorted(modules), milestone)

    def do_migration(self, projects=None):
        if not projects:
            projects = oca_projects.get_repositories()
        for project in projects:
            self._migrate_project(project)


def get_parser():
    parser = argparse.ArgumentParser(
        description='Migrate one OCA branch from one version to another, '
                    'applying the needed transformations',
        add_help=True)
    parser.add_argument('source', help="Source branch (existing)")
    parser.add_argument('target', help="Target branch (to create)")
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
    return parser


def main():
    args = get_parser().parse_args()
    migrator = BranchMigrator(
        source=args.source, target=args.target, target_org=args.target_org,
        email=args.email)
    migrator.do_migration(projects=args.projects)


if __name__ == '__main__':
    main()
