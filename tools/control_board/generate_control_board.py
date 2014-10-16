#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Script to generate travis/coverage status for a subset of org on
github.
"""

import github3
import getpass
import re
import argparse
import sys


travis_badge = (
    "[![Build Status]"
    "(https://travis-ci.org/{ORG}/{REPO}.svg?branch={BRANCH})]"
    "(https://travis-ci.org/{ORG}/{REPO})"
)
coverage_badge = (
    "[![Coverage Status]"
    "(https://coveralls.io/repos/{ORG}/{REPO}/badge.png?branch={BRANCH})]"
    "(https://coveralls.io/r/{ORG}/{REPO}?branch={BRANCH})"
)


def get_badges(org, repo_name, branch_name):
    return (travis_badge + coverage_badge).format(
        ORG=org, REPO=repo_name, BRANCH=branch_name
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-O', '--org', help='Github org')
    parser.add_argument('-u', '--user', help='Github username')
    parser.add_argument('-o', '--out', help='Output file, stdout if null')
    parser.add_argument('-x', '--exclude', default=set(), nargs='+',
                        help='Branch names to ignore')
    return parser.parse_args()


def generate_badge_file(username, password, org_name, exclude):
    out = "# %s repo quality control board\n\n" % org_name
    gh = github3.login(username, password)
    all_branch_names = set()
    repo_branch_names = dict()
    org = gh.organization(org_name)
    for repo in org.iter_repos():
        branch_names = set(branch.name for branch in repo.iter_branches())
        repo_branch_names[repo.name] = branch_names
        all_branch_names.update(branch_names)
    all_branch_names -= exclude
    all_branch_names = sorted(all_branch_names)
    line = "repo | " + " | ".join(all_branch_names)
    out += line + "\n" + re.sub("[^|]", "-", line) + "\n"
    for repo in sorted(repo_branch_names):
        branch_name_list = set(repo_branch_names[repo])
        if not branch_name_list.intersection(all_branch_names):
            continue
        line = repo + " | " + " | ".join(
            get_badges(org_name, repo, branch)
            if branch in branch_name_list else ""
            for branch in all_branch_names
        )
        out += line + "\n"
    return out


def main():
    args = parse_args()
    org_name = args.org or raw_input('Org to scan: ')
    username = args.user or raw_input('Github username: ')
    exclude = set(args.exclude)
    password = getpass.getpass()
    out = generate_badge_file(username, password, org_name, exclude)
    f = open(args.out, 'w') if args.out else sys.stdout
    f.write(out)
    f.close()


if __name__ == '__main__':
    main()
