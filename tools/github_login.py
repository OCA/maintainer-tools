# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import absolute_import, print_function

import argparse
import os
import sys
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


def authorize_token(user):
    config = read_config()
    if config.get("GitHub", "token"):
        print("The token already exists.")
        sys.exit()

    password = getpass("Password for {0}: ".format(user))

    note = "OCA (odoo community association) Maintainers Tools"
    note_url = "https://github.com/OCA/maintainers-tools"
    scopes = ["repo", "read:org", "write:org", "admin:org"]

    try:
        # Python 2
        prompt = raw_input
    except NameError:
        # Python 3
        prompt = input

    def two_factor_prompt():
        code = ""
        while not code:
            # The user could accidentally press Enter before being ready,
            # let's protect them from doing that.
            code = prompt("Enter 2FA code: ")
        return code

    try:
        auth = github3.authorize(
            user,
            password,
            scopes,
            note,
            note_url,
            two_factor_callback=two_factor_prompt,
        )
    except github3.GitHubError as err:
        if err.code == 422:
            for error in err.errors:
                if error["code"] == "already_exists":
                    msg = (
                        "The 'OCA (odoo community association) Maintainers "
                        "Tools' token already exists. You will find it at "
                        "https://github.com/settings/tokens and can "
                        "revoke it or set the token manually in the "
                        "configuration file."
                    )
                    sys.exit(msg)
        raise

    config.set("GitHub", "token", auth.token)
    write_config(config)
    print("Token stored in configuration file")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="GitHub Username")
    args = parser.parse_args()

    authorize_token(args.username)


if __name__ == "__main__":
    main()
