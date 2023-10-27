#!/usr/bin/env python3
"""Generate setup/_metapackage with dependencies on all installable addons in repo."""

import datetime
import re
import sys
from pathlib import Path
from typing import Any, List, Optional


from manifestoo_core.odoo_series import (
    OdooSeries,
    detect_from_addon_version as detect_odoo_series_from_addon_version,
)
from manifestoo_core.addon import is_addon_dir, Addon
from manifestoo_core.metadata import addon_name_to_requirement

from .compat import tomllib

METAPACKAGE_PATH = Path("setup") / "_metapackage"

PYPROJECT_TOML_METAPACKAGE = """\
[project]
name = "{name}"
version = "{version}"
dependencies = {dependencies}
classifiers=[
    "Programming Language :: Python",
    "Framework :: Odoo",
    "Framework :: Odoo :: {odoo_series}",
]
"""


def _gen_metapackage(addons_dir: Path, name: str):
    meta_install_requires = []
    odoo_series_detected = set()
    metapackage_path = addons_dir / METAPACKAGE_PATH
    pyproject_toml_path = metapackage_path / "pyproject.toml"

    for addon_dir in addons_dir.iterdir():
        if not is_addon_dir(addon_dir):
            continue
        addon = Addon.from_addon_dir(addon_dir)
        odoo_series = detect_odoo_series_from_addon_version(addon.manifest.version)
        if not odoo_series:
            sys.stderr.write(
                f"Could not detect Odoo series from addon version in {addon_dir}\n"
            )
            return
        meta_install_requires.append(
            addon_name_to_requirement(addon_dir.name, odoo_series)
        )
        odoo_series_detected.add(odoo_series)

    if len(meta_install_requires) == 0:
        sys.stderr.write("No installable addon found, not generating metapackage.\n")
        return
    if len(odoo_series_detected) > 1:
        raise RuntimeError(
            f"Not all addon are for the same Odoo version: {odoo_series_detected}"
        )

    odoo_series = next(iter(odoo_series_detected))

    dependencies = "[\n{}]".format(
        "".join(
            [
                " " * 4 + '"' + install_require + '",\n'
                for install_require in sorted(meta_install_requires)
            ]
        ),
    )

    version = _get_current_version(pyproject_toml_path)
    if set(meta_install_requires) != set(
        _get_current_dependencies(pyproject_toml_path)
    ):
        version = _get_next_version(odoo_series, version)

    if not metapackage_path.exists():
        metapackage_path.mkdir(parents=True)
    pyproject_toml = PYPROJECT_TOML_METAPACKAGE.format(
        name=name,
        version=version,
        odoo_series=odoo_series.value,
        dependencies=dependencies,
    )
    pyproject_toml_path.write_text(pyproject_toml)

    _cleanup(metapackage_path)


def _get_current_dependencies(pyproject_toml_path: Path) -> Any:
    if not pyproject_toml_path.exists():
        return []
    pyproject_toml = tomllib.loads(pyproject_toml_path.read_text())
    return pyproject_toml.get("project", {}).get("dependencies", [])


def _get_current_version(pyproject_toml_path: Path) -> Optional[str]:
    if not pyproject_toml_path.exists():
        return None
    pyproject_toml = tomllib.loads(pyproject_toml_path.read_text())
    return pyproject_toml.get("project", {}).get("version", None)


def _get_next_version(odoo_series: OdooSeries, current_version: str):
    version_date = datetime.date.today().strftime("%Y%m%d")
    if current_version:
        version_re = r"^[0-9]{1,2}\.0.(?P<date>[0-9]{8})\.(?P<index>[0-9]+)$"
        mo = re.match(version_re, current_version)
        if not mo:
            raise RuntimeError(f"Could not parse version {current_version}")
        if mo.group("date") == version_date:
            index = int(mo.group("index")) + 1
        else:
            index = 0
    else:
        index = 0
    return f"{odoo_series.value}.{version_date}.{index}"


def _cleanup(metapackage_path: Path):
    for name in ("setup.py", "setup.cfg", "VERSION.txt"):
        path = metapackage_path / name
        if path.exists():
            path.unlink()


def main(argv: Optional[List[str]] = None) -> int:
    _gen_metapackage(Path.cwd(), argv[0] if argv else sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
