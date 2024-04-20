# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import absolute_import, print_function

import argparse
import os
from getpass import getpass
import github3
from .config import read_config, write_config


class GitHubLoginError(RuntimeError):
    pass


def login():
    if os.environ.get("GITHUB_TOKEN"):
        token = os.environ["GITHUB_TOKEN"]
    else:
        config = read_config()
        token = config.get("GitHub", "token")
    if not token:
        raise GitHubLoginError(
            "No token has been generated for this script. "
            "Please run 'oca-github-login' or set the GITHUB_TOKEN "
            "environment variable."
        )
    return github3.login(token=token)


def store_token():
    config = read_config()
    if config.get("GitHub", "token"):
        print("Note: a token already exists and will be replaced.")
    token = getpass("Enter Github Client Token: ")
    auth = github3.login(token=token)
    config.set("GitHub", "token", token)
    write_config(config)
    print("Token stored in configuration file.")
    return auth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the Github authentication.",
    )
    args = parser.parse_args()

    if args.test:
        auth = login()
    else:
        auth = store_token()
    print("Authenticated as %s." % auth.me().login)


if __name__ == "__main__":
    main()
