from __future__ import unicode_literals
import subprocess
import textwrap


def test_update_pre_commit_excluded_addons(tmp_path):
    pre_commit = tmp_path / ".pre-commit-config.yaml"
    pre_commit.write_text(
        textwrap.dedent(
            """\
                exclude: |
                  (?x)
                  # NOT INSTALLABLE ADDONS
                  # END NOT INSTALLABLE ADDONS
                  tail_exclude
                default_language_version:
                  python: python3
            """
        )
    )
    addon1 = tmp_path / "addon1"
    addon1.mkdir()
    m1 = addon1 / "__manifest__.py"
    addon2 = tmp_path / "addon2"
    addon2.mkdir()
    m2 = addon2 / "__manifest__.py"
    addon3 = tmp_path / "addon3"
    addon3.mkdir()
    m3 = addon3 / "__manifest__.py"
    # addon1 and addon2 installable
    m1.write_text("{}")
    m2.write_text("{}")
    m3.write_text("{}")
    subprocess.check_call(["oca-update-pre-commit-excluded-addons"], cwd=str(tmp_path))
    assert pre_commit.read_text() == textwrap.dedent(
        """\
            exclude: |
              (?x)
              # NOT INSTALLABLE ADDONS
              # END NOT INSTALLABLE ADDONS
              tail_exclude
            default_language_version:
              python: python3
        """
    )
    # addon1 installable and addon2 not installable
    m2.write_text("{'installable': False}")
    subprocess.check_call(["oca-update-pre-commit-excluded-addons"], cwd=str(tmp_path))
    assert pre_commit.read_text() == textwrap.dedent(
        """\
            exclude: |
              (?x)
              # NOT INSTALLABLE ADDONS
              ^addon2/|
              # END NOT INSTALLABLE ADDONS
              tail_exclude
            default_language_version:
              python: python3
        """
    )
    # addon1 installable and addon2, addon3 not installable
    m3.write_text("{'installable': False}")
    subprocess.check_call(["oca-update-pre-commit-excluded-addons"], cwd=str(tmp_path))
    assert pre_commit.read_text() == textwrap.dedent(
        """\
            exclude: |
              (?x)
              # NOT INSTALLABLE ADDONS
              ^addon2/|
              ^addon3/|
              # END NOT INSTALLABLE ADDONS
              tail_exclude
            default_language_version:
              python: python3
        """
    )


def test_update_pre_commit_excluded_addons_subdir(tmp_path):
    pre_commit = tmp_path / ".pre-commit-config.yaml"
    pre_commit.write_text(
        textwrap.dedent(
            """\
                exclude: |
                  (?x)
                  # NOT INSTALLABLE ADDONS
                  # END NOT INSTALLABLE ADDONS
                  tail_exclude
                default_language_version:
                  python: python3
            """
        )
    )
    addon1 = tmp_path / "odoo" / "addons" / "addon1"
    addon1.mkdir(parents=True)
    m1 = addon1 / "__manifest__.py"
    # addon1 installable
    m1.write_text("{}")
    subprocess.check_call(["oca-update-pre-commit-excluded-addons"], cwd=str(tmp_path))
    assert pre_commit.read_text() == textwrap.dedent(
        """\
            exclude: |
              (?x)
              # NOT INSTALLABLE ADDONS
              # END NOT INSTALLABLE ADDONS
              tail_exclude
            default_language_version:
              python: python3
        """
    )
    # addon1 not installable
    m1.write_text("{'installable': False}")
    subprocess.check_call(
        ["oca-update-pre-commit-excluded-addons", "--addons-dir", "odoo/addons"],
        cwd=str(tmp_path),
    )
    assert pre_commit.read_text() == textwrap.dedent(
        """\
            exclude: |
              (?x)
              # NOT INSTALLABLE ADDONS
              ^odoo/addons/addon1/|
              # END NOT INSTALLABLE ADDONS
              tail_exclude
            default_language_version:
              python: python3
        """
    )


def test_update_coveragerc(tmp_path):
    coveragerc = tmp_path / ".coveragerc"
    coveragerc.write_text(
        textwrap.dedent(
            """\
              [resport]
              omit=
                # NOT INSTALLABLE ADDONS
                # END NOT INSTALLABLE ADDONS
                **/tests/*

              [run]
            """
        )
    )
    addon = tmp_path / "addon1"
    addon.mkdir()
    m = addon / "__manifest__.py"
    # addoninstallable
    m.write_text("{}")
    subprocess.check_call(["oca-update-pre-commit-excluded-addons"], cwd=str(tmp_path))
    assert coveragerc.read_text() == textwrap.dedent(
        """\
          [resport]
          omit=
            # NOT INSTALLABLE ADDONS
            # END NOT INSTALLABLE ADDONS
            **/tests/*

          [run]
      """
    )
    # addon installable
    m.write_text("{'installable': False}")
    subprocess.check_call(["oca-update-pre-commit-excluded-addons"], cwd=str(tmp_path))
    assert coveragerc.read_text() == textwrap.dedent(
        """\
          [resport]
          omit=
            # NOT INSTALLABLE ADDONS
            addon1/*
            # END NOT INSTALLABLE ADDONS
            **/tests/*

          [run]
      """
    )
