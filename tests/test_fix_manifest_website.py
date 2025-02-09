from click.testing import CliRunner

from tools.fix_manifest_website import main


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


def test_fix_specific_manifest_website(tmp_path):
    (tmp_path / "a1").mkdir()
    (tmp_path / "a1" / "__manifest__.py").write_text(
        """{'name': 'a1', 'website': '...'}"""
    )
    (tmp_path / "a2").mkdir()
    manifest_path_a2 = tmp_path / "a2" / "__manifest__.py"
    manifest_path_a2.write_text(
        """{'name': 'a2', "website"   :\n "https://bad.url"}"""
    )
    # Only manifest under a2 directory should be fixed
    result = CliRunner().invoke(
        main, ["--addons-dir", str(tmp_path), "https://new.url", str(manifest_path_a2)]
    )
    assert result.exit_code == 0
    assert (
        tmp_path / "a1" / "__manifest__.py"
    ).read_text() == """{'name': 'a1', 'website': '...'}"""
    manifest_content = """{'name': 'a2', "website"   :\n "https://new.url"}"""
    assert manifest_path_a2.read_text() == manifest_content
