# Copyright 2018 ACSONE SA/NV.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import hashlib
import os


def _walk(top):
    for dirpath, dirnames, filenames in os.walk(top):
        dirnames.sort()
        reldir = os.path.relpath(dirpath, top)
        if reldir == ".":
            reldir = ""
        for filename in sorted(filenames):
            filepath = os.path.join(reldir, filename)
            yield filepath


def dir_hash(top):
    """Compute a sha256 digest of file contents."""
    m = hashlib.sha256()
    for filepath in _walk(top):
        # hash filename so empty files influence the hash
        m.update(filepath.encode("utf-8"))
        # hash file content
        with open(os.path.join(top, filepath), "rb") as f:
            m.update(f.read())
    return m.name + ":" + m.hexdigest()
