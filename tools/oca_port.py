# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# Copyright 2021 Camptocamp SA
"""Tool helping to port an addon or missing commits of an addon from one branch
to another.

If the addon does not exist on the target branch, it will assist the user
in the migration, following the OCA migration guide.

If the addon already exists on the target branch, it will retrieve missing
commits to port. If a Pull Request exists for a missing commit, it will be
ported with all its commits if they were not yet (fully) ported.

To check if an addon could be migrated or to get eligible commits to port:

    $ export GITHUB_TOKEN=<token>
    $ oca-port 13.0 14.0 shopfloor --verbose

To effectively migrate the addon or port its commits, use the `--fork` option:

    $ oca-port 13.0 14.0 shopfloor --fork camptocamp


Migration of addon
------------------

The tool follows the usual OCA migration guide to port commits of an addon,
and will invite the user to fullfill the mentionned steps that can't be
performed automatically.

Port of commits/Pull Requests
-----------------------------

The tool will ask the user if he wants to open draft pull requests against
the upstream repository.

If there are several Pull Requests to port, it will ask the user if he wants to
base the next PR on the previous one, allowing the user to cumulate ported PRs
in one branch and creating a draft PR against the upstream repository with all
of them.
"""
from collections import abc, defaultdict
import contextlib
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse

import click
import git
import requests

from .manifest import MANIFEST_NAMES, get_manifest_path


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = '\033[96m'
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[39m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ENDD = "\033[22m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


GITHUB_API_URL = "https://api.github.com"

AUTHOR_EMAILS_TO_SKIP = [
    "transbot@odoo-community.org",
    "oca-git-bot@odoo-community.org",
    "oca+oca-travis@odoo-community.org",
    "oca-ci@odoo-community.org",
    "shopinvader-git-bot@shopinvader.com",
]

SUMMARY_TERMS_TO_SKIP = [
    "Translated using Weblate",
    "Added translation using Weblate",
]

PR_BRANCH_NAME = (
    "oca-port-pr-{pr_number}-from-{from_branch}-to-{to_branch}"
)


PO_FILE_REGEX = re.compile(r".*i18n/.+\.pot?$")

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
    f"\n{bcolors.BOLD}{bcolors.OKCYAN}The next steps are:{bcolors.END}",
    (
        "\t1) Reduce the number of commits "
        f"('{bcolors.DIM}OCA Transbot...{bcolors.END}'):"
    ),
    f"\t\t=> {bcolors.BOLD}{MIG_MERGE_COMMITS_URL}{bcolors.END}",
    "\t2) Adapt the module to the {to_branch} version:",
    f"\t\t=> {bcolors.BOLD}" "{mig_tasks_url}" f"{bcolors.END}",
    (
        "\t3) On a shell command, type this for uploading the content to GitHub:\n"
        f"{bcolors.DIM}"
        "\t\t$ git add --all\n"
        "\t\t$ git commit -m \"[MIG] {addon}: Migration to {to_branch}\"\n"
        "\t\t$ git push {fork} {mig_branch} --set-upstream"
        f"{bcolors.END}"
    ),
    "\t4) Create the PR against {upstream_org}/{repo_name}:",
    f"\t\t=> {bcolors.BOLD}" "{new_pr_url}" f"{bcolors.END}",
])


@click.command()
@click.argument("from_branch", required=True)
@click.argument("to_branch", required=True)
@click.argument("addon", required=True)
@click.option("--upstream-org", default="OCA", show_default=True,
              help="Upstream organization name.")
@click.option("--upstream", default="origin", show_default=True, required=True,
              help="Git remote from which source and target branches are fetched.")
@click.option("--repo-name", help="Repository name, eg. server-tools.")
@click.option("--fork",
              help="Git remote on which branches containing ported commits are pushed.")
@click.option("--user-org", show_default="--fork", help="User organization name.")
@click.option("--verbose", is_flag=True,
              help="List the commits of Pull Requests.")
