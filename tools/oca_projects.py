# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
Data about OCA Projects, with a few helper functions.

OCA_REPOSITORY_NAMES: list of OCA repository names

"""
from __future__ import print_function
from contextlib import contextmanager
import os
import shutil
import subprocess
import tempfile

import appdirs
from .config import NOT_ADDONS, is_main_branch
from .github_login import login

ALL = ["OCA_REPOSITORY_NAMES", "url"]


def get_repositories():
    gh = login()
    all_repos = [
        repo.name for repo in gh.repositories_by("OCA") if repo.name not in NOT_ADDONS
    ]
    return all_repos


def get_repositories_and_branches(repos=(), branches=(), branch_filter=is_main_branch):
    gh = login()
    for repo in gh.repositories_by("OCA"):
        if repos and repo.name not in repos:
            continue
        if repo.name in NOT_ADDONS:
            continue
        for branch in repo.branches():
            if branches and branch.name not in branches:
                continue
            if branch_filter and not branch_filter(branch.name):
                continue
            yield repo.name, branch.name


try:
    OCA_REPOSITORY_NAMES = get_repositories()
except Exception as exc:
    print(exc)
    OCA_REPOSITORY_NAMES = []

OCA_REPOSITORY_NAMES.sort()

_OCA_REPOSITORY_NAMES = set(OCA_REPOSITORY_NAMES)

_URL_MAPPINGS = {
    "git": "git@github.com:%s/%s.git",
    "ssh": "ssh://git@github.com/%s/%s.git",
    "https": "https://github.com/%s/%s.git",
}


def url(project_name, protocol="git", org_name="OCA"):
    """get the URL for an OCA project repository"""
    return _URL_MAPPINGS[protocol] % (org_name, project_name)


class BranchNotFoundError(RuntimeError):
    pass


@contextmanager
def temporary_clone(project_name, branch=None, protocol="git", org_name="OCA"):
    """context manager that clones a git branch and cd to it, with cache"""
    # init cache directory
    cache_dir = appdirs.user_cache_dir("oca-mqt")
    repo_cache_dir = os.path.join(
        cache_dir, "github.com", org_name.lower(), project_name.lower()
    )
    if not os.path.isdir(repo_cache_dir):
        os.makedirs(repo_cache_dir)
        subprocess.check_call(["git", "init", "--bare"], cwd=repo_cache_dir)
    repo_url = url(project_name, protocol, org_name)
    # fetch all branches into cache
    fetch_cmd = [
        "git",
        "fetch",
        "--quiet",
        "--force",
        repo_url,
        "refs/heads/*:refs/heads/*",
    ]
    subprocess.check_call(fetch_cmd, cwd=repo_cache_dir)
    if branch:
        # check if branch exist
        branches = subprocess.check_output(
            ["git", "branch"], universal_newlines=True, cwd=repo_cache_dir
        )
        branches = [b.strip() for b in branches.split()]
        if branch not in branches:
            raise BranchNotFoundError()
    # clone to temp dir, with --reference to cache
    tempdir = tempfile.mkdtemp()
    try:
        clone_cmd = [
            "git",
            "clone",
            "--quiet",
            "--reference",
            repo_cache_dir,
        ]
        if branch:
            clone_cmd += [
                "--branch",
                branch,
            ]
        clone_cmd += [
            "--",
            repo_url,
            tempdir,
        ]
        subprocess.check_call(clone_cmd)
        cwd = os.getcwd()
        os.chdir(tempdir)
        try:
            yield
        finally:
            os.chdir(cwd)
    finally:
        shutil.rmtree(tempdir)
