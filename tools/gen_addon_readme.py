# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV
# Copyright (c) 2018 GRAP (http://www.grap.coop)

import atexit
import functools
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Union
from urllib.parse import urljoin

import click
from docutils.core import publish_file
from jinja2 import Template
import pypandoc

from .gitutils import commit_if_needed
from .manifest import get_manifest_path, read_manifest, find_addons, NoManifestFound
from ._hash import hash

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class FragmentProperties:
    def __init__(self, level: int):
        self.level = level


FragmentFormat = Literal[".rst", ".md"]

FRAGMENTS_DIR = "readme"

FRAGMENTS = {
    "DESCRIPTION": FragmentProperties(level=2),
    "CONTEXT": FragmentProperties(level=2),
    "INSTALL": FragmentProperties(level=2),
    "CONFIGURE": FragmentProperties(level=2),
    "USAGE": FragmentProperties(level=2),
    "ROADMAP": FragmentProperties(level=2),
    "DEVELOP": FragmentProperties(level=2),
    "CONTRIBUTORS": FragmentProperties(level=3),
    "CREDITS": FragmentProperties(level=3),
    "HISTORY": FragmentProperties(level=2),
}

LICENSE_BADGES = {
    "AGPL-3": (
        "https://img.shields.io/badge/licence-AGPL--3-blue.png",
        "http://www.gnu.org/licenses/agpl-3.0-standalone.html",
        "License: AGPL-3",
    ),
    "LGPL-3": (
        "https://img.shields.io/badge/licence-LGPL--3-blue.png",
        "http://www.gnu.org/licenses/lgpl-3.0-standalone.html",
        "License: LGPL-3",
    ),
    "GPL-3": (
        "https://img.shields.io/badge/licence-GPL--3-blue.png",
        "http://www.gnu.org/licenses/gpl-3.0-standalone.html",
        "License: GPL-3",
    ),
}

DEVELOPMENT_STATUS_BADGES = {
    "mature": (
        "https://img.shields.io/badge/maturity-Mature-brightgreen.png",
        "https://odoo-community.org/page/development-status",
        "Mature",
    ),
    "production/stable": (
        "https://img.shields.io/badge/maturity-Production%2FStable-green.png",
        "https://odoo-community.org/page/development-status",
        "Production/Stable",
    ),
    "beta": (
        "https://img.shields.io/badge/maturity-Beta-yellow.png",
        "https://odoo-community.org/page/development-status",
        "Beta",
    ),
    "alpha": (
        "https://img.shields.io/badge/maturity-Alpha-red.png",
        "https://odoo-community.org/page/development-status",
        "Alpha",
    ),
}

# this comes from pypa/readme_renderer
RST2HTML_SETTINGS = {
    # Prevent local files from being included into the rendered output.
    # This is a security concern because people can insert files
    # that are part of the system, such as /etc/passwd.
    "file_insertion_enabled": False,
    # Halt rendering and throw an exception if there was any errors or
    # warnings from docutils.
    "halt_level": 2,
    # Output math blocks as LaTeX that can be interpreted by MathJax for
    # a prettier display of Math formulas.
    "math_output": "MathJax",
    # Disable raw html as enabling it is a security risk, we do not want
    # people to be able to include any old HTML in the final output.
    "raw_enabled": False,
    # Use typographic quotes, and transform --, ---, and ... into their
    # typographic counterparts.
    "smart_quotes": True,
    # Use the short form of syntax highlighting so that the generated
    # Pygments CSS can be used to style the output.
    "syntax_highlight": "short",
    # Since odoo/odoo@8d06889, Odoo emits a warning
    # if index.html contains an xml declaration
    "xml_declaration": False,
    # ...but even for previous versions we don't need
    # the xml declaration as docutils adds a <meta> tag:
    # <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    # utf-8 is default value for output_encoding
    # but let's make it explicit here:
    "output_encoding": "utf-8",
}

# GitHub Flavored Markdown
# - raw html is disabled
# - auto identifiers is disabled because pylint-odoo complains about them (Hyperlink
#   target "..;" is not referenced.)
PANDOC_MARKDOWN_FORMAT = "gfm-raw_html-gfm_auto_identifiers"


@functools.lru_cache(maxsize=None)
def ensure_pandoc_installed() -> None:
    pypandoc.ensure_pandoc_installed()


