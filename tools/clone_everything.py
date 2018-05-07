#!/usr/bin/env python

import argparse
import subprocess

from oca_projects import OCA_REPOSITORY_NAMES, url
import os


def clone(organization_remotes=None,
          remove_old_repos=False):
    for project in OCA_REPOSITORY_NAMES:
        cmd = ['git', 'clone', '--quiet', url(project), project]
        try:
            subprocess.check_call(cmd)
        except Exception:
            cmd = ['git',
                   '--git-dir=' + os.path.join(project, '.git'),
                   'fetch', '--all']
            subprocess.call(cmd)
        if organization_remotes:
            for organization_remote in organization_remotes.split(','):
                cmd = ['git', '--git-dir=' + os.path.join(project, '.git'),
                       'remote', 'add', organization_remote,
                       url(project, org_name=organization_remote)]
                subprocess.call(cmd)

                cmd = ['git', '--git-dir=' + os.path.join(project, '.git'),
                       'fetch', organization_remote]
                subprocess.call(cmd)
    if remove_old_repos:
        for d in os.listdir('.'):
            if d not in OCA_REPOSITORY_NAMES and \
                    os.path.isdir(d) and \
                    os.path.isdir(os.path.join(d, '.git')):
                subprocess.check_call(['rm', '-fr', d])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--organization-remotes", dest="org_remotes",
                        help="Specify additional remote to add"
                        " (separated by commas).\n"
                        "This is used after of clone, add organization"
                        " remote into git branch cloned",
                        nargs=1, default=None)
    parser.add_argument("--remove-old-repos", action='store_true',
                        help="Remove all git repositories in the current"
                        " directory that are not OCA repositories anymore."
                        " THIS IS DANGEROUS: make sure"
                        " you run this command in a directory reserved"
                        " for the purpose of running this script as all"
                        " other subdirectories will be erased permanently. "
                        " This option is useful to cope with repository"
                        " renames.")
    args = parser.parse_args()
    org_remotes = args.org_remotes and args.org_remotes[0] or None
    clone(organization_remotes=org_remotes,
          remove_old_repos=args.remove_old_repos)


if __name__ == '__main__':
    main()
