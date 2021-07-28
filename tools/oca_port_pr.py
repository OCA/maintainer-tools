# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# Copyright 2021 Camptocamp SA
"""Tool helping to port missing commits between two branches for an addon.

If a Pull Request exists for a missing commit, it will be ported with all its
commits if they were not yet (fully) ported.

To get an output of eligible commits to port:

    $ oca-port-pr --from 13.0 --to 14.0 --addon shopfloor_packing_info --verbose

To create new branches and push them to your fork, use the `--fork` option:

    $ oca-port-pr --from 13.0 --to 14.0 --addon shopfloor_packing_info --fork sebalix

The tool will also ask you if you also want to open draft pull requests against
the upstream repository.
"""
from collections import abc, defaultdict
import contextlib
import os
import re
import shutil
import tempfile

import click
import git
import requests


GITHUB_API_URL = "https://api.github.com"

AUTHOR_EMAILS_TO_SKIP = [
    "transbot@odoo-community.org",
    "oca-git-bot@odoo-community.org",
    "oca+oca-travis@odoo-community.org",
]

SUMMARY_TERMS_TO_SKIP = [
    "Translated using Weblate",
    "Added translation using Weblate",
]

MANIFEST_FILES = {
    "__openerp__.py",
    "__manifest__.py",
}


@click.command()
@click.option("--org-name", default="OCA",
              help="Organization name, eg. OCA.")
@click.option("--repo-name", help="Repository name, eg. server-tools.")
@click.option("--addon", required=True, help="Module name to port.")
@click.option("--from", "from_branch", required=True, help="Odoo series. eg 13.0.")
@click.option("--to", "to_branch", required=True, help="Odoo series. eg 14.0.")
@click.option("--upstream", default="origin", required=True,
              help="Git remote from which source and target branches are fetched.")
@click.option("--fork",
              help="Git remote on which branches containing ported commits are pushed.")
@click.option("--verbose", is_flag=True,
              help="List the commits of Pull Requests.")
def main(
        org_name, repo_name, addon, from_branch, to_branch, upstream, fork, verbose
        ):
    """List Pull Requests to port from `from_branch` to `to_branch`.

    The PRs are found from source branch commits that do not exist in the
    target branch.

    If the option `--fork` is set, one branche per PR will be created with
    missing commits and will be pushed to the indicated fork on GitHub.
    """
    repo = git.Repo()
    if repo.is_dirty():
        raise click.ClickException("changes not committed detected in this repository.")
    if fork and fork not in repo.remotes:
        raise click.ClickException(f"No remote '{fork}' in the current repository.")
    repo_name = repo_name or os.path.basename(os.getcwd())
    _fetch_branches(repo, upstream, from_branch, to_branch)
    diff = BranchesDiff(
        repo, org_name, repo_name, addon,
        f"{upstream}/{from_branch}", f"{upstream}/{to_branch}"
    )
    diff.print_diff(verbose)
    if fork:
        print()
        _port_pull_requests(
            diff, org_name, repo_name, upstream, from_branch, to_branch, fork
        )


class Commit():
    # Attributes used to check equality between commits.
    # We do not want to use the SHA here as it changed from one branch to another
    # when a commit is ported (obviously).
    base_equality_attrs = (
        "author_name",
        "author_email",
        "authored_datetime",
        "summary",
        "message",
    )
    other_equality_attrs = (
        "paths",
    )
    eq_strict = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _get_equality_attrs(self):
        return (
            [attr for attr in self.base_equality_attrs if hasattr(self, attr)]
            +
            [
                attr for attr in self.other_equality_attrs
                if self.__class__.eq_strict and hasattr(self, attr)
            ]
        )

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
                    # 'git am' without '--keep' option removes text in '[]'
                    # brackets generating false-positive when comparing commits.
                    clean_text(getattr(self, attr)) == clean_text(getattr(other, attr))
                    if attr in ("summary", "message")
                    else getattr(self, attr) == getattr(other, attr)
                )
                for attr in self._get_equality_attrs()
            ]
            return all(checks)

    def __repr__(self):
        attrs = ", ".join([f"{k}={v}" for k, v in self.__dict__.items()])
        return f"{self.__class__.__name__}({attrs})"

    @property
    def addon_created(self):
        for diff in self.diffs:
            if any(manifest in diff.b_path for manifest in MANIFEST_FILES):
                return True
        return False


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
    """Clean text by removing patterns like '[13.0]' or '[IMP]'."""
    return re.sub(r"\[.*\]", "", text).strip()


