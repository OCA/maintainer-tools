#!/usr/bin/python
# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
Create res.users for OCA members with a github login filled in.

This enables adding them to project teams in the OCA instance.
"""
from __future__ import absolute_import, print_function

import xmlrpclib

from .odoo_login import login, get_parser


def main():
    parser = get_parser(with_help=True)
    args = parser.parse_args()
    client = login(args.username, args.store)
    ResPartner = client.ResPartner
    ResUsers = client.ResUsers
    ResGroups = client.ResGroups
    grp_project_user = ResGroups.get("project.group_project_user")
    members_with_gh = ResPartner.search(
        [("x_github_login", "!=", False), ("user_ids", "=", False)]
    )
    if not members_with_gh:
        return
    for partner in ResPartner.browse(members_with_gh):
        try:
            user = ResUsers.create(
                {
                    "partner_id": partner.id,
                    "login": partner.email,
                    "groups_id": [(4, grp_project_user.id, 0)],
                }
            )
        except xmlrpclib.Fault:
            print(
                "unable to create user for partner %r (%s) : "
                "probable email address issue" % (partner.x_github_login, partner.id)
            )
        else:
            print("created user %r for partner %r" % (user, partner.x_github_login))


if __name__ == "__main__":
    main()
