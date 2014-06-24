# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from pkg_resources import resource_string
import yaml
from .github_login import login


def main():
    login()
    projects = resource_string(__name__, 'branches.yaml')
    projects = yaml.load(projects)
    for project in projects['projects']:
        gh_url = project['github']
        for source, target in project['branches']:
            print(source, '→', target, 'on', gh_url)


if __name__ == '__main__':
    main()