def _fetch_branches(repo, remote, *branches):
    """Fetch `branches` of the given repository.

    The way a branch is spelled defines the remote from which it is fetched:
    - '14.0' => fetch from 'origin'
    - 'OCA/14.0' => fetch from 'OCA'
    """
    for branch in branches:
        remote_url = repo.remotes[remote].url
        print(f"Fetch {remote}/{branch} from {remote_url}")
        repo.remotes[remote].fetch(branch)


def _new_commit_from_local_repo_data(commit):
    """Create a new Commit instance from local repository data."""
    files = {f for f in set(commit.stats.files.keys()) if "=>" not in f}
    if commit.parents:
        diffs = commit.diff(commit.parents[0], R=True)
    else:
        diffs = commit.diff(git.NULL_TREE)
    return Commit(
        author_name=commit.author.name,
        author_email=commit.author.email,
        authored_datetime=commit.authored_datetime.replace(tzinfo=None).isoformat(),
        summary=commit.summary,
        message=commit.message,
        hexsha=commit.hexsha,
        committed_datetime=commit.committed_datetime.replace(tzinfo=None),
        parents=[parent.hexsha for parent in commit.parents],
        files=files,
        paths={f.split("/", maxsplit=1)[0] for f in files},
        diffs=diffs,
    )


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


def _get_branch_commits(repo, branch, path="."):
    """Get commits from the local repository `repo` for the given `branch`.

    An optional `path` parameter can be set to limit commits to a given folder.
    This function also filters out undesirable commits (merge or translation
    commits...).

    Return two data structures:
        - a list of Commit objects `[Commit, ...]`
        - a dict of Commits objects grouped by SHA `{SHA: Commit, ...}`
    """
    commits = repo.iter_commits(branch, paths=path)
    commits_list = []
    commits_by_sha = {}
    for commit in commits:
        com = _new_commit_from_local_repo_data(commit)
        if _skip_commit(com):
            continue
        commits_list.append(com)
        commits_by_sha[commit.hexsha] = com
    return commits_list, commits_by_sha


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
    def __init__(self, repo, org_name, repo_name, path, from_branch, to_branch):
        self.repo = repo
        self.org_name = org_name
        self.repo_name = repo_name
        self.path = path
        self.from_branch, self.to_branch = from_branch, to_branch
        self.from_branch_path_commits, _ = _get_branch_commits(
            repo, self.from_branch, path
        )
        self.from_branch_all_commits, _ = _get_branch_commits(repo, self.from_branch)
        self.to_branch_path_commits, _ = _get_branch_commits(repo, self.to_branch, path)
        self.to_branch_all_commits, _ = _get_branch_commits(repo, self.to_branch)
        self.commits_diff = self.get_commits_diff()

    def print_diff(self, verbose=False):
        lines_to_print = ["", ""]
        counter = 0
        for pr in self.commits_diff:
            counter += 1
            if pr.number:
                lines_to_print.append(
                    f"- PR #{pr.number} ({pr.url or 'w/o PR'}) {pr.title}:"
                )
            else:
                lines_to_print.append("- w/o PR:")
            lines_to_print.append(f"\tBy {pr.author}, merged at {pr.merged_at}")
            if verbose:
                lines_to_print.append(f"\t=> Updates: {list(pr.paths)}")
            lines_to_print.append(f"\t=> Not ported: {pr.paths_not_ported}")
            lines_to_print.append(
                f"\t=> {len(self.commits_diff[pr])} commit(s) not (fully) ported"
            )
            if verbose:
                for commit in self.commits_diff[pr]:
                    lines_to_print.append(
                        f"\t\t{commit.hexsha} {commit.summary}"
                    )
        lines_to_print.insert(
            1,
            f"{counter} pull request(s) related to '{self.path}' to port from "
            f"{self.from_branch} to {self.to_branch}"
        )
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
                    f"repos/{self.org_name}/{self.repo_name}"
                    f"/commits/{commit.hexsha}/pulls"
                )
                full_repo_name = f"{self.org_name}/{self.repo_name}"
                gh_commit_pull = [
                    data for data in gh_commit_pulls
                    if data["base"]["repo"]["full_name"] == full_repo_name
                ]
                # Fake PR for commits w/o related PR
                pr = PullRequest(*[""] * 6, tuple(), tuple())
                if gh_commit_pull:
                    pr = _new_pull_request_from_github_data(gh_commit_pull[0])
                    # Get all commits of the related PR as they could update
                    # others addons than the one the user is interested in
                    gh_pr_commits = _request_github(
                        f"repos/{self.org_name}/{self.repo_name}"
                        f"/pulls/{pr.number}/commits"
                    )
                    for gh_pr_commit in gh_pr_commits:
                        raw_commit = self.repo.commit(gh_pr_commit["sha"])
                        pr_commit = _new_commit_from_local_repo_data(raw_commit)
                        pr.paths.update(pr_commit.paths)
                        if _skip_commit(pr_commit):
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


