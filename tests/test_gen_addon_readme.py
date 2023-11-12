# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.gen_addon_readme import (
    get_fragment_format,
    get_fragments_format,
    safe_remove,
    _get_source_digest,
)


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
        expected = os.path.join(addon_dir, "README.expected-" + suffix + ".rst")
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


def test_gen_addon_readme_if_fragments_changed(addons_dir):
    cmd = [
        sys.executable,
        "-m",
        "tools.gen_addon_readme",
        "--addon-dir",
        "addon1",
        "--repo-name",
        "server-tools",
        "--branch",
        "12.0",
    ]
    readme_filename = os.path.join(addons_dir, "addon1", "README.rst")
    assert not os.path.exists(readme_filename)
    subprocess.check_call([*cmd, "--if-fragments-changed"], cwd=str(addons_dir))
    assert os.path.exists(readme_filename)
    # append something to the README file
    with open(readme_filename, "a") as readme_file:
        readme_file.write("trailer")
    # check the file is not regenerated
    subprocess.check_call([*cmd, "--if-fragments-changed"], cwd=str(addons_dir))
    with open(readme_filename) as readme_file:
        assert readme_file.read().endswith("trailer")
    # change something and check the file is regenerated
    with open(os.path.join(addons_dir, "addon1", "readme", "CHUNK.rst"), "w") as f:
        f.write("CHUNK")
    subprocess.check_call([*cmd, "--if-fragments-changed"], cwd=str(addons_dir))
    with open(readme_filename) as readme_file:
        assert not readme_file.read().endswith("trailer")


def test_gen_addon_readme_keep_source_digest(addons_dir):
    cmd = [
        sys.executable,
        "-m",
        "tools.gen_addon_readme",
        "--addon-dir",
        "addon1",
        "--repo-name",
        "server-tools",
        "--branch",
        "12.0",
    ]
    readme_filename = os.path.join(addons_dir, "addon1", "README.rst")
    assert not os.path.exists(readme_filename)
    subprocess.check_call(cmd, cwd=str(addons_dir))
    assert os.path.exists(readme_filename)
    source_digest = _get_source_digest(readme_filename)
    # change something and check the previous source digest is preserved
    chunk_path = Path(addons_dir, "addon1", "readme", "DESCRIPTION.rst")
    with chunk_path.open("a") as f:
        f.write("* CHUNK\n")
    subprocess.check_call([*cmd, "--keep-source-digest"], cwd=str(addons_dir))
    assert _get_source_digest(readme_filename) == source_digest
    # change something again and check the source digest is changed
    with chunk_path.open("a") as f:
        f.write("* CHUNK2\n")
    subprocess.check_call([*cmd], cwd=str(addons_dir))
    assert _get_source_digest(readme_filename) != source_digest


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


def test_get_fragment_format(tmp_path):
    readme_path = tmp_path / "readme"
    readme_path.mkdir()
    readme_path.joinpath("DESCRIPTION.rst").touch()
    assert get_fragment_format(tmp_path, "DESCRIPTION") == ".rst"
    readme_path.joinpath("USAGE.md").touch()
    assert get_fragment_format(tmp_path, "USAGE") == ".md"
    readme_path.joinpath("USAGE.rst").touch()
    with pytest.raises(SystemExit) as e:
        get_fragment_format(tmp_path, "USAGE")
    assert "Both .md and .rst found for USAGE" in str(e)


def test_get_fragments_format_rst(tmp_path):
    readme_path = tmp_path / "readme"
    readme_path.mkdir()
    readme_path.joinpath("DESCRIPTION.rst").touch()
    assert get_fragments_format(tmp_path) == ".rst"
    readme_path.joinpath("USAGE.rst").touch()
    assert get_fragments_format(tmp_path) == ".rst"
    readme_path.joinpath("INSTALL.md").touch()
    with pytest.raises(SystemExit) as e:
        get_fragments_format(tmp_path)
    assert "Both .md and .rst fragments found" in str(e)


def test_safe_ramove(tmp_path):
    file_path = tmp_path / "file"
    file_path.touch()
    safe_remove(file_path)
    assert not file_path.exists()
    safe_remove(file_path)  # removing non-existent file does not raise


def test_get_source_digest(tmp_path):
    readme_path = tmp_path / "README.rst"
    readme_path.write_text("blah\n!! source digest: sha256:abc123\n...")
    assert _get_source_digest(str(readme_path)) == "sha256:abc123"
    readme_path.unlink()
    assert _get_source_digest(str(readme_path)) is None
    readme_path.write_text("!! source digest: ")
    assert _get_source_digest(str(readme_path)) is None
