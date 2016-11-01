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


BRANCHES = ['8.0', '9.0', '10.0']


class FatalError(RuntimeError):
    pass


class NonFatalError(RuntimeError):
    pass


def call(cmd, cwd, raise_on_error=True, raise_fatal_error=True, shell=False):
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
    call(['oca-clone-everything', '--remove-old-repos'], cwd='.')
    for d in sorted(os.listdir('.')):
        if not os.path.isdir(os.path.join(d, '.git')):
            continue
        sys.stderr.write("============> updating addons table in %s\n" % d)
        for branch in BRANCHES:
            try:
                call(['git', 'checkout', branch], cwd=d,
                     raise_fatal_error=False)
                call(['git', 'reset', '--hard', 'origin/' + branch], cwd=d)
                if not os.path.isfile(os.path.join(d, 'README.md')):
                    continue
                call(['oca-gen-addons-table'], cwd=d,
                     raise_fatal_error=False)
                r = call(['git', 'diff', '--exit-code', 'README.md'], cwd=d,
                         raise_on_error=False)
                if r != 0:
                    call(['git', 'commit',
                          '-m', '[UPD] addons table in README.md',
                          'README.md'],
                         cwd=d)
                    call(['git', 'push', 'origin'], cwd=d)
            except NonFatalError:
                logging.exception("Error in %s", d, exc_info=True)


if __name__ == '__main__':
    main()
