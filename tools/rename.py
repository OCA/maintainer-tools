# -*- encoding: utf-8 -*-
'''
This script simply will walk over a repository and look for all the README.md
files and will rename them as README.rst files.

usage:
    python rename.py path-to-repository
    python rename.py  <-- if you are in the repository folder.
'''
import os
from subprocess import call
import sys


def rename(path='.'):
    for base, dirs, files in os.walk(path):
        if 'README.md' in files:
            md = os.path.join(base, 'README.md')
            rst = os.path.join(base, 'README.rst')
            call(['git', 'mv', md, rst])
            call(['git', 'commit', '-m',
                  '"[MIG] %s Renaming md '
                  'files to rst."' % (base.split('/')[0])])

if __name__=='__main__':
    rename(sys.argv[1])
