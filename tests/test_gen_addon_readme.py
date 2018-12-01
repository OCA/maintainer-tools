# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV

import shutil
import subprocess
import sys

import pathlib
import pytest


@pytest.fixture
def addons_dir(tmp_path):
    here = pathlib.Path(__file__).parent
    addons_dir = tmp_path / "addons"
    shutil.copytree(here / "data" / "readme_tests", addons_dir)
    yield addons_dir


def _assert_expected(addons_dir, suffix):
    for addon_dir in addons_dir.iterdir():
        if not addon_dir.is_dir():
            continue
        actual = addon_dir / "README.rst"
        expected = addon_dir / ("README.expected-" + suffix)
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
    subprocess.check_call(cmd, cwd=addons_dir)
    _assert_expected(addons_dir, "oca")
