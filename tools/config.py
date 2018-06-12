# -*- coding: utf-8 -*-
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import absolute_import, print_function

import os

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

CREDENTIALS_FILE = 'oca.cfg'


def init_config():
    config = configparser.ConfigParser()
    config.add_section("GitHub")
    config.set("GitHub", "username", "")
    config.set("GitHub", "token", "")
    config.add_section("odoo")
    config.set("odoo", "username", "")
    config.set("odoo", "password", "")
    config.add_section("Transifex")
    config.set("Transifex", "username", "transbot@odoo-community.org")
    config.set("Transifex", "password", "")
    config.set("Transifex", "num_retries", 3)
    config.set("Transifex", "organization", "OCA")
    write_config(config)


def read_config():
    if not os.path.exists(CREDENTIALS_FILE):
        init_config()
    config = configparser.ConfigParser()
    config.read(CREDENTIALS_FILE)
    return config


def write_config(config):
    with open(CREDENTIALS_FILE, 'w') as fd:
        config.write(fd)
