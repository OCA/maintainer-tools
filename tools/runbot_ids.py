# Copyright (c) 2018 ACSONE SA/NV
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
import re

import requests

REPO_ID_LINE_RE = re.compile(r"^(?P<repo_id>[0-9]+)\|github\.com/OCA/(?P<repo_name>.*)")

REPOS_WITH_IDS_URL = (
    "https://raw.githubusercontent.com/OCA/maintainer-tools/"
    "master/tools/repos_with_ids.txt"
)


def get_runbot_ids():
    """return a dictionary of runbot id by project name"""
    res = {}
    repos_with_ids = requests.get(REPOS_WITH_IDS_URL).text
    for repo_id_line in repos_with_ids.split("\n"):
        repo_id_line = repo_id_line.strip()
        if not repo_id_line:
            continue
        mo = REPO_ID_LINE_RE.match(repo_id_line)
        if not mo:
            print("warning: invalid repos_with_ids line:", repo_id_line)
            continue
        repo_id = mo.group("repo_id")
        repo_name = mo.group("repo_name")
        res[repo_name] = repo_id
    return res
