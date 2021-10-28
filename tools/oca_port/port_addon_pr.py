# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from collections import defaultdict
import shutil
import tempfile
import os
import sys

import click
import git

from ..manifest import get_manifest_path
from . import misc
from .misc import bcolors as bc

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


class PortAddonPullRequest():
    def __init__(
            self, repo, upstream_org, repo_name,
            from_branch, to_branch, fork, user_org, addon, verbose=False,
            non_interactive=False, create_branch=True, push_branch=True
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
        self.non_interactive = non_interactive
        self.create_branch = create_branch
        self.push_branch = push_branch

    def run(self):
        print(
            f"{bc.BOLD}{self.addon}{bc.END} already exists "
            f"on {bc.BOLD}{self.to_branch.name}{bc.END}, "
            "checking PRs to port..."
        )
        branches_diff = BranchesDiff(
            self.repo, self.upstream_org, self.repo_name, self.addon,
            self.from_branch, self.to_branch
        )
        branches_diff.print_diff(self.verbose)
        if self.non_interactive:
            if branches_diff.commits_diff:
                # Exit with an error code if commits are eligible for (back)porting
                sys.exit(1)
            return
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
                f"- {bc.BOLD}{bc.OKCYAN}Port PR #{pr.number}{bc.END} "
                f"({pr.url}) {bc.OKCYAN}{pr.title}{bc.ENDC}..."
            )
        else:
            print(f"- {bc.BOLD}{bc.OKCYAN}Port commits w/o PR{bc.END}...")
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
                # If the local branch already exists, ask the user if he wants
                # to recreate it + check if this existing branch is based on
                # the previous PR branch
                if previous_pr_branch:
                    based_on_previous = self.repo.is_ancestor(
                        previous_pr_branch, branch_name
                    )
                confirm = (
                    f"\tBranch {bc.BOLD}{branch_name}{bc.END} already exists, "
                    "recreate it?\n\t(⚠️  you will lose the existing branch)"
                )
                if not click.confirm(confirm):
                    return misc.Branch(self.repo, branch_name), based_on_previous
                self.repo.delete_head(branch_name, "-f")
            if previous_pr and click.confirm(
                    f"\tUse the previous {bc.BOLD}PR #{previous_pr.number}{bc.END} "
                    "branch as base?"
                    ):
                base_ref = previous_pr_branch
                based_on_previous = True
            print(
                f"\tCreate branch {bc.BOLD}{branch_name}{bc.END} from {base_ref}..."
            )
            self.repo.git.checkout("--no-track", "-b", branch_name, base_ref.ref())
        else:
            branch_name = self.to_branch.name

        # Cherry-pick commits of the source PR
        for commit in commits:
            print(
                f"\t\tApply {bc.OKCYAN}{commit.hexsha[:8]}{bc.ENDC} "
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
                    os.path.join(patches_dir, f)
                    for f in sorted(os.listdir(patches_dir))
                ]
                self.repo.git.am("-3", "--keep", *patches)
                shutil.rmtree(patches_dir)
            except git.exc.GitCommandError as exc:
                print(f"{bc.FAIL}ERROR:{bc.ENDC}\n{exc}\n")
                # High chance a conflict occurs, ask the user to resolve it
                if not click.confirm(
                        "⚠️  A conflict occurs, please resolve it and "
                        "confirm to continue the process (y) or skip this commit (N)."
                        ):
                    self.repo.git.am("--abort")
                    continue
        return misc.Branch(self.repo, branch_name), based_on_previous

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
                    f"{bc.WARNING}SKIP diff "
                    f"{bc.BOLD}{diff.change_type} {diff.b_path}{bc.END}: "
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
            f"\tPush branch '{bc.BOLD}{branch.name}{bc.END}' "
            f"to remote '{bc.BOLD}{self.fork}{bc.END}'?"
        )
        if click.confirm(confirm):
            branch.repo.git.push(self.fork, branch.name, "--force-with-lease")
            branch.remote = self.fork
            return True

    def _prepare_pull_request_data(self, processed_prs, pr_branch):
        if len(processed_prs) > 1:
            title = (
                f"[{self.to_branch.name}][FW] {self.addon}: multiple ports "
                f"from {self.from_branch.name}"
            )
            lines = [f"- #{pr.number}" for pr in processed_prs]
            body = "\n".join(
                [
                    f"Port of the following PRs from {self.from_branch.name} "
                    f"to {self.to_branch.name}:"
                ]
                + lines
            )
        else:
            pr = processed_prs[0]
            title = f"[{self.to_branch.name}][FW] {pr.title}"
            body = (
                f"Port of #{pr.number} from {self.from_branch.name} "
                f"to {self.to_branch.name}."
            )
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
        response = misc._request_github("search/issues", params=params)
        if response["items"]:
            return response["items"][0]["html_url"]

    def _create_pull_request(self, pr_branch, pr_data, processed_prs):
        if len(processed_prs) > 1:
            print(
                "\tPR(s) ported locally:",
                ", ".join(
                    [f"{bc.OKCYAN}#{pr.number}{bc.ENDC}" for pr in processed_prs]
                )
            )
        if click.confirm(
                f"\tCreate a draft PR from '{bc.BOLD}{pr_branch.name}{bc.END}' "
                f"to '{bc.BOLD}{self.to_branch.name}{bc.END}' "
                f"against {bc.BOLD}{self.upstream_org}/{self.repo_name}{bc.END}?"
                ):
            response = misc._request_github(
                f"repos/{self.upstream_org}/{self.repo_name}/pulls",
                method="post",
                json=pr_data
            )
            pr_url = response["html_url"]
            print(
                f"\t\t{bc.BOLD}{bc.OKCYAN}PR created =>"
                f"{bc.ENDC} {pr_url}{bc.END}"
            )
            return pr_url


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
            com = misc.Commit(commit)
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
                    f"{i}) {bc.BOLD}{bc.OKBLUE}PR #{pr.number}{bc.END} "
                    f"({pr.url or 'w/o PR'}) {bc.OKBLUE}{pr.title}{bc.ENDC}:"
                )
                lines_to_print.append(f"\tBy {pr.author}, merged at {pr.merged_at}")
            else:
                lines_to_print.append(
                    f"{i}) {bc.BOLD}{bc.OKBLUE}w/o PR{bc.END}:"
                )
                fake_pr = pr
            if verbose:
                pr_paths = ", ".join(
                    [f"{bc.DIM}{path}{bc.ENDD}" for path in pr.paths]
                )
                lines_to_print.append(
                    f"\t=> Updates: {pr_paths}"
                )
            if pr.number:
                pr_paths_not_ported = ", ".join(
                    [
                        f"{bc.OKBLUE}{path}{bc.ENDC}"
                        for path in pr.paths_not_ported
                    ]
                )
                lines_to_print.append(
                    f"\t=> Not ported: {pr_paths_not_ported}"
                )
            lines_to_print.append(
                f"\t=> {bc.BOLD}{bc.OKBLUE}{len(self.commits_diff[pr])} "
                f"commit(s){bc.END} not (fully) ported"
            )
            if verbose or not pr.number:
                for commit in self.commits_diff[pr]:
                    lines_to_print.append(
                        f"\t\t{bc.DIM}{commit.hexsha[:8]} "
                        f"{commit.summary}{bc.ENDD}"
                    )
        if fake_pr:
            # We have commits without PR, adapt the message
            i -= 1
            nb_commits = len(self.commits_diff[fake_pr])
            message = (
                f"{bc.BOLD}{bc.OKBLUE}{i} pull request(s){bc.END} "
                f"and {bc.BOLD}{bc.OKBLUE}{nb_commits} commit(s) w/o "
                f"PR{bc.END} related to '{bc.OKBLUE}{self.path}"
                f"{bc.ENDC}' to port from {self.from_branch.ref()} "
                f"to {self.to_branch.ref()}"
            )
        else:
            message = (
                f"{bc.BOLD}{bc.OKBLUE}{i} pull request(s){bc.END} "
                f"related to '{bc.OKBLUE}{self.path}{bc.ENDC}' to port from "
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
                gh_commit_pulls = misc._request_github(
                    f"repos/{self.upstream_org}/{self.repo_name}"
                    f"/commits/{commit.hexsha}/pulls"
                )
                full_repo_name = f"{self.upstream_org}/{self.repo_name}"
                gh_commit_pull = [
                    data for data in gh_commit_pulls
                    if data["base"]["repo"]["full_name"] == full_repo_name
                ]
                # Fake PR for commits w/o related PR
                pr = misc.PullRequest(*[""] * 6, tuple(), tuple())
                if gh_commit_pull:
                    pr = self._new_pull_request_from_github_data(gh_commit_pull[0])
                    # Get all commits of the related PR as they could update
                    # others addons than the one the user is interested in
                    gh_pr_commits = misc._request_github(
                        f"repos/{self.upstream_org}/{self.repo_name}"
                        f"/pulls/{pr.number}/commits"
                    )
                    for gh_pr_commit in gh_pr_commits:
                        raw_commit = self.repo.commit(gh_pr_commit["sha"])
                        pr_commit = misc.Commit(raw_commit)
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
                            with misc.no_strict_commit_equality():
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
        return misc.PullRequest(
            number=pr_number,
            url=pr_url,
            author=pr_author,
            title=pr_title,
            body=pr_body,
            merged_at=pr_merge_at,
            paths=paths,
            ported_paths=ported_paths,
        )
