# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import ConfigParser
import os

CREDENTIALS_FILE = 'oca.cfg'


def init_config():
    config = ConfigParser.ConfigParser()
    config.add_section("GitHub")
    config.set("GitHub", "token", "")
    config.add_section("odoo")
    config.set("odoo", "username", "")
    config.set("odoo", "password", "")
    write_config(config)


def read_config():
    if not os.path.exists(CREDENTIALS_FILE):
        init_config()
    config = ConfigParser.ConfigParser()
    config.read(CREDENTIALS_FILE)
    return config


def write_config(config):
    with open(CREDENTIALS_FILE, 'w') as fd:
        config.write(fd)
