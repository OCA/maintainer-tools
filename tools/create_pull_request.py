# -*- coding: utf-8 -*-

'''
Script to create pull request from a repo/branch to other repo
'''

import argparse
import re
import requests
import simplejson
import sys

from .github_login import read_config, CREDENTIALS_FILE


def github(repo_base, url, payload=None, delete=False):
    """Return a http request to be sent to github"""
    config = read_config(CREDENTIALS_FILE)
    token = config.get('GitHub', 'token')
    if not token:
        raise Exception('Does not have a token to authenticate')
    match_object = re.search('([^/]+)/([^/]+)/([^/.]+(.git)?)', repo_base)
    if match_object:
        url = url.replace(':owner', match_object.group(2))
        url = url.replace(':repo', match_object.group(3))
        url = 'https://api.%s%s' % (match_object.group(1), url)
        session = requests.Session()
        session.auth = (token, 'x-oauth-basic')
        session.headers.update({
            'Accept': 'application/vnd.github.she-hulk-preview+json'
        })
        if payload:
            response = session.post(url, data=simplejson.dumps(payload))
        elif delete:
            response = session.delete(url)
        else:
            response = session.get(url)
        return response.json()


def create_pull_request(project_base, branch_base,
                        branch_head, title, comment=None):
    '''
    Method to make pull request from a repo/branch to other repo
    @repo_base Repo where show pr
    @branch_dest Branch name destination use username:branchname
    '''
    pr_data = {
        "title": title,
        "head": branch_head,
        "base": branch_base,
        "body": comment,
    }
    return github(repo_base=project_base,
                  url='/repos/:owner/:repo/pulls', payload=pr_data)


def main():
    '''
    Method main to get args and call create_pull_request method
    '''

    parser = argparse.ArgumentParser(description='For more info see:'
                                     'https://developer.github.com/v3/pulls/'
                                     '#create-a-pull-request')
    parser.add_argument("branch_base",
                        help="The name of the branch you want your"
                        " changes pulled into. This should be an"
                        " existing branch on the current repository."
                        " You cannot submit a pull request to one"
                        " repository that requests a merge to a base"
                        " of another repository."
                        " e.g. 'master'")
    parser.add_argument("project_base",
                        help="The name of the project of branch base."
                        " Use organization/project"
                        " e.g. 'oca/maintainers-tools'")
    parser.add_argument("branch_head",
                        help="The name of the branch where your changes"
                        " are implemented. For cross-repository pull"
                        " requests in the same network, namespace head"
                        " with a user like this: username:branch."
                        " e.g. 'oca-travis:my-dev-branch'")
    parser.add_argument("title",
                        help="The title of the pull request."
                        " e.g. '[FIX] Fix error xyz'")
    parser.add_argument("--body", dest='body',
                        help="Optional contents of the pull request."
                        " e.g. 'This is large description of pr'",
                        required=False)
    parser.add_argument('--debug',
                        dest='debug_mode',
                        default=True,
                        help='Enable debug mode.'
                        'Use False to inactivate'
                        'Default is active')
    args = parser.parse_args()

    res_pr = create_pull_request('https://github.com/' + args.project_base,
                                 args.branch_base,
                                 args.branch_head,
                                 args.title,
                                 args.body,)
    if args.debug_mode is True:
        sys.stdout.write("Result of pr: " + str(res_pr))


if __name__ == '__main__':
    main()
