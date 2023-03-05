# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
This script helps you to add all the OCA repositories in batch in apps.odoo.com
platform. For now it's not adapted to other organization as it takes the
information from static mapping here. It shouldn't be too much difficult to
adapt this to other organizations.

It also serves as status scanner for knowing which repos are not yet being
automatically scanned (showing the conflict but ommited in case of simply
empty repo), and allowing to force the scan in that moment. Note that current
platform auto-scan all the repositories daily, so this operation is not really
needed except being in a hurry.

WARNING: This work is based on current platform implementation. This might
stop working if Odoo changes it through time.

Installation
============

It requires to have Python library `selenium`, that you can install regularly
through pip doing `sudo pip3 install selenium` or using specific OS packages.

It also requires chromedriver binary. If you are in Ubuntu or derivative, you
can do:

`sudo apt-get install chromium-chromedriver`

The 'chromedriver' executable must be in your PATH.

Configuration
=============

You can have a file called oca.cfg on the same folder of the script for
storing credentials parameters. You can generate an skeleton config running
this script for a first time.

The credentials are stored in the section [apps.odoo.com], with the names
"username" and "password", which are self-explanatory.

If not set, a prompt will ask you to enter user and password.

Usage
=====

oca-publish-modules [OPTIONS]

Options:
  --branch TEXT                   Limit to specific Odoo series. eg 11.0.
  --repository TEXT               Limit to a repository. eg contract.
  --registration / --no-registration
                                  Perform the registration of repositories.
  --status / --no-status          Retrieve the status of bad repositories.
  --force-scan / --no-force-scan  If auto-scan not activated, activate it and
                                  perform a scan in that moment.
  --scan-skip-empty / --scan-no-skip-empty
                                  Skip scan of empty repositories (no matter
                                  force scan value).
  --help                          Show the help.
"""

from __future__ import print_function
import logging
from getpass import getpass
import click
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

from .oca_projects import get_repositories_and_branches, url
from .config import read_config

_logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--branch", "target_branch", help="Limit to specific Odoo series. eg 11.0."
)
@click.option(
    "--repository", "target_repository", help="Limit to a repository. eg contract."
)
@click.option("--org", help="GitHub organization (default=OCA)", default="OCA")
@click.option(
    "--registration/--no-registration",
    "do_registration",
    default=True,
    help="Perform the registration of repositories.",
)
@click.option(
    "--status/--no-status",
    "do_status",
    default=True,
    help="Retrieve the status of bad repositories.",
)
@click.option(
    "--force-scan/--no-force-scan",
    "force_scan",
    default=False,
    help="If auto-scan not activated, activate it and request "
    "apps.odoo.com to perform a scan in that moment.",
)
@click.option(
    "--scan-skip-empty/--scan-no-skip-empty",
    "scan_skip_empty",
    default=True,
    help="Skip scan of empty repositories (no matter force scan " "value).",
)
def main(
    target_branch,
    target_repository,
    org,
    do_registration,
    do_status,
    force_scan,
    scan_skip_empty,
):
    config = read_config()
    user = config.get("apps.odoo.com", "username")
    if not user:
        user = input("Odoo.com publisher account:")
    password = config.get("apps.odoo.com", "password")
    if not password:
        password = getpass(prompt="Odoo.com account password:")
    # Selenium options
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(
        options=options,
    )
    login(driver, user, password)
    # First pass: register all repositories (if already registered, there
    # will be an immediate warning in the current browser page and won't
    # continue, so we can simply overwrite the value in the field).
    if do_registration:
        for repository, branch in get_repositories_and_branches():
            if target_branch and branch != target_branch:
                continue
            if target_repository and target_repository != repository:
                continue
            repository_url = url(repository) + "#" + branch
            print(
                "INFO: Adding %s#%s from %s... (if not yet present)"
                % (
                    repository,
                    branch,
                    repository_url,
                )
            )
            register_repository(driver, repository_url)
    # Second pass: check published state and try to publish if not yet done
    if do_status:
        for repository, branch in get_repositories_and_branches():
            if target_branch and branch != target_branch:
                continue
            if target_repository and target_repository != repository:
                continue
            # assume this query returns everything we need in one page
            driver.get(
                "https://apps.odoo.com/apps/dashboard/repos?"
                "search_in=url&search={org}/{repository}".format(
                    org=org, repository=repository
                )
            )
            scan_repository(
                driver,
                org,
                repository,
                branch,
                force_scan,
                scan_skip_empty,
            )


def login(driver, user, password):
    wait = WebDriverWait(driver, 10)
    driver.get(
        "https://www.odoo.com/web/login?redirect=%2Foauth2%2Fauth%2F%3Fscope"
        "%3Duserinfo%26redirect_uri%3Dhttps%253A%252F%252Fapps.odoo.com%252F"
        "auth_oauth%252Fsignin%26state%3D%257B%2522p%2522%253A%2B1%252C%2B"
        "%2522r%2522%253A%2B%2522%25252F%25252Fapps.odoo.com%25252Fapps%25"
        "22%252C%2B%2522d%2522%253A%2B%2522apps%2522%257D%26response_type%3D"
        "token%26client_id%3Da0a30d16-6095-11e2-9c70-002590a17fd8&scope=user"
        "info&mode=login&redirect_hostname=https%3A%2F%2Fapps.odoo.com&login="
    )
    login_field = driver.find_element_by_id("login")
    login_field.clear()
    login_field.send_keys(user)
    password_field = driver.find_element_by_id("password")
    password_field.clear()
    password_field.send_keys(password)
    login_button = driver.find_element_by_xpath(
        './/form[@action="/web/login"]//button[@type="submit"]'
    )
    login_button.click()
    wait.until(lambda driver: driver.current_url == "https://apps.odoo.com/apps")


def register_repository(driver, repository):
    driver.get("https://apps.odoo.com/apps/upload")
    url_field = driver.find_element_by_name("url")
    url_field.clear()
    url_field.send_keys(repository)
    submit_button = driver.find_element_by_id("apps_submit_repo_button")
    submit_button.click()


def scan_repository(driver, org, repository, branch, force_scan, scan_skip_empty):
    wait = WebDriverWait(driver, 300)
    for protocol in ("https", "ssh"):
        repository_url = url(repository, protocol=protocol, org_name=org) + "#" + branch
        try:
            item_container = driver.find_element_by_xpath(
                './/span[@id="repo_url" and text()="%s"]'
                "/ancestor::li[1]" % repository_url
            )
        except NoSuchElementException:
            pass
        else:
            break  # found
    else:
        # not found
        print(
            "WARNING: {org}/{repository}#{branch} "
            "not registered in this account.".format(
                org=org, repository=repository, branch=branch
            )
        )
        return
    try:
        error_item = item_container.find_element_by_xpath(
            './/div[@id="help_error"]/div/p',
        )
    except NoSuchElementException:
        error_item = False
    is_empty = False
    if error_item:
        is_empty = error_item.text.startswith("No module found in repository")
        if not is_empty:
            print("ERROR: %s:\n%s" % (repository_url, error_item.text))
    if force_scan and not (is_empty and scan_skip_empty):
        print("INFO: Doing the scan on %s" % repository_url)
        auto_scan_checkbox = item_container.find_element_by_xpath(
            './/input[@name="auto_scan"]'
        )
        if not auto_scan_checkbox.is_selected():
            auto_scan_checkbox.click()
            scan_link = item_container.find_element_by_class_name("js_repo_scan")
            scan_link.click()
            wait.until(
                lambda driver: driver.current_url
                == "https://apps.odoo.com/apps/dashboard/repos"
            )


if __name__ == "__main__":
    main()
