import subprocess
import sys
import textwrap

import pytest

from tools.gen_external_dependencies import main as gen_external_dependencies

from .utils import dir_changer


def _make_addon(
    addons_dir, addon_name, depends, external_dependencies, installable=True
):
    addon_dir = addons_dir / addon_name
    addon_dir.mkdir()
    manifest = {
        "name": addon_name,
        "version": "16.0.1.0.0",
        "depends": depends,
        "external_dependencies": external_dependencies,
        "installable": installable,
    }
    addon_dir.joinpath("__manifest__.py").write_text(repr(manifest))
    addon_dir.joinpath("__init__.py").touch()


@pytest.mark.skipif("sys.version_info < (3,7)")
def test_gen_external_dependencies(tmp_path):
    ...
    _make_addon(
        tmp_path,
        addon_name="addon1",
        depends=["mis_builder"],
        external_dependencies={"python": ["requests", "xlrd"]},
    )
    _make_addon(
        tmp_path,
        addon_name="addon2",
        depends=[],
        external_dependencies={"python": ["requests", "pydantic>=2"]},
    )
    _make_addon(
        tmp_path,
        addon_name="addon3",
        depends=[],
        external_dependencies={},
        installable=False,
    )
    with dir_changer(tmp_path):
        assert gen_external_dependencies() != 0  # no pyproject.toml
        subprocess.run([sys.executable, "-m", "whool", "init"], check=True)
        assert tmp_path.joinpath("addon1").joinpath("pyproject.toml").is_file()
        assert tmp_path.joinpath("addon2").joinpath("pyproject.toml").is_file()
        assert gen_external_dependencies() == 0
        requirements_txt_path = tmp_path.joinpath("requirements.txt")
        assert requirements_txt_path.is_file()
        assert requirements_txt_path.read_text() == textwrap.dedent(
            """\
            # generated from manifests external_dependencies
            pydantic>=2
            requests
            xlrd
            """
        )
