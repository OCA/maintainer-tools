# -*- coding: utf-8 -*-

'''
Script to add team to a particular repository or a list of repositories
located by organization.
'''

import argparse
import sys
import github3

from github_login import login


def add_team_repo(repositories, org, team):
    gh_login = login()
    user = gh_login.user()
    team_get = None
    # Team object for the org and team given
    for org_obj in user.iter_orgs():
        if (str(org_obj.login)).lower() == org.lower():
            for team_obj in org_obj.iter_teams():
                if str(team_obj.name) == team:
                    team_get = team_obj
    # Repo object for the org and repositories given
    for repo in github3.iter_user_repos(org):
        for repository in repositories:
            if str(repo.name) == repository:
                team_get.add_repo(repo)

def main():
    '''
    Method main to get args and call add_team_repo method
    '''

    parser = argparse.ArgumentParser(description="For more info see:"
                                     "https://github3py.readthedocs.org/\
                                     en/latest/orgs.html"
                                     "#add-team-repo")
    parser.add_argument('-l',
                        '--list',
                        help="The names of repositories to use."
                        " Use repositories names comma separated without spaces"
                        " e.g. '-l maintainers-tools,partner-contact'",
                        type=str)
    parser.add_argument("org",
                        help="The name of the organization to use."
                        " Use owner"
                        " e.g. 'oca'")
    parser.add_argument("team",
                        help="The name of the team to add to repository.")

    args = parser.parse_args()
    
    repo_list = [str(item) for item in args.list.split(',')]
    #~ res = add_team_repo(repo_list, args.org, args.team)


if __name__ == '__main__':
    main()
