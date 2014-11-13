# -*- coding: utf-8 -*-

'''
Script to fork all project from a organization to other organization
'''

import argparse
import sys

import github3

from .github_login import login


def fork(organization_from, organization_to):
    '''
    Method to fork all project from a organization to other organization
    @organization_from: Organization origin
    @organization_to: Organization destination
    '''
    gh_login = login()

    org_to = gh_login.organization(organization_to)
    all_repos = gh_login.iter_user_repos(organization_from)
    for repo in all_repos:
        forked = False
        try:
            repo.create_fork(org_to)
            forked = True
        except github3.models.GitHubError, error_attemp1:
            try:
                repo.create_fork(organization_to)
                forked = True
            except github3.models.GitHubError, error_attemp2:
                pass
        if forked:
            sys.stdout.write("Repo forked: " + repo.name + '\n')
        else:
            sys.stdout.write("Error repo not forked: {repo_name} \n"
                             "Attemp1 error: {error_attemp1}\n"
                             "Attemp2 error: {error_attemp2}\n"
                             .format(repo_name=repo.name,
                                     error_attemp1=error_attemp1.message,
                                     error_attemp2=error_attemp2.message))


def main():
    '''
    Method main to get args and call fork method
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--org_to",
                        help="Destination of organization to fork it all"
                        " repositories",
                        required=True)
    parser.add_argument("--org_from",
                        help="Organization origin to get all repositories."
                        " Default: oca",
                        default='oca')
    args = parser.parse_args()

    fork(args.org_from, args.org_to)


if __name__ == '__main__':
    main()