def _port_pull_requests(
        diff, org_name, repo_name, upstream, from_branch, to_branch, fork
        ):
    """Open new Pull Requests (if it doesn't exist) on the GitHub repository."""
    repo = diff.repo
    base_ref = diff.to_branch   # e.g. 'origin/14.0'
    for pr, commits in diff.commits_diff.items():
        pr_branch = _port_pr_in_branch(
            repo, pr, commits, upstream, from_branch, to_branch, base_ref,
        )
        if pr_branch:
            is_pushed = _push_branch_to_remote(repo, pr_branch, fork)
            if not is_pushed:
                continue
            pr_data = _prepare_pull_request_data(
                org_name, repo_name, from_branch, to_branch, pr, pr_branch, fork
            )
            pr_url = _search_pull_request(org_name, repo_name, pr_data)
            if pr_url:
                print(f"\tExisting PR has been refreshed => {pr_url}")
            else:
                _create_pull_request(org_name, repo_name, to_branch, pr_branch, pr_data)


def _port_pr_in_branch(repo, pr, commits, upstream, from_branch, to_branch, base_ref):
    """Cherry-pick commits of a Pull Request in a new branch."""
    if pr.number:
        print(f"- Port PR #{pr.number} ({pr.url}) {pr.title}...")
    else:
        print("- Port commits w/o PR...")
    # Ensure to not start to work from a working branch
    remote_to_branch = f"{upstream}/{to_branch}"
    if to_branch in repo.heads:
        repo.heads[to_branch].checkout()
    else:
        repo.git.checkout("-b", to_branch, remote_to_branch)
    # Create a local branch based on last `{remote}/{to_branch}`
    branch_name = (
        f"oca-port-pr-{pr.number}-from-{from_branch}-to-{to_branch}"
    )
    if branch_name in repo.heads:
        confirm = (
            f"\tBranch {branch_name} already exists, recreate it? "
            "\n\t(WARNING: you will lose the existing branch)"
        )
        if not click.confirm(confirm):
            return branch_name
        repo.delete_head(branch_name, "-f")
    elif not click.confirm("\tPort it?"):
        return
    print(f"\tCreate branch {branch_name}...")
    branch = repo.create_head(branch_name, base_ref)
    branch.checkout()
    # Get commits from this branch (in case it's the 2nd time we run this)
    branch_commits = _get_branch_commits(repo, branch_name)

    def accept_diff(repo, branch_name, diff, diff_path):
        if diff.change_type == "A":
            # Accept creation of files in existing addons
            if diff_path in repo.commit(branch_name).tree:
                return True
        elif diff.change_type == "M":
            # Accept updates on existing files
            if os.path.exists(diff.b_path):
                return True
        elif diff.change_type == "D":
            # Accept deletion of existing files
            if os.path.exists(diff.b_path):
                return True
        return False

    # Cherry-pick commits of the source PR
    for commit in commits:
        print(f"\t\tApply {commit.hexsha} {commit.summary}...")
        # Skip it if it has already been included in the dev branch
        if commit in branch_commits:
            continue
        # Port only relevant diffs/paths from the commit
        #   - no need to port a diff related to an addon/file that does not
        #     exist on the target branch
        #   - unless the diff is related to the creation of the addon
        paths_to_port = set(pr.paths_not_ported)
        if not commit.addon_created:
            for diff in commit.diffs:
                diff_path = diff.b_path.split("/", maxsplit=1)[0]
                if diff_path not in paths_to_port:
                    # Nothing to port from this diff, already ported
                    continue
                # Accept creation of addons
                if not accept_diff(repo, branch_name, diff, diff_path):
                    paths_to_port.remove(diff_path)
                    print(
                        f"\t\t\tWARNING: diff related to '{diff_path}' has been "
                        f"skipped (relates to unported file/module)"
                    )
        if not commit.paths & paths_to_port:
            print("\t\t\tWARNING: Nothing to port from this commit, skipping")
            continue
        try:
            patches_dir = tempfile.mkdtemp()
            repo.git.format_patch(
                "--keep-subject", "-o", patches_dir, "-1", commit.hexsha,
                "--", *paths_to_port
            )
            patches = [
                os.path.join(patches_dir, f) for f in sorted(os.listdir(patches_dir))
            ]
            repo.git.am("-3", "--keep", *patches)
            shutil.rmtree(patches_dir)
        except git.exc.GitCommandError as exc:
            print(f"\n{exc}\n")
            # High chance a conflict occurs, ask the user to resolve it
            if not click.confirm(
                    "A conflict occurs, please resolve it and "
                    "confirm to continue the process (y) or skip this commit (N)."
                    ):
                repo.git.am("--abort")
                continue
    return branch_name


