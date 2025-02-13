# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2018 ACSONE SA/NV
import sys
import textwrap

import pytest
import toml
from click.testing import CliRunner

from tools.oca_towncrier import _make_issue_format, _prepare_config, oca_towncrier


def test_make_issue_format():
    assert (
        _make_issue_format("OCA", "repo", "rst")
        == "`#{issue} <https://github.com/OCA/repo/issues/{issue}>`_"
    )
    assert (
        _make_issue_format("OCA", "repo", "md")
        == "[#{issue}](https://github.com/OCA/repo/issues/{issue})"
    )


def test_prepare_config(tmp_path):
    with _prepare_config(str(tmp_path), "OCA", "repo") as (fn, result_file):
        with open(fn) as f:
            pyproject = toml.load(f)
            assert set(pyproject["tool"]["towncrier"].keys()) == {
                "template",
                "underlines",
                "issue_format",
                "directory",
                "filename",
            }


def test_oca_towncrier(tmp_path):
    addon_path = tmp_path / "addon_a"
    readme_path = addon_path / "readme"
    history_path = readme_path / "HISTORY.rst"
    news_path = readme_path / "newsfragments"
    news_path.mkdir(parents=True)
    (news_path / "50.bugfix").write_text("Bugfix description.")
    runner = CliRunner()
    runner.invoke(
        oca_towncrier,
        [
            "--addon-dir",
            str(addon_path),
            "--version",
            "14.0.1.0.1",
            "--date",
            "2021-12-31",
            "--repo",
            "therepo",
        ],
    )
    assert history_path.exists()
    assert history_path.read_text() == textwrap.dedent(
        """\
            14.0.1.0.1 (2021-12-31)
            ~~~~~~~~~~~~~~~~~~~~~~~

            **Bugfixes**

            - Bugfix description. (`#50 <https://github.com/OCA/therepo/issues/50>`_)
        """
    )


@pytest.mark.skipif(
    sys.version_info < (3, 8), reason="MarkDow support requires python3.8 or higher"
)
def test_oca_towncrier_md(tmp_path):
    addon_path = tmp_path / "addon_a"
    readme_path = addon_path / "readme"
    history_path = readme_path / "HISTORY.md"
    news_path = readme_path / "newsfragments"
    news_path.mkdir(parents=True)
    (news_path / "50.bugfix").write_text("Bugfix description.")
    (readme_path / "description.md").write_text("Some description")
    runner = CliRunner()
    runner.invoke(
        oca_towncrier,
        [
            "--addon-dir",
            str(addon_path),
            "--version",
            "14.0.1.0.1",
            "--date",
            "2021-12-31",
            "--repo",
            "therepo",
        ],
    )
    assert history_path.exists()
    assert history_path.read_text() == textwrap.dedent(
        """\
            ## 14.0.1.0.1 (2021-12-31)

            ### Bugfixes

            - Bugfix description. ([#50](https://github.com/OCA/therepo/issues/50))
        """
    )
