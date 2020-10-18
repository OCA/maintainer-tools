from tools.fix_manifest_website import main

from click.testing import CliRunner


def test_fix_manifest_website(tmp_path):
    (tmp_path / "a1").mkdir()
    (tmp_path / "a1" / "__manifest__.py").write_text(
        """{'name': 'a1', 'website': '...'}"""
    )
    (tmp_path / "a2").mkdir()
    (tmp_path / "a2" / "__manifest__.py").write_text(
        """{'name': 'a2', "website"   :\n "https://bad.url"}"""
    )
    result = CliRunner().invoke(
        main, ["--addons-dir", str(tmp_path), "https://new.url"]
    )
    assert result.exit_code == 0
    assert (
        tmp_path / "a1" / "__manifest__.py"
    ).read_text() == """{'name': 'a1', 'website': 'https://new.url'}"""
    assert (
        tmp_path / "a2" / "__manifest__.py"
    ).read_text() == """{'name': 'a2', "website"   :\n "https://new.url"}"""
