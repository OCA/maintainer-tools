"""Create a branch in all addons project."""
from pathlib import Path
import subprocess
from typing import Dict

import click
import yaml
import copier

from .oca_projects import get_repositories, temporary_clone

COPIER_ANSWERS_FILE = ".copier-answers.yml"
COPIER_ANSWERS_TO_CARRY_OVER = ("repo_description", "repo_name")


def _read_prev_branch_answers(prev_branch: str, answers: Dict[str, str]) -> None:
    try:
        subprocess.check_call(["git", "checkout", prev_branch])
    except subprocess.CalledProcessError:
        # likely branch not found
        return
    if not Path(COPIER_ANSWERS_FILE).is_file():
        return
    with open(COPIER_ANSWERS_FILE) as f:
        prev_branch_answers = yaml.load(f, Loader=yaml.SafeLoader)
    for question in COPIER_ANSWERS_TO_CARRY_OVER:
        if question not in prev_branch_answers:
            continue
        answers[question] = prev_branch_answers[question]


@click.command("Create an orphan branch from a 'copier' template")
@click.argument("new_branch")
@click.option(
    "--copier-template",
    default="gh:oca/oca-addons-repo-template",
    show_default=True,
)
@click.option(
    "--copier-template-vcs-ref",
)
@click.option(
    "--repo",
    "repos",
    multiple=True,
)
@click.option(
    "--prev-branch",
    help="Previous branch where to read some copier answers.",
)
def main(new_branch, copier_template, copier_template_vcs_ref, repos, prev_branch):
    for repo in repos or sorted(get_repositories()):
        print("=" * 10, repo, "=" * 10)
        with temporary_clone(repo):
            # check if branch already exists
            if subprocess.check_output(
                ["git", "ls-remote", "--head", "origin", new_branch]
            ):
                print(f"branch {new_branch} already exist in {repo}")
                continue
            # set git user/email
            subprocess.check_call(
                ["git", "config", "user.name", "oca-git-bot"],
            )
            subprocess.check_call(
                ["git", "config", "user.email", "oca-git-bot@odoo-community.org"],
            )
            # read answers from previous branch
            answers = {
                "odoo_version": float(new_branch),
                "repo_slug": repo,
                "repo_name": repo,
                "ci": "GitHub",
            }
            if prev_branch:
                _read_prev_branch_answers(prev_branch, answers)
            # create empty git branch
            subprocess.check_call(["git", "checkout", "--orphan", new_branch])
            subprocess.check_call(["git", "reset", "--hard"])
            # copier
            copier.run_copy(
                src_path=copier_template,
                dst_path=".",
                data=answers,
                defaults=True,
                vcs_ref=copier_template_vcs_ref,
                unsafe=True,
            )
            # pre-commit run -a
            subprocess.check_call(["git", "add", "."])
            subprocess.call(["pre-commit", "run", "-a"])
            # commit and push
            subprocess.check_call(["git", "add", "."])
            subprocess.check_call(
                ["git", "commit", "-m", f"Initialize {new_branch} branch"]
            )
            subprocess.check_call(["pre-commit", "run", "-a"])  # to be sure
            subprocess.check_call(["git", "push", "origin", new_branch])
