# Copyright 2023 ACSONE SA/NV.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import hashlib
import os


def _walk(*args, relative_to):
    for arg in args:
        if os.path.isfile(arg):
            reldir = os.path.relpath(os.path.dirname(arg), relative_to)
            if reldir == ".":
                reldir = ""
            yield os.path.join(reldir, os.path.basename(arg))
        elif os.path.isdir(arg):
            for dirpath, dirnames, filenames in os.walk(arg):
                dirnames.sort()
                reldir = os.path.relpath(dirpath, relative_to)
                if reldir == ".":
                    reldir = ""
                for filename in sorted(filenames):
                    if filename.startswith("."):
                        continue
                    yield os.path.join(reldir, filename)
        else:
            raise ValueError("Not a file or directory: %r" % arg)


def hash(*args, relative_to):
    """Compute a sha256 digest of file contents."""
    m = hashlib.sha256()
    for filepath in _walk(*args, relative_to=relative_to):
        # hash filename so empty files influence the hash
        m.update(filepath.encode("utf-8"))
        # hash file content
        with open(os.path.join(relative_to, filepath), "rb") as f:
            m.update(f.read())
    return m.name + ":" + m.hexdigest()