def main(
        from_branch, to_branch, addon, upstream_org, upstream, repo_name,
        fork, user_org, verbose
        ):
    """Migrate ADDON from FROM_BRANCH to TO_BRANCH or list Pull Requests to port
    if ADDON already exists on TO_BRANCH.

    The PRs are found from source branch commits that do not exist in the target branch.

    If the option `--fork` is set, one branche per PR will be created with
    missing commits and will be pushed to the indicated fork on GitHub.
    """
    repo = git.Repo()
    if repo.is_dirty():
        raise click.ClickException("changes not committed detected in this repository.")
    repo_name = repo_name or os.path.basename(os.getcwd())
    if not user_org:
        # Assume that the fork remote has the same name than the user organization
        user_org = fork
    if fork and fork not in repo.remotes:
        raise click.ClickException(
            f"No remote {bcolors.FAIL}{fork}{bcolors.END} in the current repository.\n"
            "To add it:\n"
            f"\t{bcolors.DIM}$ git remote add {fork} "
            f"git@github.com:{user_org}/{repo_name}.git{bcolors.END} "
            "# This mode requires an SSH key in the GitHub account\n"
            "Or:\n"
            f"\t{bcolors.DIM}$ git remote add {fork} "
            f"https://github.com/{user_org}/{repo_name}.git{bcolors.END} "
            "# This will require to enter user/password each time\n"
            "\nYou can change the GitHub organization with the "
            f"{bcolors.DIM}--user-org{bcolors.END} option."
        )
    from_branch = Branch(repo, from_branch, upstream)
    to_branch = Branch(repo, to_branch, upstream)
    _fetch_branches(from_branch, to_branch, verbose=verbose)
    _check_branches(from_branch, to_branch)
    _check_addon_exists(addon, from_branch, raise_exc=True)
    # Check if the addon (folder) exists on the target branch
    #   - if it already exists, check if some PRs could be ported
    if _check_addon_exists(addon, to_branch):
        PortAddonPullRequest(
            repo, upstream_org, repo_name, from_branch, to_branch,
            fork, user_org, addon, verbose=verbose
        ).run()
    #   - if not, migrate it
    else:
        MigrateAddon(
            repo, upstream_org, repo_name, from_branch, to_branch,
            fork, user_org, addon, verbose
        ).run()


def _fetch_branches(*branches, verbose=False):
    """Fetch `branches`."""
    for branch in branches:
        if not branch.remote:
            continue
        remote_url = branch.repo.remotes[branch.remote].url
        if verbose:
            print(
                f"Fetch {bcolors.BOLD}{branch.ref()}{bcolors.END} from {remote_url}"
            )
        branch.repo.remotes[branch.remote].fetch(branch.name)


def _check_branches(from_branch, to_branch):
    """Check that all required branches exist in the current repository."""
    # Check if the source branch exists (required)
    if not from_branch.remote:
        raise click.ClickException(
            "No source branch "
            f"{bcolors.BOLD}{from_branch.ref()}{bcolors.END} available."
        )
    # Check if the target branch exists (with or w/o remote, allowing to work
    # on a local one)
    if not to_branch.remote and to_branch.name not in to_branch.repo.heads:
        raise click.ClickException(
            f"No target branch {bcolors.BOLD}{to_branch.name}{bcolors.END} or "
            f"{bcolors.BOLD}{to_branch.ref()}{bcolors.END} available locally."
        )
    return True


def _check_addon_exists(addon, branch, raise_exc=False):
    """Check that `addon` exists on `branch`."""
    branch_addons = [t.path for t in branch.repo.commit(branch.ref()).tree.trees]
    if addon not in branch_addons:
        if not raise_exc:
            return False
        raise click.ClickException(
            f"{bcolors.FAIL}{addon}{bcolors.ENDC} does not exist on {branch.ref()}"
        )
    return True


