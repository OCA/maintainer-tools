# Copyright (c) 2015-2018 ACSONE SA/NV
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)

import ast
import os

MANIFEST_NAMES = ('__manifest__.py', '__openerp__.py', '__terp__.py')


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


def find_addons(addons_dir, installable_only=True):
    """ yield (addon_name, addon_dir, manifest) """
    for addon_name in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, addon_name)
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        if installable_only and not manifest.get('installable', True):
            continue
        yield addon_name, addon_dir, manifest