def make_runboat_badge(repo, branch):
    return (
        "https://img.shields.io/badge/runboat-Try%20me-875A7B.png",
        "https://runboat.odoo-community.org/builds?"
        "repo=OCA/{repo}&target_branch={branch}".format(**locals()),
        "Try me on Runboat",
    )


def make_weblate_badge(repo_name, branch, addon_name):
    branch = branch.replace(".", "-")
    return (
        "https://img.shields.io/badge/weblate-Translate%20me-F47D42.png",
        "https://translation.odoo-community.org/projects/"
        "{repo_name}-{branch}/{repo_name}-{branch}-{addon_name}".format(**locals()),
        "Translate me on Weblate",
    )


def make_repo_badge(org_name, repo_name, branch, addon_name):
    badge_repo_name = repo_name.replace("-", "--")
    badge_org_name = org_name.replace("-", "--")
    return (
        "https://img.shields.io/badge/github-{badge_org_name}%2F{badge_repo_name}"
        "-lightgray.png?logo=github".format(**locals()),
        "https://github.com/{org_name}/{repo_name}/tree/"
        "{branch}/{addon_name}".format(**locals()),
        "{org_name}/{repo_name}".format(**locals()),
    )


def generate_fragment(org_name, repo_name, branch, addon_name, file):
    fragment_lines = file.readlines()
    if not fragment_lines:
        return False

    # Replace relative path by absolute path for figures
    image_path_re = re.compile(r".*\s*\.\..* (figure|image)::\s+(?P<path>.*?)\s*$")
    module_url = (
        "https://raw.githubusercontent.com/{org_name}/{repo_name}"
        "/{branch}/{addon_name}/".format(**locals())
    )
    for index, fragment_line in enumerate(fragment_lines):
        mo = image_path_re.match(fragment_line)
        if not mo:
            continue
        path = mo.group("path")

        if path.startswith("http"):
            # It is already an absolute path
            continue
        else:
            # remove '../' if exists that make the fragment working
            # on github interface, in the 'readme' subfolder
            relative_path = path.replace("../", "")
            fragment_lines[index] = fragment_line.replace(
                path, urljoin(module_url, relative_path)
            )
    fragment = "".join(fragment_lines)

    # ensure that there is a new empty line at the end of the fragment
    if fragment[-1] != "\n":
        fragment += "\n"
    return fragment


def get_fragment_format(
    addon_dir: str, fragment_name: str
) -> Union[FragmentFormat, None]:
    """Return the format of the named fragment of the given addon.

    Raise an exception if several formats are found.
    """
    fragment_rst_filename = make_fragment_filename(addon_dir, fragment_name, ".rst")
    fragment_md_filename = make_fragment_filename(addon_dir, fragment_name, ".md")
    if os.path.exists(fragment_rst_filename):
        if os.path.exists(fragment_md_filename):
            raise SystemExit(
                f"Both .md and .rst found for {fragment_name}. Please remove one"
                f" of {fragment_rst_filename} or {fragment_md_filename}."
            )
        return ".rst"
    if os.path.exists(fragment_md_filename):
        return ".md"
    return None


def get_fragments_format(addon_dir: str) -> FragmentFormat:
    """Return the format of the fragments of the given addon.

    Raise an exception if several formats are found.
    """
    fragments_format = None
    for fragment_name in FRAGMENTS:
        this_fragment_format = get_fragment_format(addon_dir, fragment_name)
        if this_fragment_format is None:
            # fragment does not exist
            continue
        if fragments_format and this_fragment_format != fragments_format:
            raise SystemExit(
                f"Both .md and .rst fragments found in {addon_dir}/readme. "
                f"Please ensure the same format is used for all fragments."
            )
        fragments_format = this_fragment_format
    return fragments_format


def make_fragment_filename(
    addon_dir: str, fragment_name: str, format: FragmentFormat
) -> str:
    return os.path.join(
        addon_dir,
        FRAGMENTS_DIR,
        fragment_name + format,
    )


def safe_remove(filename: str) -> None:
    try:
        os.remove(filename)
    except Exception:
        pass


