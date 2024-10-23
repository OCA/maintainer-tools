"""Apply a patch with git am on a branch in all addons project.
"""
import os
import subprocess

import click

from .oca_projects import BranchNotFoundError, get_repositories, temporary_clone


@click.command()
@click.argument("branch")
@click.argument("patch-file", type=click.Path(exists=True, dir_okay=False))
def main(branch, patch_file):
    patch_file = os.path.abspath(patch_file)
    for repo in get_repositories():
        try:
            with temporary_clone(repo, branch):
                print("=" * 10, repo, "=" * 10)
                # set git user/email
                subprocess.check_call(
                    ["git", "config", "user.name", "oca-git-bot"],
                )
                subprocess.check_call(
                    ["git", "config", "user.email", "oca-git-bot@odoo-community.org"],
                )
                # apply patch and commit
                r = subprocess.call(["git", "am", patch_file])
                if r != 0:
                    continue
                # subprocess.check_call(["pre-commit", "run", "-a"])
                # subprocess.check_call(["git", "commit", "-am", commit_message])
                subprocess.check_call(["git", "push"])
        except BranchNotFoundError:
            pass
