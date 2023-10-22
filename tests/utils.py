import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def dir_changer(path: Path) -> Iterator[None]:
    """A context manager that changes the current working directory"""
    old_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)
