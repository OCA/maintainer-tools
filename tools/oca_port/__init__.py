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
import os

import click
import git

from . import misc
from .misc import bcolors as bc
from .migrate_addon import MigrateAddon
from .port_addon_pr import PortAddonPullRequest


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
@click.option("--non-interactive", is_flag=True,
              help="Disable all interactive prompts.")
def main(
        from_branch, to_branch, addon, upstream_org, upstream, repo_name,
        fork, user_org, verbose, non_interactive
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
            f"No remote {bc.FAIL}{fork}{bc.END} in the current repository.\n"
            "To add it:\n"
            f"\t{bc.DIM}$ git remote add {fork} "
            f"git@github.com:{user_org}/{repo_name}.git{bc.END} "
            "# This mode requires an SSH key in the GitHub account\n"
            "Or:\n"
            f"\t{bc.DIM}$ git remote add {fork} "
            f"https://github.com/{user_org}/{repo_name}.git{bc.END} "
            "# This will require to enter user/password each time\n"
            "\nYou can change the GitHub organization with the "
            f"{bc.DIM}--user-org{bc.END} option."
        )
    from_branch = misc.Branch(repo, from_branch, upstream)
    to_branch = misc.Branch(repo, to_branch, upstream)
    storage = misc.InputStorage(repo.working_dir)
    _fetch_branches(from_branch, to_branch, verbose=verbose)
    _check_branches(from_branch, to_branch)
    _check_addon_exists(addon, from_branch, raise_exc=True)
    # Check if the addon (folder) exists on the target branch
    #   - if it already exists, check if some PRs could be ported
    if _check_addon_exists(addon, to_branch):
        PortAddonPullRequest(
            repo, upstream_org, repo_name, from_branch, to_branch,
            fork, user_org, addon, storage, verbose, non_interactive
        ).run()
    #   - if not, migrate it
    else:
        MigrateAddon(
            repo, upstream_org, repo_name, from_branch, to_branch,
            fork, user_org, addon, storage, verbose, non_interactive
        ).run()


def _fetch_branches(*branches, verbose=False):
    """Fetch `branches`."""
    for branch in branches:
        if not branch.remote:
            continue
        remote_url = branch.repo.remotes[branch.remote].url
        if verbose:
            print(
                f"Fetch {bc.BOLD}{branch.ref()}{bc.END} from {remote_url}"
            )
        branch.repo.remotes[branch.remote].fetch(branch.name)


def _check_branches(from_branch, to_branch):
    """Check that all required branches exist in the current repository."""
    # Check if the source branch exists (required)
    if not from_branch.remote:
        raise click.ClickException(
            "No source branch "
            f"{bc.BOLD}{from_branch.ref()}{bc.END} available."
        )
    # Check if the target branch exists (with or w/o remote, allowing to work
    # on a local one)
    if not to_branch.remote and to_branch.name not in to_branch.repo.heads:
        raise click.ClickException(
            f"No target branch {bc.BOLD}{to_branch.name}{bc.END} or "
            f"{bc.BOLD}{to_branch.ref()}{bc.END} available locally."
        )
    return True


def _check_addon_exists(addon, branch, raise_exc=False):
    """Check that `addon` exists on `branch`."""
    branch_addons = [t.path for t in branch.repo.commit(branch.ref()).tree.trees]
    if addon not in branch_addons:
        if not raise_exc:
            return False
        raise click.ClickException(
            f"{bc.FAIL}{addon}{bc.ENDC} does not exist on {branch.ref()}"
        )
    return True


if __name__ == '__main__':
    main()
