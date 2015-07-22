#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
This script is meant to pull the translations from Transifex .
Technically, it will pull the translations from Transifex,
compare it with the po files in the repository and replace it if needed

Installation
============

For using this utility, you need to install these dependencies:

* github3.py library for handling Github calls. To install it, use:
  `sudo pip install github3.py`.
* slumber library for handling Transifex calls (REST calls). To install it,
  use `sudo pip install slumber`.
* polib library for po handling. To install it, use `sudo pip install polib`.

Configuration
=============

You must have a file called oca.cfg on the same folder of the script for
storing credentials parameters. You can generate an skeleton config running
this script for a first time.

Usage
=====

tx_pull.py [-h] [-p PROJECTS [PROJECTS ...]]

optional arguments:
  -h, --help            show this help message and exit
  -p PROJECTS [PROJECTS ...], --projects PROJECTS [PROJECTS ...]
                        List of slugs of Transifex projects to pull

You have to set correctly the configuration file (oca.cfg), and then you'll
see the progress in the screen. The script will:

* Scan all accesible projects for the user (or only the passed ones with
  -p/--projects argument).
* Check which ones contain 'OCA-' string.
* Retrieve the available translation strings
* Reverse the name of the project slug to get GitHub branch
* Compare with the existing GitHub files
* If changed, a commit is pushed to GitHub with the updated files

Known issues / Roadmap
======================

* This script is only valid for OCA projects pushed to Transifex with default
  naming scheme. This is because there's a reversal operation in the name to
  get the GitHub repo. It can be easily adapted to get pairs of Transifex slugs
  with the corresponding GitHub branch.
