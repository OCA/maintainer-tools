# -*- coding: utf-8 -*-
""" OCA Tools package """

__all__ = ['check_contrib',
           'clone_everything',
           'config',
           'copy_branches',
           'copy_maintainers',
           'github_login',
           'oca_projects',
           'oca_sync_users',
           'odoo_login',
           'set_repo_labels',
           'Colors',
           'colors']


class Colors(object):
    # pylint: disable=R0903
    """ Color Enumeration """
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

# pylint: disable=C0103
colors = Colors
