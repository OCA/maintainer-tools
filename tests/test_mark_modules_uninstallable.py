import textwrap

from tools.manifest import mark_modules_uninstallable, mark_manifest_uninstallable


def test_mark_module_uninstallable(tmp_path):
    (tmp_path / "mod1").mkdir()
    (tmp_path / "mod1" / "__manifest__.py").write_text("""{'name': 'mod1'}""")
    mark_modules_uninstallable(tmp_path)
    assert (tmp_path / "mod1" / "__manifest__.py").read_text() == (
        """{'name': 'mod1',\n    'installable': False,\n}\n"""
    )


def test_mark_module_uninstallable_key_exists(tmp_path):
    (tmp_path / "mod1").mkdir()
    (tmp_path / "mod1" / "__manifest__.py").write_text(
        """{'name': 'mod1', "installable": True}"""
    )
    mark_modules_uninstallable(tmp_path)
    assert (tmp_path / "mod1" / "__manifest__.py").read_text() == (
        """{'name': 'mod1', "installable": False}"""
    )


def test_mark_module_uninstallable_curly_braces(tmp_path):
    assert mark_manifest_uninstallable(
        textwrap.dedent(
            """\
            {
                'name': 'mod1',
                'external_dependencies': {
                    'python': ['some_package'],
                },
                'license': 'AGPL-3',
            }
            """
        )
    ) == textwrap.dedent(
        """\
            {
                'name': 'mod1',
                'external_dependencies': {
                    'python': ['some_package'],
                },
                'license': 'AGPL-3',
                'installable': False,
            }
            """
    )