def prepare_rst_fragment(addon_dir: str, fragment_name: str) -> Union[str, None]:
    fragment_rst_filename = make_fragment_filename(addon_dir, fragment_name, ".rst")
    fragment_md_filename = make_fragment_filename(addon_dir, fragment_name, ".md")
    if os.path.exists(fragment_rst_filename):
        if os.path.exists(fragment_md_filename):
            raise SystemExit(
                f"Both .md and .rst fragment found. Please remove one of "
                f"{fragment_rst_filename} or {fragment_md_filename}."
            )
        return fragment_rst_filename
    if not os.path.exists(fragment_md_filename):
        # no .rst nor .md fragment found
        return None
    # convert .md to .rst
    fragment_properties = FRAGMENTS[fragment_name]
    ensure_pandoc_installed()
    atexit.register(safe_remove, fragment_rst_filename)
    pypandoc.convert_file(
        fragment_md_filename,
        format=PANDOC_MARKDOWN_FORMAT,
        to="rst",
        outputfile=fragment_rst_filename,
        extra_args=[f"--shift-heading-level-by={fragment_properties.level-2}"],
        sandbox=True,
    )
    return fragment_rst_filename


def fragment_exists(addon_dir: str, fragment_name: str) -> bool:
    return os.path.exists(
        make_fragment_filename(
            addon_dir,
            fragment_name,
            ".rst",
        )
    ) or os.path.exists(
        make_fragment_filename(
            addon_dir,
            fragment_name,
            ".md",
        )
    )


def convert_fragments_to_md(addon_dir: str) -> None:
    """Convert all fragments from .rst to .md format."""
    for fragment_name in FRAGMENTS:
        fragment_rst_filename = make_fragment_filename(
            addon_dir,
            fragment_name,
            ".rst",
        )
        if not os.path.exists(fragment_rst_filename):
            continue
        fragment_md_filename = make_fragment_filename(
            addon_dir,
            fragment_name,
            ".md",
        )
        if os.path.exists(fragment_md_filename):
            continue
        ensure_pandoc_installed()
        pypandoc.convert_file(
            fragment_rst_filename,
            format="rst",
            to=PANDOC_MARKDOWN_FORMAT,
            outputfile=fragment_md_filename,
            extra_args=["--shift-heading-level=1"],
            sandbox=True,
        )
        os.remove(fragment_rst_filename)


def gen_one_addon_readme(
    org_name,
    repo_name,
    branch,
    addon_name,
    addon_dir,
    manifest,
    template_filename,
    readme_filename,
    source_digest,
):
    fragments_format = get_fragments_format(addon_dir)
    fragments = {}
    for fragment_name in FRAGMENTS:
        fragment_filename = prepare_rst_fragment(addon_dir, fragment_name)
        if fragment_filename:
            with open(fragment_filename, "r", encoding="utf8") as f:
                fragment = generate_fragment(org_name, repo_name, branch, addon_name, f)
                if fragment:
                    fragments[fragment_name] = fragment
    badges = []
    development_status = manifest.get("development_status", "Beta").lower()
    if development_status in DEVELOPMENT_STATUS_BADGES:
        badges.append(DEVELOPMENT_STATUS_BADGES[development_status])
    license = manifest.get("license")
    if license in LICENSE_BADGES:
        badges.append(LICENSE_BADGES[license])
    badges.append(make_repo_badge(org_name, repo_name, branch, addon_name))
    if org_name == "OCA":
        badges.append(make_weblate_badge(repo_name, branch, addon_name))
    if org_name == "OCA":
        badges.append(make_runboat_badge(repo_name, branch))
    authors = [
        a.strip()
        for a in manifest.get("author", "").split(",")
        if "(OCA)" not in a
        # remove OCA because it's in authors for the purpose
        # of finding OCA addons in apps.odoo.com, OCA is not
        # a real author, but is rather referenced in the
        # maintainers section
    ]
    # generate
    with open(template_filename, "r", encoding="utf8") as tf:
        template = Template(tf.read())
    with open(readme_filename, "w", encoding="utf8") as rf:
        rf.write(
            template.render(
                addon_name=addon_name,
                authors=authors,
                badges=badges,
                branch=branch,
                fragments=fragments,
                manifest=manifest,
                org_name=org_name,
                repo_name=repo_name,
                development_status=development_status,
                source_digest=source_digest,
                level3_underline="~" if fragments_format == ".rst" else "-",
            )
        )


def check_rst(readme_filename):
    with tempfile.NamedTemporaryFile() as f:
        publish_file(
            source_path=readme_filename,
            destination=f,
            writer_name="html4css1",
            settings_overrides=RST2HTML_SETTINGS,
        )


