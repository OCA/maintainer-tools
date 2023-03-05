# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import absolute_import, print_function

import configparser
import os
import re

CREDENTIALS_FILE = "oca.cfg"


def init_config():
    config = configparser.ConfigParser()
    config.add_section("GitHub")
    config.set("GitHub", "username", "")
    config.set("GitHub", "token", "")
    config.add_section("odoo")
    config.set("odoo", "username", "")
    config.set("odoo", "password", "")
    config.add_section("apps.odoo.com")
    config.set("apps.odoo.com", "username", "")
    config.set("apps.odoo.com", "password", "")
    config.set(
        "apps.odoo.com",
        "chromedriver_path",
        "/usr/lib/chromium-browser/chromedriver",
    )
    write_config(config)


def read_config():
    if not os.path.exists(CREDENTIALS_FILE):
        init_config()
    config = configparser.ConfigParser()
    config.read(CREDENTIALS_FILE)
    return config


def write_config(config):
    with open(CREDENTIALS_FILE, "w") as fd:
        config.write(fd)


NOT_ADDONS = {
    ".github",
    "ansible-odoo",
    "connector-magento-php-extension",
    "contribute-md-template",
    "maintainer-quality-tools",
    "maintainer-tools",
    "mirrors-flake8",
    "oca-addons-repo-template",
    "oca-ci",
    "oca-custom",
    "oca-decorators",
    "oca-github-bot",
    "oca-port",
    "oca-weblate-deployment",
    "OCB",
    "odoo-community.org",
    "odoo-module-migrator",
    "odoo-pre-commit-hooks",
    "odoo-sentinel",
    "odoo-sphinx-autodoc",
    "odoorpc",
    "OpenUpgrade",
    "openupgradelib",
    "pylint-odoo",
}


# deprecated, use is_main_branch() instead
MAIN_BRANCHES = (
    "6.1",
    "7.0",
    "8.0",
    "9.0",
    "10.0",
    "11.0",
    "12.0",
    "13.0",
    "14.0",
    "15.0",
    "16.0",
)


def is_main_branch(branch):
    return re.match(r"^(6\.1|\d+\.0)$", branch)