* The scan is made downloading each translation file, so it's an slow process.
  Maybe we can improve this using Transifex statistics (see
  http://docs.transifex.com/api/statistics/) to check if there is no update
  in the resource, and comparing with the date of the last commit made by
  this script (but forces also to check for this commit on GitHub). Another
  option is to add an argument to provide a date, and check if there is an
  update for the resource translation beyond that date. As this also needs a
  call, it has to be tested if we improve or not the speed.

Credits
=======

Contributors
------------

* Samuel Lefever
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
import os.path
import os
import re

import polib
from slumber import API, exceptions

from . import github_login
from .config import read_config

TX_USERNAME_DEFAULT = 'transbot@odoo-community.org'
TX_ORG_DEFAULT = "OCA"
# Read arguments
parser = argparse.ArgumentParser(
    description=u'Pull OCA Transifex updated translations to GitHub')
parser.add_argument(
    '-p', '--projects', dest='projects', nargs='+',
    default=[], help='List of slugs of Transifex projects to pull')
args = parser.parse_args()
# Read config
config = read_config()
gh_token = config.get('GitHub', 'token')
tx_username = config.get('Transifex', 'username') \
    or os.environ.get('TRANSIFEX_USER') \
    or TX_USERNAME_DFT
tx_password = config.get('Transifex', 'password') \
    or os.environ.get('TRANSIFEX_PASSWORD')
tx_num_retries = config.get('Transifex', 'num_retries') \
    or os.environ.get('TRANSIFEX_RETRIES')
tx_org = config.get('Transifex', 'organization') \
    or os.environ.get('TRANSIFEX_ORGANIZATION') \
    or TX_ORG_DEFAULT
# Connect to GitHub
github = github_login.login()
gh_user = github.user()

gh_credentials = {'name': gh_user.name or str(gh_user),
                  'email': gh_user.email}

# Connect to Transifex
tx_url = "https://www.transifex.com/api/2/"
tx_api = API(tx_url, auth=(tx_username, tx_password))


def _load_po_dict(po_file):
    po_dict = {}
    for po_entry in po_file:
        if po_entry.msgstr:
            key = u'\n'.join(x[0] for x in po_entry.occurrences)
            key += u'\nmsgid "%s"' % po_entry.msgid
            po_dict[key] = po_entry.msgstr
    return po_dict


def process_project(tx_project):
    print "Processing project '%s'..." % tx_project['name']
    tx_slug = tx_project['slug']
    regex = r'(?P<org>)' + tx_org + \
        '\-(?P<repo>[A-Za-z\-\_]+)\-(?P<branch>[A-Za-z0-9.\-\_]+)'
    match_object = re.search(regex, tx_slug)

    oca_project = match_object.group('repo')
    gh_repo = github.repository(tx_org, oca_project)
    oca_branch = match_object.group('branch').replace('-', '.')
    gh_branch = gh_repo.branch(oca_branch)
    tree_data = []
    tree_sha = gh_branch.commit.commit.tree.sha
    resources = tx_api.project(tx_project['slug']).resources().get()
    for resource in resources:
        print "Checking resource %s..." % resource['name']
        resource = tx_api.project(tx_project['slug']).resource(
            resource['slug']).get(details=True)
        for lang in resource['available_languages']:
            cont = 0
            tx_lang = False
            while cont < tx_num_retries and not tx_lang:
                # for some weird reason, sometimes Transifex fails to answer
                # some requests, so this retry mechanism handles this problem
                try:
                    tx_lang = tx_api.project(tx_project['slug']).resource(
                        resource['slug']).translation(lang['code']).get()
                except exceptions.HttpClientError:
                    tx_lang = False
                    cont += 1
            if tx_lang:
                try:
                    tx_po_file = polib.pofile(tx_lang['content'])
                    tx_po_dict = _load_po_dict(tx_po_file)
                    # Discard empty languages
                    if not tx_po_dict:
                        continue
                    gh_i18n_path = os.path.join('/', resource['slug'], "i18n")
                    gh_file_path = os.path.join(
                        gh_i18n_path, lang['code'] + '.po')
                    gh_file = gh_repo.contents(gh_file_path, gh_branch.name)
                    if gh_file:
                        gh_po_file = polib.pofile(
                            gh_file.decoded.decode('utf-8'))
                        gh_po_dict = _load_po_dict(gh_po_file)
                        unmatched_items = (set(gh_po_dict.items()) ^
                                           set(tx_po_dict.items()))
                        if not unmatched_items:
                            print "...no change in %s" % gh_file_path
                            continue
                    print '..replacing %s' % gh_file_path
                    new_file_blob = gh_repo.create_blob(
                        tx_lang['content'], encoding='utf-8')
                    tree_data.append({
                        'path': gh_file_path[1:],
                        'mode': '100644',
                        'type': 'blob',
                        'sha': new_file_blob})
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    print "ERROR: processing lang '%s'" % lang['code']
            else:
                print "ERROR: fetching lang '%s'" % lang['code']
    if tree_data:
        tree = gh_repo.create_tree(tree_data, tree_sha)
        message = 'OCA Transbot updated translations from Transifex'
        print "message", message
        commit = gh_repo.create_commit(
            message=message, tree=tree.sha, parents=[gh_branch.commit.sha],
            author=gh_credentials, committer=gh_credentials)
        print "git pushing"
        ## UNCOMMENT THIS LINE gh_repo.ref('heads/{}'.format(gh_branch.name)).update(commit.sha)


def main():
    projects = []
    if args.projects:
        # Check that provided projects are correct
        for project_slug in args.projects:
            try:
                tx_project = tx_api.project(project_slug).get()
                projects.append(tx_project)
            except:
                print "ERROR: Transifex project slug %s is invalid" % (
                    project_slug)
                return
    else:
        start = 1
        temp_projects = []
        print "Getting Transifex projects..."
        while temp_projects or start == 1:
            temp_projects = tx_api.projects().get(start=start)
            start += len(temp_projects)
            projects += temp_projects
    for project in projects:
        if tx_org + '-' in project['slug']:
            process_project(project)


if __name__ == '__main__':
    main()
