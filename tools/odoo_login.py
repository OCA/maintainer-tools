# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import absolute_import, print_function

import argparse
import os
import sys
import erppeek
from getpass import getpass
from .config import read_config, write_config


ODOO_URL = os.environ.get("ODOO_URL", "https://odoo-community.org")
ODOO_DB = os.environ.get("ODOO_DB", "odoo_community_prod")


def login(username, store):
    if username:
        password = getpass("Password for {0}: ".format(username))
        if store:
            config = read_config()
            config.set("odoo", "username", username)
            config.set("odoo", "password", password)
            write_config(config)
    else:
        username = os.environ.get("ODOO_LOGIN")
        password = os.environ.get("ODOO_PASSWORD")
        if not (username and password):
            config = read_config()
            username = config.get("odoo", "username")
            password = config.get("odoo", "password")
        if not (username and password):
            sys.exit(
                "You must provide a Odoo username and password "
                "in the configuration file or with ODOO_USER and "
                "ODOO_PASSWORD environment variables."
            )

    client = erppeek.Client(ODOO_URL)
    # workaround to connect on saas:
    # https://github.com/tinyerp/erppeek/issues/58
    client._db = ODOO_DB
    client.login(username, password)
    return client


def get_parser(with_help=False):
    parser = argparse.ArgumentParser(add_help=with_help)
    group = parser.add_argument_group("odoo options")
    group.add_argument(
        "-u",
        "--username",
        help="Odoo Username. When a username is not provided,"
        " it will read the configuration file.",
    )
    group.add_argument(
        "--store",
        action="store_true",
        help="Store the username and password in a "
        "configuration file. Warning, clear text!",
    ),
    return parser


def main():
    parser = get_parser(with_help=True)
    args = parser.parse_args()
    login(args.username, args.store)


if __name__ == "__main__":
    main()
