# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys
from . import github_login
from . import odoo_login


MAINTAINERS_TEAM_ID = 844365
BLACKLIST = [MAINTAINERS_TEAM_ID,
             829420  # 'Owners' team
             ]

def copy_users(odoo):
    gh = github_login.login()

    sys.exit('not implemented')
    org = gh.organization('oca')

    teams = org.iter_teams()
    maintainers_team = next((team for team in teams if
                            team.id == MAINTAINERS_TEAM_ID),
                            None)
    assert maintainers_team, "Maintainers Team not found"

    maintainers = set(maintainers_team.iter_members())

    for team in teams:
        if team.id in BLACKLIST:
            continue
        team_members = set(team.iter_members())
        print("Team {0}".format(team.name))
        missing = maintainers - team_members
        if not missing:
            print("All maintainers are registered")
        for member in missing:
            print("Adding {0}".format(member.login))
            team.add_member(member.login)


def main():
    args = odoo_login.get_args()
    odoo = odoo_login.login(args.username, args.store)
    copy_users(odoo)


if __name__ == '__main__':
    main()
