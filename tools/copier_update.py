"""Run copier update on a branch in all addons repos.
"""
from pathlib import Path
import subprocess
import textwrap
from typing import Optional

import click
import requests

from .gitutils import commit_if_needed
from .oca_projects import BranchNotFoundError, get_repositories, temporary_clone


ORG = "OCA"


def _make_update_dotfiles_branch(branch):
    return f"{branch}-ocabot-update-dotfiles"


def _make_commit_msg(ci_skip: bool) -> str:
    msg = "[IMP] update dotfiles"
    if ci_skip:
        msg += " [ci skip]"
    return msg


def _get_update_dotfiles_open_pr(org: str, repo: str, branch: str) -> Optional[str]:
    r = requests.get(
        f"https://api.github.com/repos"
        f"/{org}/{repo}/pulls"
        f"?base={branch}&head=OCA:{_make_update_dotfiles_branch(branch)}"
    )
    r.raise_for_status()
    prs = r.json()
    if not prs:
        return None
    pr = prs[0]
    if pr["state"] == "open":
        return pr["number"]
    return None


def _make_update_dotfiles_pr(org: str, repo: str, branch: str) -> None:
    subprocess.check_call(
        ["git", "checkout", "-B", _make_update_dotfiles_branch(branch)]
    )
    subprocess.check_call(["git", "add", "."])
    subprocess.check_call(["git", "commit", "-m", _make_commit_msg(ci_skip=False)])
    subprocess.check_call(["git", "push", "-f"])
    if not _get_update_dotfiles_open_pr(org, repo, branch):
        subprocess.check_call(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                f"{org}/{repo}",
                "--base",
                branch,
                "--title",
                f"[{branch}] dotfiles update needs manual intervention",
                "--body",
                textwrap.dedent(
                    """\
                        Dear maintainer,

                        After updating the dotfiles, `pre-commit run -a`
                        fails in a manner that cannot be resolved automatically.

                        Can you please have a look, fix and merge?

                        Thanks,
                    """
                ),
                "--label",
                "help wanted",
            ]
        )


@click.command()
@click.argument("branch")
def main(branch):
    for repo in get_repositories():
        if repo not in ("event",):
            continue
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
                if not Path(".copier-answers.yml").exists():
                    print(f"Skipping {repo} because it has no .copier-answers.yml")
                    continue
                r = subprocess.call(["copier", "-f", "update"])
                if r != 0:
                    print("$" * 10, f"copier update failed on {repo}")
                    continue
                # git add updated files so pre-commit run -a will pick them up
                # (notably newly created .rej files)
                subprocess.check_call(["git", "add", "."])
                # run up to 3 pre-commit passes, in case fixes cause
                for _ in range(3):
                    r = subprocess.call(["pre-commit", "run", "-a"])
                    # git add, in case pre-commit created new files
                    subprocess.check_call(["git", "add", "."])
                    if r == 0:
                        break
                if r != 0:
                    print("$" * 10, f"need manual intervention in {repo}")
                    _make_update_dotfiles_pr(ORG, repo, branch)
                    continue
                if commit_if_needed(["."], _make_commit_msg(ci_skip=True)):
                    subprocess.check_call(["git", "push"])
        except BranchNotFoundError:
            pass
