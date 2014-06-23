# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import ConfigParser
import os
import sys
from getpass import getpass
import github3
from github3 import authorize, GitHubError

CREDENTIALS_FILE = 'oca.cfg'


def init_config(path):
    config = ConfigParser.ConfigParser()
    config.add_section("GitHub")
    config.set("GitHub", "token", "")
    with open(path, "wb") as config_file:
        config.write(config_file)


def read_config(path):
    if not os.path.exists(CREDENTIALS_FILE):
        init_config(CREDENTIALS_FILE)
    config = ConfigParser.ConfigParser()
    config.read(CREDENTIALS_FILE)
    return config


def login():
    config = read_config(CREDENTIALS_FILE)
    token = config.get('GitHub', 'token')
    if not token:
        sys.exit("No token has been generated for this script. "
                 "Please run 'oca-github-login'.")
    return github3.login(token=token)


def authorize_token(user):
    config = read_config(CREDENTIALS_FILE)
    if config.get('GitHub', 'token'):
        print("The token already exists.")
        sys.exit()

    password = getpass('Password for {0}: '.format(user))

    note = 'OCA (odoo community association) Maintainers Tools'
    note_url = 'https://github.com/OCA/maintainers-tools'
    scopes = ['repo', 'read:org', 'write:org', 'admin:org']

    try:
        auth = github3.authorize(user, password, scopes, note, note_url)
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
    with open(CREDENTIALS_FILE, 'w') as fd:
        config.write(fd)
    print("Token stored in configuration file")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username",
                        help="GitHub Username")
    args = parser.parse_args()

    authorize_token(args.username)


if __name__ == '__main__':
    main()