class PortAddonPullRequest():
    def __init__(
            self, repo, upstream_org, repo_name,
            from_branch, to_branch, fork, user_org, addon, verbose=False,
            create_branch=True, push_branch=True
            ):
        """Port pull requests of `addon`."""
        self.repo = repo
        self.upstream_org = upstream_org
        self.repo_name = repo_name
        self.from_branch = from_branch
        self.to_branch = to_branch
        self.fork = fork
        self.user_org = user_org
        self.addon = addon
        self.verbose = verbose
        self.create_branch = create_branch
        self.push_branch = push_branch

    def run(self):
        print(
            f"{bcolors.BOLD}{self.addon}{bcolors.END} already exists "
            f"on {bcolors.BOLD}{self.to_branch.name}{bcolors.END}, "
            "checking PRs to port..."
        )
        branches_diff = BranchesDiff(
            self.repo, self.upstream_org, self.repo_name, self.addon,
            self.from_branch, self.to_branch
        )
        branches_diff.print_diff(self.verbose)
        if self.fork:
            print()
            self._port_pull_requests(branches_diff)

    def _port_pull_requests(self, branches_diff):
        """Open new Pull Requests (if it doesn't exist) on the GitHub repository."""
        base_ref = branches_diff.to_branch  # e.g. 'origin/14.0'
        previous_pr = previous_pr_branch = None
        processed_prs = []
        last_pr = (
            list(branches_diff.commits_diff.keys())[-1]
            if branches_diff.commits_diff else None
        )
        for pr, commits in branches_diff.commits_diff.items():
            current_commit = self.repo.commit(self.to_branch.name)
            pr_branch, based_on_previous = self._port_pull_request_commits(
                pr, commits, base_ref, previous_pr, previous_pr_branch,
            )
            if pr_branch:
                # Check if commits have been ported
                if self.repo.commit(pr_branch.ref()) == current_commit:
                    print("\tℹ️  Nothing has been ported, skipping")
                    continue
                previous_pr = pr
                previous_pr_branch = pr_branch
                if based_on_previous:
                    processed_prs.append(pr)
                else:
                    processed_prs = [pr]
                if pr == last_pr:
                    print("\t🎉 Last PR processed! 🎉")
                if not self.push_branch:
                    continue
                is_pushed = self._push_branch_to_remote(pr_branch)
                if not is_pushed:
                    continue
                pr_data = self._prepare_pull_request_data(processed_prs, pr_branch)
                pr_url = self._search_pull_request(pr_data["base"], pr_data["title"])
                if pr_url:
                    print(f"\tExisting PR has been refreshed => {pr_url}")
                else:
                    self._create_pull_request(pr_branch, pr_data, processed_prs)

    def _port_pull_request_commits(
            self, pr, commits, base_ref, previous_pr=None, previous_pr_branch=None,
            ):
        """Port commits of a Pull Request in a new branch."""
        if pr.number:
            print(
                f"- {bcolors.BOLD}{bcolors.OKCYAN}Port PR #{pr.number}{bcolors.END} "
                f"({pr.url}) {bcolors.OKCYAN}{pr.title}{bcolors.ENDC}..."
            )
        else:
            print(f"- {bcolors.BOLD}{bcolors.OKCYAN}Port commits w/o PR{bcolors.END}...")
        based_on_previous = False
        # Ensure to not start to work from a working branch
        if self.to_branch.name in self.repo.heads:
            self.repo.heads[self.to_branch.name].checkout()
        else:
            self.repo.git.checkout(
                "--no-track", "-b", self.to_branch.name, self.to_branch.ref()
            )
        if not click.confirm("\tPort it?" if pr.number else "\tPort them?"):
            return None, based_on_previous
        # Create a local branch based on upstream
        if self.create_branch:
            branch_name = PR_BRANCH_NAME.format(
                pr_number=pr.number,
                from_branch=self.from_branch.name,
                to_branch=self.to_branch.name,
            )
            if branch_name in self.repo.heads:
                # If the local branch already exists, ask the user if he wants to recreate it
                # + check if this existing branch is based on the previous PR branch
                if previous_pr_branch:
                    based_on_previous = self.repo.is_ancestor(previous_pr_branch, branch_name)
                confirm = (
                    f"\tBranch {bcolors.BOLD}{branch_name}{bcolors.END} already exists, "
                    "recreate it?\n\t(⚠️  you will lose the existing branch)"
                )
                if not click.confirm(confirm):
                    return Branch(self.repo, branch_name), based_on_previous
                self.repo.delete_head(branch_name, "-f")
            if previous_pr and click.confirm(
                    f"\tUse the previous {bcolors.BOLD}PR #{previous_pr.number}{bcolors.END} "
                    "branch as base?"
                    ):
                base_ref = previous_pr_branch
                based_on_previous = True
            print(
                f"\tCreate branch {bcolors.BOLD}{branch_name}{bcolors.END} from {base_ref}..."
            )
            self.repo.git.checkout("--no-track", "-b", branch_name, base_ref.ref())
        else:
            branch_name = self.to_branch.name

        # Cherry-pick commits of the source PR
        for commit in commits:
            print(
                f"\t\tApply {bcolors.OKCYAN}{commit.hexsha[:8]}{bcolors.ENDC} "
                f"{commit.summary}..."
            )
            # Port only relevant diffs/paths from the commit
            paths_to_port = set(commit.paths_to_port)
            for diff in commit.diffs:
                skip, message = self._skip_diff(commit, diff)
                if skip:
                    if message:
                        print(f"\t\t\t{message}")
                    if diff.a_path in paths_to_port:
                        paths_to_port.remove(diff.a_path)
                    if diff.b_path in paths_to_port:
                        paths_to_port.remove(diff.b_path)
                    continue
            if not paths_to_port:
                print(
                    "\t\t\tℹ️  Nothing to port from this commit, skipping"
                )
                continue
            try:
                patches_dir = tempfile.mkdtemp()
                self.repo.git.format_patch(
                    "--keep-subject", "-o", patches_dir, "-1", commit.hexsha,
                    "--", *paths_to_port
                )
                patches = [
                    os.path.join(patches_dir, f) for f in sorted(os.listdir(patches_dir))
                ]
                self.repo.git.am("-3", "--keep", *patches)
                shutil.rmtree(patches_dir)
            except git.exc.GitCommandError as exc:
                print(f"{bcolors.FAIL}ERROR:{bcolors.ENDC}\n{exc}\n")
                # High chance a conflict occurs, ask the user to resolve it
                if not click.confirm(
                        "⚠️  A conflict occurs, please resolve it and "
                        "confirm to continue the process (y) or skip this commit (N)."
                        ):
                    self.repo.git.am("--abort")
                    continue
        return Branch(self.repo, branch_name), based_on_previous

    @staticmethod
    def _skip_diff(commit, diff):
        """Check if a commit diff should be skipped or not.

        A skipped diff won't have its file path ported through 'git format-path'.

        Return a tuple `(bool, message)` if the diff is skipped.
        """
        if diff.deleted_file:
            if diff.a_path not in commit.paths_to_port:
                return True, ""
        if diff.b_path not in commit.paths_to_port:
            return True, ""
        if diff.renamed:
            return False, ""
        diff_path = diff.b_path.split("/", maxsplit=1)[0]
        # Do not accept diff on unported addons
        if not get_manifest_path(diff_path) and diff_path not in commit.addons_created:
            return (
                True,
                (
                    f"{bcolors.WARNING}SKIP diff "
                    f"{bcolors.BOLD}{diff.change_type} {diff.b_path}{bcolors.END}: "
                    "relates to an unported addon"
                )
            )
        if diff.change_type in ("M", "D"):
            # Do not accept update and deletion on non-existing files
            if not os.path.exists(diff.b_path):
                return (
                    True,
                    (
                        f"SKIP: '{diff.change_type} {diff.b_path}' diff relates "
                        "to a non-existing file"
                    )
                )
        return False, ""

    def _push_branch_to_remote(self, branch):
        """Force push the local branch to remote fork."""
        confirm = (
            f"\tPush branch '{bcolors.BOLD}{branch.name}{bcolors.END}' "
            f"to remote '{bcolors.BOLD}{self.fork}{bcolors.END}'?"
        )
        if click.confirm(confirm):
            branch.repo.git.push(self.fork, branch.name, "--force-with-lease")
            branch.remote = self.fork
            return True

    def _prepare_pull_request_data(self, processed_prs, pr_branch):
        if len(processed_prs) > 1:
            title = (
                f"[{self.to_branch.name}][FW] {self.addon}: multiple ports from {self.from_branch.name}"
            )
            lines = [f"- #{pr.number}" for pr in processed_prs]
            body = "\n".join(
                [f"Port of the following PRs from {self.from_branch.name} to {self.to_branch.name}:"]
                + lines
            )
        else:
            pr = processed_prs[0]
            title = f"[{self.to_branch.name}][FW] {pr.title}"
            body = f"Port of #{pr.number} from {self.from_branch.name} to {self.to_branch.name}."
        return {
            "draft": True,
            "title": title,
            "head": f"{self.user_org}:{pr_branch.name}",
            "base": self.to_branch.name,
            "body": body,
        }

    def _search_pull_request(self, base_branch, title):
        params = {
            "q": (
                f"is:pr repo:{self.upstream_org}/{self.repo_name} base:{base_branch} "
                f"state:open {title} in:title"
            ),
        }
        response = _request_github("search/issues", params=params)
        if response["items"]:
            return response["items"][0]["html_url"]

    def _create_pull_request(self, pr_branch, pr_data, processed_prs):
        if len(processed_prs) > 1:
            print(
                "\tPR(s) ported locally:",
                ", ".join(
                    [f"{bcolors.OKCYAN}#{pr.number}{bcolors.ENDC}" for pr in processed_prs]
                )
            )
        if click.confirm(
                f"\tCreate a draft PR from '{bcolors.BOLD}{pr_branch.name}{bcolors.END}' "
                f"to '{bcolors.BOLD}{self.to_branch.name}{bcolors.END}' "
                f"against {bcolors.BOLD}{self.upstream_org}/{self.repo_name}{bcolors.END}?"
                ):
            response = _request_github(
                f"repos/{self.upstream_org}/{self.repo_name}/pulls",
                method="post",
                json=pr_data
            )
            pr_url = response["html_url"]
            print(
                f"\t\t{bcolors.BOLD}{bcolors.OKCYAN}PR created =>"
                f"{bcolors.ENDC} {pr_url}{bcolors.END}"
            )
            return pr_url


