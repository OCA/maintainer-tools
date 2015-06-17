# -*- coding: utf-8 -*-

"""
This script is meant to pull the translations from Transifex .
Technically, it will pull the translations from transifex,
compare it with the po files in the repository and replace it if needed
"""

from transifex.api import TransifexAPI
import os
import shutil
import difflib
import re
from config import read_config
# from oca_projects import OCA_REPOSITORY_NAMES

config = read_config()
# Github parameter
# from github_login import login
# github = login()

from github3 import login
username = 'samuellefever'
token = config.get('GitHub', 'token')
github = login(username=username, token=token)

WORKDIR = "/tmp/tx"

# Transifex parameter

tx_username = config.get('Transifex', 'username')
tx_password = config.get('Transifex', 'password')
URL = "http://transifex.com"
TXAPI = TransifexAPI(tx_username, tx_password, URL)


def treat_project(tx_project, repo, branch):

    resources = TXAPI.list_resources(tx_project)

    tree_data = []
    tree_sha = branch.commit.commit.tree.sha

    for resource in resources:
        slug = resource.get('slug')
        path_to_resource = os.path.join(
            WORKDIR, "translations", tx_project, slug)
        languages = TXAPI.list_languages(tx_project, slug)

        print 'Getting po file for resource %s' % slug
        os.makedirs(path_to_resource)
        for lang in languages:
            filepath = os.path.join(path_to_resource, lang + ".po")
            TXAPI.get_translation(tx_project, slug, lang, filepath)

            tx_file = open(filepath, 'r')
            tx_file_content = tx_file.readlines()

            repo_i18n_path = os.path.join('/', slug, "i18n")
            repo_file_path = os.path.join(repo_i18n_path, lang + '.po')

            repo_file = repo.file_contents(repo_file_path)
            if repo_file:
                repo_file_content = repo_file.decoded.splitlines()

                diff = difflib.unified_diff(repo_file_content,
                                            tx_file_content)
                diff = ''.join(diff)

                if not re.search(r'^\+msgstr\ \".+\"$', diff, re.MULTILINE):
                    print 'No change'
                    continue

            print 'replacing %s by %s' % (filepath, repo_file_path)
            new_file_blob = repo.create_blob(
                ''.join(tx_file_content), encoding='utf-8')
            tree_data.append({
                'path': repo_file_path[1:],
                'mode': '100644',
                'type': 'blob',
                'sha': new_file_blob})

    if tree_data:
        tree = repo.create_tree(tree_data, tree_sha)
        message = 'Add new translations from Transifex'
        c = repo.create_commit(
            message=message, tree=tree.sha, parents=[branch.commit.sha])
        ref = repo.ref('heads/{}'.format(branch))
        ref.update(c.sha)


def main():
    connected = TXAPI.ping()

    if not connected:
        raise Exception('Problem with server connection')

    if os.path.isdir(WORKDIR):
        print 'Deleting working directory : %s' % WORKDIR
        shutil.rmtree(WORKDIR)

    os.makedirs(WORKDIR)
    os.makedirs(WORKDIR + "/translations")

    for oca_project in ['management-system']:  # OCA_REPOSITORY_NAMES:
        tx_project_v8 = "OCA-%s-8-0" % oca_project

        if not TXAPI.project_exists(tx_project_v8):
            print 'Project %s does not exist in transifex : %s' % (
                tx_project_v8, oca_project)
            continue

        repo = github.repository(username, oca_project)

        treat_project(tx_project_v8, repo, repo.branch('8.0'))

        tx_project_v7 = "OCA-%s-7-0" % oca_project

        if not TXAPI.project_exists(tx_project_v7):
            print 'Project %s does not exist in transifex : %s' % (
                tx_project_v7, oca_project)
            continue

        treat_project(tx_project_v7, repo, repo.branch('7.0'))

if __name__ == '__main__':
    main()
