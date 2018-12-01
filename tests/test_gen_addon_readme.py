# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
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
