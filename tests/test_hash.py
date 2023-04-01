from tools._hash import dir_hash


def test_hash(tmp_path):
    def populate(top):
        top.joinpath("a").write_text("a")
        top.joinpath("b").touch()
        top.joinpath("d").mkdir()
        top.joinpath("d", "c").write_text("c")

    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    populate(dir1)
    digest = dir_hash(dir1)
    assert digest.startswith("sha256:")
    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    populate(dir2)
    assert dir_hash(dir2) == digest
    # add empty file
    dir2.joinpath("e").touch()
    assert dir_hash(dir2) != digest
    # modify file
    dir1.joinpath("a").write_text("b")
    assert dir_hash(dir1) != digest