def _push_branch_to_remote(repo, branch, remote):
    """Force push the local branch to remote."""
    if click.confirm(f"\tPush branch '{branch}' to remote '{remote}'?"):
        repo.git.push(remote, branch, "--force-with-lease")
        return True


def _prepare_pull_request_data(
        org_name, repo_name, from_branch, to_branch, pr, pr_branch, fork
        ):
    # Clean PR title by removing patterns like '[13.0]' or '[IMP]'
    pr_title = clean_text(pr.title)
    title = f"[{from_branch}->{to_branch}][oca-port-pr-#{pr.number}] {pr_title}"
    return {
        "draft": True,
        "title": title,
        # FIXME assume that the fork remote has the same name than the owner
        "head": f"{fork}:{pr_branch}",
        "base": to_branch,
        "body": f"Port of #{pr.number} from {from_branch} to {to_branch}.",
    }


def _search_pull_request(org_name, repo_name, pr_data):
    params = {
        "q": f"is:pr repo:{org_name}/{repo_name} state:open {pr_data['title']} in:title"
    }
    response = _request_github("search/issues", params=params)
    if response["items"]:
        return response["items"][0]["html_url"]


def _create_pull_request(org_name, repo_name, to_branch, pr_branch, pr_data):
    if click.confirm(
            f"\tCreate a draft PR from '{pr_branch}' to '{to_branch}' "
            f"against {org_name}/{repo_name}?"
            ):
        response = _request_github(
            f"repos/{org_name}/{repo_name}/pulls",
            method="post",
            json=pr_data
        )
        pr_url = response["html_url"]
        print(f"\t\tPR created => {pr_url}")
        return pr_url


if __name__ == '__main__':
    main()
