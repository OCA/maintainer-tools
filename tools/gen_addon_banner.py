# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV
# Copyright (c) 2018 GRAP (http://www.grap.coop)

import os
import click
from .manifest import read_manifest, find_addons, NoManifestFound
from .gitutils import commit_if_needed
from PIL import Image


def gen_one_addon_banner(addon_name, addon_dir, manifest, background, font):
    # It would be cleaner to modify the readme, but it is easier
    image = Image.open(background)
    # TODO:Maybe we could add the title of the addon...
    modified = []
    for path in manifest["images"]:
        image.save("%s/%s" % (addon_dir, path))
        modified.append("%s/%s" % (addon_dir, path))
    return modified


@click.command()
@click.option(
    "--background",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    default=os.path.join(
        os.path.dirname(__file__),
        "gen_addon_banner.png",
    ),
    help="Path of the Background to use",
)
@click.option(
    "--font",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="Path of the Font to use",
)
@click.option(
    "--addon-dir",
    "addon_dirs",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    multiple=True,
    help="Directory where addon manifest is located. This option " "may be repeated.",
)
@click.option(
    "--addons-dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="Directory containing several addons, the README will be "
    "generated for all installable addons found there.",
)
@click.option(
    "--commit/--no-commit",
    help="git commit changes to README.rst and index.html, if any.",
)
def gen_addon_banner(
    background,
    font,
    addon_dirs,
    addons_dir,
    commit,
):
    addons = []
    if addons_dir:
        addons.extend(find_addons(addons_dir))
    for addon_dir in addon_dirs:
        addon_name = os.path.basename(os.path.abspath(addon_dir))
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        addons.append((addon_name, os.path.abspath(addon_dir), manifest))
    modified = []
    for addon_name, addon_dir, manifest in addons:
        print(addon_dir)
        if "images" not in manifest:
            continue
        modified += gen_one_addon_banner(
            addon_name, addon_dir, manifest, background, font
        )
    if commit:
        commit_if_needed(modified, "[UPD] banners")


if __name__ == "__main__":
    gen_addon_banner()
