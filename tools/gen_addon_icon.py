# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2019 Eficent Business and IT Consulting Services S.L.
#        (http://www.eficent.com)

import os
import shutil
import json
import asyncio
import click
from pyppeteer import launch
from string import Template

from .gitutils import commit_if_needed
from .manifest import NoManifestFound, find_addons, read_manifest

ICONS_DIR = os.path.join("static", "description")

ICON_TYPE = "png"

ICON_TYPES = ["png", "svg", "pdf"]

COLORS = ["orange", "pink", "yellow", "gray", "teal", "blue1", "blue2", "red", "green"]

SUPPORTED_SERVICE_URLS = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css",  # noqa
    "https://cdnjs.cloudflare.com/ajax/libs/simple-line-icons/2.5.5/css/simple-line-icons.min.css",  # noqa
    "https://cdnjs.cloudflare.com/ajax/libs/open-iconic/1.1.1/font/css/open-iconic.min.css",  # noqa
    "https://cdnjs.cloudflare.com/ajax/libs/material-design-icons/3.0.2/iconfont/material-icons.min.css",  # noqa
    "https://cdnjs.cloudflare.com/ajax/libs/tabler-icons/1.35.0/iconfont/tabler-icons.min.css",  # noqa
    "https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css",  # noqa
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css",  # noqa
    "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css",  # noqa
    "https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css",  # noqa
    "https://www.experimentalenhancements.com/FontCountry/FontCountry.css",  # noqa
]

TEMPLATE = Template(
    """
<html>
    <body>
        <div class="icon-box o$icon_color">
            <span>
                <i class="$icon_set_params"></i>
                $icon_extra
            </span>
        </div>
    </body>
</html>
"""
)


def gen_one_addon_icon(icon_dir, src_icon=None, filetype=ICON_TYPE):
    icon_filename = os.path.join(icon_dir, "icon.%s" % filetype)
    if not src_icon:
        src_icon = os.path.join(
            os.path.dirname(__file__).rpartition("tools")[0],
            "template",
            "module",
            ICONS_DIR,
            "icon.%s" % filetype,
        )
    if os.path.exists(src_icon):
        if not os.path.exists(icon_dir):
            os.makedirs(icon_dir)
        shutil.copyfile(src_icon, icon_filename)
        return icon_filename
    return None


def _prepare_extra_icon_html(icon_extra):
    if not icon_extra:
        return ""
    icon_extra = json.loads(icon_extra.replace("'", '"'))
    extra_styles = {"top", "left", "shadow", "color", "position", "font-size"}
    icon_extra_html = ""
    for icon, params in icon_extra.items():
        params.setdefault("color", "white")
        params.setdefault("position", "absolute")
        params.setdefault("font-size", "90px")
        params.setdefault("top", "15px")
        params.setdefault("left", "20px")
        style = [
            "{}: {}".format(x, params[x]) for x in extra_styles if x in params.keys()
        ]
        icon_extra_html += """
        <i class="{}" style="{}" />
        """.format(icon, ";".join(style))
    return icon_extra_html


minimal_args = [
    "--autoplay-policy=user-gesture-required",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-default-apps",
    "--disable-dev-shm-usage",
    "--disable-domain-reliability",
    "--disable-extensions",
    "--disable-features=AudioServiceOutOfProcess",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-notifications",
    "--disable-offer-store-unmasked-wallet-cards",
    "--disable-popup-blocking",
    "--disable-print-preview",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-setuid-sandbox",
    "--disable-speech-api",
    "--disable-sync",
    "--hide-scrollbars",
    "--ignore-gpu-blacklist",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-default-browser-check",
    "--no-first-run",
    "--no-pings",
    "--no-sandbox",
    "--no-zygote",
    "--password-store=basic",
]


async def generate_template_screenshot(template, options, filetype):
    """Generate custom icon with chromium headless"""
    styles_filename = os.path.join(os.path.dirname(__file__), "gen_addon_icon.css")
    browser = await launch(headless=True, args=minimal_args)
    page = await browser.newPage()
    await page.goto("data:text/html,{}".format(template))
    for url in SUPPORTED_SERVICE_URLS:
        await page.addStyleTag({"url": url})
    await page.addStyleTag({"path": styles_filename})
    await page.emulateMedia("screen")
    if filetype in ["png", "jpg"]:
        await page.screenshot(options)
    else:
        await page.pdf(options)
    await browser.close()


def gen_special_addon_icon(icon_dir, icon_set_params, icon_color, icon_extra, filetype):
    """Generate icons using popular icon libraries like fontawesome, etc"""
    icon_filename = os.path.join(icon_dir, "icon.%s" % filetype)
    if filetype in ["png", "jpg"]:
        options = {
            "path": icon_filename,
            "omitBackground": True,
            "quality": 100,
            "clip": {
                "y": 0,
                "x": 0,
                "width": 140,
                "height": 140,
            },
        }
    else:
        options = {
            "path": icon_filename,
            "width": 140,
            "height": 140,
            "printBackground": False,
            "omitBackground": True,
            "scale": 1,
        }
    template = TEMPLATE.substitute(
        icon_set_params=icon_set_params,
        icon_color=icon_color,
        icon_extra=_prepare_extra_icon_html(icon_extra),
    )
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
    asyncio.get_event_loop().run_until_complete(
        generate_template_screenshot(template, options, filetype)
    )
    return icon_filename


@click.command()
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
    help="Directory containing several addons, the icon will be "
    "put for all installable addons found there.",
)
@click.option("--commit/--no-commit", help="git commit icon, if not any.")
@click.option("--icon-set-params", help="Use this set to generate an automatic icon")
@click.option(
    "--icon-color",
    help="Options: orange, pink, yellow, gray, teal, " "blue1, blue2, red, green",
)
@click.option("--icon-extra", help="Extra icons to overlap")
@click.option("--format", help="Icon format, you can choose between png or pdf")
def gen_addon_icon(
    addon_dirs, addons_dir, commit, icon_set_params, icon_color, icon_extra, format
):
    """Put default OCA icon of type ICON_TYPE.

    Do nothing if the icon already exists in ICONS_DIR, otherwise put
    the default icon.
    """
    addons = []
    if addons_dir:
        addons.extend(find_addons(addons_dir))
    for addon_dir in addon_dirs:
        addon_name = os.path.basename(os.path.abspath(addon_dir))
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        addons.append((addon_name, addon_dir, manifest))
    icon_filenames = []
    for addon_name, addon_dir, manifest in addons:
        if not manifest.get("preloadable", True):
            continue
        icon_dir = os.path.join(addon_dir, ICONS_DIR)
        exist = False
        for icon_type in ICON_TYPES:
            icon_filename = os.path.join(icon_dir, "icon.%s" % icon_type)
            if os.path.exists(icon_filename):
                # icon was created manually
                exist = True
                break
        if exist and not icon_set_params and not icon_extra:
            continue
        if icon_set_params or icon_extra:
            # Apply some default so we can just put the icon params
            icon_color = icon_color or "teal"
            if format not in ICON_TYPES:
                format = "png"
            icon_filename = gen_special_addon_icon(
                icon_dir,
                icon_set_params=icon_set_params,
                icon_color=icon_color,
                icon_extra=icon_extra,
                filetype=format,
            )
        else:
            icon_filename = gen_one_addon_icon(icon_dir)
        if icon_filename:
            icon_filenames.append(icon_filename)

    if icon_filenames and commit:
        commit_if_needed(icon_filenames, "[ADD] icon.%s" % ICON_TYPE)


if __name__ == "__main__":
    gen_addon_icon()
