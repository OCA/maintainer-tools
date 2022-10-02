from tools.config import is_main_branch


def test_is_main_branch():
    assert is_main_branch("6.1")
    assert is_main_branch("8.0")
    assert is_main_branch("10.0")
    assert is_main_branch("16.0")
    assert is_main_branch("17.0")
    assert not is_main_branch("14.0-ocabot-thing")
    assert not is_main_branch("14.1")
