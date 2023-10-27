import textwrap

from freezegun import freeze_time

from tools.gen_metapackage import main as gen_metapackage

from .utils import dir_changer


def _make_addon(addons_dir, addon_name, installable=True):
    addon_dir = addons_dir / addon_name
    addon_dir.mkdir()
    manifest = {
        "name": addon_name,
        "version": "16.0.1.0.0",
        "installable": installable,
    }
    addon_dir.joinpath("__manifest__.py").write_text(repr(manifest))
    addon_dir.joinpath("__init__.py").touch()


@freeze_time("2023-05-01")
def test_gen_metapackage(tmp_path):
    _make_addon(tmp_path, "addon1")
    _make_addon(tmp_path, "addon2")
    with dir_changer(tmp_path):
        gen_metapackage(["odoo-addons-oca-test-repo"])
        assert (
            tmp_path / "setup" / "_metapackage" / "pyproject.toml"
        ).read_text() == textwrap.dedent(
            """\
            [project]
            name = "odoo-addons-oca-test-repo"
            version = "16.0.20230501.0"
            dependencies = [
                "odoo-addon-addon1>=16.0dev,<16.1dev",
                "odoo-addon-addon2>=16.0dev,<16.1dev",
            ]
            classifiers=[
                "Programming Language :: Python",
                "Framework :: Odoo",
                "Framework :: Odoo :: 16.0",
            ]
            """
        )
        # regenerate with no change
        gen_metapackage(["odoo-addons-oca-test-repo"])
        assert (
            tmp_path / "setup" / "_metapackage" / "pyproject.toml"
        ).read_text() == textwrap.dedent(
            """\
            [project]
            name = "odoo-addons-oca-test-repo"
            version = "16.0.20230501.0"
            dependencies = [
                "odoo-addon-addon1>=16.0dev,<16.1dev",
                "odoo-addon-addon2>=16.0dev,<16.1dev",
            ]
            classifiers=[
                "Programming Language :: Python",
                "Framework :: Odoo",
                "Framework :: Odoo :: 16.0",
            ]
            """
        )
        # regenerate with one more addon, test version was incremented
        _make_addon(tmp_path, "addon3")
        gen_metapackage(["odoo-addons-oca-test-repo"])
        assert (
            tmp_path / "setup" / "_metapackage" / "pyproject.toml"
        ).read_text() == textwrap.dedent(
            """\
            [project]
            name = "odoo-addons-oca-test-repo"
            version = "16.0.20230501.1"
            dependencies = [
                "odoo-addon-addon1>=16.0dev,<16.1dev",
                "odoo-addon-addon2>=16.0dev,<16.1dev",
                "odoo-addon-addon3>=16.0dev,<16.1dev",
            ]
            classifiers=[
                "Programming Language :: Python",
                "Framework :: Odoo",
                "Framework :: Odoo :: 16.0",
            ]
            """
        )
