# Copyright (c) 2018 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import os
import re


REPO_ID_LINE_RE = \
    re.compile(r'^(?P<repo_id>[0-9]+)\|github\.com/OCA/(?P<repo_name>.*)')


def get_runbot_ids():
    """ return a dictionary of runbot id by project name """
    res = {}
    repos_with_ids = \
        os.path.join(os.path.dirname(__file__), 'repos_with_ids.txt')
    for repo_id_line in open(repos_with_ids, "rU"):
        repo_id_line = repo_id_line.strip()
        mo = REPO_ID_LINE_RE.match(repo_id_line)
        if not mo:
            print("warning: invalid repos_with_ids line:", repo_id_line)
            continue
        repo_id = mo.group('repo_id')
        repo_name = mo.group('repo_name')
        res[repo_name] = repo_id
    return res
