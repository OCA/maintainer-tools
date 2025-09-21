"""Set the website key in addons manifests."""

import os
import re
from pathlib import Path

import click

from .manifest import get_manifest_path, parse_manifest

WEBSITE_KEY_RE = re.compile(r"""(["']website["']\s*:\s*["'])([^"']*)(["'])""")


@click.command()
@click.argument("url")
@click.argument("manifest", nargs=-1, type=click.Path())
@click.option("--addons-dir", default=".")
def main(url, addons_dir, manifest):
    # Specifying one or more manifest files has the highest priority
    if manifest:
        for manifest_file in manifest:
            _fix_website(Path(manifest_file).parent, manifest_file, url)
    else:
        for addon_dir in os.listdir(addons_dir):
            manifest_path = get_manifest_path(os.path.join(addons_dir, addon_dir))
            if not manifest_path:
                continue
            _fix_website(addon_dir, manifest_path, url)


def _fix_website(addon_dir, manifest_path, url):
    """
    Replaces the website in the manifest pointed by manifest_path by url.

    :param manifest_path: path to the manifest file, relative or absolute
    :param addon_dir: used to indicate errors, points to parent path of manifest file
    :param url: new value for the "website" key in the manifest content
    """
    try:
        with open(manifest_path) as manifest_file:
            manifest = parse_manifest(manifest_file.read())
    except Exception:
        raise click.ClickException(
            "Error parsing manifest {}.".format(manifest_path)
        )
    if "website" not in manifest:
        raise click.ClickException(
            "website key not found in manifest in {}.".format(addon_dir)
        )
    with open(manifest_path) as manifest_file:
        manifest_str = manifest_file.read()
    new_manifest_str, n = WEBSITE_KEY_RE.subn(
        r"\g<1>" + url + r"\g<3>", manifest_str
    )
    if n == 0:
        raise click.ClickException(
            "no website key match in manifest in {}.".format(addon_dir)
        )
    if n > 1:
        raise click.ClickException(
            "more than one website key match in manifest in {}.".format(addon_dir)
        )
    if new_manifest_str != manifest_str:
        with open(manifest_path, "w") as manifest_file:
            manifest_file.write(new_manifest_str)
