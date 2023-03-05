# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV

import os
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def addons_dir(tmpdir):
    here = os.path.dirname(__file__)
    addons_dir = str(tmpdir / "addons")
    shutil.copytree(os.path.join(here, "data", "readme_tests"), addons_dir)
    yield addons_dir


def _assert_expected(addons_dir, suffix):
    for addon_dir in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, addon_dir)
        if not os.path.isdir(addon_dir):
            continue
        actual = os.path.join(addon_dir, "README.rst")
        expected = os.path.join(addon_dir, "README.expected-" + suffix)
        with open(actual) as actual_f, open(expected) as expected_f:
            assert actual_f.read() == expected_f.read()


def test_gen_addon_readme_oca(addons_dir):
    cmd = [
        sys.executable,
        "-m",
        "tools.gen_addon_readme",
        "--addons-dir",
        ".",
        "--repo-name",
        "server-tools",
        "--branch",
        "12.0",
    ]
    subprocess.check_call(cmd, cwd=str(addons_dir))
    _assert_expected(addons_dir, "oca")


def test_gen_addon_readme_acme(addons_dir):
    cmd = [
        sys.executable,
        "-m",
        "tools.gen_addon_readme",
        "--addons-dir",
        ".",
        "--repo-name",
        "server-tools",
        "--branch",
        "12.0",
        "--org-name",
        "acme",
    ]
    subprocess.check_call(cmd, cwd=str(addons_dir))
    _assert_expected(addons_dir, "acme")


def test_rst_error(tmp_path):
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    with (addon_dir / "__manifest__.py").open("w") as f:
        f.write("{'name': 'addon'}")
    with (addon_dir / "__init__.py").open("w") as f:
        pass
    readme_dir = addon_dir / "readme"
    readme_dir.mkdir()
    with (readme_dir / "DESCRIPTION.rst").open("w") as f:
        f.write("Some description.")
    with (readme_dir / "USAGE.rst").open("w") as f:
        f.write("Usage\n-----\n\nblah.\n")
    cmd = [
        sys.executable,
        "-m",
        "tools.gen_addon_readme",
        "--addon-dir",
        str(addon_dir),
        "--repo-name",
        "server-tools",
        "--branch",
        "12.0",
    ]
    opts_list = ([], ["--no-gen-html"])
    for opts in opts_list:
        try:
            subprocess.check_output(
                cmd + opts, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as e:
            assert "Title level inconsistent" in e.output
        else:
            assert False, "A rst syntax error should have been detected."
