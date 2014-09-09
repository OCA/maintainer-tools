# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import ConfigParser
import sys
import erppeek
from getpass import getpass
from . config import read_config, write_config


ODOO_URL = 'https://community.odoo.com'
ODOO_DB = 'community'


def login(username, store):
    config = read_config()
    if username:
        password = getpass('Password for {0}: '.format(username))
        if store:
            config.set("odoo", "username", username)
            config.set("odoo", "password", password)
            write_config(config)
    else:
        username = config.get("odoo", "username")
        password = config.get("odoo", "password")
        if not (username and password):
            sys.exit("You must provide a username.")

    client = erppeek.Client(ODOO_URL)
    # workaround to connect on saas:
    # https://github.com/tinyerp/erppeek/issues/58
    client._db = ODOO_DB
    client.login(username, password)
    return client


def add_args(parser):
    parser.add_argument("-u", "--username",
                        help="Odoo Username. When a username is not provided,"
                             " it will read the configuration file.")
    parser.add_argument("--store",
                        action='store_true',
                        help="Store the username and password in a "
                             "configuration file. Warning, clear text!"),


def main():
    parser = argparse.ArgumentParser()
    add_args(parser)
    args = parser.parse_args()
    login(args.username, args.store)


if __name__ == '__main__':
    main()
