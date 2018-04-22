""" Update all addons tables in README.md in all OCA repositories

This script must be run in an initially empty directory.
It will clone all OCA repositories from github, update all the addons tables
and push the changes to github.

CAUTION: it is important that this script is run in a directory
dedicated to this purpose, as it will run oca-clone-everything with
the --remove-old-repos option.
"""
import logging
import os
import subprocess
import sys

from .oca_projects import get_repositories_and_branches, temporary_clone


class FatalError(RuntimeError):
    pass


class NonFatalError(RuntimeError):
    pass


def call(cmd, cwd='.', raise_on_error=True, raise_fatal_error=True,
         shell=False):
    r = subprocess.call(cmd, cwd=cwd, shell=shell)
    if r != 0 and raise_on_error:
        if not shell:
            cmdstr = ' '.join(cmd)
        else:
            cmdstr = cmd
        msg = "Command '%s' returned %d in %s" % (cmdstr, r, cwd)
        if raise_fatal_error:
            raise FatalError(msg)
        else:
            raise NonFatalError(msg)
    return r


def main():
    for repo, branch in get_repositories_and_branches():
        with temporary_clone(repo, branch):
            sys.stderr.write(
                "============> updating addons table in %s@%s\n" %
                (repo, branch)
            )
            try:
                if not os.path.isfile('README.md'):
                    continue
                call(['oca-gen-addons-table'],
                     raise_fatal_error=False)
                r = call(['git', 'diff', '--exit-code', 'README.md'],
                         raise_on_error=False)
                if r != 0:
                    call([
                        'git', 'commit',
                        '-m',
                        '[UPD] addons table in README.md [ci skip]',
                        'README.md',
                    ])
                    call(['git', 'push', 'origin', branch])
            except NonFatalError:
                logging.exception("Non fatal error in %s", repo,
                                  exc_info=True)


if __name__ == '__main__':
    main()
