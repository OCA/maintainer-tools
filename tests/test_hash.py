from tools._hash import hash, _walk

import pytest


def test_hash(tmp_path):
    def populate(top):
        top.joinpath("a").write_text("a")
        top.joinpath("b").touch()
        top.joinpath("d").mkdir()
        top.joinpath("d", "c").write_text("c")

    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    populate(dir1)
    digest = hash(dir1, relative_to=dir1)
    assert digest.startswith("sha256:")
    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    populate(dir2)
    assert hash(dir2, relative_to=dir2) == digest
    # add dotfile (ignored, so no hash change)
    dir2.joinpath("newfragments").mkdir()
    dir2.joinpath("newfragments", ".gitignore").touch()
    assert hash(dir2, relative_to=dir2) == digest
    # add empty file
    dir2.joinpath("e").touch()
    assert hash(dir2, relative_to=dir2) != digest
    # modify file
    dir1.joinpath("a").write_text("b")
    assert hash(dir1, relative_to=dir1) != digest


def test_hash_single_file(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("stuff\n")
    assert (
        hash(f, relative_to=tmp_path)
        == "sha256:8404bbca373449b5db01eeaff06da34b8693b4f44301dab537c814c3bdb42235"
    )


def test_hash_walk(tmp_path):
    tmp_path.joinpath("a").touch()
    tmp_path.joinpath("d").mkdir()
    tmp_path.joinpath("d", "b").touch()
    tmp_path.joinpath("d", "c").touch()
    assert list(_walk(tmp_path / "a", tmp_path / "d", relative_to=tmp_path)) == [
        "a",
        "d/b",
        "d/c",
    ]


def test_hash_not_a_file(tmp_path):
    with pytest.raises(ValueError):
        hash(tmp_path / "a", relative_to=tmp_path)
