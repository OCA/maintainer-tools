# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from pkg_resources import resource_string
import yaml
from .github_login import login



def main():
    gh = login()
    branches = resource_string(__name__, 'branches.yaml')
    import pdb; pdb.set_trace()
    org = gh.organization('oca')


if __name__ == '__main__':
    main()
