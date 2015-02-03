#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Create res.users for OCA members with a github login filled in.

This enables adding them to project teams in the OCA instance.
"""
from __future__ import absolute_import, print_function

from . odoo_login import login, get_parser


def main():
    parser = get_parser(with_help=True)
    args = parser.parse_args()
    client = login(args.username, args.store)
    ResPartner = client.ResPartner
    ResUsers = client.ResUsers
    ResGroups = client.ResGroups
    grp_project_user = ResGroups.get('project.group_project_user')
    members_with_gh = ResPartner.search([('x_github_login', '!=', False),
                                         ('user_ids', '=', False)])
    for partner in ResPartner.browse(members_with_gh):
        user = ResUsers.create({'partner_id': partner.id,
                                'login': partner.email,
                                'group_ids': [(4, grp_project_user.id, 0)],
                                })
        print('created user', user, 'for', partner.x_github_login)

if __name__ == '__main__':
    main()
