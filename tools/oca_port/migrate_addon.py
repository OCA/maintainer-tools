# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import click
import os
import subprocess
import tempfile
import urllib.parse

from . import misc
from .misc import bcolors as bc
from .port_addon_pr import PortAddonPullRequest

MIG_BRANCH_NAME = (
    "{branch}-mig-{addon}"
)
MIG_MERGE_COMMITS_URL = (
    "https://github.com/OCA/maintainer-tools/wiki/Merge-commits-in-pull-requests"
)
MIG_TASKS_URL = (
    "https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-{branch}"
    "#tasks-to-do-in-the-migration"
)
MIG_NEW_PR_TITLE = "[{to_branch}][MIG] {addon}"
MIG_NEW_PR_URL = (
    "https://github.com/{upstream_org}/{repo_name}/compare/"
    "{to_branch}...{user_org}:{mig_branch}?expand=1&title={title}"
)
MIG_TIPS = "\n".join([
    f"\n{bc.BOLD}{bc.OKCYAN}The next steps are:{bc.END}",
    (
        "\t1) Reduce the number of commits "
        f"('{bc.DIM}OCA Transbot...{bc.END}'):"
    ),
    f"\t\t=> {bc.BOLD}{MIG_MERGE_COMMITS_URL}{bc.END}",
    "\t2) Adapt the module to the {to_branch} version:",
    f"\t\t=> {bc.BOLD}" "{mig_tasks_url}" f"{bc.END}",
    (
        "\t3) On a shell command, type this for uploading the content to GitHub:\n"
        f"{bc.DIM}"
        "\t\t$ git add --all\n"
        "\t\t$ git commit -m \"[MIG] {addon}: Migration to {to_branch}\"\n"
        "\t\t$ git push {fork} {mig_branch} --set-upstream"
        f"{bc.END}"
    ),
    "\t4) Create the PR against {upstream_org}/{repo_name}:",
    f"\t\t=> {bc.BOLD}" "{new_pr_url}" f"{bc.END}",
])


class MigrateAddon():
    def __init__(
            self, repo, upstream_org, repo_name, from_branch, to_branch,
            fork, user_org, addon, storage, verbose=False, non_interactive=False
            ):
        self.repo = repo
        self.upstream_org = upstream_org
        self.repo_name = repo_name
        self.from_branch = from_branch
        self.to_branch = to_branch
        self.fork = fork
        self.user_org = user_org
        self.addon = addon
        self.storage = storage
        self.mig_branch = misc.Branch(
            repo, MIG_BRANCH_NAME.format(branch=to_branch.name[:4], addon=addon)
        )
        self.verbose = verbose
        self.non_interactive = non_interactive

    def run(self):
        if self.storage.is_addon_blacklisted(
                self.from_branch.name, self.to_branch.name, self.addon
                ):
            print(
                f"{bc.DIM}Migration to {self.to_branch.name} for "
                f"{bc.BOLD}{self.addon}{bc.END} {bc.DIM}blacklisted{bc.ENDD}")
            return
        if self.non_interactive:
            # Exit with an error code if the addon is eligible for a migration
            raise SystemExit(1)
        confirm = (
            f"Migrate {bc.BOLD}{self.addon}{bc.END} "
            f"from {bc.BOLD}{self.from_branch.name}{bc.END} "
            f"to {bc.BOLD}{self.to_branch.name}{bc.END}?"
        )
        if not click.confirm(confirm):
            self.storage.blacklist_addon(
                self.from_branch.name, self.to_branch.name,
                self.addon, confirm=True
            )
            return
        # Check if a migration PR already exists
        # TODO
        if not self.fork:
            raise click.UsageError("Please set the '--fork' option")
        if self.repo.untracked_files:
            raise click.ClickException("Untracked files detected, abort")
        self._checkout_base_branch()
        if self._create_mig_branch():
            with tempfile.TemporaryDirectory() as patches_dir:
                self._generate_patches(patches_dir)
                self._apply_patches(patches_dir)
            self._run_pre_commit()
        # Check if the addon has commits that update neighboring addons to
        # make it work properly
        PortAddonPullRequest(
            self.repo, self.upstream_org, self.repo_name,
            self.from_branch, self.mig_branch, self.fork, self.user_org,
            self.addon, self.storage, self.verbose,
            create_branch=False, push_branch=False
        ).run()
        self._print_tips()

    def _checkout_base_branch(self):
        # Ensure to not start to work from a working branch
        if self.to_branch.name in self.repo.heads:
            self.repo.heads[self.to_branch.name].checkout()
        else:
            self.repo.git.checkout(
                "--no-track", "-b", self.to_branch.name, self.to_branch.ref()
            )

    def _create_mig_branch(self):
        create_branch = True
        if self.mig_branch.name in self.repo.heads:
            confirm = (
                f"Branch {bc.BOLD}{self.mig_branch.name}{bc.END} already exists, "
                "recreate it?\n(⚠️  you will lose the existing branch)"
            )
            if click.confirm(confirm):
                self.repo.delete_head(self.mig_branch.name, "-f")
            else:
                create_branch = False
        if create_branch:
            # Create branch
            print(
                f"\tCreate branch {bc.BOLD}{self.mig_branch.name}{bc.END} "
                f"from {self.to_branch.ref()}..."
            )
            self.repo.git.checkout(
                "--no-track", "-b", self.mig_branch.name, self.to_branch.ref()
            )
        return create_branch

    def _generate_patches(self, patches_dir):
        print("\tGenerate patches...")
        self.repo.git.format_patch(
            "--keep-subject", "-o", patches_dir,
            f"{self.to_branch.ref()}..{self.from_branch.ref()}",
            "--", self.addon
        )

    def _apply_patches(self, patches_dir):
        patches = [
            os.path.join(patches_dir, f) for f in sorted(os.listdir(patches_dir))
        ]
        # Apply patches with git-am
        print(f"\tApply {len(patches)} patches...")
        self.repo.git.am("-3", "--keep", *patches)
        print(
            f"\t\tCommits history of {bc.BOLD}{self.addon}{bc.END} "
            f"has been migrated."
        )

    def _run_pre_commit(self):
        # Run pre-commit
        print(
            f"\tRun {bc.BOLD}pre-commit{bc.END} and commit changes if any..."
        )
        # First ensure that 'pre-commit' is initialized for the repository,
        # then run it (without checking the return code on purpose)
        subprocess.check_call("pre-commit install", shell=True)
        subprocess.run("pre-commit run -a", shell=True)
        if self.repo.untracked_files or self.repo.is_dirty():
            self.repo.git.add("-A")
            self.repo.git.commit(
                "-m", f"[IMP] {self.addon}: black, isort, prettier", "--no-verify"
            )

    def _print_tips(self):
        mig_tasks_url = MIG_TASKS_URL.format(branch=self.to_branch.name)
        pr_title_encoded = urllib.parse.quote(
            MIG_NEW_PR_TITLE.format(to_branch=self.to_branch.name[:4], addon=self.addon)
        )
        new_pr_url = MIG_NEW_PR_URL.format(
            upstream_org=self.upstream_org, repo_name=self.repo_name,
            to_branch=self.to_branch.name, user_org=self.user_org,
            mig_branch=self.mig_branch.name, title=pr_title_encoded
        )
        tips = MIG_TIPS.format(
            upstream_org=self.upstream_org, repo_name=self.repo_name,
            addon=self.addon, to_branch=self.to_branch.name, fork=self.fork,
            mig_branch=self.mig_branch.name, mig_tasks_url=mig_tasks_url,
            new_pr_url=new_pr_url
        )
        print(tips)
