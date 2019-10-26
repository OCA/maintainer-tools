# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV

import toml

from tools.oca_towncrier import (
    _make_issue_format,
    _preserve_file,
    _prepare_pyproject_toml,
)


def test_make_issue_format():
    assert (
        _make_issue_format("OCA", "repo")
        == "`#{issue} <https://github.com/OCA/repo/issues/{issue}>`_"
    )


def test_preserve_file(tmp_path):
    p = tmp_path / "dummy"
    with _preserve_file(str(p)):
        # path does not exist
        p.write_text(u"abc")
    assert not p.exists()
    p.write_text(u"abc")
    with _preserve_file(str(p)):
        p.write_text(u"xyz")
    assert p.read_text() == u"abc"


def test_prepare_pyproject_toml(tmp_path):
    with _prepare_pyproject_toml(str(tmp_path), "OCA", "repo"):
        with open(str(tmp_path / "pyproject.toml")) as f:
            pyproject = toml.load(f)
            assert set(pyproject["tool"]["towncrier"].keys()) == {
                "template",
                "underlines",
                "title_format",
                "issue_format",
                "directory",
                "filename",
            }
