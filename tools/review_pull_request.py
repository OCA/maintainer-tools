#!/usr/bin/env python
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import argparse
from collections import Counter
from datetime import datetime, timedelta

from github_login import login

from oca_projects import OCA_USERNAME, OCA_REPOSITORY_NAMES

contributions_cache = None


def get_contribution_counts():
    global contributions_cache

    if contributions_cache is not None:
        return contributions_cache

    github = login()
    contributions_cache = Counter()

    for repository_name in OCA_REPOSITORY_NAMES:
        repository = github.repository(OCA_USERNAME, repository_name)
        for user in repository.contributors():
            contributions_cache[user.id] += user.contributions_count

    return contributions_cache


def tag_new_pull_requests(repository_name, dry_run=False):
    github = login()
    repository = github.repository(OCA_USERNAME, repository_name)
    contributions = get_contribution_counts()

    for pull_request in repository.pull_requests():
        if contributions[pull_request.user.id] < 3:
            if dry_run:
                print('Pull request "{}" ({}) made by new contributor'.format(
                    pull_request.title,
                    pull_request.html_url
                ))
            else:
                pull_request.issue().add_labels('new contributor')


def tag_all_new_pull_requests(dry_run=False):
    for repository_name in OCA_REPOSITORY_NAMES:
        tag_new_pull_requests(repository_name, dry_run=dry_run)


def close_abandoned_pull_requests(repository_name, dry_run=False):
    github = login()
    repository = github.repository(OCA_USERNAME, repository_name)

    for pull_request in repository.pull_requests():
        full_pull_request = repository.pull_request(pull_request.number)

        now = datetime.now(pull_request.created_at.tzinfo)
        pr_is_old = now - pull_request.created_at > timedelta(days=31 * 6)

        if pr_is_old and full_pull_request.comments_count == 0:
            if dry_run:
                print('Pull request "{}" ({}) abandoned'.format(
                    pull_request.title,
                    pull_request.html_url
                ))
            else:
                pull_request.create_comment("Please re-open if necessary")
                pull_request.close()


def close_all_abandoned_pull_requests(dry_run=False):
    for repository_name in OCA_REPOSITORY_NAMES:
        close_abandoned_pull_requests(repository_name, dry_run=dry_run)


def tag_ready_pull_requests(repository_name, dry_run=False):
    github = login()
    repository = github.repository(OCA_USERNAME, repository_name)

    for pull_request in repository.pull_requests():
        full_pull_request = repository.pull_request(pull_request.number)

        has_enough_reviews = sum(
            1
            for review in pull_request.reviews()
            if review.state == 'APPROVED'
        ) >= 2

        now = datetime.now(pull_request.created_at.tzinfo)
        pr_is_old_enough = now - pull_request.created_at > timedelta(days=5)

        if (
            has_enough_reviews and
            pr_is_old_enough and
            full_pull_request.mergeable
        ):
            if dry_run:
                print('Pull request "{}" ({}) ready to merge'.format(
                    pull_request.title,
                    pull_request.html_url
                ))
            else:
                pull_request.issue().add_labels('merge ready')
                pull_request.create_comment("Ready to merge")


def tag_all_ready_pull_requests(dry_run=False):
    for repository_name in OCA_REPOSITORY_NAMES:
        tag_ready_pull_requests(repository_name, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tag-new-pull-requests",
        help="Tag open pull requests made by new contributors in the given "
             "repositories.\n"
             "Contributors are considered new if they have fewer than 3 "
             "commits in the master branches of all OCA repositories.",
        nargs="+",
        default=(),
        metavar="repository-name"
    )
    parser.add_argument(
        "--tag-all-new-pull-requests",
        help="Tag open pull requests made by new contributors in all "
             "repositories.",
        action="store_true"
    )
    parser.add_argument(
        "--close-abandoned-pull-requests",
        help="Close abandoned pull requests in the given repositories.\n"
             "Pull requests are considered abandoned if they have no "
             "comments, and are over 6 months old",
        nargs="+",
        default=(),
        metavar="repository-name"
    )
    parser.add_argument(
        "--close-all-abandoned-pull-requests",
        help="Close abandoned pull requests in all repositories.",
        action="store_true"
    )
    parser.add_argument(
        "--tag-ready-pull-requests",
        help="Tag open pull requests that are ready to merge in the given "
             "repositories.\n"
             "Pull requests are considered ready to merge with two approvals, "
             "green CI, and have been open at least 5 days",
        nargs="+",
        default=(),
        metavar="repository-name"
    )
    parser.add_argument(
        "--tag-all-ready-pull-requests",
        help="Tag open pull requests that are ready to merge in all "
             "repositories.",
        action="store_true"
    )
    parser.add_argument(
        "--dry-run",
        help="Print the actions that this command would run, "
             "instead of applying them.",
        action="store_true"
    )
    args = parser.parse_args()

    for repository_name in args.tag_new_pull_requests:
        tag_new_pull_requests(repository_name, dry_run=args.dry_run)

    if args.tag_all_new_pull_requests:
        tag_all_new_pull_requests(dry_run=args.dry_run)

    for repository_name in args.close_abandoned_pull_requests:
        close_abandoned_pull_requests(repository_name, dry_run=args.dry_run)

    if args.close_all_abandoned_pull_requests:
        close_all_abandoned_pull_requests(dry_run=args.dry_run)

    for repository_name in args.tag_ready_pull_requests:
        tag_ready_pull_requests(repository_name, dry_run=args.dry_run)

    if args.tag_all_ready_pull_requests:
        tag_all_ready_pull_requests(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
