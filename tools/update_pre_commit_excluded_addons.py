#!/usr/bin/env python
import ast
import os

import click

PRE_COMMIT_FILE_PATH = ".pre-commit-config.yaml"
PRE_COMMIT_EXCLUDE_SEPARATOR = "# NOT INSTALLABLE ADDONS"
PRE_COMMIT_EXCLUDE_SEPARATOR_END = "# END NOT INSTALLABLE ADDONS"

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")


class NoManifestFound(Exception):
    pass


def get_manifest_path(addon_dir):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.isfile(manifest_path):
            return manifest_path


def parse_manifest(s):
    return ast.literal_eval(s)


def read_manifest(addon_dir):
    manifest_path = get_manifest_path(addon_dir)
    if not manifest_path:
        raise NoManifestFound("no Odoo manifest found in %s" % addon_dir)
    with open(manifest_path) as mf:
        return parse_manifest(mf.read())


def is_not_installable_addon(addon_dir):
    try:
        manifest = read_manifest(addon_dir)
    except NoManifestFound:
        return False
    return not manifest.get("installable", True)


@click.command()
@click.option("--addons-dir", default="")
def main(addons_dir):
    """ Update .pre-commit-config.yaml exclude section with the list of
        uninstallable addons. The section must begin with a line
        containing '# NOT INSTALLABLE ADDONS' and end with a line
        containing '# END NOT INSTALLABLE ADDONS'.
    """
    not_installable_addons = []
    addons = os.listdir(addons_dir or ".")
    for addon in addons:
        addon_dir = os.path.join(addons_dir, addon)
        if is_not_installable_addon(addon_dir):
            exclude_addon = "  ^{addon_dir}/".format(addon_dir=addon_dir)
            not_installable_addons.append(exclude_addon)
    not_installable_addons.sort()
    not_installable_addons_pre_commit = "|\n".join(not_installable_addons)
    if not_installable_addons_pre_commit:
        not_installable_addons_pre_commit += "|\n"
    replace_on = False
    with open(PRE_COMMIT_FILE_PATH, "r+") as pre_commit_file:
        pre_commit_file_lines = pre_commit_file.readlines()
        pre_commit_file.seek(0)
        for line in pre_commit_file_lines:
            if PRE_COMMIT_EXCLUDE_SEPARATOR_END in line:
                replace_on = False
            if replace_on:
                continue
            if PRE_COMMIT_EXCLUDE_SEPARATOR in line:
                replace_on = True
                pre_commit_file.write(line)
                pre_commit_file.write(not_installable_addons_pre_commit)
                continue
            pre_commit_file.write(line)
        pre_commit_file.truncate()


if __name__ == "__main__":
    main()
