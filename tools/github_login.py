# -*- coding: utf-8 -*-
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import absolute_import, print_function

import argparse
import os
import sys
import time
from getpass import getpass

import github3
from github3.models import GitHubError

from .config import read_config, write_config


def login():
    if os.environ.get('GITHUB_TOKEN'):
        token = os.environ['GITHUB_TOKEN']
    else:
        config = read_config()
        token = config.get('GitHub', 'token')
    if not token:
        sys.exit("No token has been generated for this script. "
                 "Please run 'oca-github-login'.")
    return github3.login(token=token)


def authorize_token(user):
    config = read_config()
    if config.get('GitHub', 'token'):
        print("The token already exists.")
        sys.exit()

    password = getpass('Password for {0}: '.format(user))

    note = 'OCA (odoo community association) Maintainers Tools'
    note_url = 'https://github.com/OCA/maintainers-tools'
    scopes = ['repo', 'read:org', 'write:org', 'admin:org']

    try:
        # Python 2
        prompt = raw_input
    except NameError:
        # Python 3
        prompt = input

    def two_factor_prompt():
        code = ''
        while not code:
            # The user could accidentally press Enter before being ready,
            # let's protect them from doing that.
            code = prompt('Enter 2FA code: ')
        return code
    try:
        auth = github3.authorize(user, password, scopes, note, note_url,
                                 two_factor_callback=two_factor_prompt)
    except github3.GitHubError as err:
        if err.code == 422:
            for error in err.errors:
                if error['code'] == 'already_exists':
                    msg = ("The 'OCA (odoo community association) Maintainers "
                           "Tools' token already exists. You will find it at "
                           "https://github.com/settings/applications and can "
                           "revoke it or set the token manually in the "
                           "configuration file.")
                    sys.exit(msg)
        raise

    config.set("GitHub", "token", auth.token)
    write_config(config)
    print("Token stored in configuration file")


def wrap_github_call(func, args=None, kwargs=None):
    """Intercept GitHub call to wait when the API rate limit is reached."""
    retry = 0
    while True:
        try:
            if args is None:
                args = []
            if kwargs is None:
                kwargs = {}
            return func(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except GitHubError as e:
            if e.code == 403:
                print("WARNING: %s. Sleeping 300 seconds" % e.message)
                time.sleep(300)
            elif e.code == 405:
                retry += 1
                if retry < 4:
                    print("WARNING: Temporary error: %s. Retrying..." % (
                        e.message
                    ))
                    time.sleep(5)
                else:
                    print("WARNING: GitHub error: %s. Aborting..." % (
                        e.message
                    ))
                    break
            else:
                raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username",
                        help="GitHub Username")
    args = parser.parse_args()

    authorize_token(args.username)


if __name__ == '__main__':
    main()
