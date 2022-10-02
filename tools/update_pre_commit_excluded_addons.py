#!/usr/bin/env python
import ast
import os

import click

PRE_COMMIT_FILE_PATH = ".pre-commit-config.yaml"
COVERAGE_FILE_PATH = ".coveragerc"
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


def update_not_installable_addons_dir_in_file(
    not_installable_addons_dir, file_path, line_format=None, line_end="\n"
):
    if not os.path.exists(file_path):
        click.echo(f"File {file_path} not found: Skipped")
        return
    if line_format:
        not_installable_addons_dir = [
            line_format.format(addon_dir=addon_dir)
            for addon_dir in not_installable_addons_dir
        ]
    if not_installable_addons_dir:
        with open(file_path, "r+") as text_io:
            lines = text_io.readlines()
            text_io.seek(0)
            replace_on = False
            for line in lines:
                if PRE_COMMIT_EXCLUDE_SEPARATOR_END in line:
                    replace_on = False
                if replace_on:
                    continue
                if PRE_COMMIT_EXCLUDE_SEPARATOR in line:
                    replace_on = True
                    text_io.write(line)
                    preprend_spaces = line[: len(line) - len(line.lstrip(" "))]
                    content_to_replace = line_end.join(
                        [
                            f"{preprend_spaces}{addon_dir}"
                            for addon_dir in not_installable_addons_dir
                        ]
                    )
                    content_to_replace += line_end
                    text_io.write(content_to_replace)
                    continue
                text_io.write(line)
            text_io.truncate()


@click.command()
@click.option("--addons-dir", default="")
def main(addons_dir):
    """Update .pre-commit-config.yaml and .coveragerc files to exclude
    uninstallable addons. The content block to update must begin with a line
    containing '# NOT INSTALLABLE ADDONS' and end with a line
    containing '# END NOT INSTALLABLE ADDONS'.

    In .pre-commit-config.yaml:

    .. code-block:: yaml

        exclude:  |
          # NOT INSTALLABLE ADDONS
          # END NOT INSTALLABLE ADDONS
    ..

    In .coveragerc

    .. code-block:: yaml

        [report]
        omit =
            # NOT INSTALLABLE ADDONS
            # END NOT INSTALLABLE ADDONS
    ..

    """
    not_installable_addons_dir = []
    addons = os.listdir(addons_dir or ".")
    for addon in addons:
        addon_dir = os.path.join(addons_dir, addon)
        if is_not_installable_addon(addon_dir):
            not_installable_addons_dir.append(addon_dir)
    not_installable_addons_dir.sort()
    update_not_installable_addons_dir_in_file(
        not_installable_addons_dir, PRE_COMMIT_FILE_PATH, "^{addon_dir}/", "|\n"
    )
    update_not_installable_addons_dir_in_file(
        not_installable_addons_dir, COVERAGE_FILE_PATH, "{addon_dir}/*", "\n"
    )


if __name__ == "__main__":
    main()
