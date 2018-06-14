# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import print_function
import time

import click
import requests

from .oca_projects import get_repositories


OCA_TRAVIS_GITHUB_USER = 'oca-travis'
OCA_TRAVIS_GITHUB_EMAIL = 'oca+oca-travis@odoo-community.org'


class Travis(object):

    def __init__(self, travis_token):
        self.api_url = 'https://api.travis-ci.org'
        self.headers = {
            'Accept': 'application/vnd.travis-ci.2.1+json',
            'Authorization': 'token ' + travis_token,
        }
        self.count = 0

    def request(self, method, url, json=None):
        self.count += 1
        print(self.count, method, url, json)
        r = requests.request(
            method,
            self.api_url + url,
            headers=self.headers,
            json=json,
        )
        if not r.ok:
            print("travis error:", r.text)
        r.raise_for_status()
        return r.json()

    def get(self, url):
        return self.request('get', url)

    def post(self, url, json):
        return self.request('post', url, json=json)

    def delete(self, url):
        return self.request('delete', url)

    def set_env_var(self, repo_id, name, value):
        env_vars = self.get(
            '/settings/env_vars?repository_id={}'.format(repo_id),
        )
        found = None
        for env_var in env_vars['env_vars']:
            if env_var['name'] == name:
                found = env_var
                break
        if found:
            if value and found['value'] == value:
                # variable already set
                return
            # variable exists with another value (or is private so we
            # don't know its value), delete it
            self.delete(
                '/settings/env_vars/{}?repository_id={}'.
                format(found['id'], repo_id),
            )
        # add variable
        self.post(
            '/settings/env_vars?repository_id={}'.format(repo_id),
            json={
                'env_var': {
                    'name': name,
                    'value': value,
                },
            },
        )


@click.command()
@click.option('--travis-token', required=True, envvar='TRAVIS_TOKEN',
              help="Find your travis token at "
                   "https://travis-ci.org/profile")
@click.option('--repo', help="repo name (default=all)")
@click.option('--oca-travis-github-token', required=True,
              prompt="oca-travis github token (from OCA Board keepass file)",
              help="Find this in the OCA Board keepass.")
def main(repo, oca_travis_github_token, travis_token):
    """ Configure Travis for OCA on one or all projects. """
    if repo:
        repos = [repo]
    else:
        repos = get_repositories()
    travis = Travis(travis_token)
    for repo in repos:
        print("Configuring travis for", repo)
        repo_id = travis.get('/repos/OCA/' + repo)['repo']['id']
        travis.set_env_var(repo_id, 'GITHUB_USER', OCA_TRAVIS_GITHUB_USER)
        travis.set_env_var(repo_id, 'GITHUB_EMAIL', OCA_TRAVIS_GITHUB_EMAIL)
        travis.set_env_var(repo_id, 'GITHUB_TOKEN', oca_travis_github_token)
        # rate limit
        time.sleep(20)