class MigrateAddon():
    def __init__(
            self, repo, upstream_org, repo_name, from_branch, to_branch,
            fork, user_org, addon, verbose
            ):
        self.repo = repo
        self.upstream_org = upstream_org
        self.repo_name = repo_name
        self.from_branch = from_branch
        self.to_branch = to_branch
        self.fork = fork
        self.user_org = user_org
        self.addon = addon
        self.mig_branch = Branch(
            repo, MIG_BRANCH_NAME.format(branch=to_branch.name[:4], addon=addon)
        )
        self.verbose = verbose

    def run(self):
        confirm = (
            f"Migrate {bcolors.BOLD}{self.addon}{bcolors.END} "
            f"from {bcolors.BOLD}{self.from_branch.name}{bcolors.END} "
            f"to {bcolors.BOLD}{self.to_branch.name}{bcolors.END}?"
        )
        if not click.confirm(confirm):
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
            self.addon, verbose=self.verbose, create_branch=False, push_branch=False
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
                f"Branch {bcolors.BOLD}{self.mig_branch.name}{bcolors.END} already exists, "
                "recreate it?\n(⚠️  you will lose the existing branch)"
            )
            if click.confirm(confirm):
                self.repo.delete_head(self.mig_branch.name, "-f")
            else:
                create_branch = False
        if create_branch:
            # Create branch
            print(
                f"\tCreate branch {bcolors.BOLD}{self.mig_branch.name}{bcolors.END} "
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
            f"\t\tCommits history of {bcolors.BOLD}{self.addon}{bcolors.END} "
            f"has been migrated."
        )

    def _run_pre_commit(self):
        # Run pre-commit
        print(
            f"\tRun {bcolors.BOLD}pre-commit{bcolors.END} and commit changes if any..."
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


class Branch():
    def __init__(self, repo, name, remote=None):
        self.repo = repo
        self.name = name
        self.remote = None
        if remote:
            if repo.git.ls_remote("--heads", remote, name):
                self.remote = remote

    def ref(self):
        ref = self.name
        if self.remote:
            ref = f"{self.remote}/{self.name}"
        return ref


class Commit():
    # Attributes used to check equality between commits.
    # We do not want to use the SHA here as it changed from one branch to another
    # when a commit is ported (obviously).
    base_equality_attrs = (
        "author_name",
        "author_email",
        "authored_datetime",
        "message",
    )
    other_equality_attrs = (
        "paths",
    )
    eq_strict = True

    def __init__(self, commit):
        """Initializes a new Commit instance from a GitPython Commit object."""
        self.raw_commit = commit
        self.author_name = commit.author.name
        self.author_email = commit.author.email
        self.authored_datetime = commit.authored_datetime.replace(
            tzinfo=None
        ).isoformat()
        self.summary = commit.summary
        self.message = commit.message
        self.hexsha = commit.hexsha
        self.committed_datetime = commit.committed_datetime.replace(tzinfo=None)
        self.parents = [parent.hexsha for parent in commit.parents]
        self.files = {f for f in set(commit.stats.files.keys()) if "=>" not in f}
        self.paths = {f.split("/", maxsplit=1)[0] for f in self.files}
        self.ported_commits = []

    def _get_equality_attrs(self):
        return (
            [attr for attr in self.base_equality_attrs if hasattr(self, attr)]
            +
            [
                attr for attr in self.other_equality_attrs
                if self.__class__.eq_strict and hasattr(self, attr)
            ]
        )

    def _lazy_eq_message(self, other):
        """Compare commit messages."""
        # If the subject has been put on two lines, 'git-am' won't preserve it
        # if '--keep-cr' option is not set, this generates false-positive.
        # Replace all carriage returns and double spaces by one space character
        # when performing the comparison.
        self_value = self.message.replace("\n", " ").replace("  ", " ")
        other_value = other.message.replace("\n", " ").replace("  ", " ")
        # 'git am' without '--keep' option removes text in '[]' brackets
        # generating false-positive.
        return clean_text(self_value) == clean_text(other_value)

    def __eq__(self, other):
        """Consider a commit equal to another if some of its keys are the same."""
        if not isinstance(other, Commit):
            return super().__eq__(other)
        if self.__class__.eq_strict:
            return all(
                [
                    getattr(self, attr) == getattr(other, attr)
                    for attr in self._get_equality_attrs()
                ]
            )
        else:
            checks = [
                (
                    self._lazy_eq_message(other)
                    if attr == "message"
                    else getattr(self, attr) == getattr(other, attr)
                )
                for attr in self._get_equality_attrs()
            ]
            return all(checks)

    def __repr__(self):
        attrs = ", ".join([f"{k}={v}" for k, v in self.__dict__.items()])
        return f"{self.__class__.__name__}({attrs})"

    @property
    def addons_created(self):
        """Returns the list of addons created by this commit."""
        addons = set()
        for diff in self.diffs:
            if (
                    any(manifest in diff.b_path for manifest in MANIFEST_NAMES)
                    and diff.change_type == "A"
                    ):
                addons.add(diff.b_path.split("/", maxsplit=1)[0])
        return addons

    @property
    def paths_to_port(self):
        """Return the list of file paths to port."""
        current_paths = {
            diff.a_path for diff in self.diffs
            if self._keep_diff_path(diff, diff.a_path)
        }.union(
            {
                diff.b_path for diff in self.diffs
                if self._keep_diff_path(diff, diff.b_path)
            }
        )
        ported_paths = set()
        for ported_commit in self.ported_commits:
            for diff in ported_commit.diffs:
                ported_paths.add(diff.a_path)
                ported_paths.add(diff.b_path)
        return current_paths - ported_paths

    def _keep_diff_path(self, diff, path):
        """Check if a file path should be ported."""
        # Ignore 'setup' files
        if path.startswith("setup"):
            return False
        # Ignore changes on po/pot files
        if PO_FILE_REGEX.match(path):
            return False
        return True

    @property
    def diffs(self):
        if self.raw_commit.parents:
            return self.raw_commit.diff(self.raw_commit.parents[0], R=True)
        return self.raw_commit.diff(git.NULL_TREE)


class PullRequest(abc.Hashable):
    eq_attrs = ("number", "url", "author", "title", "body", "merged_at")

    def __init__(
            self, number, url, author, title, body, merged_at,
            paths=None, ported_paths=None
            ):
        self.number = number
        self.url = url
        self.author = author
        self.title = title
        self.body = body
        self.merged_at = merged_at
        self.paths = set(paths) if paths else set()
        self.ported_paths = set(ported_paths) if ported_paths else set()

    def __eq__(self, other):
        if not isinstance(other, PullRequest):
            return super().__eq__(other)
        return all(
            [
                getattr(self, attr) == getattr(other, attr)
                for attr in self.__class__.eq_attrs
            ]
        )

    def __hash__(self):
        attr_values = tuple(getattr(self, attr) for attr in self.eq_attrs)
        return hash(attr_values)

    @property
    def paths_not_ported(self):
        return list(self.paths - self.ported_paths)


@contextlib.contextmanager
def no_strict_commit_equality():
    try:
        Commit.eq_strict = False
        yield
    finally:
        Commit.eq_strict = True


def clean_text(text):
    """Clean text by removing patterns like '13.0', '[13.0]' or '[IMP]'."""
    return re.sub(r"\[.*\]|\d+\.\d+", "", text).strip()


def _request_github(url, method="get", params=None, json=None):
    """Request GitHub API."""
    headers = {"Accept": "application/vnd.github.groot-preview+json"}
    if os.environ.get("GITHUB_TOKEN"):
        token = os.environ.get("GITHUB_TOKEN")
        headers.update({"Authorization": f"token {token}"})
    full_url = "/".join([GITHUB_API_URL, url])
    kwargs = {"headers": headers}
    if json:
        kwargs.update(json=json)
    if params:
        kwargs.update(params=params)
    response = getattr(requests, method)(full_url, **kwargs)
    if not response.ok:
        raise RuntimeError(response.text)
    return response.json()


class BranchesDiff():
    """Helper to compare easily commits (and related PRs) between two branches."""
    def __init__(self, repo, upstream_org, repo_name, path, from_branch, to_branch):
        self.repo = repo
        self.upstream_org = upstream_org
        self.repo_name = repo_name
        self.path = path
        self.from_branch, self.to_branch = from_branch, to_branch
        self.from_branch_path_commits, _ = self._get_branch_commits(
            self.from_branch.ref(), path
        )
        self.from_branch_all_commits, _ = self._get_branch_commits(
            self.from_branch.ref()
        )
        self.to_branch_path_commits, _ = self._get_branch_commits(
            self.to_branch.ref(), self.path
        )
        self.to_branch_all_commits, _ = self._get_branch_commits(self.to_branch.ref())
        self.commits_diff = self.get_commits_diff()

    def _get_branch_commits(self, branch, path="."):
        """Get commits from the local repository for the given `branch`.

        An optional `path` parameter can be set to limit commits to a given folder.
        This function also filters out undesirable commits (merge or translation
        commits...).

        Return two data structures:
            - a list of Commit objects `[Commit, ...]`
            - a dict of Commits objects grouped by SHA `{SHA: Commit, ...}`
        """
        commits = self.repo.iter_commits(branch, paths=path)
        commits_list = []
        commits_by_sha = {}
        for commit in commits:
            com = Commit(commit)
            if self._skip_commit(com):
                continue
            commits_list.append(com)
            commits_by_sha[commit.hexsha] = com
        return commits_list, commits_by_sha

    @staticmethod
    def _skip_commit(commit):
        """Check if a commit should be skipped or not.

        Merge or translations commits are skipped for instance.
        """
        return (
            # Skip merge commit
            len(commit.parents) > 1
            or commit.author_email in AUTHOR_EMAILS_TO_SKIP
            or any([term in commit.summary for term in SUMMARY_TERMS_TO_SKIP])
        )

    def print_diff(self, verbose=False):
        lines_to_print = [""]
        fake_pr = None
        i = 0
        for i, pr in enumerate(self.commits_diff, 1):
            if pr.number:
                lines_to_print.append(
                    f"{i}) {bcolors.BOLD}{bcolors.OKBLUE}PR #{pr.number}{bcolors.END} "
                    f"({pr.url or 'w/o PR'}) {bcolors.OKBLUE}{pr.title}{bcolors.ENDC}:"
                )
                lines_to_print.append(f"\tBy {pr.author}, merged at {pr.merged_at}")
            else:
                lines_to_print.append(
                    f"{i}) {bcolors.BOLD}{bcolors.OKBLUE}w/o PR{bcolors.END}:"
                )
                fake_pr = pr
            if verbose:
                pr_paths = ", ".join(
                    [f"{bcolors.DIM}{path}{bcolors.ENDD}" for path in pr.paths]
                )
                lines_to_print.append(
                    f"\t=> Updates: {pr_paths}"
                )
            if pr.number:
                pr_paths_not_ported = ", ".join(
                    [
                        f"{bcolors.OKBLUE}{path}{bcolors.ENDC}"
                        for path in pr.paths_not_ported
                    ]
                )
                lines_to_print.append(
                    f"\t=> Not ported: {pr_paths_not_ported}"
                )
            lines_to_print.append(
                f"\t=> {bcolors.BOLD}{bcolors.OKBLUE}{len(self.commits_diff[pr])} "
                f"commit(s){bcolors.END} not (fully) ported"
            )
            if verbose or not pr.number:
                for commit in self.commits_diff[pr]:
                    lines_to_print.append(
                        f"\t\t{bcolors.DIM}{commit.hexsha[:8]} "
                        f"{commit.summary}{bcolors.ENDD}"
                    )
        if fake_pr:
            # We have commits without PR, adapt the message
            i -= 1
            nb_commits = len(self.commits_diff[fake_pr])
            message = (
                f"{bcolors.BOLD}{bcolors.OKBLUE}{i} pull request(s){bcolors.END} "
                f"and {bcolors.BOLD}{bcolors.OKBLUE}{nb_commits} commit(s) w/o "
                f"PR{bcolors.END} related to '{bcolors.OKBLUE}{self.path}"
                f"{bcolors.ENDC}' to port from {self.from_branch.ref()} "
                f"to {self.to_branch.ref()}"
            )
        else:
            message = (
                f"{bcolors.BOLD}{bcolors.OKBLUE}{i} pull request(s){bcolors.END} "
                f"related to '{bcolors.OKBLUE}{self.path}{bcolors.ENDC}' to port from "
                f"{self.from_branch.ref()} to {self.to_branch.ref()}"
            )
        lines_to_print.insert(0, message)
        print("\n".join(lines_to_print))

    def get_commits_diff(self):
        """Returns the commits which do not exist in `to_branch`, grouped by
        their related Pull Request.

        :return: a dict {PullRequest: {Commit: data, ...}, ...}
        """
        commits_by_pr = defaultdict(list)
        for commit in self.from_branch_path_commits:
            if commit in self.to_branch_all_commits:
                continue
            # Get related Pull Request if any
            if any("github.com" in remote.url for remote in self.repo.remotes):
                gh_commit_pulls = _request_github(
                    f"repos/{self.upstream_org}/{self.repo_name}"
                    f"/commits/{commit.hexsha}/pulls"
                )
                full_repo_name = f"{self.upstream_org}/{self.repo_name}"
                gh_commit_pull = [
                    data for data in gh_commit_pulls
                    if data["base"]["repo"]["full_name"] == full_repo_name
                ]
                # Fake PR for commits w/o related PR
                pr = PullRequest(*[""] * 6, tuple(), tuple())
                if gh_commit_pull:
                    pr = self._new_pull_request_from_github_data(gh_commit_pull[0])
                    # Get all commits of the related PR as they could update
                    # others addons than the one the user is interested in
                    gh_pr_commits = _request_github(
                        f"repos/{self.upstream_org}/{self.repo_name}"
                        f"/pulls/{pr.number}/commits"
                    )
                    for gh_pr_commit in gh_pr_commits:
                        raw_commit = self.repo.commit(gh_pr_commit["sha"])
                        pr_commit = Commit(raw_commit)
                        pr.paths.update(pr_commit.paths)
                        if self._skip_commit(pr_commit):
                            continue
                        # Check that this PR commit does not change the current
                        # addon we are interested in, in such case also check
                        # for each updated addons that the commit has already
                        # been ported.
                        # Indeed a commit could have been ported partially
                        # in the past (with git-format-patch), and we now want
                        # to port the remaining chunks.
                        if pr_commit not in self.to_branch_path_commits:
                            paths = set(pr_commit.paths)
                            # A commit could have been ported several times
                            # if it was impacting several addons and the
                            # migration has been done with git-format-patch
                            # on each addon separately
                            to_branch_all_commits = self.to_branch_all_commits[:]
                            skip_pr_commit = False
                            with no_strict_commit_equality():
                                while pr_commit in to_branch_all_commits:
                                    index = to_branch_all_commits.index(pr_commit)
                                    ported_commit = to_branch_all_commits.pop(index)
                                    pr.ported_paths.update(ported_commit.paths)
                                    pr_commit.ported_commits.append(ported_commit)
                                    paths -= ported_commit.paths
                                    if not paths:
                                        # The ported commits have already updated
                                        # the same addons than the original one,
                                        # we can skip it.
                                        skip_pr_commit = True
                            if skip_pr_commit:
                                continue
                        # We want to port commits that were still not ported
                        # for the addon we are interested in.
                        # If the commit has already been included, skip it.
                        if (
                                pr_commit in self.to_branch_path_commits
                                and pr_commit in self.to_branch_all_commits
                        ):
                            continue
                        existing_pr_commits = commits_by_pr.get(pr, [])
                        for existing_pr_commit in existing_pr_commits:
                            if (
                                existing_pr_commit == pr_commit and
                                existing_pr_commit.hexsha == pr_commit.hexsha
                            ):
                                # This PR commit has already been appended, skip
                                break
                        else:
                            commits_by_pr[pr].append(pr_commit)
                # No related PR: add the current commit anyway
                else:
                    commits_by_pr[pr].append(commit)
            else:
                # FIXME log?
                pass
        # Sort PRs on the merge date (better to port them in the right order)
        sorted_commits_by_pr = {}
        for pr in sorted(commits_by_pr, key=lambda pr: pr.merged_at):
            sorted_commits_by_pr[pr] = commits_by_pr[pr]
        return sorted_commits_by_pr

    @staticmethod
    def _new_pull_request_from_github_data(data, paths=None, ported_paths=None):
        """Create a new PullRequest instance from GitHub data."""
        pr_number = data["number"]
        pr_url = data["html_url"]
        pr_author = data["user"].get("login", "")
        pr_title = data["title"]
        pr_body = data["body"]
        pr_merge_at = data["merged_at"]
        return PullRequest(
            number=pr_number,
            url=pr_url,
            author=pr_author,
            title=pr_title,
            body=pr_body,
            merged_at=pr_merge_at,
            paths=paths,
            ported_paths=ported_paths,
        )


if __name__ == '__main__':
    main()