def gen_one_addon_index(readme_filename):
    addon_dir = os.path.dirname(readme_filename)
    index_dir = os.path.join(addon_dir, "static", "description")
    index_filename = os.path.join(index_dir, "index.html")
    if os.path.exists(index_filename):
        with open(index_filename) as f:
            if "oca-gen-addon-readme" not in f.read():
                # index was created manually
                return
    if not os.path.isdir(index_dir):
        os.makedirs(index_dir)
    publish_file(
        source_path=readme_filename,
        destination_path=index_filename,
        writer_name="html4css1",
        settings_overrides=RST2HTML_SETTINGS,
    )
    with open(index_filename, "rb") as f:
        index = f.read()
    # remove the docutils version from generated html, to avoid
    # useless changes in the readme
    index = re.sub(
        rb"(<meta.*generator.*Docutils)\s*[\d.]+", rb"\1", index, re.MULTILINE
    )
    with open(index_filename, "wb") as f:
        f.write(index)
    return index_filename


def _source_digest_match(readme_filename, source_digest):
    if not os.path.isfile(readme_filename):
        return False
    digest_comment = f"!! source digest: {source_digest}"
    with open(readme_filename, "r", encoding="utf8") as f:
        for line in f:
            if digest_comment in line:
                return True
    return False


def _get_source_digest(readme_filename: str) -> Union[str, None]:
    """Get the source digest from the given readme file.

    Return None if the file does not exist, or if the digest is not found.
    """
    readme_path = Path(readme_filename)
    if not readme_path.is_file():
        return None
    digest_re = re.compile(r"!! source digest: (?P<digest>sha256:\w+)")
    mo = digest_re.search(readme_path.read_text(encoding="utf8"))
    if not mo:
        return None
    return mo.group("digest")


@click.command()
@click.option("--org-name", default="OCA", help="Organization name, eg. OCA.")
@click.option("--repo-name", required=True, help="Repository name, eg. server-tools.")
@click.option("--branch", required=True, help="Odoo series. eg 11.0.")
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
    "--if-source-changed",
    "--if-fragments-changed",
    "if_fragments_changed",
    is_flag=True,
    default=False,
    help="Only generate if source fragments or manifest changed.",
)
@click.option(
    "--keep-source-digest",
    is_flag=True,
    default=False,
    help=(
        "Do not update the source digest in the generated file. "
        "Useful to avoid merge conflicts when changes that do not impact "
        "the generated file are made to the manifest."
    ),
)
@click.option(
    "--commit/--no-commit",
    help="git commit changes to README.rst and index.html, if any.",
)
@click.option(
    "--gen-html/--no-gen-html",
    default=True,
    help="Generate index html file.",
)
@click.option(
    "--template-filename",
    default=os.path.join(
        os.path.dirname(__file__),
        "gen_addon_readme.rst.jinja",
    ),
    help="Template file to use.",
)
@click.option(
    "--convert-fragments-to-markdown",
    is_flag=True,
    default=False,
)
def gen_addon_readme(
    org_name,
    repo_name,
    branch,
    addon_dirs,
    addons_dir,
    commit,
    gen_html,
    template_filename,
    if_fragments_changed,
    convert_fragments_to_markdown,
    keep_source_digest,
):
    """Generate README.rst from fragments.

    Do nothing if readme/DESCRIPTION(.rst|.md) is absent, otherwise overwrite
    existing README.rst with content generated from the template,
    fragments (DESCRIPTION(.rst|.md), USAGE(.rst|.md), etc) and the addon manifest.
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
    readme_filenames = []
    for addon_name, addon_dir, manifest in addons:
        if convert_fragments_to_markdown:
            convert_fragments_to_md(addon_dir)
        if not fragment_exists(addon_dir, "DESCRIPTION"):
            continue
        readme_filename = os.path.join(addon_dir, "README.rst")
        source_digest = hash(
            get_manifest_path(addon_dir),
            os.path.join(addon_dir, FRAGMENTS_DIR),
            relative_to=addon_dir,
        )
        if if_fragments_changed:
            if _source_digest_match(readme_filename, source_digest):
                continue
        if keep_source_digest:
            source_digest = _get_source_digest(readme_filename) or source_digest
        gen_one_addon_readme(
            org_name,
            repo_name,
            branch,
            addon_name,
            addon_dir,
            manifest,
            template_filename,
            readme_filename,
            source_digest,
        )
        check_rst(readme_filename)
        readme_filenames.append(readme_filename)
        if gen_html:
            if not manifest.get("preloadable", True):
                continue
            index_filename = gen_one_addon_index(readme_filename)
            if index_filename:
                readme_filenames.append(index_filename)
    if commit:
        commit_if_needed(readme_filenames, "[UPD] README.rst")


if __name__ == "__main__":
    gen_addon_readme()
